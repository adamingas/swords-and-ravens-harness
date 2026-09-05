from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.schemas import AgentCreate, AgentPublic


def test_agent_configuration_persists_without_exposing_credentials(tmp_path) -> None:
    database = Database(tmp_path / "test.db")
    store = AgentStore(database)
    created = store.create_agent(
        AgentCreate(
            name="A Wolf",
            model="gpt-5",
            game_server_url="ws://localhost:5000",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )

    loaded = store.get_agent(created.id)
    assert loaded is not None
    assert loaded.auth_token.get_secret_value() == "secret"
    public = AgentPublic.from_record(loaded).model_dump(by_alias=True)
    assert "authToken" not in public
    assert public["authTokenConfigured"] is True
    database.close()
