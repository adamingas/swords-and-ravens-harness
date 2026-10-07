# Round 1: recorded decisions and state evidence

<a id="d001"></a>

## D001 — baratheon — submit_orders (completed)

Run `beee11e5-8128-4b65-9c6a-56d68e377c85`. Requests: 3; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "kingswood", "preferred_order": "march", "starred_preference": "prefer", "priority": 100}, {"region_id": "shipbreaker-bay", "preferred_order": "consolidate_power", "starred_preference": "avoid", "priority": 30}, {"region_id": "dragonstone", "preferred_order": "march", "starred_preference": "avoid", "priority": 70}], "applied_orders": [{"region_id": "kingswood", "order_id": 3, "order": "march"}, {"region_id": "shipbreaker-bay", "order_id": 10, "order": "consolidate_power"}, {"region_id": "dragonstone", "order_id": 2, "order": "march"}]}`

Handoff: Priorities: Capture The Reach castle (or Crackclaw Point) using a starred March from Kingswood to secure a new castle area. Use a regular Consolidate Power at Shipbreaker Bay to gain an extra power token for future bidding. Assign a regular March at Dragonstone for flexibility to move the knight or footman later, possibly to reinforce The Reach or capture another target. Preserve control of key territories and stay within the single starred order limit.

Previous plan: 

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 1, "controlledLandAreas": 2, "controlledCastleAreas": 1, "controlledSupplyIcons": 2, "controlledRegions": ["kingswood", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 1, "controlledLandAreas": 2, "controlledCastleAreas": 1, "controlledSupplyIcons": 2, "controlledRegions": ["stoney-sept", "lannisport", "the-golden-sound", "port-of-lannisport"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d002"></a>

## D002 — lannister — submit_orders (completed)

Run `383770fe-9c6e-49b8-a381-fae73172cf20`. Requests: 3; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "lannisport", "preferred_order": "march", "starred_preference": "avoid", "priority": 100}, {"region_id": "stoney-sept", "preferred_order": "march", "starred_preference": "avoid", "priority": 100}, {"region_id": "the-golden-sound", "preferred_order": "support", "starred_preference": "avoid", "priority": 80}], "applied_orders": [{"region_id": "lannisport", "order_id": 1, "order": "march"}, {"region_id": "stoney-sept", "order_id": 2, "order": "march"}, {"region_id": "the-golden-sound", "order_id": 7, "order": "support"}]}`

Handoff: Aim to capture two new castle/stronghold areas: move footman from Lannisport to Riverrun (stronghold) using ship transport, and march footman from Stoney Sept into Harrenhal (castle). Keep Lannisport defended by retaining the knight, and place a support order on the Golden Sound to provide ship support for future combats. Preserve supply limits and avoid losing control of existing strongholds.

