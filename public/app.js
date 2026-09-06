const grid = document.querySelector("#agent-grid");
const emptyState = document.querySelector("#empty-state");
const template = document.querySelector("#agent-template");
const agentDialog = document.querySelector("#agent-dialog");
const detailsDialog = document.querySelector("#details-dialog");
const form = document.querySelector("#agent-form");
let monitors = [];
let detailsAgentId = null;
let detailsTab = "overview";
let detailsRunId = null;
let detailsLoading = false;
let detailsReloadRequested = false;
let refreshPromise = null;
let configuredModel = "";

document.querySelector("#new-agent").addEventListener("click", () => agentDialog.showModal());
document.querySelector("#close-dialog").addEventListener("click", () => agentDialog.close());
document.querySelector("#cancel-dialog").addEventListener("click", () => agentDialog.close());
document.querySelector("#close-details").addEventListener("click", () => detailsDialog.close());
document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", async () => {
    detailsTab = button.dataset.tab;
    detailsRunId = null;
    setActiveTab();
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
    form.elements.model.value = configuredModel;
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
  if (refreshPromise) return refreshPromise;
  refreshPromise = refreshDashboard().finally(() => {
    refreshPromise = null;
  });
  return refreshPromise;
}

async function refreshDashboard() {
  const [{ agents: nextMonitors }, health] = await Promise.all([
    api("/api/dashboard"),
    api("/api/health"),
  ]);
  monitors = nextMonitors;
  render();
  const status = document.querySelector("#api-status");
  const provider = health.modelApiConfigured
    ? health.modelProvider + " ready"
    : health.modelProvider + " key missing";
  const rules = health.rulesOracleAvailable ? "rules ready" : "rules unavailable";
  const traces = health.telemetryExportConfigured ? "OTLP export on" : "local traces";
  status.textContent = provider + " · " + rules + " · " + traces;
  status.className = "api-status " + (health.modelApiConfigured ? "ready" : "missing");
  if (detailsDialog.open) await loadDetails({ showLoading: false });
}

async function loadModels() {
  const { models } = await api("/api/models");
  if (!models.length) return;
  configuredModel = models[0].id;
  const select = form.elements.model;
  select.replaceChildren(...models.map((model) => {
    const option = document.createElement("option");
    option.value = model.id;
    option.textContent = model.name;
    return option;
  }));
  select.value = configuredModel;
}

