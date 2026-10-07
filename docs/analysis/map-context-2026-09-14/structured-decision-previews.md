# Current decision instructions and final-answer schemas

Offline previews of the same ten historical decisions. No model calls were made. These instructions go in the current user message, not the system prompt.

## Case 1 — stark, round 1

You are playing House Stark in round 1. This is a new decision; you have not submitted an action for it.

You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision.

You may investigate before deciding. The available tools have these purposes:

check_neighbours looks up an area's direct neighbours and their current owners, units, wounds, orders, terrain and castles. Ask about the battlefield when checking possible support. Direct neighbours are not the same as all legal ship-transport destinations.

recall_game_state retrieves an earlier observation from your private game history. Use it when a past decision matters; the current observation takes precedence if facts differ.

remember_strategy records a proposed update to your private plan. It does not place orders or move units, and the note is saved only after your final action is accepted.

ask_rules_oracle asks a rules specialist a focused question using the local rulebook and FAQ. It explains rules; it does not choose or submit your action.

These tools do not submit a gameplay action. After a tool returns, you can inspect its result, ask another question, or finish your decision. You are not limited to one tool call.

When you are ready, return one final JSON answer matching the response schema. That final answer is your action submission; there is no gameplay tool or separate end-turn call to make. The harness checks it against the current game state before sending it to the server. Do not submit a tentative action just to find out what happens. If the schema has no remaining fields, submit {} to carry out the fully determined action.

### Final-answer schema

```json
{
  "properties": {
    "starting_region_id": {
      "description": "Region containing the march order and moving units.",
      "title": "Starting Region Id",
      "type": "string",
      "enum": [
        "the-shivering-sea",
        "white-harbor"
      ]
    },
    "moves": {
      "description": "Destination groups and moving unit IDs. Unlisted units stay in the source. An empty list discards the order. Every group must be legal and fit Supply; an illegal final action is rejected without submitting the march.",
      "items": {
        "additionalProperties": false,
        "properties": {
          "destination_region_id": {
            "title": "Destination Region Id",
            "type": "string",
            "enum": [
              "castle-black",
              "karhold",
              "moat-cailin",
              "the-narrow-sea",
              "widows-watch",
              "winterfell"
            ]
          },
          "unit_ids": {
            "items": {
              "type": "integer",
              "enum": [
                3,
                4
              ]
            },
            "minItems": 1,
            "title": "Unit Ids",
            "type": "array",
            "maxItems": 2
          }
        },
        "required": [
          "destination_region_id",
          "unit_ids"
        ],
        "title": "UnitMove",
        "type": "object"
      },
      "title": "Moves",
      "type": "array",
      "maxItems": 1
    },
    "leave_power_token": {
      "description": "Spend one available power token to preserve control when legally vacating the source area. This must be false if units remain or control cannot be established.",
      "title": "Leave Power Token",
      "type": "boolean"
    }
  },
  "required": [
    "starting_region_id",
    "moves",
    "leave_power_token"
  ],
  "title": "resolve_march_args",
  "type": "object",
  "additionalProperties": false,
  "description": "You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision."
}
```

## Case 2 — stark, round 5

You are playing House Stark in round 5. This is a new decision; you have not submitted an action for it.

You are placing planning orders for this round. Assign an order preference to each required occupied area, respecting the displayed restrictions and starred-order limit. Your final answer submits the whole order draft and marks your house ready. These orders determine what your armies can do later; this decision does not move units. The harness allocates the physical order tokens, preserving higher-priority preferences when not all requested categories fit the available tokens.

You may investigate before deciding. The available tools have these purposes:

check_neighbours looks up an area's direct neighbours and their current owners, units, wounds, orders, terrain and castles. Ask about the battlefield when checking possible support. Direct neighbours are not the same as all legal ship-transport destinations.

recall_game_state retrieves an earlier observation from your private game history. Use it when a past decision matters; the current observation takes precedence if facts differ.