Previous plan: 

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 1, "controlledLandAreas": 2, "controlledCastleAreas": 1, "controlledSupplyIcons": 2, "controlledRegions": ["kingswood", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 1, "controlledLandAreas": 2, "controlledCastleAreas": 1, "controlledSupplyIcons": 2, "controlledRegions": ["stoney-sept", "lannisport", "the-golden-sound", "port-of-lannisport"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d003"></a>

## D003 — stark — submit_orders (completed)

Run `6eb348ec-7fdf-46c0-ab8d-b78fbe961b5e`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "winterfell", "preferred_order": "march", "starred_preference": "prefer", "priority": 100}, {"region_id": "white-harbor", "preferred_order": "defense", "starred_preference": "avoid", "priority": 60}, {"region_id": "the-shivering-sea", "preferred_order": "support", "starred_preference": "prefer", "priority": 80}], "applied_orders": [{"region_id": "winterfell", "order_id": 3, "order": "march"}, {"region_id": "white-harbor", "order_id": 4, "order": "defense"}, {"region_id": "the-shivering-sea", "order_id": 9, "order": "support"}]}`

Handoff: Goal: capture Moat Cailin by marching from Winterfell (using a starred March +1) this turn. Defend White Harbor with a regular Defense order to protect our castle. Use the ship in the Shivering Sea to provide support (starred Support +1) for any upcoming combats, enabling stronger attacks on enemy units. This plan expands our castle count while preserving supply and maintaining a defensive posture.

Previous plan: 

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 1, "controlledLandAreas": 2, "controlledCastleAreas": 1, "controlledSupplyIcons": 2, "controlledRegions": ["kingswood", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 1, "controlledLandAreas": 2, "controlledCastleAreas": 1, "controlledSupplyIcons": 2, "controlledRegions": ["stoney-sept", "lannisport", "the-golden-sound", "port-of-lannisport"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d004"></a>

## D004 — lannister — skip_raven_order_replacement (completed)

Run `7117fe67-a05f-41d4-bab5-453f5c8c1193`. Requests: 30; counts: `{"submissions": 30, "explicitRejections": 29, "schemaInvalidSubmissions": 29, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Keep current orders; they already support plan to capture Riverrun and Harrenhal. No replacement needed.

Previous plan: Aim to capture two new castle/stronghold areas: move footman from Lannisport to Riverrun (stronghold) using ship transport, and march footman from Stoney Sept into Harrenhal (castle). Keep Lannisport defended by retaining the knight, and place a support order on the Golden Sound to provide ship support for future combats. Preserve supply limits and avoid losing control of existing strongholds.

Pending: `{"type": "replace-order"}`

Guidance: `{"decision": "raven-order-replacement", "legalReplacements": [{"regionId": "lannisport", "originalOrderId": 1, "availableOrderIds": [1, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15]}, {"regionId": "stoney-sept", "originalOrderId": 2, "availableOrderIds": [2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15]}, {"regionId": "the-golden-sound", "originalOrderId": 7, "availableOrderIds": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]}], "safeChoices": ["Choose skip_raven_order_replacement to keep every order.", "Choose inspect_top_wildling_card to use the Raven on the Wildling deck."]}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 1, "controlledLandAreas": 2, "controlledCastleAreas": 1, "controlledSupplyIcons": 2, "controlledRegions": ["kingswood", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 1, "controlledLandAreas": 2, "controlledCastleAreas": 1, "controlledSupplyIcons": 2, "controlledRegions": ["stoney-sept", "lannisport", "the-golden-sound", "port-of-lannisport"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d005"></a>

## D005 — baratheon — resolve_march (completed)

Run `54659e4a-7210-4131-9806-75663e6eb243`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "dragonstone", "moves": [{"destination_region_id": "crackclaw-point", "unit_ids": [9]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Moved footman from Dragonstone to capture Crackclaw Point, gaining a second castle while keeping the knight at Dragonstone. No power token needed. Next focus on resolving Kingswood march to secure The Reach or reinforce positions.

Previous plan: Priorities: Capture The Reach castle (or Crackclaw Point) using a starred March from Kingswood to secure a new castle area. Use a regular Consolidate Power at Shipbreaker Bay to gain an extra power token for future bidding. Assign a regular March at Dragonstone for flexibility to move the knight or footman later, possibly to reinforce The Reach or capture another target. Preserve control of key territories and stay within the single starred order limit.

Pending: `{"type": "resolve-single-march", "houseId": "baratheon", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "dragonstone", "orderId": 2, "order": "March +0", "unitIds": [9, 10], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "crackclaw-point", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[9], [10], [9, 10]]}, {"regionId": "kingswood", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[9], [10], [9, 10]]}], "canLeavePowerToken": false}, {"regionId": "kingswood", "orderId": 3, "order": "March +1", "unitIds": [13], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "crackclaw-point", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[13]]}, {"regionId": "dragonstone", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[13]]}, {"regionId": "the-reach", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[13]]}], "canLeavePowerToken": true}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 1, "controlledLandAreas": 2, "controlledCastleAreas": 1, "controlledSupplyIcons": 2, "controlledRegions": ["kingswood", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 1, "controlledLandAreas": 2, "controlledCastleAreas": 1, "controlledSupplyIcons": 2, "controlledRegions": ["stoney-sept", "lannisport", "the-golden-sound", "port-of-lannisport"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d006"></a>

## D006 — lannister — resolve_march (completed)

Run `230e3403-8f40-4a61-8ad0-bdf2a196f337`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "lannisport", "moves": [{"destination_region_id": "riverrun", "unit_ids": [5]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Moved footman (ID 5) from Lannisport to capture the stronghold at Riverrun, gaining a second castle/stronghold area. Retained the knight (ID 6) at Lannisport for defense; no power token needed as Lannisport is home. Next March order (Stoney Sept) will target Harrenhal to secure an additional castle.

Previous plan: Keep current orders; they already support plan to capture Riverrun and Harrenhal. No replacement needed.

Pending: `{"type": "resolve-single-march", "houseId": "lannister", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "lannisport", "orderId": 1, "order": "March -1", "unitIds": [5, 6], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "riverrun", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5], [6], [5, 6]]}, {"regionId": "searoad-marches", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5], [6], [5, 6]]}, {"regionId": "stoney-sept", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5], [6], [5, 6]]}], "canLeavePowerToken": false}, {"regionId": "stoney-sept", "orderId": 2, "order": "March +0", "unitIds": [8], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "blackwater", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "harrenhal", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "lannisport", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "riverrun", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "searoad-marches", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}], "canLeavePowerToken": true}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 1, "controlledLandAreas": 2, "controlledCastleAreas": 1, "controlledSupplyIcons": 2, "controlledRegions": ["stoney-sept", "lannisport", "the-golden-sound", "port-of-lannisport"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d007"></a>

## D007 — stark — resolve_march (completed)

Run `9e225216-70d1-429d-b905-93184602ee36`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "winterfell", "moves": [{"destination_region_id": "moat-cailin", "unit_ids": [1]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Moved footman from Winterfell to capture Moat Cailin, gaining a new castle area while keeping the knight in Winterfell to defend the home stronghold. White Harbor remains defended by its Defense order. Ship at The Shivering Sea provides support for future combats. Next steps: monitor enemy moves, consider using the remaining knight for defense or further expansion, and leverage support from the ship for attacks.

Previous plan: Goal: capture Moat Cailin by marching from Winterfell (using a starred March +1) this turn. Defend White Harbor with a regular Defense order to protect our castle. Use the ship in the Shivering Sea to provide support (starred Support +1) for any upcoming combats, enabling stronger attacks on enemy units. This plan expands our castle count while preserving supply and maintaining a defensive posture.

Pending: `{"type": "resolve-single-march", "houseId": "stark", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "winterfell", "orderId": 3, "order": "March +1", "unitIds": [1, 2], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "castle-black", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[1], [2], [1, 2]]}, {"regionId": "karhold", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[1], [2], [1, 2]]}, {"regionId": "moat-cailin", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[1], [2], [1, 2]]}, {"regionId": "the-stony-shore", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[1], [2], [1, 2]]}, {"regionId": "white-harbor", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "stark", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[1], [2], [1, 2]]}, {"regionId": "widows-watch", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[1], [2], [1, 2]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 3, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d008"></a>

## D008 — baratheon — resolve_march (completed)

Run `312c329f-5628-46da-a62d-23069b8d431a`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "kingswood", "moves": [{"destination_region_id": "the-reach", "unit_ids": [13]}], "leave_power_token": true, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Moved footman from Kingswood to The Reach, capturing a Castle (new Baratheon castle area). Used one power token to keep control of Kingswood after vacating. Follow-up: consolidate power at Shipbreaker Bay for extra power, and monitor Lannister and Stark actions.

Previous plan: Moved footman from Dragonstone to capture Crackclaw Point, gaining a second castle while keeping the knight at Dragonstone. No power token needed. Next focus on resolving Kingswood march to secure The Reach or reinforce positions.

Pending: `{"type": "resolve-single-march", "houseId": "baratheon", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "kingswood", "orderId": 3, "order": "March +1", "unitIds": [13], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "crackclaw-point", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[13]]}, {"regionId": "dragonstone", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[13]]}, {"regionId": "the-reach", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[13]]}], "canLeavePowerToken": true}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 3, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d009"></a>

## D009 — lannister — resolve_march (completed)

Run `cfaaeb30-478a-4cda-abb1-ace5fb44e20f`. Requests: 4; counts: `{"submissions": 3, "explicitRejections": 2, "schemaInvalidSubmissions": 2, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "stoney-sept", "moves": [{"destination_region_id": "harrenhal", "unit_ids": [8]}], "leave_power_token": true, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Moved footman (ID 8) from Stoney Sept to capture the castle at Harrenhal, gaining a third castle/stronghold area. Left a power token in Stoney Sept to retain control of the land area despite it being empty. This improves our victory position while preserving land presence. Future focus: reinforce Harrenhal if needed and consider further expansion from strongholds.

Previous plan: Moved footman (ID 5) from Lannisport to capture the stronghold at Riverrun, gaining a second castle/stronghold area. Retained the knight (ID 6) at Lannisport for defense; no power token needed as Lannisport is home. Next March order (Stoney Sept) will target Harrenhal to secure an additional castle.

Pending: `{"type": "resolve-single-march", "houseId": "lannister", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "stoney-sept", "orderId": 2, "order": "March +0", "unitIds": [8], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "blackwater", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "harrenhal", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "lannisport", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "riverrun", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "searoad-marches", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}], "canLeavePowerToken": true}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 2, "controlledRegions": ["the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 5, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 3, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