function render() {
  grid.replaceChildren();
  emptyState.classList.toggle("hidden", monitors.length !== 0);
  renderGlobalSummary();
  for (const monitor of monitors) {
    const agent = monitor.agent;
    const state = monitor.state;
    const player = state?.player || {};
    const metrics = monitor.metrics;
    const latest = monitor.recentRuns[0];
    const node = template.content.firstElementChild.cloneNode(true);
    const status = node.querySelector(".status");
    status.classList.add(agent.runtime.status);
    node.querySelector(".status-label").textContent = agent.runtime.status;
    node.querySelector(".agent-name").textContent = agent.name;
    node.querySelector(".model-name").textContent = agent.model;
    node.querySelector(".game-id").textContent = agent.gameId;
    node.querySelector(".seat").textContent = agent.runtime.houseId || "user " + agent.userId;
    node.querySelector(".phase").textContent = agent.runtime.phase || "—";
    node.querySelector(".sigil").textContent = (agent.runtime.houseId || "R")[0].toUpperCase();

    node.querySelector(".victory").textContent = player.currentVictoryPoints == null
      ? "—"
      : player.currentVictoryPoints + "/" + (state.game.victoryPointsToWin ?? "?");
    node.querySelector(".power").textContent = player.powerTokens ?? "—";
    node.querySelector(".supply").textContent = player.supply ?? "—";
    node.querySelector(".units").textContent = player.units?.length ?? "—";

    const turnFlag = node.querySelector(".turn-flag");
    const decisionName = node.querySelector(".decision-name");
    const decisionPathLabel = node.querySelector(".decision-path-label");
    const decisionPathValue = node.querySelector(".decision-path-value");
    if (agent.runtime.status === "running") {
      turnFlag.textContent = elapsedLabel(agent.runtime.runStartedAt);
      turnFlag.classList.add("thinking");
      decisionName.textContent = "Model is choosing an action";
      decisionPathLabel.textContent = "Available tools: ";
      decisionPathValue.textContent = (agent.runtime.currentTools || []).join(" · ") || "None";
    } else if (state?.isYourTurn) {
      turnFlag.textContent = "Action required";
      turnFlag.classList.add("active");
      decisionName.textContent = label(state.pendingDecision?.type || state.game.phase);
      decisionPathValue.textContent = (state.statePath || []).join(" › ");
    } else if (state) {
      turnFlag.textContent = "Watching game";
      decisionName.textContent = label(state.pendingDecision?.type || state.game.phase);
      decisionPathValue.textContent = (state.statePath || []).join(" › ");
    }

    node.querySelector(".latest-run").textContent = latest
      ? latest.status + ": " + (latest.tool || "no action") + " · " + formatDuration(latest.durationMs)
      : "No model runs";
    node.querySelector(".run-totals").textContent =
      number(metrics.tokens.total) + " tokens · " + formatCost(metrics.costUsd);

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
    const canChooseLobbyHouse = agent.runtime.phase === "lobby";
    run.disabled = !connected
      || agent.runtime.status === "running"
      || (!canChooseLobbyHouse && !state?.isYourTurn);
    run.addEventListener("click", () => perform(agent.id, "run"));

    const autoplay = node.querySelector(".autoplay");
    autoplay.disabled = !connected
      || agent.runtime.status === "running"
      || agent.runtime.phase === "lobby";
    autoplay.textContent = agent.runtime.autoplay ? "Stop autoplay" : "Autoplay";
    autoplay.classList.toggle("primary", agent.runtime.autoplay);
    autoplay.addEventListener("click", async () => {
      await api("/api/agents/" + agent.id + "/autoplay", {
        method: "POST",
        body: JSON.stringify({ enabled: !agent.runtime.autoplay }),
      });
      await refresh();
    });

    const setup = node.querySelector(".setup");
    setup.disabled = !connected || agent.runtime.phase !== "lobby" || !state?.isOwner;
    setup.addEventListener("click", async () => {
      await guarded(async () => {
        await api("/api/agents/" + agent.id + "/lobby/setup", {
          method: "POST",
          body: JSON.stringify({
            setupId: "base-game",
            playerCount: 6,
            pbem: true,
            vassals: false,
            victoryPointsToWin: 7,
          }),
        });
      });
    });

    const launch = node.querySelector(".launch");
    launch.disabled = !connected || agent.runtime.phase !== "lobby" || !state?.isOwner;
    launch.addEventListener("click", async () => {
      await guarded(() => api("/api/agents/" + agent.id + "/lobby/launch", { method: "POST" }));
    });

    node.querySelector(".inspect").addEventListener("click", () => inspect(agent.id));
    node.querySelector(".delete").addEventListener("click", async () => {
      if (!confirm("Delete " + agent.name + " and all of its traces?")) return;
      await api("/api/agents/" + agent.id, { method: "DELETE" });
      await refresh();
    });
    grid.append(node);
  }
}

function renderGlobalSummary() {
  const totals = monitors.reduce((result, monitor) => {
    const metrics = monitor.metrics || {};
    result.runs += Number(metrics.runCount || 0);
    result.failures += Number(metrics.statusCounts?.failed || 0);
    result.tokens += Number(metrics.tokens?.total || 0);
    result.cost += Number(metrics.costUsd || 0);
    return result;
  }, { runs: 0, failures: 0, tokens: 0, cost: 0 });
  document.querySelector("#summary-agents").textContent = number(monitors.length);
  document.querySelector("#summary-runs").textContent = number(totals.runs);
  document.querySelector("#summary-failures").textContent = number(totals.failures);
  document.querySelector("#summary-tokens").textContent = number(totals.tokens);
  document.querySelector("#summary-cost").textContent = formatCost(totals.cost);
}

