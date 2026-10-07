# How the Swords and Ravens game server works over WebSockets

This guide follows a game from connection and house choice through planning,
Westeros cards, actions, combat, and game end. The examples come from:

- a live local capture made against a clean server on port `45173`, with random
  seed `424242`, using four clients; and
- the repository's archived deterministic six-player run
  `data/evaluations/deterministic-protocol-smoke-6a7e5bb`, which reached round
  two and contains a complete combat.

Large snapshots below are abridged, but field names and values shown are real.

## The short version

The game uses **state synchronization**, not command replay.

1. A browser authenticates over a raw WebSocket.
2. The server sends a player-specific full game snapshot.
3. The browser constructs the same game/state-machine objects used by the
   server from that snapshot.
4. A player sends a small command such as `choose-house`, `submit-orders`, or
   `resolve-march-order`.
5. The server validates the command and remains authoritative.
6. The server broadcasts small mutation messages (`move-units`,
   `change-power-token`, and so on) and, when the active decision/phase changes,
   a `game-state-change` containing the changed subtree.
7. `add-game-log` messages provide the durable human-readable history of what
   happened and why.

The most useful mental model is therefore:

```text
full snapshot on connect/resync
        +
incremental mutation events
        +
state-machine subtree replacements
        =
the browser's current local game
```

## 1. What is actually on the wire

This is a raw WebSocket protocol, not Socket.IO. Every application message is:

```text
TypeScript object -> JSON -> DEFLATE -> base64 string -> WebSocket frame
```

The reverse happens on receipt. A frame seen in browser network tools therefore
looks like this, not like JSON:

```text
eJxlVE1v2zAM/SuGeo2B5cOpk1tabN2AdiuWFDsMPdAy7WiRJYOSGxhF/...
```

In the live capture, the initial frame was 756 base64 characters and inflated
to 1,185 bytes of JSON. Client frames use exactly the same codec. The server
validates inflated client JSON against its generated JSON schema before acting.

Relevant code:

- `swords-and-ravens/agot-bg-game-server/src/client/GameClient.ts`: socket lifecycle and dispatch
- `swords-and-ravens/agot-bg-game-server/src/client/utils/compression.ts`: browser codec
- `swords-and-ravens/agot-bg-game-server/src/server/GlobalServer.ts`: authentication, validation,
  routing, broadcast, and persistence
- `swords-and-ravens/agot-bg-game-server/src/server/utils/compression.ts`: server codec
- `swords-and-ravens/agot-bg-game-server/src/messages/ClientMessage.ts`: browser-to-server types
- `swords-and-ravens/agot-bg-game-server/src/messages/ServerMessage.ts`: server-to-browser types

The browser also sends a `ping` every 30 seconds. This is an application-level
message used to keep the connection alive; it causes no response.

## 2. The two kinds of state update

### Small mutations

These alter one part of the browser's existing model. Examples include:

```json
{"type":"move-units","from":"ironmans-bay","to":"the-golden-sound","units":[8]}
```

```json
{"type":"change-power-token","houseId":"stark","powerTokenCount":8}
```

```json
{"type":"add-game-log","data":{"type":"turn-begin","turn":2},"time":1788677961,"resolvedAutomatically":false}
```

### State-tree replacements

The active game is a nested state machine. Typical paths are:

```text
EntireGame -> Lobby

EntireGame -> Ingame -> Planning -> PlaceOrders

EntireGame -> Ingame -> Action -> ResolveMarchOrder
           -> Combat -> ChooseHouseCard

EntireGame -> Ingame -> Westeros -> ClashOfKings -> Bidding
```

Calling `setChildGameState(...)` marks a state subtree dirty and generates a
new UUID `leafStateId`. At the end of processing a client command, the server
sends a player-specific replacement:

```json
{
  "type": "game-state-change",
  "level": 4,
  "serializedGameState": {"type": "combat", "...": "..."},
  "newLeafId": "db3cc3f4-8063-4de0-a976-ecf7e1006c2f",
  "waitedForUserIds": ["2", "3"]
}
```