remember_strategy records a proposed update to your private plan. It does not place orders or move units, and the note is saved only after your final action is accepted.

ask_rules_oracle asks a rules specialist a focused question using the local rulebook and FAQ. It explains rules; it does not choose or submit your action.

These tools do not submit a gameplay action. After a tool returns, you can inspect its result, ask another question, or finish your decision. You are not limited to one tool call.

When you are ready, return one final JSON answer matching the response schema. That final answer is your action submission; there is no gameplay tool or separate end-turn call to make. The harness checks it against the current game state before sending it to the server. Do not submit a tentative action just to find out what happens. If the schema has no remaining fields, submit {} to carry out the fully determined action.

### Final-answer schema

```json
{
  "properties": {
    "assignments": {
      "description": "The exact requested number of semantic order assignments.\nRegion IDs must be distinct. When there are fewer usable tokens than\noccupied regions, choose which regions receive no order.",
      "items": {
        "additionalProperties": false,
        "description": "One semantic order choice assigned to one board region.",
        "properties": {
          "region_id": {
            "description": "ID of a region containing your units.",
            "minLength": 1,
            "title": "Region Id",
            "type": "string",
            "enum": [
              "bay-of-ice",
              "castle-black",
              "karhold",
              "winterfell",
              "the-narrow-sea"
            ]
          },
          "preferred_order": {
            "description": "Preferred order category. The harness preserves this preference when the global physical-token inventory and Westeros restrictions permit it, and otherwise substitutes a legal category. The currently restricted categories are raid.",
            "enum": [
              "march",
              "defense",
              "support",
              "consolidate_power",
              "raid"
            ],
            "title": "OrderCategory",
            "type": "string"
          },
          "starred_preference": {
            "description": "Prefer a starred token when it is legal and available, or avoid one unless the order inventory forces it.",
            "enum": [
              "prefer",
              "avoid"
            ],
            "title": "StarredPreference",
            "type": "string"
          },
          "priority": {
            "description": "Relative importance from 0 to 100. Higher-priority regions receive scarce starred tokens and stronger March modifiers first.",
            "maximum": 100,
            "minimum": 0,
            "title": "Priority",
            "type": "integer"
          }
        },
        "required": [
          "region_id",
          "preferred_order",
          "starred_preference",
          "priority"
        ],
        "title": "OrderAssignment",
        "type": "object"
      },
      "title": "Assignments",
      "type": "array",
      "minItems": 5,
      "maxItems": 5
    }
  },
  "required": [
    "assignments"
  ],
  "title": "submit_orders_args",
  "type": "object",
  "additionalProperties": false,
  "description": "You are placing planning orders for this round. Assign an order preference to each required occupied area, respecting the displayed restrictions and starred-order limit. Your final answer submits the whole order draft and marks your house ready. These orders determine what your armies can do later; this decision does not move units. The harness allocates the physical order tokens, preserving higher-priority preferences when not all requested categories fit the available tokens."
}
```

## Case 3 — stark, round 7

You are playing House Stark in round 7. This is a new decision; you have not submitted an action for it.

You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision.

This march starts in Winterfell. No control token will be spent. These details are already settled. Your final answer only needs the remaining choices.

You may investigate before deciding. The available tools have these purposes:

check_neighbours looks up an area's direct neighbours and their current owners, units, wounds, orders, terrain and castles. Ask about the battlefield when checking possible support. Direct neighbours are not the same as all legal ship-transport destinations.

recall_game_state retrieves an earlier observation from your private game history. Use it when a past decision matters; the current observation takes precedence if facts differ.

remember_strategy records a proposed update to your private plan. It does not place orders or move units, and the note is saved only after your final action is accepted.

ask_rules_oracle asks a rules specialist a focused question using the local rulebook and FAQ. It explains rules; it does not choose or submit your action.

These tools do not submit a gameplay action. After a tool returns, you can inspect its result, ask another question, or finish your decision. You are not limited to one tool call.