async function guarded(operation) {
  try {
    await operation();
  } catch (error) {
    alert(error.message);
  }
  await refresh();
}

async function perform(id, action) {
  const monitor = monitors.find((candidate) => candidate.agent.id === id);
  if (monitor) {
    monitor.agent.runtime.status = action === "start"
      ? "connecting"
      : action === "run"
        ? "running"
        : monitor.agent.runtime.status;
  }
  render();
  await guarded(() => api("/api/agents/" + id + "/" + action, { method: "POST" }));
}

async function inspect(agentId) {
  detailsAgentId = agentId;
  detailsTab = "overview";
  detailsRunId = null;
  setActiveTab();
  const monitor = monitors.find((candidate) => candidate.agent.id === agentId);
  document.querySelector("#details-title").textContent =
    monitor?.agent.name || "Agent details";
  detailsDialog.showModal();
  await loadDetails();
}

function setActiveTab() {
  document.querySelectorAll(".tab").forEach((candidate) => {
    candidate.classList.toggle("active", candidate.dataset.tab === detailsTab);
  });
}

async function loadDetails({ showLoading = true } = {}) {
  if (!detailsAgentId || !detailsDialog.open) return;
  if (detailsLoading) {
    detailsReloadRequested = true;
    return;
  }
  detailsLoading = true;
  try {
    do {
      detailsReloadRequested = false;
      await loadDetailsOnce({ showLoading });
      showLoading = false;
    } while (detailsReloadRequested && detailsDialog.open);
  } finally {
    detailsLoading = false;
  }
}

async function loadDetailsOnce({ showLoading }) {
  const agentId = detailsAgentId;
  const tab = detailsTab;
  const runId = detailsRunId;
  const content = document.querySelector("#details-content");
  if (showLoading) {
    content.replaceChildren();
    content.textContent = "Loading…";
  }
  if (tab === "overview") {
    renderOverview();
    return;
  }
  try {
    if (tab === "runs" && runId) {
      const { run } = await api("/api/agents/" + agentId + "/runs/" + runId);
      if (isCurrentDetails(agentId, tab, runId)) renderRunTrace(content, run);
      return;
    }
    const data = await api("/api/agents/" + agentId + "/" + tab);
    if (!isCurrentDetails(agentId, tab, runId)) return;
    if (tab === "runs") {
      renderRuns(content, data.runs);
    } else {
      renderJson(content, data[tab]);
    }
  } catch (error) {
    if (isCurrentDetails(agentId, tab, runId)) content.textContent = error.message;
  }
}

function isCurrentDetails(agentId, tab, runId) {
  return detailsDialog.open
    && detailsAgentId === agentId
    && detailsTab === tab
    && detailsRunId === runId;
}