`level` identifies where in the tree the replacement starts. The browser walks
to the parent at `level - 1`, deserializes `serializedGameState`, and replaces
that parent's child. A transition from lobby to game is a level-1 replacement;
a transition deep inside combat can replace only that deep subtree.

`newLeafId` identifies the exact decision state. The root Python harness calls
this `stateId` and uses it as a durable decision boundary. `waitedForUserIds`
is the authoritative list of users who may/must act now.

## 3. Connection and authentication

The development client reads the URL hash as:

```text
http://localhost:<client-port>/static/#<userId>.<authToken>.<gameId>
```

It opens the configured game-server WebSocket and sends:

```json
{
  "type": "authenticate",
  "authData": {
    "userId": "1",
    "requestUserId": "1",
    "gameId": "1",
    "authToken": "1"
  }
}
```

The server checks the user, token, game, and ban state. It then attaches this
socket to the game's `User`. One user can have multiple connected sockets; a
broadcast to a user is sent to all of that user's open sockets.

The first response contains a full, player-scoped snapshot:

```json
{
  "type": "authenticate-response",
  "userId": "1",
  "game": {
    "id": "1",
    "name": "Local Test Game",
    "users": [
      {
        "id": "1",
        "name": "Super Long Player Name #1",
        "settings": {
          "mapScrollbar": true,
          "chatHouseNames": true,
          "muted": true
        }
      }
    ],
    "ownerUserId": "1",
    "publicChatRoomId": "chat-Chat for game 1",
    "gameSettings": {
      "setupId": "mother-of-dragons",
      "playerCount": 8,
      "pbem": true,
      "vassals": true,
      "seaOrderTokens": true,
      "allowGiftingPowerTokens": true,
      "ironBank": true
    },
    "leafStateId": "483f5a54-58cd-49b3-9f62-245fd6e11588",
    "childGameState": {
      "type": "lobby",
      "availableHouseIds": [
        "baratheon", "lannister", "stark", "martell",
        "greyjoy", "tyrell", "arryn", "targaryen"
      ],
      "players": [],
      "readyUsers": null
    }
  }
}
```

Other connected clients then receive `new-user` and
`update-connection-status`. A reconnect receives another complete
`authenticate-response`; it does not need to replay missed events.

At any time an authenticated client can explicitly request a fresh snapshot:

```json
{"type":"sync-game","requestId":"my-request-123"}
```

The response echoes the ID:

```json
{"type":"game-snapshot","requestId":"my-request-123","game":{"...":"full player-scoped game"}}
```

## 4. Lobby: choosing a house

The browser sends:

```json
{"type":"choose-house","house":"targaryen","password":""}
```

The server checks availability and the lobby password, replaces any previous
choice by that user, then broadcasts the complete house-to-user assignment:

```json
{
  "type": "house-chosen",
  "players": [
    ["targaryen", "1"],
    ["stark", "2"],
    ["lannister", "3"],
    ["baratheon", "4"]
  ]
}
```

This is a useful recurring pattern: the command is phrased as the requested
operation, but the response often contains the resulting authoritative state.

For PBEM games the owner sends `launch-game` and startup is immediate. Live
games first broadcast `ready-check`; players send `ready`, and the game starts
only when everyone is ready.

The exact owner-client sequence captured locally was:

```text
C->S authenticate
S->C authenticate-response
S->C new-user / connection updates as other clients joined
C->S choose-house
S->C house-chosen                       (broadcast after every choice)
C->S launch-game
S->C game-started
S->C add-game-log                       (house assignments)
S->C update-house-cards                 (one per player-controlled house)
S->C update-draft-pool
S->C update-loan-cards
S->C add-game-log                       (turn 1 begins)
S->C new-turn
S->C vassal-relations
S->C add-game-log                       (initial world snapshot)
S->C add-game-log                       (claim-vassals began)
S->C game-state-change                  (Lobby -> Ingame)
```

Every connected client received the broadcast messages. The final
`game-state-change` was 6,204 base64 characters for player 1, and its active
path was:

```text
ingame -> planning -> claim-vassals -> claim-vassal
```

The server was waiting for user 4, who controlled Baratheon and was first on
the Iron Throne track.

