// Read-only projection from a PLAYER snapshot, using the pinned game engine.
// Never load a server save or advance the state machine.
const path = require('path');
const fs = require('fs');
const root = process.cwd();
const EntireGame = require(path.join(root, 'src/common/EntireGame')).default;
const Combat = require(path.join(root, 'src/common/ingame-game-state/action-game-state/resolve-march-order-game-state/combat-game-state/CombatGameState')).default;
const Action = require(path.join(root, 'src/common/ingame-game-state/action-game-state/ActionGameState')).default;
const inputs = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = inputs.map(input => {
  const entire = EntireGame.deserializeFromServer(input.snapshot);
  const ingame = entire.childGameState;
  const game = ingame.game;
  let state = ingame;
  let combat = null;
  while (state) {
    if (state instanceof Combat) combat = state;
    state = state.childGameState;
  }
  const supportingRegions = region => Action.prototype.getPossibleSupportingRegions.call(
    {game, ordersOnBoard: ingame.ordersOnBoard}, region
  ).map(({region}) => ({area: region.id, house: region.getController()?.id}));
  const summary = combat ? {
    battlefield: combat.defendingRegion.id,
    attacker: combat.attacker.id, defender: combat.defender.id,
    tieWinner: game.whoIsAheadInTrack(game.fiefdomsTrack, combat.attacker, combat.defender).id,
    bladeHolder: game.valyrianSteelBladeHolder.id,
    bladeUsedThisRound: game.valyrianSteelBladeUsed,
    supporters: combat.supporters.entries.map(([house, side]) => [house.id, side?.id ?? null]),
    eligibleSupportingAreas: supportingRegions(combat.defendingRegion),
    sides: [combat.attacker, combat.defender].map(house => {
      const data = combat.houseCombatDatas.get(house);
      return {
        house: house.id, origin: data.region.id,
        units: data.army.map(unit => ({id: unit.id, type: unit.type.id,
          wounded: unit.wounded, strength: combat.getCombatStrengthOfUnit(house, unit, false)})),
        army: combat.getBaseCombatStrength(house), order: combat.getOrderBonus(house),
        support: combat.getSupportStrengthForSide(house), garrison: combat.getGarrisonCombatStrength(house),
        card: data.houseCard?.id ?? null, cardStrength: combat.getHouseCardCombatStrength(house),
        blade: combat.getValyrianBladeBonus(house), total: combat.getTotalCombatStrength(house)
      };
    })
  } : null;
  return {key: input.key, combat: summary, wildlingStrength: game.wildlingStrength,
    ranking: game.getPotentialWinners().map(house => house.id),
    support: Object.fromEntries(game.world.regions.values.map(region => [region.id, supportingRegions(region)]))};
});
process.stdout.write(JSON.stringify(results));