function renderOverview() {
  const content = document.querySelector("#details-content");
  const monitor = monitors.find((candidate) => candidate.agent.id === detailsAgentId);
  content.replaceChildren();
  if (!monitor) {
    content.textContent = "Agent not found.";
    return;
  }
  content.className = "details-content overview";
  const state = monitor.state;
  if (!state) {
    content.append(section("Connection", textNode("Connect this agent to see its player state.")));
    content.append(section("Recent model runs", runTable(monitor.recentRuns)));
    return;
  }
  const player = state.player || {};
  const stats = document.createElement("div");
  stats.className = "overview-stats";
  [
    ["Victory", (player.currentVictoryPoints ?? "—") + "/" + (state.game.victoryPointsToWin ?? "?")],
    ["Power", player.powerTokens ?? "—"],
    ["Supply", player.supply ?? "—"],
    ["Castles", player.controlledCastleAreas ?? "—"],
    ["Land", player.controlledLandAreas ?? "—"],
    ["Units", player.units?.length ?? 0],
  ].forEach(([name, value]) => stats.append(stat(name, value)));
  content.append(stats);

  const decision = document.createElement("div");
  decision.className = "overview-decision " + (state.isYourTurn ? "active" : "");
  decision.append(
    textNode(state.isYourTurn ? "ACTION REQUIRED" : "CURRENT STATE", "eyebrow"),
    textNode(label(state.pendingDecision?.type || state.game.phase), "overview-title"),
    textNode((state.statePath || []).join(" › "), "muted-line"),
  );
  content.append(decision);

  content.append(section("Available house cards", cardList(player.availableHouseCards || [])));
  content.append(section("Units", unitTable(player.units || [])));
  content.append(section(
    "Controlled regions",
    pillList((player.controlledRegionDetails || []).map((region) =>
      region.name + (region.castleLevel ? " · castle " + region.castleLevel : "")
    )),
  ));
  content.append(section("Standings", standingsTable(state.standings || [])));
  content.append(section("Board", boardTable(state.board || [])));
  content.append(section("Action guidance", structuredValue(state.actionGuidance)));
  content.append(section("Influence tracks", trackList(state.tracks || {})));
  content.append(section("Recent model runs", runTable(monitor.recentRuns)));
  content.append(section("Current decision data", jsonBlock(state.pendingDecision)));
  content.append(section("Recent game events", jsonBlock(state.recentEvents)));
}

function section(title, child) {
  const element = document.createElement("section");
  element.className = "overview-section";
  element.append(textNode(title, "section-title"), child);
  return element;
}

function stat(name, value) {
  const element = document.createElement("div");
  element.className = "overview-stat";
  element.append(textNode(name, "stat-name"), textNode(String(value), "stat-value"));
  return element;
}

function cardList(cards) {
  if (!cards.length) return textNode("No available house cards.", "muted-line");
  const list = document.createElement("div");
  list.className = "item-grid";
  cards.forEach((card) => {
    const item = document.createElement("div");
    item.className = "item-card";
    item.append(
      textNode(card.name || card.id, "item-name"),
      textNode(
        "Strength " + (card.strength ?? 0) + " · " + (card.swords ?? 0)
          + " swords · " + (card.towers ?? 0) + " towers",
        "muted-line",
      ),
      textNode(
        "Ability: " + (card.ability ? label(card.ability) : "None"),
        "muted-line",
      ),
    );
    list.append(item);
  });
  return list;
}

function standingsTable(standings) {
  if (!standings.length) return textNode("No standings are available.", "muted-line");
  const ordered = [...standings].sort((left, right) =>
    Number(right.currentVictoryPoints || 0) - Number(left.currentVictoryPoints || 0)
      || Number(right.controlledCastleAreas || 0) - Number(left.controlledCastleAreas || 0)
      || Number(right.controlledLandAreas || 0) - Number(left.controlledLandAreas || 0)
  );
  return dataTable(
    ["House", "Victory", "Castles", "Land", "Power", "Supply", "Supply icons"],
    ordered.map((house) => [
      house.name || label(house.id),
      house.currentVictoryPoints ?? "—",
      house.controlledCastleAreas ?? "—",
      house.controlledLandAreas ?? "—",
      house.powerTokens ?? "—",
      house.supply ?? "—",
      house.controlledSupplyIcons ?? "—",
    ]),
  );
}

function boardTable(board) {
  if (!board.length) return textNode("No occupied or controlled regions.", "muted-line");
  const ordered = [...board].sort((left, right) =>
    String(left.name || left.id).localeCompare(String(right.name || right.id))
  );
  return dataTable(
    ["Region", "Type", "Units", "Control", "Garrison", "Castle", "Supply", "Crowns"],
    ordered.map((region) => [
      region.name || label(region.id),
      label(region.type),
      formatUnits(region.units || []),
      region.controlPowerToken ? label(region.controlPowerToken) : "—",
      region.garrison || "—",
      region.castleLevel || "—",
      region.supplyIcons || "—",
      region.crownIcons || "—",
    ]),
  );
}

