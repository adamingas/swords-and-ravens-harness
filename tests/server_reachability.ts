// Independent geometric oracle: upstream map and World.getReachableRegions.
// No Python traversal or legality calculations are reused.
const path = require("path");
const readline = require("readline");
const base = path.join(process.cwd(), "src/common/ingame-game-state");
const data = path.join(base, "game-data-structure");
// Match the server's entry point to initialize its circular game-state imports.
require(path.join(process.cwd(), "src/common/EntireGame"));
const World = require(path.join(data, "World")).default;
const Game = require(path.join(data, "Game")).default;
const Region = require(path.join(data, "Region")).default;
const Unit = require(path.join(data, "Unit")).default;
const unitTypes = require(path.join(data, "unitTypes")).default;
const getStaticWorld = require(path.join(data, "static-data-structure/getStaticWorld")).default;
const BetterMap = require(path.join(process.cwd(), "src/utils/BetterMap")).default;

function query(input) {
  const snapshot = input.snapshot;
  const serialized = snapshot.childGameState.game;
  const settings = snapshot.gameSettings;
  const game = Object.create(Game.prototype);
  const world = Object.create(World.prototype);
  game.world = world;
  world.settings = settings;
  const ingame = {
    entireGame: { gameSettings: settings },
    getOtherVassalFamilyHouses: () => [],
    isVassalHouse: () => false,
  };
  game.ingame = ingame;
  const houseIds = ["stark", "baratheon", "lannister", "greyjoy", "tyrell", "martell"];
  game.houses = new BetterMap(houseIds.map(id => [id, {
    id, supplyLevel: serialized.houses.find(h => h.id === id)?.supplyLevel ?? 0,
  }]));
  const house = game.houses.get(input.houseId);
  world.regions = new BetterMap(getStaticWorld(settings).staticRegions.values.map(s => {
    const state = serialized.world.regions.find(r => r.id === s.id) ?? {};
    const region = Object.create(Region.prototype);
    Object.assign(region, {
      id: s.id, game, garrison: state.garrison ?? 0,
      castleModifier: state.castleModifier ?? 0,
      controlPowerToken: game.houses.tryGet(state.controlPowerToken, null),
      overwrittenSuperControlPowerToken: game.houses.tryGet(state.overwrittenSuperControlPowerToken, null),
    });
    region.units = new BetterMap((state.units ?? []).map(u => {
      const unit = new Unit(u.id, unitTypes.get(u.type), game.houses.get(u.allegiance));
      unit.wounded = u.wounded ?? false;
      unit.region = region;
      return [unit.id, unit];
    }));
    return [region.id, region];
  }));
  const source = world.regions.get(input.source);
  // Geographic query: use a synthetic movement type without changing the board.
  const army = [new Unit(-1, unitTypes.get(source.type.id === "land" ? "footman" : "ship"), house)];
  if (source.garrison === 1000) return { routes: [] };
  // The production geometric helper does not exclude blocked areas. Apply the
  // tool's explicit blocked-area contract to traversal, then use real server DFS.
  const neighbours = world.getNeighbouringRegions.bind(world);
  const traversal = Object.create(world);
  traversal.getNeighbouringRegions = region => neighbours(region).filter(r => r.garrison !== 1000);
  return { routes: traversal.getReachableRegions(source, house, army).map(r => r.id).sort() };
}

readline.createInterface({ input: process.stdin }).on("line", line => {
  try { process.stdout.write(JSON.stringify(query(JSON.parse(line))) + "\n"); }
  catch (error) { process.stdout.write(JSON.stringify({ error: String(error.stack) }) + "\n"); }
});