When you are ready, return one final JSON answer matching the response schema. That final answer is your action submission; there is no gameplay tool or separate end-turn call to make. The harness checks it against the current game state before sending it to the server. Do not submit a tentative action just to find out what happens. If the schema has no remaining fields, submit {} to carry out the fully determined action.

### Final-answer schema

```json
{
  "properties": {
    "moves": {
      "description": "Destination groups and moving unit IDs. Unlisted units stay in the source. An empty list discards the order. Every group must be legal and fit Supply; an illegal final action is rejected without submitting the march.",
      "items": {
        "additionalProperties": false,
        "properties": {
          "destination_region_id": {
            "title": "Destination Region Id",
            "type": "string",
            "enum": [
              "castle-black",
              "flints-finger",
              "greywater-watch",
              "karhold",
              "moat-cailin",
              "the-stony-shore",
              "white-harbor"
            ]
          }
        },
        "required": [
          "destination_region_id"
        ],
        "title": "UnitMove",
        "type": "object"
      },
      "title": "Moves",
      "type": "array",
      "maxItems": 1
    }
  },
  "required": [
    "moves"
  ],
  "title": "resolve_march_args",
  "type": "object",
  "additionalProperties": false,
  "description": "You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision."
}
```

## Case 4 — stark, round 10

You are playing House Stark in round 10. This is a new decision; you have not submitted an action for it.

You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision.

No control token will be spent. These details are already settled. Your final answer only needs the remaining choices.

You may investigate before deciding. The available tools have these purposes:

check_neighbours looks up an area's direct neighbours and their current owners, units, wounds, orders, terrain and castles. Ask about the battlefield when checking possible support. Direct neighbours are not the same as all legal ship-transport destinations.

recall_game_state retrieves an earlier observation from your private game history. Use it when a past decision matters; the current observation takes precedence if facts differ.

remember_strategy records a proposed update to your private plan. It does not place orders or move units, and the note is saved only after your final action is accepted.

ask_rules_oracle asks a rules specialist a focused question using the local rulebook and FAQ. It explains rules; it does not choose or submit your action.

These tools do not submit a gameplay action. After a tool returns, you can inspect its result, ask another question, or finish your decision. You are not limited to one tool call.

When you are ready, return one final JSON answer matching the response schema. That final answer is your action submission; there is no gameplay tool or separate end-turn call to make. The harness checks it against the current game state before sending it to the server. Do not submit a tentative action just to find out what happens. If the schema has no remaining fields, submit {} to carry out the fully determined action.

### Final-answer schema

```json
{
  "properties": {
    "starting_region_id": {
      "description": "Region containing the march order and moving units.",
      "title": "Starting Region Id",
      "type": "string",
      "enum": [
        "bay-of-ice",
        "moat-cailin"
      ]
    },
    "moves": {
      "description": "Destination groups and moving unit IDs. Unlisted units stay in the source. An empty list discards the order. Every group must be legal and fit Supply; an illegal final action is rejected without submitting the march.",
      "items": {
        "additionalProperties": false,
        "properties": {
          "destination_region_id": {
            "title": "Destination Region Id",
            "type": "string",
            "enum": [
              "greywater-watch",
              "port-of-winterfell",
              "seagard",
              "sunset-sea",
              "the-twins",
              "white-harbor",
              "winterfell"
            ]
          },
          "unit_ids": {
            "items": {
              "type": "integer",
              "enum": [
                40,
                48,
                55
              ]
            },
            "minItems": 1,
            "title": "Unit Ids",
            "type": "array",
            "maxItems": 3
          }
        },
        "required": [
          "destination_region_id",
          "unit_ids"
        ],
        "title": "UnitMove",
        "type": "object"
      },
      "title": "Moves",
      "type": "array",
      "maxItems": 2
    }
  },
  "required": [
    "starting_region_id",
    "moves"
  ],
  "title": "resolve_march_args",
  "type": "object",
  "additionalProperties": false,
  "description": "You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision."
}
```

## Case 6 — martell, round 3