function formatUnits(units) {
  if (!units.length) return "—";
  return units.map((unit) => {
    const wounded = unit.wounded ? " (wounded)" : "";
    return label(unit.allegiance) + " " + label(unit.type) + " #" + unit.id + wounded;
  }).join(", ");
}

function structuredValue(value) {
  if (value == null) return textNode("No derived guidance for this state.", "muted-line");
  if (Array.isArray(value)) {
    if (!value.length) return textNode("None", "muted-line");
    if (value.every((item) => item == null || typeof item !== "object")) {
      return pillList(value.map(displayValue));
    }
    const list = document.createElement("div");
    list.className = "structured-list";
    value.forEach((item) => list.append(structuredValue(item)));
    return list;
  }
  if (typeof value === "object") {
    const object = document.createElement("div");
    object.className = "structured-object";
    Object.entries(value).forEach(([name, child]) => {
      const row = document.createElement("div");
      row.className = "structured-row";
      row.append(textNode(label(name), "structured-name"), structuredValue(child));
      object.append(row);
    });
    return object;
  }
  return textNode(displayValue(value), "structured-value");
}

function displayValue(value) {
  if (value == null) return "None";
  if (value === true) return "Yes";
  if (value === false) return "No";
  return String(value);
}

function unitTable(units) {
  if (!units.length) return textNode("No units in the current observation.", "muted-line");
  return dataTable(
    ["Region", "Unit", "ID", "State"],
    units.map((unit) => [
      label(unit.regionId),
      label(unit.type),
      unit.id,
      unit.wounded ? "Wounded" : "Ready",
    ]),
  );
}

function trackList(tracks) {
  const wrapper = document.createElement("div");
  wrapper.className = "tracks";
  for (const [name, houses] of Object.entries(tracks)) {
    const row = document.createElement("div");
    row.append(textNode(label(name), "track-name"), pillList(houses.map(label)));
    wrapper.append(row);
  }
  return wrapper;
}

function runTable(runs) {
  if (!runs.length) return textNode("No model runs recorded.", "muted-line");
  return dataTable(
    ["Status", "Action", "Latency", "Input", "Output", "Cost"],
    runs.map((run) => [
      run.status,
      run.tool || run.error || "No action",
      formatDuration(run.durationMs),
      number(run.usage?.inputTokens || 0),
      number(run.usage?.outputTokens || 0),
      formatCost(runCost(run)),
    ]),
    runs.map((run) => run.status),
  );
}

function renderRuns(content, runs) {
  content.className = "details-content overview";
  content.replaceChildren();
  if (!runs.length) {
    content.append(textNode("No model runs recorded.", "muted-line"));
    return;
  }

  const table = document.createElement("table");
  table.className = "data-table";
  const head = document.createElement("thead");
  const heading = document.createElement("tr");
  ["Status", "Action", "Started", "Latency", "Input", "Output", "Cost", ""].forEach(
    (name) => heading.append(textNode(name, "table-heading", "th")),
  );
  head.append(heading);
  table.append(head);

  const body = document.createElement("tbody");
  runs.forEach((run) => {
    const row = document.createElement("tr");
    row.classList.add(run.status);
    [
      run.status,
      run.tool || run.error || "No action",
      formatTimestamp(run.createdAt),
      formatDuration(run.durationMs),
      number(run.usage?.inputTokens || 0),
      number(run.usage?.outputTokens || 0),
      formatCost(runCost(run)),
    ].forEach((value) => row.append(textNode(String(value), "", "td")));
    const actionCell = document.createElement("td");
    const open = textNode("Open", "button quiet", "button");
    open.type = "button";
    open.addEventListener("click", async () => {
      detailsRunId = run.id;
      await loadDetails();
    });
    actionCell.append(open);
    row.append(actionCell);
    body.append(row);
  });
  table.append(body);
  const scroll = document.createElement("div");
  scroll.className = "table-scroll";
  scroll.append(table);
  content.append(
    textNode("Select a run to inspect the complete stored trace.", "muted-line"),
    scroll,
  );
}