## 5. Where the initial armies come from

In the standard setups, choosing a house does **not** send a series of army
placement messages. `beginGame` creates the board from the selected setup on
the authoritative server. The level-1 `game-state-change` that replaces the
lobby with `ingame` embeds the complete initial world.

For example, player 1's real startup state contained:

```json
{
  "game": {
    "turn": 1,
    "lastUnitId": 53,
    "world": {
      "regions": [
        {
          "id": "pentos",
          "units": [
            {"id":45,"type":"knight","wounded":false,"allegiance":"targaryen"},
            {"id":46,"type":"footman","wounded":false,"allegiance":"targaryen"}
          ],
          "garrison": 2
        },
        {
          "id": "port-of-pentos",
          "units": [
            {"id":47,"type":"ship","wounded":false,"allegiance":"targaryen"}
          ]
        }
      ]
    }
  }
}
```

The client renders the map from these region objects. Units are referred to by
stable numeric IDs in later messages, while regions, houses, cards, and most
other game objects use string IDs.

Some variants add interactive setup states such as drafting, mustering, or
selecting units/regions. In those cases clients send the appropriate
`select-*` or `muster` command and receive ordinary `game-state-change`,
`add-units`, `remove-units`, and log events. The fixed initial setup above is
the common case and is why no initial `add-units` burst appeared in the capture.

## 6. Planning: secret orders and readiness

The active tree becomes something like:

```text
ingame -> planning -> place-orders
```

The planning state contains:

```json
{
  "type": "planning",
  "placedOrders": [],
  "planningRestrictions": [],
  "revealedWesterosCardIds": [],
  "childGameState": {
    "type": "place-orders",
    "readyHouses": []
  }
}
```

A browser may place one order at a time:

```json
{"type":"place-order","regionId":"winterfell","orderId":13}
```

or atomically submit its complete draft:

```json
{
  "type": "submit-orders",
  "requestId": "orders-42",
  "orders": [
    {"regionId":"winterfell","orderId":13},
    {"regionId":"white-harbor","orderId":10},
    {"regionId":"the-shivering-sea","orderId":2}
  ]
}
```

The private acknowledgement is:

```json
{
  "type":"submit-orders-response",
  "requestId":"orders-42",
  "accepted":true,
  "reason":"ok",
  "stateId":"<current leaf UUID>"
}
```

Order secrecy is enforced in serialization and events:

- the player who placed an order receives `order-placed` with the real numeric
  `order` ID;
- everyone else receives the same region with `"order": null`, meaning “there
  is a face-down order here”; and
- player-specific state snapshots also replace other players' order IDs with
  `null`.

When a player commits, all clients receive `player-ready` and an
`add-game-log` whose nested data is `player-action`. Once all players (and any
vassal-order steps) finish, the server broadcasts:

```json
{
  "type":"reveal-orders",
  "orders":[
    ["winterfell",13],
    ["white-harbor",10],
    ["the-shivering-sea",2]
  ]
}
```

It then sends a `game-state-change` into the action phase. The archived round-2
snapshot shows the resulting public `ordersOnBoard`, for example:

```json
[
  ["white-harbor",10],
  ["greywater-watch",7],
  ["ironmans-bay",2],
  ["the-golden-sound",7],
  ["dragonstone",12]
]
```

## 7. The action phase

The action state moves through children in rules order:

```text
use-raven -> resolve-raid-order -> resolve-march-order
          -> resolve-consolidate-power -> end-of-round work
```

The active child tells the browser both what panel to render and who may act.
Representative browser commands are:

```json
{"type":"replace-order","regionId":"winterfell","orderId":2}
```

```json
{"type":"resolve-raid","orderRegionId":"winterfell","targetRegionId":null}
```

```json
{
  "type":"resolve-march-order",
  "startingRegionId":"ironmans-bay",
  "moves":[["the-golden-sound",[8]]],
  "leavePowerToken":false
}
```

The server validates each command against the current state and commanding
player. Other clients learn the result through a combination of:

- `action-phase-change-order` when an order changes or is consumed;
- `move-units`, `add-units`, `remove-units`, and `units-wounded` for board
  mutations;