You are playing House Martell in round 3. This is a new decision; you have not submitted an action for it.

You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision.

This march starts in Kingswood. These details are already settled. Your final answer only needs the remaining choices.

You may investigate before deciding. The available tools have these purposes:

check_neighbours looks up an area's direct neighbours and their current owners, units, wounds, orders, terrain and castles. Ask about the battlefield when checking possible support. Direct neighbours are not the same as all legal ship-transport destinations.

recall_game_state retrieves an earlier observation from your private game history. Use it when a past decision matters; the current observation takes precedence if facts differ.

remember_strategy records a proposed update to your private plan. It does not place orders or move units, and the note is saved only after your final action is accepted.

ask_rules_oracle asks a rules specialist a focused question using the local rulebook and FAQ. It explains rules; it does not choose or submit your action.

These tools do not submit a gameplay action. After a tool returns, you can inspect its result, ask another question, or finish your decision. You are not limited to one tool call.

When you are ready, return one final JSON answer matching the response schema. That final answer is your action submission; there is no gameplay tool or separate end-turn call to make. The harness checks it against the current game state before sending it to the server. Do not submit a tentative action just to find out what happens. If the schema has no remaining fields, submit {} to carry out the fully determined action.

### Final-answer schema

```json
{
  "properties": {
    "moves": {
      "description": "Destination groups and moving unit IDs. Unlisted units stay in the source. An empty list discards the order. Every group must be legal and fit Supply; an illegal final action is rejected without submitting the march.",
      "items": {
        "additionalProperties": false,
        "properties": {
          "destination_region_id": {
            "title": "Destination Region Id",
            "type": "string",
            "enum": [
              "storms-end",
              "the-boneway",
              "the-reach"
            ]
          },
          "unit_ids": {
            "items": {
              "type": "integer",
              "enum": [
                25,
                26
              ]
            },
            "minItems": 1,
            "title": "Unit Ids",
            "type": "array",
            "maxItems": 2
          }
        },
        "required": [
          "destination_region_id",
          "unit_ids"
        ],
        "title": "UnitMove",
        "type": "object"
      },
      "title": "Moves",
      "type": "array",
      "maxItems": 2
    },
    "leave_power_token": {
      "description": "Spend one available power token to preserve control when legally vacating the source area. This must be false if units remain or control cannot be established.",
      "title": "Leave Power Token",
      "type": "boolean"
    }
  },
  "required": [
    "moves",
    "leave_power_token"
  ],
  "title": "resolve_march_args",
  "type": "object",
  "additionalProperties": false,
  "description": "You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision."
}
```

## Case 8 — greyjoy, round 6

You are playing House Greyjoy in round 6. This is a new decision; you have not submitted an action for it.

You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision.

This march starts in Moat Cailin. These details are already settled. Your final answer only needs the remaining choices.

You may investigate before deciding. The available tools have these purposes:

check_neighbours looks up an area's direct neighbours and their current owners, units, wounds, orders, terrain and castles. Ask about the battlefield when checking possible support. Direct neighbours are not the same as all legal ship-transport destinations.

recall_game_state retrieves an earlier observation from your private game history. Use it when a past decision matters; the current observation takes precedence if facts differ.

remember_strategy records a proposed update to your private plan. It does not place orders or move units, and the note is saved only after your final action is accepted.

ask_rules_oracle asks a rules specialist a focused question using the local rulebook and FAQ. It explains rules; it does not choose or submit your action.

These tools do not submit a gameplay action. After a tool returns, you can inspect its result, ask another question, or finish your decision. You are not limited to one tool call.

When you are ready, return one final JSON answer matching the response schema. That final answer is your action submission; there is no gameplay tool or separate end-turn call to make. The harness checks it against the current game state before sending it to the server. Do not submit a tentative action just to find out what happens. If the schema has no remaining fields, submit {} to carry out the fully determined action.

### Final-answer schema

