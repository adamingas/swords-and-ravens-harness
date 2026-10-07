# Round 3: recorded decisions and state evidence

<a id="d023"></a>

## D023 — stark — choose_option (completed)

Run `0fa8f241-6279-42d0-9871-bb339f440f5e`. Requests: 9; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"choice_index": 2}`

Handoff: Choose No restrictions to retain all order options. This preserves ability to use March +1 orders for attacks given low supply, and Defense orders to protect our castles, avoiding any self‑imposed penalties.

Previous plan: Move footman from Moat Cailin to White Harbor, consolidating forces while spending a power token to keep Moat Cailin castle under our control.

Pending: `{"type": "simple-choice", "houseId": "stark", "description": "The holder of the Valyrian Steel Blade can choose between No March +1 Orders, no Defense Orders, or no restrictions.", "choices": ["No March +1 Orders", "No Defense Orders", "No restrictions"]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d024"></a>

## D024 — baratheon — place-orders (failed)

Run `b2430998-f70f-45a6-960a-7711110fd158`. Requests: 2; counts: `{"submissions": 0, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: None

Previous plan: Capture Blackwater to gain 2 supply icons, increase supply track, and retain control of The Reach castle with a power token.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d025"></a>

## D025 — lannister — submit_orders (completed)

Run `16049b72-cfd6-4853-a023-ef59127db345`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "harrenhal", "preferred_order": "defense", "starred_preference": "prefer", "priority": 100}, {"region_id": "seagard", "preferred_order": "march", "starred_preference": "prefer", "priority": 100}, {"region_id": "the-golden-sound", "preferred_order": "support", "starred_preference": "prefer", "priority": 80}, {"region_id": "lannisport", "preferred_order": "defense", "starred_preference": "avoid", "priority": 70}], "applied_orders": [{"region_id": "harrenhal", "order_id": 6, "order": "defense"}, {"region_id": "seagard", "order_id": 3, "order": "march"}, {"region_id": "the-golden-sound", "order_id": 9, "order": "support"}, {"region_id": "lannisport", "order_id": 4, "order": "defense"}]}`

Handoff: Plan: Use a starred Defense+2 at Harrenhal to protect our stronghold from Baratheon attacks. Execute a starred March order from Seagard to capture the neighboring Castle at Moat Cailin, and after the move leave a Power token (we have two available) to retain control of Seagard. Assign a starred Support+1 at The Golden Sound to aid future combats. Keep Lannisport safe with a normal Defense order to protect our knight and home area. This maintains our castle count, expands to a new castle, and preserves key positions.

Previous plan: Move footman from Riverrun to capture the stronghold at Seagard, leaving a power token to retain control of the stronghold at Riverrun. Increases our castle count toward victory while preserving existing holdings.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d026"></a>

## D026 — stark — submit_orders (completed)

Run `79509356-29ef-4a4d-a670-5b8cbe147272`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "white-harbor", "preferred_order": "defense", "starred_preference": "prefer", "priority": 100}, {"region_id": "the-shivering-sea", "preferred_order": "support", "starred_preference": "prefer", "priority": 80}, {"region_id": "the-stony-shore", "preferred_order": "march", "starred_preference": "avoid", "priority": 60}], "applied_orders": [{"region_id": "white-harbor", "order_id": 6, "order": "defense"}, {"region_id": "the-shivering-sea", "order_id": 9, "order": "support"}, {"region_id": "the-stony-shore", "order_id": 2, "order": "march"}]}`

Handoff: Defend White Harbor with a starred Defense order to protect our castle, provide a starred Support order from the ship in the Shivering Sea to boost future combat, and assign a regular March order to the knight on The Stony Shore for movement next round.

Previous plan: Choose No restrictions to retain all order options. This preserves ability to use March +1 orders for attacks given low supply, and Defense orders to protect our castles, avoiding any self‑imposed penalties.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d027"></a>

## D027 — baratheon — place-orders (failed)

Run `d25afcc3-e88c-4930-99ac-ce2de4f0ec6f`. Requests: 1; counts: `{"submissions": 0, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: None

Previous plan: Capture Blackwater to gain 2 supply icons, increase supply track, and retain control of The Reach castle with a power token.

Pending: `{"type": "place-orders", "readyHouses": ["stark"]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d028"></a>

## D028 — baratheon — submit_orders (completed)

Run `b7b9b87c-3ce4-4fd0-b96d-cda20cf84196`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "blackwater", "preferred_order": "march", "starred_preference": "prefer", "priority": 100}, {"region_id": "crackclaw-point", "preferred_order": "support", "starred_preference": "avoid", "priority": 80}, {"region_id": "kingswood", "preferred_order": "defense", "starred_preference": "avoid", "priority": 60}, {"region_id": "shipbreaker-bay", "preferred_order": "consolidate_power", "starred_preference": "avoid", "priority": 30}], "applied_orders": [{"region_id": "blackwater", "order_id": 3, "order": "march"}, {"region_id": "crackclaw-point", "order_id": 7, "order": "support"}, {"region_id": "kingswood", "order_id": 4, "order": "defense"}, {"region_id": "shipbreaker-bay", "order_id": 10, "order": "consolidate_power"}]}`

Handoff: Goal: capture Lannister's Harrenhal castle this round. Use a starred March +1 from Blackwater to attack Harrenhal, supported by a regular Support order at Crackclaw Point. Keep the Knight at Kingswood safe with a Defense order. Gain an extra Power token by Consolidate Power at Shipbreaker Bay. This plan expands our castle count while maintaining supply and securing resources for future bidding.

Previous plan: Capture Blackwater to gain 2 supply icons, increase supply track, and retain control of The Reach castle with a power token.

Pending: `{"type": "place-orders", "readyHouses": ["stark", "lannister"]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d029"></a>

## D029 — lannister — replace-order (failed)

Run `17965348-e2fb-4cfe-a044-10016b360370`. Requests: 1; counts: `{"submissions": 0, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: None

Previous plan: Plan: Use a starred Defense+2 at Harrenhal to protect our stronghold from Baratheon attacks. Execute a starred March order from Seagard to capture the neighboring Castle at Moat Cailin, and after the move leave a Power token (we have two available) to retain control of Seagard. Assign a starred Support+1 at The Golden Sound to aid future combats. Keep Lannisport safe with a normal Defense order to protect our knight and home area. This maintains our castle count, expands to a new castle, and preserves key positions.

Pending: `{"type": "replace-order"}`

Guidance: `{"decision": "raven-order-replacement", "legalReplacements": [{"regionId": "harrenhal", "originalOrderId": 6, "availableOrderIds": [1, 2, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]}, {"regionId": "lannisport", "originalOrderId": 4, "availableOrderIds": [1, 2, 4, 5, 7, 8, 10, 11, 13, 14]}, {"regionId": "seagard", "originalOrderId": 3, "availableOrderIds": [1, 2, 3, 5, 7, 8, 10, 11, 12, 13, 14, 15]}, {"regionId": "the-golden-sound", "originalOrderId": 9, "availableOrderIds": [1, 2, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15]}], "safeChoices": ["Choose skip_raven_order_replacement to keep every order.", "Choose inspect_top_wildling_card to use the Raven on the Wildling deck."]}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d030"></a>

## D030 — lannister — skip_raven_order_replacement (completed)

Run `ee803101-9f06-497f-b49c-2af044087584`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Maintain current orders: Defense+2 starred at Harrenhal, Defense+1 at Lannisport, March+1 starred at Seagard, Support+1 starred at The Golden Sound. No replacement needed. Preserve power tokens for future use, aiming to expand castle count while protecting strongholds.

Previous plan: Plan: Use a starred Defense+2 at Harrenhal to protect our stronghold from Baratheon attacks. Execute a starred March order from Seagard to capture the neighboring Castle at Moat Cailin, and after the move leave a Power token (we have two available) to retain control of Seagard. Assign a starred Support+1 at The Golden Sound to aid future combats. Keep Lannisport safe with a normal Defense order to protect our knight and home area. This maintains our castle count, expands to a new castle, and preserves key positions.

Pending: `{"type": "replace-order"}`

Guidance: `{"decision": "raven-order-replacement", "legalReplacements": [{"regionId": "harrenhal", "originalOrderId": 6, "availableOrderIds": [1, 2, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]}, {"regionId": "lannisport", "originalOrderId": 4, "availableOrderIds": [1, 2, 4, 5, 7, 8, 10, 11, 13, 14]}, {"regionId": "seagard", "originalOrderId": 3, "availableOrderIds": [1, 2, 3, 5, 7, 8, 10, 11, 12, 13, 14, 15]}, {"regionId": "the-golden-sound", "originalOrderId": 9, "availableOrderIds": [1, 2, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15]}], "safeChoices": ["Choose skip_raven_order_replacement to keep every order.", "Choose inspect_top_wildling_card to use the Raven on the Wildling deck."]}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d031"></a>

## D031 — baratheon — resolve_march (completed)

Run `aad6bca5-0628-412b-bfa0-f85532f7e809`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "blackwater", "moves": [{"destination_region_id": "harrenhal", "unit_ids": [13]}], "leave_power_token": true, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Capture Harrenhal castle using footman from Blackwater, supported by Crackclaw Point; spend a power token to retain Blackwater supply; keep Kingswood defended.

Previous plan: Goal: capture Lannister's Harrenhal castle this round. Use a starred March +1 from Blackwater to attack Harrenhal, supported by a regular Support order at Crackclaw Point. Keep the Knight at Kingswood safe with a Defense order. Gain an extra Power token by Consolidate Power at Shipbreaker Bay. This plan expands our castle count while maintaining supply and securing resources for future bidding.

Pending: `{"type": "resolve-single-march", "houseId": "baratheon", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "blackwater", "orderId": 3, "order": "March +1", "unitIds": [13], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "crackclaw-point", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[13]]}, {"regionId": "harrenhal", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "lannister", "triggersCombat": true, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[13]]}, {"regionId": "searoad-marches", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[13]]}, {"regionId": "stoney-sept", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[13]]}, {"regionId": "the-reach", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[13]]}], "canLeavePowerToken": true}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d032"></a>

## D032 — lannister — choose_combat_house_card (completed)

Run `5a4ba726-036e-4ed5-b34c-095d50e59b2c`. Requests: 3; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"house_card_id": "tywin-lannister", "force_valyrian_blade_decision": false}`

Handoff: Play Tywin Lannister to win combat at Harrenhal, secure the castle, gain 2 power tokens, maintain defenses, and continue expanding toward victory.

Previous plan: Maintain current orders: Defense+2 starred at Harrenhal, Defense+1 at Lannisport, March+1 starred at Seagard, Support+1 starred at The Golden Sound. No replacement needed. Preserve power tokens for future use, aiming to expand castle count while protecting strongholds.

Pending: `{"type": "choose-house-card", "choosableHouseCards": [["baratheon", ["patchface", "salladhor-saan", "melisandre", "ser-davos-seaworth", "brienne-of-tarth", "renly-baratheon", "stannis-baratheon"]], ["lannister", ["cersei-lannister", "ser-kevan-lannister", "tyrion-lannister", "ser-jaime-lannister", "the-hound", "ser-gregor-clegane", "tywin-lannister"]]], "houseCards": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d033"></a>

## D033 — baratheon — choose_combat_house_card (completed)

Run `5993a38e-83ec-4b3e-a2b6-32ac9b7f1d76`. Requests: 3; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"house_card_id": "stannis-baratheon", "force_valyrian_blade_decision": false}`

Handoff: Play Stannis Baratheon (strength 4) to ensure victory at Harrenhal. Our base combat strength (3) plus Stannis gives 7 vs Lannister defender (3) plus any card; even if defender ties, we win tie on Fiefdoms. No sword icons needed, so no casualties are required; defender will retreat. This secures a stronghold, increasing our castle count toward victory. Valyrian Blade not owned, so not used.

Previous plan: Capture Harrenhal castle using footman from Blackwater, supported by Crackclaw Point; spend a power token to retain Blackwater supply; keep Kingswood defended.

Pending: `{"type": "choose-house-card", "choosableHouseCards": [["baratheon", ["patchface", "salladhor-saan", "melisandre", "ser-davos-seaworth", "brienne-of-tarth", "renly-baratheon", "stannis-baratheon"]], ["lannister", ["cersei-lannister", "ser-kevan-lannister", "tyrion-lannister", "ser-jaime-lannister", "the-hound", "ser-gregor-clegane", "tywin-lannister"]]], "houseCards": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d034"></a>

## D034 — lannister — select_region (completed)

Run `99062d79-be19-4ec2-a1a8-3bf6501e4ff3`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"region_id": "riverrun"}`

Handoff: Retreat to Riverrun to reinforce our controlled stronghold, keep a unit near Seagard and Lannisport, and set up to recapture Harrenhal next round while maintaining a defensive foothold.

Previous plan: Play Tywin Lannister to win combat at Harrenhal, secure the castle, gain 2 power tokens, maintain defenses, and continue expanding toward victory.

Pending: `{"type": "select-region", "house": "lannister", "regions": ["stoney-sept", "riverrun"]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 5, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d035"></a>

## D035 — lannister — resolve_march (completed)

Run `42d34984-e8a3-48a8-ba25-734c5b30294e`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "seagard", "moves": [{"destination_region_id": "moat-cailin", "unit_ids": [5]}], "leave_power_token": true, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Moved footman from Seagard to capture Moat Cailin (castle). Left a Power token on Seagard to retain control of the stronghold, increasing Lannister's castle/stronghold count.

Previous plan: Retreat to Riverrun to reinforce our controlled stronghold, keep a unit near Seagard and Lannisport, and set up to recapture Harrenhal next round while maintaining a defensive foothold.

Pending: `{"type": "resolve-single-march", "houseId": "lannister", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "seagard", "orderId": 3, "order": "March +1", "unitIds": [5], "castleAreasLostIfEmptiedWithoutToken": 1, "reachableRegions": [{"regionId": "greywater-watch", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5]]}, {"regionId": "moat-cailin", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "stark", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5]]}, {"regionId": "riverrun", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5]]}, {"regionId": "the-twins", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5]]}], "canLeavePowerToken": true}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 3, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d036"></a>

## D036 — stark — resolve_march (completed)

Run `973e8175-07a1-4f9d-b70b-c46db002431a`. Requests: 26; counts: `{"submissions": 26, "explicitRejections": 25, "schemaInvalidSubmissions": 24, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 1}`.

Action: `{"starting_region_id": "the-stony-shore", "moves": [], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Discard the March order at The Stony Shore, keeping the knight in place and preserving our current position.

Previous plan: Defend White Harbor with a starred Defense order to protect our castle, provide a starred Support order from the ship in the Shivering Sea to boost future combat, and assign a regular March order to the knight on The Stony Shore for movement next round.

Pending: `{"type": "resolve-single-march", "houseId": "stark", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "the-stony-shore", "orderId": 2, "order": "March +0", "unitIds": [2], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "winterfell", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "stark", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[2]]}], "canLeavePowerToken": true}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