function renderRunTrace(content, run) {
  content.className = "details-content overview";
  content.replaceChildren();

  const back = textNode("← Back to runs", "button quiet", "button");
  back.type = "button";
  back.addEventListener("click", async () => {
    detailsRunId = null;
    await loadDetails();
  });
  content.append(back);

  content.append(section("Run summary", jsonBlock({
    id: run.id,
    status: run.status,
    model: run.model,
    responseId: run.responseId,
    historyId: run.historyId,
    createdAt: run.createdAt,
    finishedAt: run.finishedAt,
    durationMs: run.durationMs,
    error: run.error,
  })));
  content.append(section("Action", jsonBlock({
    tool: run.tool,
    arguments: run.arguments,
  })));
  content.append(section("Usage and cost", jsonBlock({
    usage: run.usage,
    costUsd: runCost(run),
    providerUsage: run.rawUsage,
  })));
  content.append(section("Model output", textBlock(run.modelOutput)));
  content.append(section("Instructions", textBlock(run.instructions)));
  content.append(section("Observation", jsonBlock(run.observation)));
  content.append(section("Offered tools and schemas", jsonBlock(run.tools)));
  content.append(section("Response items", jsonBlock(run.response)));
}

function dataTable(headers, rows, rowClasses = []) {
  const table = document.createElement("table");
  table.className = "data-table";
  const head = document.createElement("thead");
  const heading = document.createElement("tr");
  headers.forEach((header) => heading.append(textNode(header, "table-heading", "th")));
  head.append(heading);
  table.append(head);
  const body = document.createElement("tbody");
  rows.forEach((values, index) => {
    const row = document.createElement("tr");
    if (rowClasses[index]) row.classList.add(rowClasses[index]);
    values.forEach((value) => row.append(textNode(String(value), "", "td")));
    body.append(row);
  });
  table.append(body);
  const scroll = document.createElement("div");
  scroll.className = "table-scroll";
  scroll.append(table);
  return scroll;
}

function pillList(values) {
  const list = document.createElement("div");
  list.className = "pill-list";
  if (!values.length) {
    list.append(textNode("None", "muted-line"));
    return list;
  }
  values.forEach((value) => list.append(textNode(String(value), "pill")));
  return list;
}

function jsonBlock(value) {
  const pre = document.createElement("pre");
  pre.textContent = JSON.stringify(value, null, 2);
  return pre;
}

function textBlock(value) {
  const pre = document.createElement("pre");
  pre.textContent = value == null ? "" : String(value);
  return pre;
}

function renderJson(container, value) {
  container.className = "details-content raw";
  container.replaceChildren(jsonBlock(value));
}

function textNode(value, className = "", tag = "div") {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = value;
  return element;
}

function runCost(run) {
  return (run.rawUsage || []).reduce((sum, usage) => sum + Number(usage.cost || 0), 0);
}

function formatCost(value) {
  return "$" + Number(value || 0).toFixed(4);
}

function formatDuration(value) {
  if (value == null) return "—";
  if (value < 1000) return value + " ms";
  return (value / 1000).toFixed(1) + " s";
}

function formatTimestamp(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function elapsedLabel(startedAt) {
  if (!startedAt) return "Model running";
  const seconds = Math.max(0, Math.round((Date.now() - Date.parse(startedAt)) / 1000));
  return "Thinking · " + seconds + "s";
}

function number(value) {
  return Number(value || 0).toLocaleString();
}

function label(value) {
  return String(value || "unknown")
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "Request failed (" + response.status + ")");
  return body;
}

loadModels().then(refresh).catch((error) => {
  document.querySelector("#api-status").textContent = error.message;
});
setInterval(() => refresh().catch(() => {}), 2500);