```json
{
  "properties": {
    "moves": {
      "description": "Destination groups and moving unit IDs. Unlisted units stay in the source. An empty list discards the order. Every group must be legal and fit Supply; an illegal final action is rejected without submitting the march.",
      "items": {
        "additionalProperties": false,
        "properties": {
          "destination_region_id": {
            "title": "Destination Region Id",
            "type": "string",
            "enum": [
              "greywater-watch",
              "seagard",
              "the-twins",
              "white-harbor",
              "winterfell"
            ]
          },
          "unit_ids": {
            "items": {
              "type": "integer",
              "enum": [
                6,
                37
              ]
            },
            "minItems": 1,
            "title": "Unit Ids",
            "type": "array",
            "maxItems": 2
          }
        },
        "required": [
          "destination_region_id",
          "unit_ids"
        ],
        "title": "UnitMove",
        "type": "object"
      },
      "title": "Moves",
      "type": "array",
      "maxItems": 2
    },
    "leave_power_token": {
      "description": "Spend one available power token to preserve control when legally vacating the source area. This must be false if units remain or control cannot be established.",
      "title": "Leave Power Token",
      "type": "boolean"
    }
  },
  "required": [
    "moves",
    "leave_power_token"
  ],
  "title": "resolve_march_args",
  "type": "object",
  "additionalProperties": false,
  "description": "You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision."
}
```

## Case 10 — martell, round 3

You are playing House Martell in round 3. This is a new decision; you have not submitted an action for it.

You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision.

This march starts in Princes Pass. No control token will be spent. These details are already settled. Your final answer only needs the remaining choices.

You may investigate before deciding. The available tools have these purposes:

check_neighbours looks up an area's direct neighbours and their current owners, units, wounds, orders, terrain and castles. Ask about the battlefield when checking possible support. Direct neighbours are not the same as all legal ship-transport destinations.

recall_game_state retrieves an earlier observation from your private game history. Use it when a past decision matters; the current observation takes precedence if facts differ.

remember_strategy records a proposed update to your private plan. It does not place orders or move units, and the note is saved only after your final action is accepted.

ask_rules_oracle asks a rules specialist a focused question using the local rulebook and FAQ. It explains rules; it does not choose or submit your action.

These tools do not submit a gameplay action. After a tool returns, you can inspect its result, ask another question, or finish your decision. You are not limited to one tool call.

When you are ready, return one final JSON answer matching the response schema. That final answer is your action submission; there is no gameplay tool or separate end-turn call to make. The harness checks it against the current game state before sending it to the server. Do not submit a tentative action just to find out what happens. If the schema has no remaining fields, submit {} to carry out the fully determined action.

### Final-answer schema

```json
{
  "properties": {
    "moves": {
      "description": "Destination groups and moving unit IDs. Unlisted units stay in the source. An empty list discards the order. Every group must be legal and fit Supply; an illegal final action is rejected without submitting the march.",
      "items": {
        "additionalProperties": false,
        "properties": {
          "destination_region_id": {
            "title": "Destination Region Id",
            "type": "string",
            "enum": [
              "dornish-marches",
              "starfall",
              "the-boneway",
              "three-towers",
              "yronwood"
            ]
          }
        },
        "required": [
          "destination_region_id"
        ],
        "title": "UnitMove",
        "type": "object"
      },
      "title": "Moves",
      "type": "array",
      "maxItems": 1
    }
  },
  "required": [
    "moves"
  ],
  "title": "resolve_march_args",
  "type": "object",
  "additionalProperties": false,
  "description": "You are resolving one of your March orders. Choose which units move and their destinations. Units you omit remain in the source area; you may split an army across destinations, and a single unit can march on its own. An empty moves list removes this March order without moving anyone. Only one destination may start combat. Use the reachable destinations in actionGuidance and keep the resulting armies within Supply. Leaving a control token costs one available power token and preserves control of the source when you legally vacate it. Compare castles gained and lost, and count support around the destination battlefield before choosing an attack. Your final answer resolves this one order; another remaining order is a later decision."
}
```