- `change-control-power-token`, `change-power-token`, `change-garrison`, and
  similar counters;
- `game-state-change` for the next decision; and
- `add-game-log` for semantic history such as `raid-done`, `march-resolved`,
  or `attack`.

The log is important: low-level mutation events say what changed, while its
`data` says what game action caused the change.

## 8. Westeros cards and other decks

Round 1 normally goes straight to planning. A later `beginNewRound` broadcasts
`new-turn`, then changes the state to `westeros`.

When the Westeros phase starts, the server removes the top card from each
deck, marks it discarded, puts it at the bottom, applies immediate effects,
and broadcasts `update-westeros-decks`. Player snapshots deliberately shuffle
the unrevealed part of every deck; clients can see deck composition but not
future server order.

Which cards were actually drawn is conveyed by the Westeros state and logs.
From the archived round-2 game:

```json
{
  "type":"add-game-log",
  "data":{
    "type":"westeros-cards-drawn",
    "westerosCardTypes":[
      "a-throne-of-blades",
      "clash-of-kings",
      "put-to-the-sword"
    ],
    "addedWildlingStrength":2,
    "revealAndResolveTop3WesterosDeck4Cards":false
  }
}
```

The state subtree contains the concrete numeric IDs:

```json
{
  "type":"westeros",
  "revealedCardIds":[9,17,22],
  "currentCardI":0,
  "planningRestrictions":[],
  "childGameState":{"type":"a-throne-of-blades","...":"..."}
}
```

As resolution advances, every client receives:

```json
{"type":"proceed-westeros-card","currentCardI":1}
```

and usually a `game-state-change` describing the card's decision state, such as
mustering, bidding, or a simple choice. Effects use the same ordinary mutation
events as the rest of the game.

Wildling cards are separate. When an attack resolves, all clients receive
`reveal-wildling-card` with the card ID and an `add-game-log` with nested type
`wildling-card-revealed`. A Raven peek is private: `reveal-top-wildling-card`
is sent only to the entitled user; later `hide-top-wildling-card` removes it.

House cards are not drawn each round. They are selected secretly during
combat, then revealed together as described next.

## 9. Exactly how a battle becomes visible

A battle starts when a valid `resolve-march-order` moves at least one unit into
an enemy-controlled region. The server:

1. logs an `attack`;
2. replaces the march child with a `combat` state;
3. automatically handles obvious support, otherwise enters support decisions;
4. enters `choose-house-card`; and
5. broadcasts a player-specific `game-state-change`.

That `game-state-change` is the main “a battle is now happening” notification.
There is no separate top-level `battle-started` event.

Here is the real archived state seen during a Greyjoy attack from Ironman's Bay
into Lannister's Golden Sound:

```json
{
  "type":"combat",
  "order":2,
  "attackerId":"greyjoy",
  "defenderId":"lannister",
  "houseCombatDatas":[
    ["greyjoy",{
      "army":[8],
      "houseCardId":null,
      "regionId":"ironmans-bay"
    }],
    ["lannister",{
      "army":[13],
      "houseCardId":null,
      "regionId":"the-golden-sound"
    }]
  ],
  "supporters":[],
  "houseCardModifiers":[],
  "valyrianSteelBladeUser":null,
  "stats":[],
  "childGameState":{
    "type":"choose-house-card",
    "choosableHouseCards":[
      ["greyjoy",[
        "aeron-damphair","dagmar-cleftjaw","asha-greyjoy",
        "balon-greyjoy","theon-greyjoy","victarion-greyjoy",
        "euron-crows-eye"
      ]],
      ["lannister",[
        "cersei-lannister","ser-kevan-lannister","tyrion-lannister",
        "ser-jaime-lannister","the-hound","ser-gregor-clegane",
        "tywin-lannister"
      ]]
    ],
    "houseCards":[]
  }
}
```

The same message said `waitedForUserIds: ["2", "3"]`, so Greyjoy and
Lannister could act simultaneously.

### Secret selection and simultaneous reveal

Lannister sent:

```json
{
  "type":"choose-house-card",
  "houseCardId":"ser-gregor-clegane",
  "dontSkipVsbQuestion":false
}
```

The chooser receives:

```json
{
  "type":"house-card-chosen",
  "houseId":"lannister",
  "houseCardId":"ser-gregor-clegane",
  "dontSkipVsbQuestion":false
}
```

Every other client receives the deliberately redacted version:

```json
{
  "type":"house-card-chosen",
  "houseId":"lannister",
  "houseCardId":null,
  "dontSkipVsbQuestion":false
}
```

So all clients know Lannister has committed, but only Lannister knows the card.
After both sides commit, all clients receive the simultaneous reveal:

```json
{
  "type":"change-combat-house-card",
  "houseCardIds":[
    ["greyjoy","euron-crows-eye"],
    ["lannister","ser-gregor-clegane"]
  ],
  "animate":true
}
```

If Tides of Battle is enabled, each participant first gets its own private
`change-combat-tides-of-battle-card`, with the enemy value `null`. Once it is
time to reveal, a broadcast of that same message type contains both card IDs.

### Outcome and board mutation

The server calculates a `CombatStats` row for each side and broadcasts it:

```json
{
  "type":"update-combat-stats",
  "stats":[
    {
      "house":"greyjoy",
      "region":"ironmans-bay",
      "army":1,
      "armyUnits":["ship"],
      "woundedUnits":[],
      "orderBonus":0,
      "support":0,
      "garrison":0,
      "houseCard":"euron-crows-eye",
      "houseCardStrength":4,
      "valyrianSteelBlade":0,
      "total":5,
      "isWinner":true
    },
    {
      "house":"lannister",
      "region":"the-golden-sound",
      "army":1,
      "armyUnits":["ship"],
      "woundedUnits":[],
      "orderBonus":0,
      "support":0,
      "garrison":0,
      "houseCard":"ser-gregor-clegane",
      "houseCardStrength":3,
      "valyrianSteelBlade":0,
      "total":4,
      "isWinner":false
    }
  ]
}
```

The exact event order observed by the Greyjoy client was:

```text
house-card-chosen                 (Lannister committed; ID hidden)
add-game-log                      (player action)
house-card-chosen                 (Greyjoy's own choice)
add-game-log                      (player action)
add-game-log                      (both revealed in semantic history)
change-combat-house-card          (public simultaneous reveal)
update-combat-stats               (Greyjoy 5, Lannister 4)
add-game-log                      (combat-result)
change-state-house-card           (Greyjoy card becomes used)
change-state-house-card           (Lannister card becomes used)
add-game-log                      (casualty/retreat resolution)
combat-change-army                (defending combat army adjusted)
remove-units                      (Lannister ship removed)
action-phase-change-order         (Golden Sound order removed)
add-game-log                      (movement/result detail)
move-units                        (Greyjoy ship 8 enters Golden Sound)
action-phase-change-order         (Ironman's Bay march removed)
game-state-change                 (leave combat; next march decision)
```

The semantic result was also sent in an `add-game-log`:

```json
{
  "type":"combat-result",
  "winner":"greyjoy",
  "stats":[{"house":"greyjoy","total":5,"isWinner":true},{"house":"lannister","total":4,"isWinner":false}]
}
```

The following authoritative snapshot showed region `ironmans-bay` empty and
unit 8 in `the-golden-sound` with allegiance `greyjoy`.

## 10. End of round and end of game

After march resolution, the server resolves consolidate-power orders, applies
their ordinary counter/unit messages, then calls `beginNewRound`. Clients see
`new-turn` followed by either a Westeros subtree (round 2 onward) or the next
planning subtree.

Victory is checked at the relevant rule boundaries and at the round limit.
There is no dedicated `game-ended` WebSocket message. Clients learn the result
through:

- `add-game-log` with nested `{"type":"winner-declared","winner":"stark"}`;
  and
- `game-state-change` whose Ingame child is `{"type":"game-ended", ...}`.

The archived deterministic game ended with Stark declared as winner at the
configured two-round limit.

## 11. Who receives what

Not every message is actually identical for every client.

