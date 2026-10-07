# Round 8: recorded decisions and state evidence

<a id="d106"></a>

## D106 — baratheon — choose_option (completed)

Run `1948c755-ce34-4343-94f9-d767038d4d72`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"choice_index": 0}`

Handoff: Choose Mustering to use our 5 mustering points from Kings Landing, Dragonstone, and The Reach. Muster a footman at The Reach, two footmen at Kings Landing (stronghold), and upgrade the existing footman at Dragonstone to a knight plus add a new footman there. This adds 5 units without exceeding supply, strengthening future attacks toward Lannister and preserving our castles.

Previous plan: Moved both knights from Crackclaw Point to Kingswood to consolidate forces near shipbreaker bay, enabling future ship‑transport attacks toward Lannisport while retaining control of the castle at Crackclaw Point via existing power token. No combat triggered and supply remains within limits.

Pending: `{"type": "simple-choice", "houseId": "baratheon", "description": "The holder of the Iron Throne token can choose between Mustering, Supply, or nothing at all.", "choices": ["Mustering", "Supply", "Nothing"]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 9, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d107"></a>

## D107 — baratheon — muster_units (completed)

Run `7df26e3b-5f6f-414c-9a01-8d8ba506622f`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"musters": [{"mustering_region_id": "crackclaw-point", "recruitments": [{"unit_type": "footman", "region_id": "crackclaw-point", "upgrade_from_footman": false}]}, {"mustering_region_id": "dragonstone", "recruitments": [{"unit_type": "knight", "region_id": "dragonstone", "upgrade_from_footman": true}, {"unit_type": "footman", "region_id": "dragonstone", "upgrade_from_footman": false}]}, {"mustering_region_id": "harrenhal", "recruitments": [{"unit_type": "footman", "region_id": "harrenhal", "upgrade_from_footman": false}]}, {"mustering_region_id": "kings-landing", "recruitments": [{"unit_type": "footman", "region_id": "kings-landing", "upgrade_from_footman": false}]}], "omitted_point_unsafe_recruitments": 0, "omitted_supply_unsafe_recruitments": 1}`

Handoff: Mustered to reinforce borders and prepare attacks: upgraded Dragonstone footman to knight and added a footman there; placed footmen at Kings Landing, The Reach, Crackclaw Point, and Harrenhal. All fits supply 4.

Previous plan: Choose Mustering to use our 5 mustering points from Kings Landing, Dragonstone, and The Reach. Muster a footman at The Reach, two footmen at Kings Landing (stronghold), and upgrade the existing footman at Dragonstone to a knight plus add a new footman there. This adds 5 units without exceeding supply, strengthening future attacks toward Lannister and preserving our castles.

Pending: `{"type": "player-mustering", "house": "baratheon", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 5, "origins": [{"regionId": "crackclaw-point", "musteringPoints": 1, "destinations": [{"regionId": "crackclaw-point", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 3, "supplySafeNewUnitsWhenChosenAlone": 0, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "dragonstone", "musteringPoints": 2, "destinations": [{"regionId": "dragonstone", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "port-of-dragonstone", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 3, "supplySafeNewUnitsWhenChosenAlone": 0, "upgradeableFootmen": 0}]}, {"regionId": "harrenhal", "musteringPoints": 1, "destinations": [{"regionId": "harrenhal", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "kings-landing", "musteringPoints": 2, "destinations": [{"regionId": "kings-landing", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "the-reach", "musteringPoints": 1, "destinations": [{"regionId": "the-reach", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}]}], "availablePieces": {"footman": 8, "knight": 2, "ship": 3, "siege-engine": 2}, "supplyLimit": {"level": 4, "allowedArmySizes": [3, 3, 2, 2], "currentArmies": [{"regionId": "shipbreaker-bay", "unitCount": 3}, {"regionId": "kingswood", "unitCount": 2}], "singleUnitRegions": ["dragonstone", "harrenhal", "the-reach"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 9, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d108"></a>

## D108 — lannister — muster_units (completed)

Run `7a6dcd0e-4725-494f-a3db-108202d2d6d9`. Requests: 3; counts: `{"submissions": 3, "explicitRejections": 2, "schemaInvalidSubmissions": 2, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"musters": [{"mustering_region_id": "lannisport", "recruitments": [{"unit_type": "siege-engine", "region_id": "lannisport", "upgrade_from_footman": false}]}, {"mustering_region_id": "moat-cailin", "recruitments": [{"unit_type": "knight", "region_id": "moat-cailin", "upgrade_from_footman": true}]}, {"mustering_region_id": "riverrun", "recruitments": [{"unit_type": "siege-engine", "region_id": "riverrun", "upgrade_from_footman": false}]}, {"mustering_region_id": "seagard", "recruitments": [{"unit_type": "knight", "region_id": "seagard", "upgrade_from_footman": false}]}], "omitted_point_unsafe_recruitments": 0, "omitted_supply_unsafe_recruitments": 0}`

Handoff: Mustered to strengthen attack on Baratheon's Harrenhal and protect our castles. Added siege-engine at Lannisport and Riverrun for heavy assault capability. Upgraded footman at Moat Cailin to knight for defense. Mustered a knight at Seagard to expand presence. All within supply limits.

Previous plan: Discard Moat Cailin March order to keep the footman in place, preserving the castle area. No power token is available to leave a control token, and attacking White Harbor would likely fail against Stark's garrison and support. Maintaining the castle keeps our victory point count stable.

Pending: `{"type": "player-mustering", "house": "lannister", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "lannisport", "musteringPoints": 2, "destinations": [{"regionId": "lannisport", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}, {"regionId": "port-of-lannisport", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "moat-cailin", "musteringPoints": 1, "destinations": [{"regionId": "moat-cailin", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "riverrun", "musteringPoints": 2, "destinations": [{"regionId": "riverrun", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "seagard", "musteringPoints": 2, "destinations": [{"regionId": "seagard", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 5, "siege-engine": 2}, "supplyLimit": {"level": 4, "allowedArmySizes": [3, 3, 2, 2], "currentArmies": [], "singleUnitRegions": ["lannisport", "moat-cailin", "riverrun", "the-golden-sound"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 9, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d109"></a>

## D109 — stark — muster_units (completed)

Run `b630ffc6-7ed8-408c-ab6e-a8188a18d4ba`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"musters": [{"mustering_region_id": "winterfell", "recruitments": [{"unit_type": "footman", "region_id": "winterfell", "upgrade_from_footman": false}, {"unit_type": "footman", "region_id": "winterfell", "upgrade_from_footman": false}]}, {"mustering_region_id": "white-harbor", "recruitments": [{"unit_type": "footman", "region_id": "white-harbor", "upgrade_from_footman": false}]}], "omitted_point_unsafe_recruitments": 0, "omitted_supply_unsafe_recruitments": 0}`

Handoff: Muster two footmen at Winterfell (using both mustering points) and one footman at White Harbor (using its point). This creates a 3‑unit army at Winterfell (knight + 2 footmen) within supply, and adds a footman at White Harbor ready to march into Lannister's Moat Cailin castle next turn, leveraging ship transport from the‑Shivering Sea if needed.

Previous plan: Moved the Stark knight from The Stony Shore into Winterfell, reinforcing the stronghold without combat or power token loss.

Pending: `{"type": "player-mustering", "house": "stark", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 2, "origins": [{"regionId": "white-harbor", "musteringPoints": 1, "destinations": [{"regionId": "white-harbor", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-white-harbor", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-shivering-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "winterfell", "musteringPoints": 2, "destinations": [{"regionId": "winterfell", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}, {"regionId": "bay-of-ice", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-winterfell", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-shivering-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 10, "knight": 4, "ship": 5, "siege-engine": 2}, "supplyLimit": {"level": 2, "allowedArmySizes": [3, 2, 2], "currentArmies": [], "singleUnitRegions": ["the-shivering-sea", "winterfell"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 9, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d110"></a>

## D110 — baratheon — submit_orders (completed)

Run `735ac407-311b-40e8-b730-7a9b31a8afed`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "harrenhal", "preferred_order": "march", "starred_preference": "prefer", "priority": 100}, {"region_id": "kingswood", "preferred_order": "support", "starred_preference": "prefer", "priority": 90}, {"region_id": "shipbreaker-bay", "preferred_order": "support", "starred_preference": "prefer", "priority": 80}, {"region_id": "the-reach", "preferred_order": "march", "starred_preference": "avoid", "priority": 70}, {"region_id": "kings-landing", "preferred_order": "defense", "starred_preference": "avoid", "priority": 60}, {"region_id": "crackclaw-point", "preferred_order": "defense", "starred_preference": "avoid", "priority": 50}, {"region_id": "dragonstone", "preferred_order": "defense", "starred_preference": "avoid", "priority": 40}], "applied_orders": [{"region_id": "harrenhal", "order_id": 3, "order": "march"}, {"region_id": "kingswood", "order_id": 9, "order": "support"}, {"region_id": "shipbreaker-bay", "order_id": 7, "order": "support"}, {"region_id": "the-reach", "order_id": 2, "order": "march"}, {"region_id": "kings-landing", "order_id": 6, "order": "defense"}, {"region_id": "crackclaw-point", "order_id": 4, "order": "defense"}, {"region_id": "dragonstone", "order_id": 5, "order": "defense"}]}`

Handoff: Aim to capture Riverrun this round by marching from Harrenhal (starred March +1) with knight+footman, supported by Kingswood knights (starred Support +1) and Shipbreaker Bay ships (starred Support +1). Protect our castles: defense orders on Kings Landing, The Reach, Crackclaw Point, and Dragonstone. Future focus on moving towards Lannisport stronghold after securing Riverrun.

Previous plan: Mustered to reinforce borders and prepare attacks: upgraded Dragonstone footman to knight and added a footman there; placed footmen at Kings Landing, The Reach, Crackclaw Point, and Harrenhal. All fits supply 4.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 9, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d111"></a>

## D111 — lannister — submit_orders (completed)

Run `a4dbd744-dec0-4801-b5d6-0fda9a8895cb`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "riverrun", "preferred_order": "march", "starred_preference": "prefer", "priority": 100}, {"region_id": "lannisport", "preferred_order": "defense", "starred_preference": "avoid", "priority": 90}, {"region_id": "the-golden-sound", "preferred_order": "support", "starred_preference": "prefer", "priority": 80}, {"region_id": "seagard", "preferred_order": "support", "starred_preference": "avoid", "priority": 70}, {"region_id": "moat-cailin", "preferred_order": "defense", "starred_preference": "avoid", "priority": 60}], "applied_orders": [{"region_id": "riverrun", "order_id": 3, "order": "march"}, {"region_id": "lannisport", "order_id": 4, "order": "defense"}, {"region_id": "the-golden-sound", "order_id": 9, "order": "support"}, {"region_id": "seagard", "order_id": 7, "order": "support"}, {"region_id": "moat-cailin", "order_id": 5, "order": "defense"}]}`

Handoff: Aim to capture Baratheon’s Harrenhal by marching from Riverrun with a starred March (+1 combat). Defend Lannisport’s castle with a normal Defense. Boost naval potential at the‑golden‑sound using a starred Support. Provide normal Support at Seagard for future operations and keep Moat Cailin defended.

Previous plan: Mustered to strengthen attack on Baratheon's Harrenhal and protect our castles. Added siege-engine at Lannisport and Riverrun for heavy assault capability. Upgraded footman at Moat Cailin to knight for defense. Mustered a knight at Seagard to expand presence. All within supply limits.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 9, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d112"></a>

## D112 — stark — submit_orders (completed)

Run `019abca1-49a4-4b26-89aa-2f11c903d6e1`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "white-harbor", "preferred_order": "march", "starred_preference": "avoid", "priority": 100}, {"region_id": "the-shivering-sea", "preferred_order": "support", "starred_preference": "prefer", "priority": 90}, {"region_id": "winterfell", "preferred_order": "march", "starred_preference": "avoid", "priority": 80}], "applied_orders": [{"region_id": "white-harbor", "order_id": 2, "order": "march"}, {"region_id": "the-shivering-sea", "order_id": 9, "order": "support"}, {"region_id": "winterfell", "order_id": 1, "order": "march"}]}`

Handoff: Goal: capture Lannister's Moat Cailin stronghold using White Harbor footmen with support from the ship in the Shivering Sea (starred Support). Use Winterfell March to relocate our knight to the empty Stony Shore, expanding land control without risking our home castle (home area stays controlled automatically). This plan respects the single starred order limit and positions us for further advances next round.

Previous plan: Muster two footmen at Winterfell (using both mustering points) and one footman at White Harbor (using its point). This creates a 3‑unit army at Winterfell (knight + 2 footmen) within supply, and adds a footman at White Harbor ready to march into Lannister's Moat Cailin castle next turn, leveraging ship transport from the‑Shivering Sea if needed.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 9, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d113"></a>

## D113 — baratheon — replace_raven_order (completed)

Run `47e3cf60-02d7-431b-af45-c026918cf1f0`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"region_id": "dragonstone", "order_id": 10}`

Handoff: Swap Dragonstone's Defense +1 order for a Consolidate Power order (ID 10) to gain an extra power token while keeping our castles defended.

Previous plan: Aim to capture Riverrun this round by marching from Harrenhal (starred March +1) with knight+footman, supported by Kingswood knights (starred Support +1) and Shipbreaker Bay ships (starred Support +1). Protect our castles: defense orders on Kings Landing, The Reach, Crackclaw Point, and Dragonstone. Future focus on moving towards Lannisport stronghold after securing Riverrun.

Pending: `{"type": "replace-order"}`

Guidance: `{"decision": "raven-order-replacement", "legalReplacements": [{"regionId": "crackclaw-point", "originalOrderId": 4, "availableOrderIds": [1, 4, 8, 10, 11, 13, 14]}, {"regionId": "dragonstone", "originalOrderId": 5, "availableOrderIds": [1, 5, 8, 10, 11, 13, 14]}, {"regionId": "harrenhal", "originalOrderId": 3, "availableOrderIds": [1, 3, 8, 10, 11, 12, 13, 14, 15]}, {"regionId": "kings-landing", "originalOrderId": 6, "availableOrderIds": [1, 6, 8, 10, 11, 12, 13, 14, 15]}, {"regionId": "kingswood", "originalOrderId": 9, "availableOrderIds": [1, 8, 9, 10, 11, 12, 13, 14, 15]}, {"regionId": "shipbreaker-bay", "originalOrderId": 7, "availableOrderIds": [1, 7, 8, 10, 11, 13, 14]}, {"regionId": "the-reach", "originalOrderId": 2, "availableOrderIds": [1, 2, 8, 10, 11, 13, 14]}], "safeChoices": ["Choose skip_raven_order_replacement to keep every order.", "Choose inspect_top_wildling_card to use the Raven on the Wildling deck."]}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 9, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d114"></a>

## D114 — baratheon — resolve_march (completed)

Run `36bdf9e4-9cdd-4594-9e8c-0b20571dcd51`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "harrenhal", "moves": [{"destination_region_id": "riverrun", "unit_ids": [15, 22]}], "leave_power_token": true, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Attack Riverrun from Harrenhal using both units, capture the Lannister stronghold. Spend a power token to keep Harrenhal's castle token. This gains us a castle area and preserves existing ones, advancing towards the 7-castle win condition.

Previous plan: Swap Dragonstone's Defense +1 order for a Consolidate Power order (ID 10) to gain an extra power token while keeping our castles defended.

Pending: `{"type": "resolve-single-march", "houseId": "baratheon", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "harrenhal", "orderId": 3, "order": "March +1", "unitIds": [15, 22], "castleAreasLostIfEmptiedWithoutToken": 1, "reachableRegions": [{"regionId": "blackwater", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[15], [22], [15, 22]]}, {"regionId": "crackclaw-point", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[15], [22], [15, 22]]}, {"regionId": "riverrun", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "lannister", "triggersCombat": true, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[15], [22], [15, 22]]}, {"regionId": "stoney-sept", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[15], [22], [15, 22]]}], "canLeavePowerToken": true}, {"regionId": "the-reach", "orderId": 2, "order": "March +0", "unitIds": [16], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "blackwater", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[16]]}, {"regionId": "kings-landing", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": []}, {"regionId": "kingswood", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[16]]}, {"regionId": "searoad-marches", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[16]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 9, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d115"></a>

## D115 — lannister — choose_combat_house_card (completed)

Run `d9a9c051-cda4-49a8-bd95-e1743c85bef1`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"house_card_id": "ser-jaime-lannister", "force_valyrian_blade_decision": false}`

Handoff: Lannister is defending Riverrun. Defender strength (footman+siege-engine=5) plus support +1 =6 vs attacker 4. Victory assured. Play Ser Jaime Lannister (strength2, 1 sword) to secure win and kill one Baratheon unit. No need to force Valyrian Blade usage.

Previous plan: Aim to capture Baratheon’s Harrenhal by marching from Riverrun with a starred March (+1 combat). Defend Lannisport’s castle with a normal Defense. Boost naval potential at the‑golden‑sound using a starred Support. Provide normal Support at Seagard for future operations and keep Moat Cailin defended.

Pending: `{"type": "choose-house-card", "choosableHouseCards": [["baratheon", ["salladhor-saan", "melisandre", "ser-davos-seaworth", "brienne-of-tarth", "renly-baratheon"]], ["lannister", ["ser-kevan-lannister", "tyrion-lannister", "ser-jaime-lannister", "the-hound"]]], "houseCards": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d116"></a>

## D116 — baratheon — choose_combat_house_card (completed)

Run `36dde534-3dea-4a5f-8df4-05c54c20b979`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"house_card_id": "melisandre", "force_valyrian_blade_decision": true}`

Handoff: We play Melisandre (strength 1, 1 sword) to secure a sword casualty while winning decisively. Use Valyrian Steel Blade (+1) to ensure victory despite any defender abilities. This secures Riverrun, gaining a stronghold and a castle token, and we left a power token on Harrenhal to retain its castle. Outcome advances us toward the 7‑castle win condition.

Previous plan: Attack Riverrun from Harrenhal using both units, capture the Lannister stronghold. Spend a power token to keep Harrenhal's castle token. This gains us a castle area and preserves existing ones, advancing towards the 7-castle win condition.

Pending: `{"type": "choose-house-card", "choosableHouseCards": [["baratheon", ["salladhor-saan", "melisandre", "ser-davos-seaworth", "brienne-of-tarth", "renly-baratheon"]], ["lannister", ["ser-kevan-lannister", "tyrion-lannister", "ser-jaime-lannister", "the-hound"]]], "houseCards": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d117"></a>

## D117 — baratheon — use_valyrian_steel_blade (completed)

Run `a5cf94c0-c29f-4339-a690-e7e5989011f2`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"use": false}`

Handoff: We evaluated combat at Riverrun: attacker Baratheon (knight+footman) with March+1 order gives 4 initial strength, plus Melisandre 1 =5. Even with Valyrian Blade (+1) would be 6. Defender Lannister has footman, siege engine (likely 0 in defense), support from Seagard (knight) and The Golden Sound (ship+order), plus house card Ser Jaime (strength 2) totaling at least 7. Blade insufficient to win, so we decline to preserve it for a future battle where it may be decisive.

Previous plan: We play Melisandre (strength 1, 1 sword) to secure a sword casualty while winning decisively. Use Valyrian Steel Blade (+1) to ensure victory despite any defender abilities. This secures Riverrun, gaining a stronghold and a castle token, and we left a power token on Harrenhal to retain its castle. Outcome advances us toward the 7‑castle win condition.

Pending: `{"type": "use-valyrian-steel-blade", "houseId": "baratheon", "forNewTidesOfBattleCard": false}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d118"></a>

## D118 — baratheon — select_units (completed)

Run `86fbcd73-26ae-4e05-b9f3-f59040f76b13`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"unit_ids": [22]}`

Handoff: Destroy the footman (ID 22) at Harrenhal to preserve the knight for defense and future attacks. This keeps a strong unit in the castle while reducing our forces minimally.

Previous plan: We evaluated combat at Riverrun: attacker Baratheon (knight+footman) with March+1 order gives 4 initial strength, plus Melisandre 1 =5. Even with Valyrian Blade (+1) would be 6. Defender Lannister has footman, siege engine (likely 0 in defense), support from Seagard (knight) and The Golden Sound (ship+order), plus house card Ser Jaime (strength 2) totaling at least 7. Blade insufficient to win, so we decline to preserve it for a future battle where it may be decisive.

Pending: `{"type": "select-units", "house": "baratheon", "possibleUnits": [15, 22], "count": 1, "canBeSkipped": false, "selectedUnitsMustBeOfSameRegion": false}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d119"></a>

## D119 — lannister — resolve_march (completed)

Run `3f58a8ed-e6e1-402f-bfff-b24b5fd997a2`. Requests: 4; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "riverrun", "moves": [{"destination_region_id": "harrenhal", "unit_ids": [26]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Move siege-engine from Riverrun to Harrenhal to capture the castle while leaving the footman behind to retain control of Riverrun. No power token is spent, supply remains within limits, and we gain an additional castle area.

Previous plan: Lannister is defending Riverrun. Defender strength (footman+siege-engine=5) plus support +1 =6 vs attacker 4. Victory assured. Play Ser Jaime Lannister (strength2, 1 sword) to secure win and kill one Baratheon unit. No need to force Valyrian Blade usage.

Pending: `{"type": "resolve-single-march", "houseId": "lannister", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "riverrun", "orderId": 3, "order": "March +1", "unitIds": [8, 26], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "harrenhal", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "baratheon", "triggersCombat": true, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8], [26], [8, 26]]}, {"regionId": "lannisport", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8], [26]]}, {"regionId": "seagard", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8], [26], [8, 26]]}, {"regionId": "searoad-marches", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8], [26], [8, 26]]}, {"regionId": "stoney-sept", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8], [26], [8, 26]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d120"></a>