## Case 12 — martell, round 8

You are playing House Martell in round 8. This is a new decision; you have not submitted an action for it.

The wildlings won and Mammoth Riders imposes unit losses. Selected units are removed from the board. You are choosing the losses; the unselected units are not removed by this selection. Choose exactly 2 distinct units.

You may investigate before deciding. The available tools have these purposes:

check_neighbours looks up an area's direct neighbours and their current owners, units, wounds, orders, terrain and castles. Ask about the battlefield when checking possible support. Direct neighbours are not the same as all legal ship-transport destinations.

recall_game_state retrieves an earlier observation from your private game history. Use it when a past decision matters; the current observation takes precedence if facts differ.

remember_strategy records a proposed update to your private plan. It does not place orders or move units, and the note is saved only after your final action is accepted.

ask_rules_oracle asks a rules specialist a focused question using the local rulebook and FAQ. It explains rules; it does not choose or submit your action.

These tools do not submit a gameplay action. After a tool returns, you can inspect its result, ask another question, or finish your decision. You are not limited to one tool call.

When you are ready, return one final JSON answer matching the response schema. That final answer is your action submission; there is no gameplay tool or separate end-turn call to make. The harness checks it against the current game state before sending it to the server. Do not submit a tentative action just to find out what happens. If the schema has no remaining fields, submit {} to carry out the fully determined action.

### Final-answer schema

```json
{
  "properties": {
    "unit_ids_to_destroy": {
      "description": "Select exactly 2 distinct unit IDs from this list.",
      "items": {
        "type": "integer",
        "enum": [
          24,
          27,
          46
        ]
      },
      "title": "Unit Ids",
      "type": "array",
      "minItems": 2,
      "maxItems": 2
    }
  },
  "required": [
    "unit_ids_to_destroy"
  ],
  "title": "select_units_args",
  "type": "object",
  "additionalProperties": false,
  "description": "The wildlings won and Mammoth Riders imposes unit losses. Selected units are removed from the board. You are choosing the losses; the unselected units are not removed by this selection. Choose exactly 2 distinct units."
}
```

## Case 14 — greyjoy, round 2

You are playing House Greyjoy in round 2. This is a new decision; you have not submitted an action for it.

You are placing planning orders for this round. Assign an order preference to each required occupied area, respecting the displayed restrictions and starred-order limit. Your final answer submits the whole order draft and marks your house ready. These orders determine what your armies can do later; this decision does not move units. The harness allocates the physical order tokens, preserving higher-priority preferences when not all requested categories fit the available tokens.

You may investigate before deciding. The available tools have these purposes:

check_neighbours looks up an area's direct neighbours and their current owners, units, wounds, orders, terrain and castles. Ask about the battlefield when checking possible support. Direct neighbours are not the same as all legal ship-transport destinations.

recall_game_state retrieves an earlier observation from your private game history. Use it when a past decision matters; the current observation takes precedence if facts differ.

remember_strategy records a proposed update to your private plan. It does not place orders or move units, and the note is saved only after your final action is accepted.

ask_rules_oracle asks a rules specialist a focused question using the local rulebook and FAQ. It explains rules; it does not choose or submit your action.

These tools do not submit a gameplay action. After a tool returns, you can inspect its result, ask another question, or finish your decision. You are not limited to one tool call.

When you are ready, return one final JSON answer matching the response schema. That final answer is your action submission; there is no gameplay tool or separate end-turn call to make. The harness checks it against the current game state before sending it to the server. Do not submit a tentative action just to find out what happens. If the schema has no remaining fields, submit {} to carry out the fully determined action.

### Final-answer schema