| Situation | Recipient/data policy |
|---|---|
| Normal public mutation | Broadcast to every game user and each open socket |
| Full snapshot | Serialized separately for the requesting user |
| `game-state-change` | Crafted separately per connected user |
| Secret order placement | Real order ID to owner; `null` to others |
| House-card commitment | Real card ID to chooser; `null` to others |
| Tides of Battle draw | Own card to each participant; enemy card hidden |
| Raven wildling peek | Only the entitled player's user sockets |
| Private objectives/cards | Included only where the serializer authorizes it |
| Game log | Usually public, but its serializer can filter player-sensitive log data |

This player-specific serialization is why capturing one browser is not always
enough to understand the protocol. Two clients can receive messages with the
same `type` but different values.

## 12. Complete top-level server message catalogue

The protocol currently defines the following server-to-browser messages. Some
rare variant/card messages may never appear in a normal base-game run.

### Connection, snapshots, users, and settings

`authenticate-response`, `banned-response`, `game-snapshot`, `new-user`,
`update-connection-status`, `update-other-users-with-same-ip`,
`settings-changed`, `game-settings-changed`, `password-response`,
`hide-or-reveal-user-names`, `new-private-chat-room`, `clear-chat-room`,
`user-banned`, `user-unbanned`

### State machine, waiting, lifecycle, and clocks

`game-state-change`, `game-started`, `new-turn`, `next-house`,
`update-waited-for-data`, `start-player-clock`, `stop-player-clock`,
`game-paused`, `game-resumed`

### Lobby, draft, players, and vassals

`house-chosen`, `ready-check`, `player-ready`, `player-unready`,
`player-replaced`, `vassal-replaced`, `replaced-by-vassal`, `houses-swapped`,
`vassal-relations`, `update-draft-pool`, `update-draft-state`,
`update-game-house-cards`, `update-house-cards`,
`update-old-player-house-cards`, `update-deleted-house-cards`,
`later-house-cards-applied`

### Planning and orders

`order-placed`, `remove-placed-order`, `submit-orders-response`,
`reveal-orders`, `remove-orders`, `raven-order-replaced`,
`action-phase-change-order`

### Board, armies, ownership, tracks, and resources

`move-units`, `add-units`, `remove-units`, `units-wounded`,
`combat-change-army`, `change-garrison`, `change-control-power-token`,
`change-power-token`, `supply-adjusted`, `change-tracker`,
`change-valyrian-steel-blade-use`, `change-wildling-strength`,
`loyalty-token-gained`, `loyalty-token-placed`,
`dragon-strength-token-removed`, `update-region-modifiers`,
`update-overwritten-dominance-token-holder`

### Cards, Westeros, wildlings, loans, and objectives

`update-westeros-decks`, `proceed-westeros-card`,
`begin-see-top-wildling-card`, `reveal-top-wildling-card`,
`hide-top-wildling-card`, `reveal-wildling-card`,
`crow-killers-step-changed`, `wilding-ties-resolved`,
`preemptive-raid-new-attack`, `update-loan-cards`,
`update-completed-objectives`, `update-secret-objectives`,
`update-selectable-objectives`, `sync-shifting-ambitions`

### Bidding, combat, and house-card resolution

`bid-done`, `bidding-next-track`, `reveal-bids`, `support-declared`,
`support-refused`, `house-card-chosen`, `change-combat-house-card`,
`change-combat-tides-of-battle-card`, `manipulate-combat-house-card`,
`change-state-house-card`, `update-house-card-modifier`,
`update-combat-stats`

### History, votes, and game options

`add-game-log`, `vote-started`, `vote-cancelled`, `vote-done`,
`update-max-turns`, `accept-all-loyalty-token-movements-changed`

## 13. Browser-to-server command catalogue

These are the commands the browser can currently send.

### Transport and lobby

`ping`, `authenticate`, `sync-game`, `choose-house`, `launch-game`, `ready`,
`unready`, `kick-player`, `cancel-game`, `set-password`, `change-settings`,
`change-game-settings`, `create-private-chat-room`, `update-note`

### Planning and actions