## D120 — baratheon — choose_combat_house_card (completed)

Run `bac45b40-b63a-42a5-8b9c-04b4c18599c9`. Requests: 6; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"house_card_id": "renly-baratheon", "force_valyrian_blade_decision": false}`

Handoff: Choosing Renly Baratheon (strength 3) gives the highest combat strength possible for us. Even with Sallaadhor's ability reducing Lannister's ship support, defender remains stronger (7 vs our max 6). Thus we cannot win this combat; selecting Renly maximizes our chance and may allow footman upgrade if we miraculously succeed.

Previous plan: Destroy the footman (ID 22) at Harrenhal to preserve the knight for defense and future attacks. This keeps a strong unit in the castle while reducing our forces minimally.

Pending: `{"type": "choose-house-card", "choosableHouseCards": [["lannister", ["ser-kevan-lannister", "tyrion-lannister", "the-hound"]], ["baratheon", ["salladhor-saan", "ser-davos-seaworth", "brienne-of-tarth", "renly-baratheon"]]], "houseCards": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d121"></a>

## D121 — lannister — choose_combat_house_card (completed)

Run `091656b8-6dd0-4f87-9213-f7f8fb46cbe8`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"house_card_id": "the-hound", "force_valyrian_blade_decision": false}`

Handoff: Play The Hound (strength 2) to ensure victory in the Harrenhal combat, capturing the castle. This secures an additional castle area, advancing us toward the 7‑castle win condition while preserving our supply and power.

Previous plan: Move siege-engine from Riverrun to Harrenhal to capture the castle while leaving the footman behind to retain control of Riverrun. No power token is spent, supply remains within limits, and we gain an additional castle area.

Pending: `{"type": "choose-house-card", "choosableHouseCards": [["lannister", ["ser-kevan-lannister", "tyrion-lannister", "the-hound"]], ["baratheon", ["salladhor-saan", "ser-davos-seaworth", "brienne-of-tarth", "renly-baratheon"]]], "houseCards": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d122"></a>

## D122 — stark — resolve_march (completed)

Run `2f403db4-28c1-4b27-a35a-5e545cfd665a`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "winterfell", "moves": [{"destination_region_id": "castle-black", "unit_ids": [2]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Moved Stark knight from Winterfell to empty Castle Black to expand land control without combat. No power token needed, supply remains within limits. This preserves our home castle and positions the knight for future operations.

Previous plan: Goal: capture Lannister's Moat Cailin stronghold using White Harbor footmen with support from the ship in the Shivering Sea (starred Support). Use Winterfell March to relocate our knight to the empty Stony Shore, expanding land control without risking our home castle (home area stays controlled automatically). This plan respects the single starred order limit and positions us for further advances next round.

Pending: `{"type": "resolve-single-march", "houseId": "stark", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "white-harbor", "orderId": 2, "order": "March +0", "unitIds": [30], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "castle-black", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[30]]}, {"regionId": "karhold", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[30]]}, {"regionId": "moat-cailin", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "lannister", "triggersCombat": true, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[30]]}, {"regionId": "widows-watch", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[30]]}, {"regionId": "winterfell", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "stark", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": []}], "canLeavePowerToken": false}, {"regionId": "winterfell", "orderId": 1, "order": "March -1", "unitIds": [2, 28, 29], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "castle-black", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[2], [28], [29], [2, 28], [2, 29], [28, 29], [2, 28, 29]]}, {"regionId": "karhold", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[2], [28], [29], [2, 28], [2, 29], [28, 29], [2, 28, 29]]}, {"regionId": "moat-cailin", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "lannister", "triggersCombat": true, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[2], [28], [29], [2, 28], [2, 29], [28, 29], [2, 28, 29]]}, {"regionId": "the-stony-shore", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[2], [28], [29], [2, 28], [2, 29], [28, 29], [2, 28, 29]]}, {"regionId": "white-harbor", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "stark", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[2], [28], [29], [2, 28], [2, 29], [28, 29]]}, {"regionId": "widows-watch", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[2], [28], [29], [2, 28], [2, 29], [28, 29], [2, 28, 29]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 6, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d123"></a>

## D123 — baratheon — resolve_march (completed)

Run `61d14458-105b-4e83-b09b-39e4ebcb26c9`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "the-reach", "moves": [{"destination_region_id": "searoad-marches", "unit_ids": [16]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Moved footman from The Reach to Seared Marches to position forces for a future attack on Lannisport stronghold while preserving our castle in The Reach via existing control token.

Previous plan: Choosing Renly Baratheon (strength 3) gives the highest combat strength possible for us. Even with Sallaadhor's ability reducing Lannister's ship support, defender remains stronger (7 vs our max 6). Thus we cannot win this combat; selecting Renly maximizes our chance and may allow footman upgrade if we miraculously succeed.

Pending: `{"type": "resolve-single-march", "houseId": "baratheon", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "the-reach", "orderId": 2, "order": "March +0", "unitIds": [16], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "blackwater", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[16]]}, {"regionId": "kings-landing", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[16]]}, {"regionId": "kingswood", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[16]]}, {"regionId": "searoad-marches", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[16]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 6, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["castle-black", "winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d124"></a>

## D124 — stark — resolve_march (completed)

Run `8f243b14-c832-4cf5-b76d-7cf8c2df6569`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "white-harbor", "moves": [{"destination_region_id": "winterfell", "unit_ids": [30]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Move the lone footman from White Harbor back to Winterfell, bolstering our home army without risking combat or needing a control token. This keeps us within supply limits and preserves our castle count while positioning the unit for future operations.

Previous plan: Moved Stark knight from Winterfell to empty Castle Black to expand land control without combat. No power token needed, supply remains within limits. This preserves our home castle and positions the knight for future operations.

Pending: `{"type": "resolve-single-march", "houseId": "stark", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "white-harbor", "orderId": 2, "order": "March +0", "unitIds": [30], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "castle-black", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "stark", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[30]]}, {"regionId": "karhold", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[30]]}, {"regionId": "moat-cailin", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "lannister", "triggersCombat": true, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[30]]}, {"regionId": "widows-watch", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[30]]}, {"regionId": "winterfell", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "stark", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[30]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 6, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["castle-black", "winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