```json
{
  "properties": {
    "assignments": {
      "description": "The exact requested number of semantic order assignments.\nRegion IDs must be distinct. When there are fewer usable tokens than\noccupied regions, choose which regions receive no order.",
      "items": {
        "additionalProperties": false,
        "description": "One semantic order choice assigned to one board region.",
        "properties": {
          "region_id": {
            "description": "ID of a region containing your units.",
            "minLength": 1,
            "title": "Region Id",
            "type": "string",
            "enum": [
              "pyke",
              "ironmans-bay",
              "port-of-pyke",
              "greywater-watch"
            ]
          },
          "preferred_order": {
            "description": "Preferred order category. The harness preserves this preference when the global physical-token inventory and Westeros restrictions permit it, and otherwise substitutes a legal category. The currently restricted categories are none.",
            "enum": [
              "march",
              "defense",
              "support",
              "consolidate_power",
              "raid"
            ],
            "title": "OrderCategory",
            "type": "string"
          },
          "starred_preference": {
            "description": "Prefer a starred token when it is legal and available, or avoid one unless the order inventory forces it.",
            "enum": [
              "prefer",
              "avoid"
            ],
            "title": "StarredPreference",
            "type": "string"
          },
          "priority": {
            "description": "Relative importance from 0 to 100. Higher-priority regions receive scarce starred tokens and stronger March modifiers first.",
            "maximum": 100,
            "minimum": 0,
            "title": "Priority",
            "type": "integer"
          }
        },
        "required": [
          "region_id",
          "preferred_order",
          "starred_preference",
          "priority"
        ],
        "title": "OrderAssignment",
        "type": "object"
      },
      "title": "Assignments",
      "type": "array",
      "minItems": 4,
      "maxItems": 4
    }
  },
  "required": [
    "assignments"
  ],
  "title": "submit_orders_args",
  "type": "object",
  "additionalProperties": false,
  "description": "You are placing planning orders for this round. Assign an order preference to each required occupied area, respecting the displayed restrictions and starred-order limit. Your final answer submits the whole order draft and marks your house ready. These orders determine what your armies can do later; this decision does not move units. The harness allocates the physical order tokens, preserving higher-priority preferences when not all requested categories fit the available tokens."
}
```

## Case 17 — greyjoy, round 8

You are playing House Greyjoy in round 8. This is a new decision; you have not submitted an action for it.

The wildlings won and Mammoth Riders imposes unit losses. Selected units are removed from the board. You are choosing the losses; the unselected units are not removed by this selection. Choose exactly 2 distinct units.

You may investigate before deciding. The available tools have these purposes:

check_neighbours looks up an area's direct neighbours and their current owners, units, wounds, orders, terrain and castles. Ask about the battlefield when checking possible support. Direct neighbours are not the same as all legal ship-transport destinations.

recall_game_state retrieves an earlier observation from your private game history. Use it when a past decision matters; the current observation takes precedence if facts differ.

remember_strategy records a proposed update to your private plan. It does not place orders or move units, and the note is saved only after your final action is accepted.

ask_rules_oracle asks a rules specialist a focused question using the local rulebook and FAQ. It explains rules; it does not choose or submit your action.

These tools do not submit a gameplay action. After a tool returns, you can inspect its result, ask another question, or finish your decision. You are not limited to one tool call.

When you are ready, return one final JSON answer matching the response schema. That final answer is your action submission; there is no gameplay tool or separate end-turn call to make. The harness checks it against the current game state before sending it to the server. Do not submit a tentative action just to find out what happens. If the schema has no remaining fields, submit {} to carry out the fully determined action.

### Final-answer schema

```json
{
  "properties": {
    "unit_ids_to_destroy": {
      "description": "Select exactly 2 distinct unit IDs from this list.",
      "items": {
        "type": "integer",
        "enum": [
          7,
          8,
          9,
          6,
          37
        ]
      },
      "title": "Unit Ids",
      "type": "array",
      "minItems": 2,
      "maxItems": 2
    }
  },
  "required": [
    "unit_ids_to_destroy"
  ],
  "title": "select_units_args",
  "type": "object",
  "additionalProperties": false,
  "description": "The wildlings won and Mammoth Riders imposes unit losses. Selected units are removed from the board. You are choosing the losses; the unselected units are not removed by this selection. Choose exactly 2 distinct units."
}
```
