const grid = document.querySelector("#agent-grid");
const emptyState = document.querySelector("#empty-state");
const template = document.querySelector("#agent-template");
const agentDialog = document.querySelector("#agent-dialog");
const detailsDialog = document.querySelector("#details-dialog");
const form = document.querySelector("#agent-form");
let agents = [];
let detailsAgentId = null;
let detailsTab = "observation";
const defaultModel = "z-ai/glm-5.3-flash";

document.querySelector("#new-agent").addEventListener("click", () => agentDialog.showModal());
document.querySelector("#close-dialog").addEventListener("click", () => agentDialog.close());
document.querySelector("#cancel-dialog").addEventListener("click", () => agentDialog.close());
document.querySelector("#close-details").addEventListener("click", () => detailsDialog.close());
document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", async () => {
    detailsTab = button.dataset.tab;
    document.querySelectorAll(".tab").forEach((candidate) => candidate.classList.toggle("active", candidate === button));
    await loadDetails();
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formError = document.querySelector("#form-error");
  formError.classList.add("hidden");
  const input = Object.fromEntries(new FormData(form));
  if (!input.systemPrompt.trim()) delete input.systemPrompt;
  try {
    await api("/api/agents", { method: "POST", body: JSON.stringify(input) });
    form.reset();
    form.elements.model.value = defaultModel;
    form.elements.harnessId.value = "legacy";
    form.elements.gameServerUrl.value = "ws://localhost:5001";
    form.elements.gameId.value = "1";
    agentDialog.close();
    await refresh();
  } catch (error) {
    formError.textContent = error.message;
    formError.classList.remove("hidden");
  }
});

async function refresh() {
  const [{ agents: nextAgents }, health] = await Promise.all([
    api("/api/agents"),
    api("/api/health"),
  ]);
  agents = nextAgents;
  render();
  const status = document.querySelector("#api-status");
  status.textContent = health.modelApiConfigured ? `${health.modelProvider} configured` : `${health.modelProvider} key not configured`;
  status.className = `api-status ${health.modelApiConfigured ? "ready" : "missing"}`;
}

async function loadModels() {
  const { models } = await api("/api/models");
  if (!models.length) return;
  const select = form.elements.model;
  select.replaceChildren(...models.map((model) => {
    const option = document.createElement("option");
    option.value = model.id;
    option.textContent = `${model.name} — $${model.promptPricePerMillion}/$${model.completionPricePerMillion} per M`;
    return option;
  }));
  select.value = models.some((model) => model.id === defaultModel) ? defaultModel : models[0].id;
}

async function loadHarnesses() {
  const { harnesses } = await api("/api/harnesses");
  if (!harnesses.length) return;
  const select = form.elements.harnessId;
  select.replaceChildren(...harnesses.map((harness) => {
    const option = document.createElement("option");
    option.value = harness.id;
    option.textContent = harness.name;
    option.title = harness.description;
    return option;
  }));
  select.value = harnesses.some((harness) => harness.id === "legacy") ? "legacy" : harnesses[0].id;
}

function render() {
  grid.replaceChildren();
  emptyState.classList.toggle("hidden", agents.length !== 0);
  for (const agent of agents) {
    const node = template.content.firstElementChild.cloneNode(true);
    const status = node.querySelector(".status");
    status.classList.add(agent.runtime.status);
    node.querySelector(".status-label").textContent = agent.runtime.status;
    node.querySelector(".agent-name").textContent = agent.name;
    node.querySelector(".model-name").textContent = agent.model;
    node.querySelector(".harness-name").textContent = agent.harnessId;
    node.querySelector(".game-id").textContent = agent.gameId;
    node.querySelector(".seat").textContent = agent.runtime.houseId || agent.userId;
    node.querySelector(".phase").textContent = agent.runtime.phase || "—";
    const error = node.querySelector(".card-error");
    if (agent.runtime.lastError) {
      error.textContent = agent.runtime.lastError;
      error.classList.remove("hidden");
    }

    const connect = node.querySelector(".connect");
    const connected = ["connected", "running"].includes(agent.runtime.status);
    connect.textContent = connected ? "Disconnect" : "Connect";
    connect.disabled = ["connecting", "running"].includes(agent.runtime.status);
    connect.addEventListener("click", () => perform(agent.id, connected ? "stop" : "start"));

    const run = node.querySelector(".run");
    run.disabled = !connected || agent.runtime.status === "running";
    run.addEventListener("click", () => perform(agent.id, "run"));
    const autoplay = node.querySelector(".autoplay");
    autoplay.disabled = !connected || agent.runtime.status === "running";
    autoplay.textContent = agent.runtime.autoplay ? "Stop autoplay" : "Autoplay";
    autoplay.classList.toggle("primary", agent.runtime.autoplay);
    autoplay.addEventListener("click", async () => {
      await api(`/api/agents/${agent.id}/autoplay`, {
        method: "POST",
        body: JSON.stringify({ enabled: !agent.runtime.autoplay }),
      });
      await refresh();
    });
    const setup = node.querySelector(".setup");
    setup.disabled = !connected || agent.runtime.phase !== "lobby";
    setup.addEventListener("click", async () => {
      try {
        await api(`/api/agents/${agent.id}/lobby/setup`, {
          method: "POST",
          body: JSON.stringify({
            setupId: "base-game",
            playerCount: 3,
            pbem: true,
            vassals: false,
            victoryPointsToWin: 7,
          }),
        });
      } catch (error) {
        alert(error.message);
      }
      await refresh();
    });
    const launch = node.querySelector(".launch");
    launch.disabled = !connected || agent.runtime.phase !== "lobby";
    launch.addEventListener("click", async () => {
      try {
        await api(`/api/agents/${agent.id}/lobby/launch`, { method: "POST" });
      } catch (error) {
        alert(error.message);
      }
      await refresh();
    });
    node.querySelector(".inspect").addEventListener("click", () => inspect(agent));
    node.querySelector(".delete").addEventListener("click", async () => {
      if (!confirm(`Delete ${agent.name}?`)) return;
      await api(`/api/agents/${agent.id}`, { method: "DELETE" });
      await refresh();
    });
    grid.append(node);
  }
}

async function perform(id, action) {
  const agent = agents.find((candidate) => candidate.id === id);
  if (agent) agent.runtime.status = action === "start" ? "connecting" : action === "run" ? "running" : agent.runtime.status;
  render();
  try {
    await api(`/api/agents/${id}/${action}`, { method: "POST" });
  } catch (error) {
    alert(error.message);
  }
  await refresh();
}

async function inspect(agent) {
  detailsAgentId = agent.id;
  document.querySelector("#details-title").textContent = agent.name;
  detailsDialog.showModal();
  await loadDetails();
}

async function loadDetails() {
  if (!detailsAgentId) return;
  const content = document.querySelector("#details-content");
  content.textContent = "Loading…";
  try {
    const data = await api(`/api/agents/${detailsAgentId}/${detailsTab}`);
    content.textContent = JSON.stringify(data[detailsTab], null, 2);
  } catch (error) {
    content.textContent = error.message;
  }
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

Promise.all([loadModels(), loadHarnesses()]).then(refresh).catch((error) => {
  document.querySelector("#api-status").textContent = error.message;
});
setInterval(() => refresh().catch(() => {}), 2500);