`place-order`, `submit-orders`, `select-orders`, `replace-order`,
`skip-replace-order`, `resolve-raid`, `resolve-march-order`,
`resolve-consolidate-power-choice`, `declare-support`, `refuse-support`,
`call-for-support-against-neutral-force`, `gift-power-tokens`

### Cards, combat, and rule decisions

`choose-house-card`, `choose-casualties`, `use-valyrian-steel-blade`,
`choose-choice`, `choose-see-top-wildling-card`,
`choose-top-wildling-card-action`, `select-house-card`,
`select-westeros-card`, `select-region`, `select-units`, `muster`,
`reconcile-armies`, `resolve-ties`, `bid`, `claim-vassal`,
`distribute-power-tokens`, `drop-power-tokens`, `move-loyalty-token`,
`place-sellswords`, `resolve-spymaster`, `select-objectives`,
`score-objective`, `remove-power-token`, `add-power-token`,
`remove-garrison`, `add-garrison`

### Votes and moderation

`vote`, `cancel-vote`, `launch-cancel-game-vote`,
`launch-replace-player-vote`, `launch-replace-player-by-vassal-vote`,
`launch-replace-vassal-by-player-vote`, `launch-end-game-vote`,
`launch-pause-game-vote`, `launch-resume-game-vote`,
`launch-extend-player-clocks-vote`, `launch-swap-houses-vote`,
`launch-declare-winner-vote`, `change-accept-all-loyalty-token-movements`,
`ban-user`, `unban-user`, `game-log-seen`

## 14. Source map for further exploration

Start with these files in this order:

1. `swords-and-ravens/agot-bg-game-server/src/messages/ClientMessage.ts` and
   `swords-and-ravens/agot-bg-game-server/src/messages/ServerMessage.ts` define
   the wire vocabulary.
2. `swords-and-ravens/agot-bg-game-server/src/server/GlobalServer.ts` owns sockets,
   authentication, schema validation, persistence hooks, and fan-out.
3. `swords-and-ravens/agot-bg-game-server/src/common/EntireGame.ts` owns the state tree,
   `game-state-change`, per-user serialization, and high-level dispatch.
4. `swords-and-ravens/agot-bg-game-server/src/common/GameState.ts` implements nested states and
   dirty-subtree tracking.
5. `swords-and-ravens/agot-bg-game-server/src/common/ingame-game-state/IngameGameState.ts` owns
   the board and round transitions.
6. `swords-and-ravens/agot-bg-game-server/src/common/ingame-game-state/planning-game-state/place-orders-game-state/PlaceOrdersGameState.ts`
   is the clearest example of secret per-player event shaping.
7. `swords-and-ravens/agot-bg-game-server/src/common/ingame-game-state/westeros-game-state/WesterosGameState.ts`
   shows card draw and resolution.
8. `swords-and-ravens/agot-bg-game-server/src/common/ingame-game-state/action-game-state/resolve-march-order-game-state/combat-game-state/`
   contains combat, card secrecy, strength calculation, casualties, and
   retreat.
9. `swords-and-ravens/agot-bg-game-server/src/client/GameClient.ts` and each state's
   `onServerMessage` show exactly how browser state is patched.
10. `src/raven_harness/game/state.py` is a compact Python implementation of
    the same client-side patching rules and is useful as a protocol index.

## 15. Important design consequences

- **The server is authoritative.** Client commands are requests, and invalid
  commands are generally ignored or privately rejected.
- **State and events are complementary.** The state tree tells the UI what is
  true and what decision is active; mutations animate/update it; logs explain
  the game meaning.
- **Resync is cheap conceptually.** A stale/reconnected client can replace its
  local model with one player-scoped snapshot instead of replaying history.
- **Privacy lives in serializers and recipient selection.** Order/card secrecy
  is not provided by encryption between players; the server sends redacted or
  shuffled data to clients that are not entitled to the secret.
- **Phase changes are data.** The UI does not infer “combat started” merely
  from a move. It receives a serialized `combat` state and renders the component
  corresponding to the leaf state.
- **The game log is transported like any other mutation.** There is no separate
  history socket or event stream; each entry is an `add-game-log` message and
  full snapshots also contain serialized logs.
