// Independent combat oracle: upstream ActionGameState/CombatGameState methods.
// No Python combat or support arithmetic is reused.
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

const Combat = require(path.join(base, "action-game-state/resolve-march-order-game-state/combat-game-state/CombatGameState")).default;
const Action = require(path.join(base, "action-game-state/ActionGameState")).default;
const March = require(path.join(base, "action-game-state/resolve-march-order-game-state/resolve-single-march-order-game-state/ResolveSingleMarchOrderGameState")).default;
const HouseCard = require(path.join(data, "house-card/HouseCard")).default;
const orders = require(path.join(data, "orders")).default;
function own(object, name, value) { Object.defineProperty(object, name, {value, configurable: true}); }

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
  game.ironThroneTrack = serialized.ironThroneTrack.map(id => game.houses.get(id));
  game.fiefdomsTrack = serialized.fiefdomsTrack.map(id => game.houses.get(id));
  const action = Object.create(Action.prototype);
  own(action, "game", game);
  own(action, "ordersOnBoard", new BetterMap((input.orders ?? snapshot.childGameState.ordersOnBoard).filter(([r,o]) => o != null).map(([r,o]) => [world.regions.get(r), orders.get(o)])));
  if (input.neutral) {
    const march = Object.create(March.prototype);
    own(march, "game", game);
    own(march, "actionGameState", action);
    own(march, "ingame", ingame);
    march.house = game.houses.get(input.houseId);
    march.supportersAgainstNeutralForce = null;
    const source = world.regions.get(input.source);
    const target = world.regions.get(input.target);
    const order = action.ordersOnBoard.tryGet(source, null);
    return {canDefeatNeutral: order && [1,2,3].includes(order.id)
      ? march.hasEnoughToAttackNeutralForce(source, source.units.values, target, []) : false};
  }
  if (input.target) {
    return { supportRegions: action.getPossibleSupportingRegions(world.regions.get(input.target)).map(x => x.region.id) };
  }
  let raw = snapshot.childGameState;
  while (raw.type !== "combat") raw = raw.childGameState;
  const combat = Object.create(Combat.prototype);
  own(combat, "game", game);
  own(combat, "actionGameState", action);
  own(combat, "ingameGameState", ingame);
  own(combat, "entireGame", ingame.entireGame);
  combat.attacker = game.houses.get(raw.attackerId);
  combat.defender = game.houses.get(raw.defenderId);
  combat.order = orders.get(raw.order);
  combat.houseCardModifiers = new BetterMap(raw.houseCardModifiers);
  combat.supporters = new BetterMap(raw.supporters.map(([h,s]) => [game.houses.get(h), s ? game.houses.get(s) : null]));
  combat.valyrianSteelBladeUser = null;
  combat.houseCombatDatas = new BetterMap(raw.houseCombatDatas.map(([h, d]) => {
    const region = world.regions.get(d.regionId);
    const cardId = input.cards?.[h] ?? d.houseCardId;
    const cardData = serialized.houses.find(x => x.id === h).houseCards.find(([id,c]) => id === cardId)?.[1];
    return [game.houses.get(h), {region, army: d.army.map(id => region.units.get(id)), houseCard: cardData ? HouseCard.deserializeFromServer(cardData) : null}];
  }));
  return { battlefield: combat.defendingRegion.id, supportRegions: combat.getPossibleSupportingRegions().map(x => x.region.id),
    sides: [combat.attacker, combat.defender].map(h => ({houseId: h.id, army: combat.getBaseCombatStrength(h), order: combat.getOrderBonus(h), support: combat.getSupportStrengthForSide(h), garrison: combat.getGarrisonCombatStrength(h), card: combat.getHouseCardCombatStrength(h), swords: combat.getHouseCardSwordIcons(h), towers: combat.getHouseCardTowerIcons(h), total: combat.getTotalCombatStrength(h)})) };

}

readline.createInterface({ input: process.stdin }).on("line", line => {
  try { process.stdout.write(JSON.stringify(query(JSON.parse(line))) + "\n"); }
  catch (error) { process.stdout.write(JSON.stringify({ error: String(error.stack) }) + "\n"); }
});
