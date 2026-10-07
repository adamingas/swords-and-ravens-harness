# Round 7: recorded decisions and state evidence

<a id="d090"></a>

## D090 — baratheon — skip_mustering (completed)

Run `3a334f9e-1f3a-4dbf-b490-f44a0b4d9b6c`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Skip mustering this round to preserve power tokens for influence bidding and avoid exceeding supply while focusing on upcoming attacks on Lannister positions.

Previous plan: Moved both knights from King's Landing to Crackclaw Point to consolidate forces and threaten Lannister's Lannisport. Retained control of King's Landing stronghold via a power token. No combat initiated this turn.

Pending: `{"type": "player-mustering", "house": "baratheon", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 5, "origins": [{"regionId": "crackclaw-point", "musteringPoints": 1, "destinations": [{"regionId": "crackclaw-point", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 3, "supplySafeNewUnitsWhenChosenAlone": 0, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "dragonstone", "musteringPoints": 2, "destinations": [{"regionId": "dragonstone", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "port-of-dragonstone", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 3, "supplySafeNewUnitsWhenChosenAlone": 0, "upgradeableFootmen": 0}]}, {"regionId": "harrenhal", "musteringPoints": 1, "destinations": [{"regionId": "harrenhal", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "kings-landing", "musteringPoints": 2, "destinations": [{"regionId": "kings-landing", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "the-reach", "musteringPoints": 1, "destinations": [{"regionId": "the-reach", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}]}], "availablePieces": {"footman": 8, "knight": 2, "ship": 3, "siege-engine": 2}, "supplyLimit": {"level": 4, "allowedArmySizes": [3, 3, 2, 2], "currentArmies": [{"regionId": "shipbreaker-bay", "unitCount": 3}, {"regionId": "crackclaw-point", "unitCount": 2}], "singleUnitRegions": ["dragonstone", "harrenhal", "the-reach"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d091"></a>

## D091 — lannister — skip_mustering (completed)

Run `f935f771-2f85-45cf-b6fa-b88ea4c0e5d7`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: We skip mustering this turn to conserve resources, maintain supply balance, and keep focus on upcoming combat and bidding. No new units are recruited.

Previous plan: Combat at White Harbor vs Moat Cailin: Lannister defender has 1 footman (strength1). To secure win, play strongest card Ser Gregor Clegane (strength3, 3 swords). Baron Baratheon holds Valyrian Blade, not usable. This ensures Lannister victory and eliminates Stark footmen.

Pending: `{"type": "player-mustering", "house": "lannister", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "lannisport", "musteringPoints": 2, "destinations": [{"regionId": "lannisport", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}, {"regionId": "port-of-lannisport", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "moat-cailin", "musteringPoints": 1, "destinations": [{"regionId": "moat-cailin", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "riverrun", "musteringPoints": 2, "destinations": [{"regionId": "riverrun", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "seagard", "musteringPoints": 2, "destinations": [{"regionId": "seagard", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 4, "ship": 5, "siege-engine": 2}, "supplyLimit": {"level": 4, "allowedArmySizes": [3, 3, 2, 2], "currentArmies": [], "singleUnitRegions": ["lannisport", "moat-cailin", "riverrun", "the-golden-sound"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d092"></a>

## D092 — stark — skip_mustering (completed)

Run `5d922f37-2e19-4a2f-8a1c-54666f6810f5`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Skip mustering this round to conserve supply and avoid overextending. Maintain current forces while preparing for a future attack on Moat Cailin with existing units and support.

Previous plan: Use Catelyn Stark (strength 0) to conserve stronger cards for future combats. Victory already secured; no need for extra strength or abilities. Preserve higher-value cards for critical battles. Maintain plan to expand toward Moat Cailin castle while keeping supply safe.

Pending: `{"type": "player-mustering", "house": "stark", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 2, "origins": [{"regionId": "white-harbor", "musteringPoints": 1, "destinations": [{"regionId": "white-harbor", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-white-harbor", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-shivering-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "winterfell", "musteringPoints": 2, "destinations": [{"regionId": "winterfell", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "bay-of-ice", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-winterfell", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-shivering-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 10, "knight": 4, "ship": 5, "siege-engine": 2}, "supplyLimit": {"level": 2, "allowedArmySizes": [3, 2, 2], "currentArmies": [], "singleUnitRegions": ["the-shivering-sea", "the-stony-shore"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d093"></a>

## D093 — baratheon — submit_bid (completed)

Run `b0001c66-3dc4-4167-8572-d31084b71227`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Bid 0 to retain Iron Throne position while conserving power for upcoming Fiefdoms and King’s Court bids.

Previous plan: Skip mustering this round to preserve power tokens for influence bidding and avoid exceeding supply while focusing on upcoming attacks on Lannister positions.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["lannister", -1], ["stark", -1]], "currentTrack": {"index": 0, "id": "iron-throne", "name": "Iron Throne", "meaning": "Higher position acts earlier during the Action phase. The player in first place holds the Iron Throne token and decides unresolved non-combat ties, including tied influence bids. This track does not break combat ties."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d094"></a>

## D094 — baratheon — resolve_track_ties (completed)

Run `d9afb9d8-776d-4b84-89c5-86b84bb35952`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"preferred_house_ids": ["baratheon", "lannister", "stark"], "applied_house_ids": ["baratheon", "lannister", "stark"]}`

Handoff: Maintain Iron Throne lead by ordering Baratheon first, then Lannister, then Stark. This preserves our tie-breaking advantage for upcoming bids and actions. Keep focus on securing castles and supply while preparing for next round attacks.

Previous plan: Bid 0 to retain Iron Throne position while conserving power for upcoming Fiefdoms and King’s Court bids.

Pending: `{"type": "resolve-ties", "bidResults": [[0, ["lannister", "stark", "baratheon"]]], "currentTrack": {"index": 0, "id": "iron-throne", "name": "Iron Throne", "meaning": "Higher position acts earlier during the Action phase. The player in first place holds the Iron Throne token and decides unresolved non-combat ties, including tied influence bids. This track does not break combat ties."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d095"></a>

## D095 — baratheon — submit_bid (completed)

Run `0b67505a-5e7b-4207-abff-b71a5f977149`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Bid 0 to preserve power tokens; opponents have no available power, so we retain first place on Fiefdoms (Valyrian Steel Blade) and maintain combat advantage while conserving resources for future bids and actions.

Previous plan: Maintain Iron Throne lead by ordering Baratheon first, then Lannister, then Stark. This preserves our tie-breaking advantage for upcoming bids and actions. Keep focus on securing castles and supply while preparing for next round attacks.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["lannister", -1], ["stark", -1]], "currentTrack": {"index": 1, "id": "fiefdoms", "name": "Fiefdoms", "meaning": "Higher position wins a tied combat total. The player in first place holds the Valyrian Steel Blade and may normally spend it once per round to add +1 to their combat strength after House cards are revealed."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d096"></a>

## D096 — baratheon — resolve_track_ties (completed)

Run `53e679db-ac2f-4092-a22f-967b25eb4834`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"preferred_house_ids": ["baratheon", "lannister", "stark"], "applied_house_ids": ["baratheon", "lannister", "stark"]}`

Handoff: Maintain Valyrian Steel Blade advantage by keeping Baratheon first on Fiefdoms. Prioritize protecting our castles while expanding toward Lannister holdings. Preserve power tokens for future bids and combat. Keep supply safe and prepare March orders for next round.

Previous plan: Bid 0 to preserve power tokens; opponents have no available power, so we retain first place on Fiefdoms (Valyrian Steel Blade) and maintain combat advantage while conserving resources for future bids and actions.

Pending: `{"type": "resolve-ties", "bidResults": [[0, ["lannister", "stark", "baratheon"]]], "currentTrack": {"index": 1, "id": "fiefdoms", "name": "Fiefdoms", "meaning": "Higher position wins a tied combat total. The player in first place holds the Valyrian Steel Blade and may normally spend it once per round to add +1 to their combat strength after House cards are revealed."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d097"></a>

## D097 — baratheon — submit_bid (completed)

Run `67aed2e8-0f6b-45bd-9c65-ff2473412edf`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Bid 0 to preserve power tokens; opponents have no power, so we retain first place on King's Court, keeping our special order advantage while conserving resources for upcoming Iron Throne and Fiefdoms bids and combat.

Previous plan: Maintain Valyrian Steel Blade advantage by keeping Baratheon first on Fiefdoms. Prioritize protecting our castles while expanding toward Lannister holdings. Preserve power tokens for future bids and combat. Keep supply safe and prepare March orders for next round.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["lannister", -1], ["stark", -1]], "currentTrack": {"index": 2, "id": "kings-court", "name": "King's Court", "meaning": "Your position determines how many starred special Order tokens you may place each round; higher positions receive more. The player in first place holds the Messenger Raven and, after orders are revealed, may replace one of their orders or inspect the top Wildling card."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d098"></a>

## D098 — baratheon — resolve_track_ties (completed)

Run `441c1f4e-74de-4080-ba6f-b2dc7568ba05`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"preferred_house_ids": ["baratheon", "lannister", "stark"], "applied_house_ids": ["baratheon", "lannister", "stark"]}`

Handoff: Maintain King's Court lead to keep special orders advantage; rank Baratheon highest, then Lannister, then Stark.

Previous plan: Bid 0 to preserve power tokens; opponents have no power, so we retain first place on King's Court, keeping our special order advantage while conserving resources for upcoming Iron Throne and Fiefdoms bids and combat.

Pending: `{"type": "resolve-ties", "bidResults": [[0, ["lannister", "stark", "baratheon"]]], "currentTrack": {"index": 2, "id": "kings-court", "name": "King's Court", "meaning": "Your position determines how many starred special Order tokens you may place each round; higher positions receive more. The player in first place holds the Messenger Raven and, after orders are revealed, may replace one of their orders or inspect the top Wildling card."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d099"></a>

## D099 — lannister — submit_orders (completed)

Run `d2b63285-d712-43c0-a99f-105fdac4266e`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "moat-cailin", "preferred_order": "march", "starred_preference": "prefer", "priority": 100}, {"region_id": "riverrun", "preferred_order": "consolidate_power", "starred_preference": "avoid", "priority": 90}, {"region_id": "lannisport", "preferred_order": "support", "starred_preference": "avoid", "priority": 80}, {"region_id": "the-golden-sound", "preferred_order": "support", "starred_preference": "prefer", "priority": 85}], "applied_orders": [{"region_id": "moat-cailin", "order_id": 3, "order": "march"}, {"region_id": "riverrun", "order_id": 10, "order": "consolidate_power"}, {"region_id": "lannisport", "order_id": 7, "order": "support"}, {"region_id": "the-golden-sound", "order_id": 9, "order": "support"}]}`

Handoff: Goal: capture White Harbor castle using a starred March from Moat Cailin, gain a power token at Riverrun via Consolidate Power, keep naval support at The Golden Sound (starred) and provide ground support from Lannisport. Preserve our existing castles and increase victory points.

Previous plan: We skip mustering this turn to conserve resources, maintain supply balance, and keep focus on upcoming combat and bidding. No new units are recruited.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d100"></a>

## D100 — stark — submit_orders (completed)

Run `b6a1d5e1-ea65-4c7b-9d47-6b874b64dd3e`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "the-stony-shore", "preferred_order": "march", "starred_preference": "avoid", "priority": 100}, {"region_id": "the-shivering-sea", "preferred_order": "support", "starred_preference": "prefer", "priority": 90}], "applied_orders": [{"region_id": "the-stony-shore", "order_id": 2, "order": "march"}, {"region_id": "the-shivering-sea", "order_id": 9, "order": "support"}]}`

Handoff: Goal: Move Stark knight from The Stony Shore into Winterfell to consolidate the stronghold and keep supply safe. Use a starred Support order on the ship at The Shivering Sea to boost any upcoming combat (e.g., future attack on Moat Cailin). No defense orders allowed this round.

Previous plan: Skip mustering this round to conserve supply and avoid overextending. Maintain current forces while preparing for a future attack on Moat Cailin with existing units and support.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d101"></a>

## D101 — baratheon — submit_orders (completed)

Run `fa3226eb-89c1-49ad-a071-9d577da127f2`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "the-reach", "preferred_order": "march", "starred_preference": "avoid", "priority": 100}, {"region_id": "crackclaw-point", "preferred_order": "march", "starred_preference": "avoid", "priority": 90}, {"region_id": "harrenhal", "preferred_order": "support", "starred_preference": "prefer", "priority": 80}, {"region_id": "shipbreaker-bay", "preferred_order": "support", "starred_preference": "prefer", "priority": 70}, {"region_id": "dragonstone", "preferred_order": "consolidate_power", "starred_preference": "avoid", "priority": 60}], "applied_orders": [{"region_id": "the-reach", "order_id": 2, "order": "march"}, {"region_id": "crackclaw-point", "order_id": 1, "order": "march"}, {"region_id": "harrenhal", "order_id": 9, "order": "support"}, {"region_id": "shipbreaker-bay", "order_id": 7, "order": "support"}, {"region_id": "dragonstone", "order_id": 10, "order": "consolidate_power"}]}`

Handoff: Focus on expanding towards Lannister holdings. Use The Reach March to push footman toward Searoad Marches and eventually Lannisport. Move knights from Crackclaw Point towards Kings Landing to reinforce our stronghold. Provide starred Support from Harrenhal and Shipbreaker Bay to boost any upcoming attacks. Consolidate Power at Dragonstone to gain extra power token. Maintain supply and prepare for potential combat next round.

Previous plan: Maintain King's Court lead to keep special orders advantage; rank Baratheon highest, then Lannister, then Stark.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d102"></a>

## D102 — baratheon — replace_raven_order (completed)

Run `bdd0f79d-d889-4ede-971a-10e79fc79813`. Requests: 3; counts: `{"submissions": 3, "explicitRejections": 2, "schemaInvalidSubmissions": 2, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"region_id": "the-reach", "order_id": 6}`

Handoff: Replace The Reach's March +0 with a starred Defense +2 order (order ID 6) to fortify our castle against potential Lannister attacks, preserving our expansion momentum and securing a key stronghold.

Previous plan: Focus on expanding towards Lannister holdings. Use The Reach March to push footman toward Searoad Marches and eventually Lannisport. Move knights from Crackclaw Point towards Kings Landing to reinforce our stronghold. Provide starred Support from Harrenhal and Shipbreaker Bay to boost any upcoming attacks. Consolidate Power at Dragonstone to gain extra power token. Maintain supply and prepare for potential combat next round.

Pending: `{"type": "replace-order"}`

Guidance: `{"decision": "raven-order-replacement", "legalReplacements": [{"regionId": "crackclaw-point", "originalOrderId": 1, "availableOrderIds": [1, 3, 4, 5, 6, 8, 11, 12, 13, 14, 15]}, {"regionId": "dragonstone", "originalOrderId": 10, "availableOrderIds": [3, 4, 5, 6, 8, 10, 11, 12, 13, 14, 15]}, {"regionId": "harrenhal", "originalOrderId": 9, "availableOrderIds": [3, 4, 5, 6, 8, 9, 11, 12, 13, 14, 15]}, {"regionId": "shipbreaker-bay", "originalOrderId": 7, "availableOrderIds": [3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15]}, {"regionId": "the-reach", "originalOrderId": 2, "availableOrderIds": [2, 3, 4, 5, 6, 8, 11, 12, 13, 14, 15]}], "safeChoices": ["Choose skip_raven_order_replacement to keep every order.", "Choose inspect_top_wildling_card to use the Raven on the Wildling deck."]}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d103"></a>

## D103 — baratheon — resolve_march (completed)

Run `4b432e68-6107-4e3e-8f30-87206f488f8d`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "crackclaw-point", "moves": [{"destination_region_id": "kingswood", "unit_ids": [10, 14]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Moved both knights from Crackclaw Point to Kingswood to consolidate forces near shipbreaker bay, enabling future ship‑transport attacks toward Lannisport while retaining control of the castle at Crackclaw Point via existing power token. No combat triggered and supply remains within limits.

Previous plan: Replace The Reach's March +0 with a starred Defense +2 order (order ID 6) to fortify our castle against potential Lannister attacks, preserving our expansion momentum and securing a key stronghold.

Pending: `{"type": "resolve-single-march", "houseId": "baratheon", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "crackclaw-point", "orderId": 1, "order": "March -1", "unitIds": [10, 14], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "blackwater", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[10], [14], [10, 14]]}, {"regionId": "dragonstone", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[10], [14], [10, 14]]}, {"regionId": "harrenhal", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[10], [14], [10, 14]]}, {"regionId": "kings-landing", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[10], [14], [10, 14]]}, {"regionId": "kingswood", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[10], [14], [10, 14]]}, {"regionId": "the-mountains-of-the-moon", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[10], [14], [10, 14]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d104"></a>

## D104 — lannister — resolve_march (completed)

Run `b3a17e41-b278-461c-9a0d-4829349b64f3`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "moat-cailin", "moves": [], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Discard Moat Cailin March order to keep the footman in place, preserving the castle area. No power token is available to leave a control token, and attacking White Harbor would likely fail against Stark's garrison and support. Maintaining the castle keeps our victory point count stable.

Previous plan: Goal: capture White Harbor castle using a starred March from Moat Cailin, gain a power token at Riverrun via Consolidate Power, keep naval support at The Golden Sound (starred) and provide ground support from Lannisport. Preserve our existing castles and increase victory points.

Pending: `{"type": "resolve-single-march", "houseId": "lannister", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "moat-cailin", "orderId": 3, "order": "March +1", "unitIds": [5], "castleAreasLostIfEmptiedWithoutToken": 1, "reachableRegions": [{"regionId": "greywater-watch", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5]]}, {"regionId": "seagard", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5]]}, {"regionId": "the-twins", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5]]}, {"regionId": "white-harbor", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "stark", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5]]}, {"regionId": "winterfell", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 1, "garrison": 2, "controller": "stark", "triggersCombat": true, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[5]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d105"></a>

## D105 — stark — resolve_march (completed)

Run `49b9d051-16b3-450c-a1c1-3637d327e457`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "the-stony-shore", "moves": [{"destination_region_id": "winterfell", "unit_ids": [2]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Moved the Stark knight from The Stony Shore into Winterfell, reinforcing the stronghold without combat or power token loss.

Previous plan: Goal: Move Stark knight from The Stony Shore into Winterfell to consolidate the stronghold and keep supply safe. Use a starred Support order on the ship at The Shivering Sea to boost any upcoming combat (e.g., future attack on Moat Cailin). No defense orders allowed this round.

Pending: `{"type": "resolve-single-march", "houseId": "stark", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "the-stony-shore", "orderId": 2, "order": "March +0", "unitIds": [2], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "winterfell", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "stark", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[2]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 7, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 7, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 2, "controlledRegions": ["winterfell", "port-of-winterfell", "the-stony-shore", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

