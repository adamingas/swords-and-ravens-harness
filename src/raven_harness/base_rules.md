# Rules

Base-game decision reference for A Game of Thrones, Second Edition. The server
is authoritative. The rules oracle retains the complete official rulebook and
FAQ; ask it for card effects, unusual timing and exceptions. This summary is
used only for base games with the oracle available.

## Victory and control

Each controlled area with a castle OR stronghold scores ONE point. A stronghold's
castleLevel=2 means two mustering points, not two victory points. Reach the
configured target (normally seven) to win immediately. At the end of the final
round (normally ten), most castle areas wins; ties compare land areas, supply
track, then Iron Throne position. You can win the final scoring below seven.

Units control their area. Vacated land normally loses control unless a friendly
control token or home symbol keeps it. Leaving a control token costs one available
power token and requires legally emptying the land area. It is unnecessary at
your own home or where your control token already exists. An enemy home reverts
to its home house when vacated unless held by your control token. Control tokens
do not defend against an entering army. Ships occupy seas/ports, never land.

## Round and orders

Westeros events precede planning except in round one. Planning assigns orders to
occupied areas simultaneously and secretly. After revelation the Raven holder
may replace one order or inspect the Wildling deck. Resolve raids, then marches,
then consolidate power; houses alternate resolving one order in Iron Throne order
within each stage. Support and defence orders remain in place for the round.

Each house has three March tokens (-1, 0, starred +1), three Defence (+1, +1,
starred +2), three Support (0, 0, starred +1), three Raid (two regular, one
starred) and three Consolidate Power (two regular, one starred). King's Court
limits starred tokens, and events can restrict categories. The planning tool
allocates physical tokens according to your preferences and priorities; check
the resulting revealed orders before assuming a particular modifier.

- March: resolve one source, moving any subset of its unrouted units into one
  or more reachable destinations. Unlisted units stay. At most one destination
  may initiate combat. Empty moves discards the order. A later March in a
  destination may move arriving units again. Supply must remain legal.
- Defence: modifies defence in its own area only; permitted on land and at sea.
- Support: eligible unrouted units add strength in ADJACENT battles, plus the
  order modifier. It cannot support its own area. A land army cannot support a
  sea battle; ships may support adjacent land or sea battles. Support can assist
  multiple battles. Foreign houses choose a side or decline. Raids can remove
  support before marches. Ship transport does not extend support adjacency.
- Raid: remove an adjacent enemy Raid, Support or Consolidate Power order;
  starred Raid can also remove Defence. Land cannot raid sea. Raiding Consolidate
  Power may steal power. Null target discards your Raid.
- Consolidate Power: ordinary land resolution earns one plus crown icons.
  Open sea earns nothing. Ports follow their adjacent-sea control rule. Starred
  Consolidate Power at a castle can instead muster there; it does not also pay
  power. Recruitment happens after marches and therefore cannot march this round.

## Movement, supply and mustering

Land units move along land borders or through a continuous chain of friendly
ships at sea. Those ships stay in place and need no particular order. Ships in
ports do not create transport links. Moving a ship may break a route needed by
another army later this round. Ships move between adjacent seas and eligible
ports; port entry requires control of its associated land and capacity at most
three ships. Blocked areas cannot be entered or traversed.

Supply counts every land/sea/port group of at least TWO units as an army.
Sort army sizes descending and fit them to the supplied allowedArmySizes;
single-unit areas use no slot. The number of supply icons currently controlled
does not update the supply track until a Supply event. A reduction may force
unit removal. Individual supply-safe moves/recruits are not necessarily safe
when combined; evaluate the resulting board in submitted order.

At a Mustering event, each controlled castle has one local point and stronghold
two, including empty controlled areas. A starred Consolidate Power muster is
limited to its source. Footman or ship costs one point; knight or siege engine
costs two; replacing a footman with knight/siege costs one. Upgrades do not
increase unit count. New land pieces go in the source; ships in permitted
adjacent seas/ports. Pieces must be available, and the complete recruitment must
fit current supply and port limits. Points cannot transfer between castles and
unused points expire; no power tokens are spent for mustering.

## Combat

The attacker's participating units fight in the defender's area. Unmoved units
at the attacker's origin do not participate. Footmen/ships each contribute one,
knights two. Siege engines contribute four only when attacking or supporting an
attack against a castle/stronghold, otherwise zero. Routed units contribute zero.

Combat totals include army strength, March modifier for the attacker, Defence
modifier for the defender, defending garrison, valid support and its modifiers,
then House card strength/abilities and any Blade use. Higher total wins; equal
totals go to the house higher on Fiefdoms, not Iron Throne. The Blade holder can
normally use +1 once per round after cards reveal; its availability matters.

Both sides choose an available House card secretly. Printed abilities can
change strength, cancellation, casualties or retreat: use inspect_house_card
for the exact current card. The losing army suffers the winner's sword icons
minus its own tower icons, subject to abilities. Surviving losers retreat
legally and become routed; another defeat before recovery destroys routed
units. Siege engines cannot retreat and are destroyed on defeat. Routed units
recover during cleanup. When your final available card is played, recover
previously discarded cards while the just-played card stays discarded.

Neutral forces use their printed strength; no House cards are played against
them. They require sufficient legal attacking strength including permitted
support. Do not treat a neutral garrison like an empty castle or enemy player.

## Influence and Wildlings

Iron Throne controls action order and its holder resolves noncombat ties,
including tied bids. Fiefdoms breaks combat ties and grants the Blade to first.
King's Court sets starred-order allowances and grants the Raven to first.
During Clash of Kings, each track is a separate secret bid in that order, with
bid tokens spent even when outbid. Budget across all three. An opponent's bid
of -1 means hidden/submitted, not zero.

Wildling bids contribute to a collective defence. If the total is at least the
current Wildling strength, the Night's Watch wins and the highest bidder gets
the revealed card's reward. Other bidders suffer NO lowest-bid penalty after
a Night's Watch victory. Wildling strength resets to zero. On a defeat, the
lowest bidder suffers the card's severe penalty and others its lesser penalty;
the threat moves back two positions. All bids are spent in either outcome.
Iron Throne resolves tied highest/lowest bidders. Read the revealed card's
specific reward or penalty; ask the oracle when unsure. Other houses' promises
or past plans do not reveal their secret bids. Before the card is revealed, its
identity is unknown unless your private Raven inspection revealed it. The rules
oracle can explain possible effects but cannot discover the hidden card.
