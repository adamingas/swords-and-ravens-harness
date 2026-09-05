from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .agent_store import AgentStore
from .config import Settings
from .database import Database
from .game.client import ConnectionFactory
from .manager import AgentManager, AgentRunner
from .models.openai_agent import OpenAIAgentRunner
from .models.catalog import OpenRouterModelCatalog
from .schemas import AgentCreate, AgentPublic, AutoplayRequest, LobbySetupRequest


def create_app(
    settings: Settings | None = None,
    *,
    runner: AgentRunner | None = None,
    connection_factory: ConnectionFactory | None = None,
) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = Database(settings.resolved_database_path)
        store = AgentStore(database)
        manager = AgentManager(
            store=store,
            runner=runner
            or OpenAIAgentRunner(
                api_key=settings.model_api_key,
                base_url=settings.model_base_url,
                request_timeout_seconds=settings.model_request_timeout_seconds,
            ),
            connection_factory=connection_factory,
        )
        app.state.database = database
        app.state.store = store
        app.state.manager = manager
        app.state.model_catalog = OpenRouterModelCatalog(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_token,
        )
        try:
            yield
        finally:
            await manager.stop_all()
            database.close()

    app = FastAPI(title="Raven Harness", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(KeyError)
    async def key_error_handler(_request: Request, error: KeyError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"error": str(error.args[0])})

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(
        _request: Request, error: RuntimeError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": str(error)})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, error: RequestValidationError
    ) -> JSONResponse:
        first = error.errors()[0] if error.errors() else None
        message = first.get("msg", "Invalid request") if first else "Invalid request"
        location = (
            ".".join(str(part) for part in first.get("loc", [])[1:]) if first else ""
        )
        return JSONResponse(
            status_code=422,
            content={"error": f"{location}: {message}" if location else message},
        )

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return {
            "ok": True,
            "modelApiConfigured": bool(settings.model_api_key),
            "modelProvider": settings.model_provider,
            "openAiConfigured": bool(settings.model_api_key),
            "databasePath": str(settings.resolved_database_path),
        }

    @app.get("/api/agents")
    async def list_agents(request: Request) -> dict[str, Any]:
        return {"agents": [_public(agent) for agent in _manager(request).list_agents()]}

    @app.get("/api/models")
    async def list_models(request: Request) -> dict[str, Any]:
        if settings.model_provider != "OpenRouter":
            return {"provider": settings.model_provider, "models": []}
        return {
            "provider": settings.model_provider,
            "models": await request.app.state.model_catalog.list_cheap_tool_models(),
        }

    @app.post("/api/agents", status_code=201)
    async def create_agent(value: AgentCreate, request: Request) -> dict[str, Any]:
        record = _store(request).create_agent(value)
        agent = AgentPublic.from_record(
            record, _manager(request).get_runtime(record.id)
        )
        return {"agent": _public(agent)}

    @app.get("/api/agents/{agent_id}")
    async def get_agent(agent_id: str, request: Request) -> dict[str, Any]:
        agent = _manager(request).get_agent(agent_id)
        if agent is None:
            raise KeyError("Agent not found")
        return {"agent": _public(agent)}

    @app.delete("/api/agents/{agent_id}", status_code=204)
    async def delete_agent(agent_id: str, request: Request) -> Response:
        manager = _manager(request)
        if manager.get_agent(agent_id) is None:
            raise KeyError("Agent not found")
        await manager.stop(agent_id)
        _store(request).delete_agent(agent_id)
        return Response(status_code=204)

    @app.post("/api/agents/{agent_id}/start")
    async def start_agent(agent_id: str, request: Request) -> dict[str, Any]:
        return {"agent": _public(await _manager(request).start(agent_id))}

    @app.post("/api/agents/{agent_id}/stop")
    async def stop_agent(agent_id: str, request: Request) -> dict[str, Any]:
        agent = await _manager(request).stop(agent_id)
        if agent is None:
            raise KeyError("Agent not found")
        return {"agent": _public(agent)}

    @app.post("/api/agents/{agent_id}/run")
    async def run_agent(agent_id: str, request: Request) -> dict[str, Any]:
        return await _manager(request).run_once(agent_id)

    @app.post("/api/agents/{agent_id}/autoplay")
    async def change_autoplay(
        agent_id: str, value: AutoplayRequest, request: Request
    ) -> dict[str, Any]:
        return {
            "agent": _public(_manager(request).set_autoplay(agent_id, value.enabled))
        }

    @app.post("/api/agents/{agent_id}/lobby/setup")
    async def configure_lobby(
        agent_id: str, value: LobbySetupRequest, request: Request
    ) -> dict[str, Any]:
        return {"settings": await _manager(request).configure_lobby(agent_id, value)}

    @app.post("/api/agents/{agent_id}/lobby/launch", status_code=202)
    async def launch_game(agent_id: str, request: Request) -> dict[str, bool]:
        await _manager(request).launch_game(agent_id)
        return {"accepted": True}

    @app.get("/api/agents/{agent_id}/observation")
    async def observation(agent_id: str, request: Request) -> dict[str, Any]:
        return {"observation": _manager(request).get_observation(agent_id)}

    @app.get("/api/agents/{agent_id}/tools")
    async def tools(agent_id: str, request: Request) -> dict[str, Any]:
        return {"tools": _manager(request).get_tools(agent_id)}

    @app.get("/api/agents/{agent_id}/events")
    async def events(agent_id: str, request: Request) -> dict[str, Any]:
        if _manager(request).get_agent(agent_id) is None:
            raise KeyError("Agent not found")
        return {
            "events": [
                event.model_dump(by_alias=True)
                for event in _store(request).list_events(agent_id)
            ]
        }

    public_directory = Path(__file__).resolve().parents[2] / "public"
    app.mount("/", StaticFiles(directory=public_directory, html=True), name="dashboard")
    return app


def _manager(request: Request) -> AgentManager:
    return request.app.state.manager


def _store(request: Request) -> AgentStore:
    return request.app.state.store


def _public(agent: AgentPublic) -> dict[str, Any]:
    return agent.model_dump(by_alias=True)


app = create_app()
