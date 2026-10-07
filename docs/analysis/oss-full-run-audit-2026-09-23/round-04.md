# Round 4: recorded decisions and state evidence

<a id="d037"></a>

## D037 — baratheon — choose_option (completed)

Run `e66ae51b-920a-4810-9e20-510a1cb26c90`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"choice_index": 0}`

Handoff: Choose Mustering. We will use the 6 mustering points from our 4 castles (the‑reach, crackclaw‑point, harrenhal) and stronghold (dragonstone) to add new units: footmen at each castle and a ship at shipbreaker‑bay (or port‑of‑dragonstone) to strengthen our forces and gain ports for future power. This stays within our current supply limit and improves both offensive and defensive options.

Previous plan: Play Stannis Baratheon (strength 4) to ensure victory at Harrenhal. Our base combat strength (3) plus Stannis gives 7 vs Lannister defender (3) plus any card; even if defender ties, we win tie on Fiefdoms. No sword icons needed, so no casualties are required; defender will retreat. This secures a stronghold, increasing our castle count toward victory. Valyrian Blade not owned, so not used.

Pending: `{"type": "simple-choice", "houseId": "baratheon", "description": "The holder of the Iron Throne token can choose between Mustering, Supply, or nothing at all.", "choices": ["Mustering", "Supply", "Nothing"]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d038"></a>

## D038 — baratheon — player-mustering (failed)

Run `c7d6dc40-28a1-405e-b075-0b6b120054b2`. Requests: 1; counts: `{"submissions": 0, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: None

Previous plan: Choose Mustering. We will use the 6 mustering points from our 4 castles (the‑reach, crackclaw‑point, harrenhal) and stronghold (dragonstone) to add new units: footmen at each castle and a ship at shipbreaker‑bay (or port‑of‑dragonstone) to strengthen our forces and gain ports for future power. This stays within our current supply limit and improves both offensive and defensive options.

Pending: `{"type": "player-mustering", "house": "baratheon", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "crackclaw-point", "musteringPoints": 1, "destinations": [{"regionId": "crackclaw-point", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "dragonstone", "musteringPoints": 2, "destinations": [{"regionId": "dragonstone", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-dragonstone", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}]}, {"regionId": "harrenhal", "musteringPoints": 1, "destinations": [{"regionId": "harrenhal", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}]}, {"regionId": "the-reach", "musteringPoints": 1, "destinations": [{"regionId": "the-reach", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 4, "siege-engine": 2}, "supplyLimit": {"level": 2, "allowedArmySizes": [3, 2, 2], "currentArmies": [{"regionId": "shipbreaker-bay", "unitCount": 2}], "singleUnitRegions": ["crackclaw-point", "harrenhal", "kingswood"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d039"></a>

## D039 — baratheon — player-mustering (failed)

Run `d97dfb51-256e-41f2-827f-fd6a28419f7a`. Requests: 1; counts: `{"submissions": 0, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: None

Previous plan: Choose Mustering. We will use the 6 mustering points from our 4 castles (the‑reach, crackclaw‑point, harrenhal) and stronghold (dragonstone) to add new units: footmen at each castle and a ship at shipbreaker‑bay (or port‑of‑dragonstone) to strengthen our forces and gain ports for future power. This stays within our current supply limit and improves both offensive and defensive options.

Pending: `{"type": "player-mustering", "house": "baratheon", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "crackclaw-point", "musteringPoints": 1, "destinations": [{"regionId": "crackclaw-point", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "dragonstone", "musteringPoints": 2, "destinations": [{"regionId": "dragonstone", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-dragonstone", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}]}, {"regionId": "harrenhal", "musteringPoints": 1, "destinations": [{"regionId": "harrenhal", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}]}, {"regionId": "the-reach", "musteringPoints": 1, "destinations": [{"regionId": "the-reach", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 4, "siege-engine": 2}, "supplyLimit": {"level": 2, "allowedArmySizes": [3, 2, 2], "currentArmies": [{"regionId": "shipbreaker-bay", "unitCount": 2}], "singleUnitRegions": ["crackclaw-point", "harrenhal", "kingswood"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d040"></a>

## D040 — baratheon — player-mustering (cancelled)

Run `673bf8bb-c19c-4e44-998c-03127917072b`. Requests: 90; counts: `{"submissions": 75, "explicitRejections": 0, "schemaInvalidSubmissions": 75, "reconstructedInvalidWithoutOutput": 75, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: None

Previous plan: Choose Mustering. We will use the 6 mustering points from our 4 castles (the‑reach, crackclaw‑point, harrenhal) and stronghold (dragonstone) to add new units: footmen at each castle and a ship at shipbreaker‑bay (or port‑of‑dragonstone) to strengthen our forces and gain ports for future power. This stays within our current supply limit and improves both offensive and defensive options.

Pending: `{"type": "player-mustering", "house": "baratheon", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "crackclaw-point", "musteringPoints": 1, "destinations": [{"regionId": "crackclaw-point", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "dragonstone", "musteringPoints": 2, "destinations": [{"regionId": "dragonstone", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-dragonstone", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}]}, {"regionId": "harrenhal", "musteringPoints": 1, "destinations": [{"regionId": "harrenhal", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}]}, {"regionId": "the-reach", "musteringPoints": 1, "destinations": [{"regionId": "the-reach", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 4, "siege-engine": 2}, "supplyLimit": {"level": 2, "allowedArmySizes": [3, 2, 2], "currentArmies": [{"regionId": "shipbreaker-bay", "unitCount": 2}], "singleUnitRegions": ["crackclaw-point", "harrenhal", "kingswood"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d041"></a>

## D041 — baratheon — player-mustering (failed)

Run `ebf23e77-9f55-4405-8e38-b00ab730fc95`. Requests: 1; counts: `{"submissions": 0, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: None

Previous plan: Choose Mustering. We will use the 6 mustering points from our 4 castles (the‑reach, crackclaw‑point, harrenhal) and stronghold (dragonstone) to add new units: footmen at each castle and a ship at shipbreaker‑bay (or port‑of‑dragonstone) to strengthen our forces and gain ports for future power. This stays within our current supply limit and improves both offensive and defensive options.

Pending: `{"type": "player-mustering", "house": "baratheon", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "crackclaw-point", "musteringPoints": 1, "destinations": [{"regionId": "crackclaw-point", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "dragonstone", "musteringPoints": 2, "destinations": [{"regionId": "dragonstone", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-dragonstone", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}]}, {"regionId": "harrenhal", "musteringPoints": 1, "destinations": [{"regionId": "harrenhal", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}]}, {"regionId": "the-reach", "musteringPoints": 1, "destinations": [{"regionId": "the-reach", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 4, "siege-engine": 2}, "supplyLimit": {"level": 2, "allowedArmySizes": [3, 2, 2], "currentArmies": [{"regionId": "shipbreaker-bay", "unitCount": 2}], "singleUnitRegions": ["crackclaw-point", "harrenhal", "kingswood"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d042"></a>

## D042 — baratheon — player-mustering (cancelled)

Run `5dceff2e-93be-48a5-93da-a13927d9cec9`. Requests: 80; counts: `{"submissions": 73, "explicitRejections": 0, "schemaInvalidSubmissions": 73, "reconstructedInvalidWithoutOutput": 73, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Mustering upgrade and new units.

Previous plan: Choose Mustering. We will use the 6 mustering points from our 4 castles (the‑reach, crackclaw‑point, harrenhal) and stronghold (dragonstone) to add new units: footmen at each castle and a ship at shipbreaker‑bay (or port‑of‑dragonstone) to strengthen our forces and gain ports for future power. This stays within our current supply limit and improves both offensive and defensive options.

Pending: `{"type": "player-mustering", "house": "baratheon", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "crackclaw-point", "musteringPoints": 1, "destinations": [{"regionId": "crackclaw-point", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "dragonstone", "musteringPoints": 2, "destinations": [{"regionId": "dragonstone", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-dragonstone", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}]}, {"regionId": "harrenhal", "musteringPoints": 1, "destinations": [{"regionId": "harrenhal", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}]}, {"regionId": "the-reach", "musteringPoints": 1, "destinations": [{"regionId": "the-reach", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 4, "siege-engine": 2}, "supplyLimit": {"level": 2, "allowedArmySizes": [3, 2, 2], "currentArmies": [{"regionId": "shipbreaker-bay", "unitCount": 2}], "singleUnitRegions": ["crackclaw-point", "harrenhal", "kingswood"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d043"></a>

## D043 — baratheon — muster_units (completed)

Run `a4fdbf9e-9864-40a9-a53a-da6eca4340b8`. Requests: 3; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"musters": [{"mustering_region_id": "crackclaw-point", "recruitments": [{"unit_type": "knight", "region_id": "crackclaw-point", "upgrade_from_footman": true}]}, {"mustering_region_id": "harrenhal", "recruitments": [{"unit_type": "knight", "region_id": "harrenhal", "upgrade_from_footman": true}]}, {"mustering_region_id": "the-reach", "recruitments": [{"unit_type": "footman", "region_id": "the-reach", "upgrade_from_footman": false}]}, {"mustering_region_id": "dragonstone", "recruitments": [{"unit_type": "footman", "region_id": "dragonstone", "upgrade_from_footman": false}, {"unit_type": "ship", "region_id": "port-of-dragonstone", "upgrade_from_footman": false}]}], "omitted_point_unsafe_recruitments": 0, "omitted_supply_unsafe_recruitments": 0}`

Handoff: Muster footmen and upgrade existing footmen to knights, adding a ship at port-of-dragonstone to boost naval power while staying within supply limits, preserving power tokens for upcoming influence bids.

Previous plan: Choose Mustering. We will use the 6 mustering points from our 4 castles (the‑reach, crackclaw‑point, harrenhal) and stronghold (dragonstone) to add new units: footmen at each castle and a ship at shipbreaker‑bay (or port‑of‑dragonstone) to strengthen our forces and gain ports for future power. This stays within our current supply limit and improves both offensive and defensive options.

Pending: `{"type": "player-mustering", "house": "baratheon", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "crackclaw-point", "musteringPoints": 1, "destinations": [{"regionId": "crackclaw-point", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "dragonstone", "musteringPoints": 2, "destinations": [{"regionId": "dragonstone", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-dragonstone", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}]}, {"regionId": "harrenhal", "musteringPoints": 1, "destinations": [{"regionId": "harrenhal", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}]}, {"regionId": "the-reach", "musteringPoints": 1, "destinations": [{"regionId": "the-reach", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 4, "siege-engine": 2}, "supplyLimit": {"level": 2, "allowedArmySizes": [3, 2, 2], "currentArmies": [{"regionId": "shipbreaker-bay", "unitCount": 2}], "singleUnitRegions": ["crackclaw-point", "harrenhal", "kingswood"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d044"></a>

## D044 — lannister — player-mustering (failed)

Run `0ac4d779-caf5-458a-8003-06a2c33ee6e5`. Requests: 1; counts: `{"submissions": 0, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: None

Previous plan: Moved footman from Seagard to capture Moat Cailin (castle). Left a Power token on Seagard to retain control of the stronghold, increasing Lannister's castle/stronghold count.

Pending: `{"type": "player-mustering", "house": "lannister", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "lannisport", "musteringPoints": 2, "destinations": [{"regionId": "lannisport", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}, {"regionId": "port-of-lannisport", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "moat-cailin", "musteringPoints": 1, "destinations": [{"regionId": "moat-cailin", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "riverrun", "musteringPoints": 2, "destinations": [{"regionId": "riverrun", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "seagard", "musteringPoints": 2, "destinations": [{"regionId": "seagard", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 5, "siege-engine": 2}, "supplyLimit": {"level": 3, "allowedArmySizes": [3, 2, 2, 2], "currentArmies": [], "singleUnitRegions": ["lannisport", "moat-cailin", "riverrun", "the-golden-sound"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d045"></a>

## D045 — lannister — player-mustering (failed)

Run `b12bb675-0774-4fda-99dd-649a607a62cc`. Requests: 1; counts: `{"submissions": 0, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: None

Previous plan: Moved footman from Seagard to capture Moat Cailin (castle). Left a Power token on Seagard to retain control of the stronghold, increasing Lannister's castle/stronghold count.

Pending: `{"type": "player-mustering", "house": "lannister", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "lannisport", "musteringPoints": 2, "destinations": [{"regionId": "lannisport", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}, {"regionId": "port-of-lannisport", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "moat-cailin", "musteringPoints": 1, "destinations": [{"regionId": "moat-cailin", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "riverrun", "musteringPoints": 2, "destinations": [{"regionId": "riverrun", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "seagard", "musteringPoints": 2, "destinations": [{"regionId": "seagard", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 5, "siege-engine": 2}, "supplyLimit": {"level": 3, "allowedArmySizes": [3, 2, 2, 2], "currentArmies": [], "singleUnitRegions": ["lannisport", "moat-cailin", "riverrun", "the-golden-sound"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d046"></a>

## D046 — lannister — player-mustering (failed)

Run `49e16d52-5ee0-4ffc-8088-f916575c8090`. Requests: 2; counts: `{"submissions": 0, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: None

Previous plan: Moved footman from Seagard to capture Moat Cailin (castle). Left a Power token on Seagard to retain control of the stronghold, increasing Lannister's castle/stronghold count.

Pending: `{"type": "player-mustering", "house": "lannister", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "lannisport", "musteringPoints": 2, "destinations": [{"regionId": "lannisport", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}, {"regionId": "port-of-lannisport", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "moat-cailin", "musteringPoints": 1, "destinations": [{"regionId": "moat-cailin", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "riverrun", "musteringPoints": 2, "destinations": [{"regionId": "riverrun", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "seagard", "musteringPoints": 2, "destinations": [{"regionId": "seagard", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 5, "siege-engine": 2}, "supplyLimit": {"level": 3, "allowedArmySizes": [3, 2, 2, 2], "currentArmies": [], "singleUnitRegions": ["lannisport", "moat-cailin", "riverrun", "the-golden-sound"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d047"></a>

## D047 — lannister — player-mustering (failed)

Run `71bd88dd-38e0-4015-80fc-38b8e0e30c95`. Requests: 1; counts: `{"submissions": 0, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: None

Previous plan: Moved footman from Seagard to capture Moat Cailin (castle). Left a Power token on Seagard to retain control of the stronghold, increasing Lannister's castle/stronghold count.

Pending: `{"type": "player-mustering", "house": "lannister", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "lannisport", "musteringPoints": 2, "destinations": [{"regionId": "lannisport", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}, {"regionId": "port-of-lannisport", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "moat-cailin", "musteringPoints": 1, "destinations": [{"regionId": "moat-cailin", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "riverrun", "musteringPoints": 2, "destinations": [{"regionId": "riverrun", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "seagard", "musteringPoints": 2, "destinations": [{"regionId": "seagard", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 5, "siege-engine": 2}, "supplyLimit": {"level": 3, "allowedArmySizes": [3, 2, 2, 2], "currentArmies": [], "singleUnitRegions": ["lannisport", "moat-cailin", "riverrun", "the-golden-sound"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d048"></a>

## D048 — lannister — skip_mustering (completed)

Run `1eca60b3-eaf8-4d69-9865-f3ae524179a4`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Skip mustering to preserve power tokens for upcoming bidding and maintain supply. Current holdings are stable; we'll focus on planning orders next phase.

Previous plan: Moved footman from Seagard to capture Moat Cailin (castle). Left a Power token on Seagard to retain control of the stronghold, increasing Lannister's castle/stronghold count.

Pending: `{"type": "player-mustering", "house": "lannister", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "lannisport", "musteringPoints": 2, "destinations": [{"regionId": "lannisport", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}, {"regionId": "port-of-lannisport", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "moat-cailin", "musteringPoints": 1, "destinations": [{"regionId": "moat-cailin", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "riverrun", "musteringPoints": 2, "destinations": [{"regionId": "riverrun", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "seagard", "musteringPoints": 2, "destinations": [{"regionId": "seagard", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 5, "siege-engine": 2}, "supplyLimit": {"level": 3, "allowedArmySizes": [3, 2, 2, 2], "currentArmies": [], "singleUnitRegions": ["lannisport", "moat-cailin", "riverrun", "the-golden-sound"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d049"></a>

## D049 — stark — skip_mustering (completed)

Run `846ad081-686f-4720-993a-d5cc15260d66`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: We skip mustering to preserve power tokens and avoid exceeding supply. Maintaining current forces lets us focus on strategic attacks and defense without overextending this round.

Previous plan: Discard the March order at The Stony Shore, keeping the knight in place and preserving our current position.

Pending: `{"type": "player-mustering", "house": "stark", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 2, "origins": [{"regionId": "white-harbor", "musteringPoints": 1, "destinations": [{"regionId": "white-harbor", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 2}, {"regionId": "port-of-white-harbor", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-shivering-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "winterfell", "musteringPoints": 2, "destinations": [{"regionId": "winterfell", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "bay-of-ice", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-winterfell", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-shivering-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 5, "siege-engine": 2}, "supplyLimit": {"level": 1, "allowedArmySizes": [3, 2], "currentArmies": [{"regionId": "white-harbor", "unitCount": 2}], "singleUnitRegions": ["the-shivering-sea", "the-stony-shore"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 1, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 5, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d050"></a>

## D050 — baratheon — submit_bid (completed)

Run `1096f01c-c8cc-4d4a-9365-4bb9233026a9`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 2}`

Handoff: Bid 2 power tokens to contribute to Night Watch defence while preserving the majority of our power (4 remaining) for upcoming Influence track bids. This moderate bid should help meet the wildling strength, which is unlikely to exceed the combined bids of all houses, and avoids excessive loss of resources that could hinder future expansions.

Previous plan: Muster footmen and upgrade existing footmen to knights, adding a ship at port-of-dragonstone to boost naval power while staying within supply limits, preserving power tokens for upcoming influence bids.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 6, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 4, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 6, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d051"></a>

## D051 — lannister — submit_bid (completed)

Run `f3bc1482-96f3-4f98-8575-c53c22d13bae`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 4}`

Handoff: Bid all 4 power tokens to contribute maximally to Night's Watch defense and avoid lowest-bid penalty. Preserve remaining power for upcoming influence bidding; expect opponents to have more tokens, but a full bid maximizes chance of winning or at least strong contribution.

Previous plan: Skip mustering to preserve power tokens for upcoming bidding and maintain supply. Current holdings are stable; we'll focus on planning orders next phase.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 6, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 4, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 6, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d052"></a>

## D052 — stark — submit_bid (completed)

Run `f6ee18e0-b87f-4a14-8fb4-fe7ef0875415`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 6}`

Handoff: Bid all 6 power tokens to ensure Night's Watch total meets or exceeds the wildling strength and to secure the reward as highest bidder. This maximizes our short-term safety against the wildling attack, preserving our castles and units, even though it exhausts our current power tokens; we will regain tokens via upcoming Consolidate Power orders and future Westeros cards.

Previous plan: We skip mustering to preserve power tokens and avoid exceeding supply. Maintaining current forces lets us focus on strategic attacks and defense without overextending this round.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 6, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 4, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 6, "supply": 1, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d053"></a>

## D053 — baratheon — submit_orders (completed)

Run `7c647058-b3fc-498c-941c-e9e81c5a37ce`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "kingswood", "preferred_order": "march", "starred_preference": "avoid", "priority": 100}, {"region_id": "the-reach", "preferred_order": "support", "starred_preference": "avoid", "priority": 80}, {"region_id": "crackclaw-point", "preferred_order": "support", "starred_preference": "prefer", "priority": 70}, {"region_id": "harrenhal", "preferred_order": "defense", "starred_preference": "avoid", "priority": 60}, {"region_id": "shipbreaker-bay", "preferred_order": "consolidate_power", "starred_preference": "avoid", "priority": 50}, {"region_id": "dragonstone", "preferred_order": "defense", "starred_preference": "avoid", "priority": 40}, {"region_id": "port-of-dragonstone", "preferred_order": "defense", "starred_preference": "avoid", "priority": 30}], "applied_orders": [{"region_id": "kingswood", "order_id": 2, "order": "march"}, {"region_id": "the-reach", "order_id": 7, "order": "support"}, {"region_id": "crackclaw-point", "order_id": 8, "order": "support"}, {"region_id": "harrenhal", "order_id": 6, "order": "defense"}, {"region_id": "shipbreaker-bay", "order_id": 10, "order": "consolidate_power"}, {"region_id": "dragonstone", "order_id": 4, "order": "defense"}, {"region_id": "port-of-dragonstone", "order_id": 5, "order": "defense"}]}`

Handoff: Aim to capture Kings Landing castle next round by marching the knight from Kingswood into the empty stronghold. Support the attack with a regular support order from The Reach and a starred support at Crackclaw Point to boost future combats. Defend our existing castles at Harrenhal and Dragonstone, and collect power at Shipbreaker Bay. The port at Dragonstone holds a defense order to retain control.

Previous plan: Bid 2 power tokens to contribute to Night Watch defence while preserving the majority of our power (4 remaining) for upcoming Influence track bids. This moderate bid should help meet the wildling strength, which is unlikely to exceed the combined bids of all houses, and avoids excessive loss of resources that could hinder future expansions.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d054"></a>

## D054 — lannister — submit_orders (completed)

Run `1cda1f1b-6800-4279-a7f3-03698be7972e`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "riverrun", "preferred_order": "march", "starred_preference": "prefer", "priority": 100}, {"region_id": "lannisport", "preferred_order": "defense", "starred_preference": "prefer", "priority": 100}, {"region_id": "the-golden-sound", "preferred_order": "support", "starred_preference": "prefer", "priority": 80}, {"region_id": "moat-cailin", "preferred_order": "defense", "starred_preference": "avoid", "priority": 70}], "applied_orders": [{"region_id": "riverrun", "order_id": 3, "order": "march"}, {"region_id": "lannisport", "order_id": 6, "order": "defense"}, {"region_id": "the-golden-sound", "order_id": 9, "order": "support"}, {"region_id": "moat-cailin", "order_id": 4, "order": "defense"}]}`

Handoff: Goal: expand castle count by attacking Baratheon's knight at Harrenhal from Riverrun with a starred March +1, securing the castle if successful. Protect our knight at Lannisport with a starred Defense +2 to guard against counter‑attack. Place a starred Support +1 at The Golden Sound to boost any naval combat or future ship‑based attacks. Keep a normal Defense at Moat Cailin to hold the footman while preserving our power token there. Starred orders limited to three; assignments respect that limit.

Previous plan: Bid all 4 power tokens to contribute maximally to Night's Watch defense and avoid lowest-bid penalty. Preserve remaining power for upcoming influence bidding; expect opponents to have more tokens, but a full bid maximizes chance of winning or at least strong contribution.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d055"></a>

## D055 — stark — submit_orders (completed)

Run `0b78c4ee-dac6-4ad4-aa53-d4ed20497219`. Requests: 5; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "the-stony-shore", "preferred_order": "march", "starred_preference": "avoid", "priority": 100}, {"region_id": "white-harbor", "preferred_order": "defense", "starred_preference": "avoid", "priority": 90}, {"region_id": "the-shivering-sea", "preferred_order": "support", "starred_preference": "prefer", "priority": 80}], "applied_orders": [{"region_id": "the-stony-shore", "order_id": 2, "order": "march"}, {"region_id": "white-harbor", "order_id": 4, "order": "defense"}, {"region_id": "the-shivering-sea", "order_id": 9, "order": "support"}]}`

Handoff: Maintain our two castles (Winterfell stronghold and White Harbor castle) while reinforcing Winterfell. Use a March order from The Stony Shore to move the knight into Winterfell, strengthening our home stronghold without sacrificing control of White Harbor. Assign a Defense order to White Harbor to protect its castle. Provide a starred Support order from the ship in The Shivering Sea to boost any future combat we may initiate, giving us flexibility to attack nearby enemy holdings later. This allocation respects the two-star limit and positions us to expand toward opponent castles in upcoming rounds.

Previous plan: Bid all 6 power tokens to ensure Night's Watch total meets or exceeds the wildling strength and to secure the reward as highest bidder. This maximizes our short-term safety against the wildling attack, preserving our castles and units, even though it exhausts our current power tokens; we will regain tokens via upcoming Consolidate Power orders and future Westeros cards.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d056"></a>

## D056 — lannister — skip_raven_order_replacement (completed)

Run `af83e8b9-01f0-4a4f-819d-c4613b621858`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: We keep our current orders: Defense+2 starred at Lannisport, Defense+1 at Moat Cailin, March+1 at Riverrun, Support+1 starred at The Golden Sound. No order replacement needed; preserving defenses and support is optimal this turn.

Previous plan: Goal: expand castle count by attacking Baratheon's knight at Harrenhal from Riverrun with a starred March +1, securing the castle if successful. Protect our knight at Lannisport with a starred Defense +2 to guard against counter‑attack. Place a starred Support +1 at The Golden Sound to boost any naval combat or future ship‑based attacks. Keep a normal Defense at Moat Cailin to hold the footman while preserving our power token there. Starred orders limited to three; assignments respect that limit.

Pending: `{"type": "replace-order"}`

Guidance: `{"decision": "raven-order-replacement", "legalReplacements": [{"regionId": "lannisport", "originalOrderId": 6, "availableOrderIds": [1, 2, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]}, {"regionId": "moat-cailin", "originalOrderId": 4, "availableOrderIds": [1, 2, 4, 5, 7, 8, 10, 11, 13, 14]}, {"regionId": "riverrun", "originalOrderId": 3, "availableOrderIds": [1, 2, 3, 5, 7, 8, 10, 11, 12, 13, 14, 15]}, {"regionId": "the-golden-sound", "originalOrderId": 9, "availableOrderIds": [1, 2, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15]}], "safeChoices": ["Choose skip_raven_order_replacement to keep every order.", "Choose inspect_top_wildling_card to use the Raven on the Wildling deck."]}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d057"></a>

## D057 — baratheon — resolve_march (completed)

Run `d4393d7f-c510-44ed-9dbd-d059cfe6bd3c`. Requests: 4; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "kingswood", "moves": [{"destination_region_id": "kings-landing", "unit_ids": [10]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: March the knight from Kingswood into Kings Landing to capture the stronghold, using support from Crackclaw Point and The Reach. No control token needed; Kingswood will be vacated, gaining a castle area and improving victory position.

Previous plan: Aim to capture Kings Landing castle next round by marching the knight from Kingswood into the empty stronghold. Support the attack with a regular support order from The Reach and a starred support at Crackclaw Point to boost future combats. Defend our existing castles at Harrenhal and Dragonstone, and collect power at Shipbreaker Bay. The port at Dragonstone holds a defense order to retain control.

Pending: `{"type": "resolve-single-march", "houseId": "baratheon", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "kingswood", "orderId": 2, "order": "March +0", "unitIds": [10], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "crackclaw-point", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[10]]}, {"regionId": "dragonstone", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[10]]}, {"regionId": "kings-landing", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 1, "garrison": 5, "controller": null, "triggersCombat": true, "neutralForce": {"requiredStrength": 5, "hasStructure": true, "feasibleUnitIdGroups": [[10]]}, "supplySafeUnitIdGroupsWhenChosenAlone": [[10]]}, {"regionId": "the-reach", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[10]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 2, "currentVictoryPoints": 4, "controlledLandAreas": 6, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d058"></a>

## D058 — lannister — resolve_march (completed)

Run `2b93b80c-a44e-4217-986e-01e599a94ee2`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "riverrun", "moves": [], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Discard the March order from Riverrun to preserve the footman and our stronghold at Riverrun. No attack is viable (Harrenhal defended heavily). Keeping the footman maintains our castle count. No power token available to leave a control token, so moving would lose Riverrun. Therefore we empty the moves list, discarding the order.

Previous plan: We keep our current orders: Defense+2 starred at Lannisport, Defense+1 at Moat Cailin, March+1 at Riverrun, Support+1 starred at The Golden Sound. No order replacement needed; preserving defenses and support is optimal this turn.

Pending: `{"type": "resolve-single-march", "houseId": "lannister", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "riverrun", "orderId": 3, "order": "March +1", "unitIds": [8], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "harrenhal", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "baratheon", "triggersCombat": true, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "lannisport", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "seagard", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "searoad-marches", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "stoney-sept", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 2, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d059"></a>

## D059 — stark — resolve_march (completed)

Run `17fcd4ba-f58b-483b-99e7-7f8e7690eaf7`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "the-stony-shore", "moves": [{"destination_region_id": "winterfell", "unit_ids": [2]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Move the Stark knight from The Stony Shore to Winterfell, preserving our stronghold without losing any castle area and staying within supply. No power token is needed as the area has no castle, and this positions us for future actions.

Previous plan: Maintain our two castles (Winterfell stronghold and White Harbor castle) while reinforcing Winterfell. Use a March order from The Stony Shore to move the knight into Winterfell, strengthening our home stronghold without sacrificing control of White Harbor. Assign a Defense order to White Harbor to protect its castle. Provide a starred Support order from the ship in The Shivering Sea to boost any future combat we may initiate, giving us flexibility to attack nearby enemy holdings later. This allocation respects the two-star limit and positions us to expand toward opponent castles in upcoming rounds.

Pending: `{"type": "resolve-single-march", "houseId": "stark", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "the-stony-shore", "orderId": 2, "order": "March +0", "unitIds": [2], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "winterfell", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "stark", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[2]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["stark", "baratheon", "lannister"], "kingsCourt": ["lannister", "stark", "baratheon"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 2, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 3, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

