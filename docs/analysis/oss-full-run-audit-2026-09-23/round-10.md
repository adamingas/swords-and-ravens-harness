# Round 10: recorded decisions and state evidence

<a id="d157"></a>

## D157 — baratheon — skip_mustering (completed)

Run `bd9004f8-a31e-4f51-a53d-e8af4b9c3a99`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Baratheon skips mustering to conserve power tokens and avoid supply issues. Proceed to assign orders for final round attacks on Lannister castles and secure remaining territories.

Previous plan: Retreat survivors to Crackclaw Point as the only legal retreat for the attacking army after losing at Harrenhal. This preserves our remaining footman unit (now routed) and keeps our controlled areas intact for future actions.

Pending: `{"type": "player-mustering", "house": "baratheon", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "crackclaw-point", "musteringPoints": 1, "destinations": [{"regionId": "crackclaw-point", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 3, "supplySafeNewUnitsWhenChosenAlone": 0, "upgradeableFootmen": 0}]}, {"regionId": "dragonstone", "musteringPoints": 2, "destinations": [{"regionId": "dragonstone", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 1}, {"regionId": "port-of-dragonstone", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "shipbreaker-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 3, "supplySafeNewUnitsWhenChosenAlone": 0, "upgradeableFootmen": 0}]}, {"regionId": "kings-landing", "musteringPoints": 2, "destinations": [{"regionId": "kings-landing", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}, {"regionId": "blackwater-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "the-reach", "musteringPoints": 1, "destinations": [{"regionId": "the-reach", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 6, "knight": 4, "ship": 3, "siege-engine": 2}, "supplyLimit": {"level": 4, "allowedArmySizes": [3, 3, 2, 2], "currentArmies": [{"regionId": "shipbreaker-bay", "unitCount": 3}, {"regionId": "dragonstone", "unitCount": 2}], "singleUnitRegions": ["crackclaw-point", "kings-landing", "searoad-marches"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d158"></a>

## D158 — stark — skip_mustering (completed)

Run `56ae9286-fcc1-4ec9-bbec-a7335ccde399`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Stark skips mustering this final round. With only 3 castles controlled and no realistic path to reach 7 before round end, adding units offers minimal gain. Skipping conserves available pieces and avoids potential supply issues, focusing on the inevitable end-of-game scoring where Stark is behind.

Previous plan: Move Stark ship from The Shivering Sea to The Narrow Sea to expand naval reach for future transport without combat. No power token needed.

Pending: `{"type": "player-mustering", "house": "stark", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 3, "origins": [{"regionId": "moat-cailin", "musteringPoints": 1, "destinations": [{"regionId": "moat-cailin", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 2}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}]}, {"regionId": "white-harbor", "musteringPoints": 1, "destinations": [{"regionId": "white-harbor", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-white-harbor", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-narrow-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}, {"regionId": "the-shivering-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "winterfell", "musteringPoints": 2, "destinations": [{"regionId": "winterfell", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "bay-of-ice", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "port-of-winterfell", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-shivering-sea", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 8, "knight": 5, "ship": 5, "siege-engine": 2}, "supplyLimit": {"level": 2, "allowedArmySizes": [3, 2, 2], "currentArmies": [{"regionId": "moat-cailin", "unitCount": 2}], "singleUnitRegions": ["the-narrow-sea"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d159"></a>

## D159 — lannister — skip_mustering (completed)

Run `c1e55389-b94b-4bc0-8d2c-a1c6747b7453`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Maintain current position into final round. Preserve power tokens for possible bids. No mustering to avoid exceeding supply and to keep units ready for final March attacks targeting opponent castles.

Previous plan: Capture Harrenhal castle by moving the footman from Riverrun, increasing our castle count and weakening Baratheon. No control token needed as Riverrun stays under our control via existing control token/home symbol. This move stays within supply limits and improves position toward victory.

Pending: `{"type": "player-mustering", "house": "lannister", "musteringType": 0}`

Guidance: `{"decision": "mustering", "musteringType": 0, "maxOriginGroups": 4, "origins": [{"regionId": "harrenhal", "musteringPoints": 1, "destinations": [{"regionId": "harrenhal", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 1}]}, {"regionId": "lannisport", "musteringPoints": 2, "destinations": [{"regionId": "lannisport", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 1, "supplySafeNewUnitsWhenChosenAlone": 2, "upgradeableFootmen": 0}, {"regionId": "port-of-lannisport", "type": "port", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "riverrun", "musteringPoints": 2, "destinations": [{"regionId": "riverrun", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}, {"regionId": "the-golden-sound", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}, {"regionId": "seagard", "musteringPoints": 2, "destinations": [{"regionId": "seagard", "type": "land", "newUnitTypes": ["footman", "knight", "siege-engine"], "currentUnitCount": 2, "supplySafeNewUnitsWhenChosenAlone": 1, "upgradeableFootmen": 0}, {"regionId": "ironmans-bay", "type": "sea", "newUnitTypes": ["ship"], "currentUnitCount": 0, "supplySafeNewUnitsWhenChosenAlone": 3, "upgradeableFootmen": 0}]}], "availablePieces": {"footman": 9, "knight": 3, "ship": 6, "siege-engine": 1}, "supplyLimit": {"level": 4, "allowedArmySizes": [3, 3, 2, 2], "currentArmies": [{"regionId": "seagard", "unitCount": 2}], "singleUnitRegions": ["harrenhal", "lannisport"], "rule": "Only regions with two or more units use an army slot. Sort army sizes largest first and compare them with allowedArmySizes."}, "unitCosts": {"footman": 1, "ship": 1, "knight": 2, "siege-engine": 2, "footmanUpgradeToKnightOrSiege": 1}, "safePass": "Choose skip_mustering to recruit no units."}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d160"></a>

## D160 — baratheon — submit_bid (completed)

Run `18265d4a-ff81-40ac-9087-4a6bcab1ddec`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 2}`

Handoff: Goal: Secure Iron Throne (first turn order) to act before Lannister and Stark in final round and capture Lannister castles. Dependencies: Must outbid Lannister's max possible bid of 2 (they have 2 tokens). Immediate threat: Lannister holds 7 castle/stronghold areas, could win if we cannot disrupt. Reserve: Keep remaining 2 power tokens for upcoming Fiefdoms and King's Court bids. Assumption: Stark cannot bid (0 tokens) so they pose no competition. Bidding 2 ensures we retain Iron Throne token, giving turn-order advantage for our planned attacks.

Previous plan: Baratheon skips mustering to conserve power tokens and avoid supply issues. Proceed to assign orders for final round attacks on Lannister castles and secure remaining territories.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]], "currentTrack": {"index": 0, "id": "iron-throne", "name": "Iron Throne", "meaning": "Higher position acts earlier during the Action phase. The player in first place holds the Iron Throne token and decides unresolved non-combat ties, including tied influence bids. This track does not break combat ties."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d161"></a>

## D161 — lannister — submit_bid (completed)

Run `36f5d89b-a594-40e6-a841-bb4956ac3a24`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Bid 0 to preserve our two power tokens for the upcoming Fiefdoms track bid where influence may be more critical. With no ships or nearby forces, winning the Iron Throne order offers limited tactical benefit this final round, while conserving power maximizes our chance to influence later track positions.

Previous plan: Maintain current position into final round. Preserve power tokens for possible bids. No mustering to avoid exceeding supply and to keep units ready for final March attacks targeting opponent castles.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]], "currentTrack": {"index": 0, "id": "iron-throne", "name": "Iron Throne", "meaning": "Higher position acts earlier during the Action phase. The player in first place holds the Iron Throne token and decides unresolved non-combat ties, including tied influence bids. This track does not break combat ties."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 4, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d162"></a>

## D162 — baratheon — resolve_track_ties (completed)

Run `da0e655b-55f6-4d1a-a6e0-5c0cc4fdd318`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"preferred_house_ids": ["stark", "lannister"], "applied_house_ids": ["stark", "lannister"]}`

Handoff: Tie resolved: prioritize Stark over Lannister on Iron Throne track to keep Lannister lower on Fiefdoms, preserving Baratheon’s Valyrian Steel Blade advantage and turn order for final round attacks.

Previous plan: Goal: Secure Iron Throne (first turn order) to act before Lannister and Stark in final round and capture Lannister castles. Dependencies: Must outbid Lannister's max possible bid of 2 (they have 2 tokens). Immediate threat: Lannister holds 7 castle/stronghold areas, could win if we cannot disrupt. Reserve: Keep remaining 2 power tokens for upcoming Fiefdoms and King's Court bids. Assumption: Stark cannot bid (0 tokens) so they pose no competition. Bidding 2 ensures we retain Iron Throne token, giving turn-order advantage for our planned attacks.

Pending: `{"type": "resolve-ties", "bidResults": [[2, ["baratheon"]], [0, ["stark", "lannister"]]], "currentTrack": {"index": 0, "id": "iron-throne", "name": "Iron Throne", "meaning": "Higher position acts earlier during the Action phase. The player in first place holds the Iron Throne token and decides unresolved non-combat ties, including tied influence bids. This track does not break combat ties."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d163"></a>

## D163 — lannister — submit_bid (completed)

Run `32e45269-ca89-4bdc-b08b-0e7e6c2fbf0a`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Bid 0 on Fiefdoms to preserve our 2 power tokens for the upcoming King's Court bidding, where gaining a higher position yields more special orders for the final action phase. We cannot outbid Baratheon for first place (they have equal tokens and win ties), so saving tokens is optimal.

Previous plan: Bid 0 to preserve our two power tokens for the upcoming Fiefdoms track bid where influence may be more critical. With no ships or nearby forces, winning the Iron Throne order offers limited tactical benefit this final round, while conserving power maximizes our chance to influence later track positions.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]], "currentTrack": {"index": 1, "id": "fiefdoms", "name": "Fiefdoms", "meaning": "Higher position wins a tied combat total. The player in first place holds the Valyrian Steel Blade and may normally spend it once per round to add +1 to their combat strength after House cards are revealed."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d164"></a>

## D164 — baratheon — submit_bid (completed)

Run `3fa4083f-803f-409e-a981-c353e9e670e2`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 2}`

Handoff: Bid 2 power tokens on the Fiefdoms track to secure first place (hold Valyrian Steel Blade) and ensure tie-breaking advantage via Iron Throne token. This preserves combat strength advantage for final round and prevents Lannister from overtaking us. No tokens remain for King's Court bidding, but maintaining Fiefdoms lead is priority.

Previous plan: Tie resolved: prioritize Stark over Lannister on Iron Throne track to keep Lannister lower on Fiefdoms, preserving Baratheon’s Valyrian Steel Blade advantage and turn order for final round attacks.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]], "currentTrack": {"index": 1, "id": "fiefdoms", "name": "Fiefdoms", "meaning": "Higher position wins a tied combat total. The player in first place holds the Valyrian Steel Blade and may normally spend it once per round to add +1 to their combat strength after House cards are revealed."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d165"></a>

## D165 — baratheon — resolve_track_ties (completed)

Run `eeb2da60-0951-46c4-b8f7-4fdcfce3dd68`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"preferred_house_ids": ["stark", "lannister"], "applied_house_ids": ["stark", "lannister"]}`

Handoff: Rank Stark ahead of Lannister on the Fiefdoms track so Stark wins any tied combat against Lannister. Baratheon already holds first place, preserving our Valyrian Steel Blade advantage while limiting Lannister’s ability to capture additional castles in the final round.

Previous plan: Bid 2 power tokens on the Fiefdoms track to secure first place (hold Valyrian Steel Blade) and ensure tie-breaking advantage via Iron Throne token. This preserves combat strength advantage for final round and prevents Lannister from overtaking us. No tokens remain for King's Court bidding, but maintaining Fiefdoms lead is priority.

Pending: `{"type": "resolve-ties", "bidResults": [[2, ["baratheon"]], [0, ["stark", "lannister"]]], "currentTrack": {"index": 1, "id": "fiefdoms", "name": "Fiefdoms", "meaning": "Higher position wins a tied combat total. The player in first place holds the Valyrian Steel Blade and may normally spend it once per round to add +1 to their combat strength after House cards are revealed."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d166"></a>

## D166 — lannister — submit_bid (completed)

Run `5d0c5eb2-da7c-434a-9f78-0cb7f9db4fac`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Bid 0 to keep our 2 power tokens; we cannot feasibly improve our King's Court position enough to gain extra specials that would enable capturing another castle before end of round 10. Preserving tokens is optimal as there are no further bidding opportunities.

Previous plan: Bid 0 on Fiefdoms to preserve our 2 power tokens for the upcoming King's Court bidding, where gaining a higher position yields more special orders for the final action phase. We cannot outbid Baratheon for first place (they have equal tokens and win ties), so saving tokens is optimal.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["baratheon", -1], ["stark", -1]], "currentTrack": {"index": 2, "id": "kings-court", "name": "King's Court", "meaning": "Your position determines how many starred special Order tokens you may place each round; higher positions receive more. The player in first place holds the Messenger Raven and, after orders are revealed, may replace one of their orders or inspect the top Wildling card."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d167"></a>

## D167 — baratheon — resolve_track_ties (completed)

Run `cc0f59d6-7789-453b-866d-2c0aad2182ae`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"preferred_house_ids": ["baratheon", "stark", "lannister"], "applied_house_ids": ["baratheon", "stark", "lannister"]}`

Handoff: Maintain Baratheon on King's Court (first place) to keep 3 starred orders for this final round while keeping Stark ahead of Lannister to limit Lannister's special orders and ensure they cannot disrupt our final castle capture. This ranking supports our plan to attack Lannister castles and protect our own holdings.

Previous plan: Rank Stark ahead of Lannister on the Fiefdoms track so Stark wins any tied combat against Lannister. Baratheon already holds first place, preserving our Valyrian Steel Blade advantage while limiting Lannister’s ability to capture additional castles in the final round.

Pending: `{"type": "resolve-ties", "bidResults": [[0, ["baratheon", "stark", "lannister"]]], "currentTrack": {"index": 2, "id": "kings-court", "name": "King's Court", "meaning": "Your position determines how many starred special Order tokens you may place each round; higher positions receive more. The player in first place holds the Messenger Raven and, after orders are revealed, may replace one of their orders or inspect the top Wildling card."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d168"></a>

## D168 — lannister — submit_orders (completed)

Run `88a617be-0224-4e0e-bc55-d1f0e9c6131b`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "seagard", "preferred_order": "defense", "starred_preference": "prefer", "priority": 100}, {"region_id": "harrenhal", "preferred_order": "defense", "starred_preference": "avoid", "priority": 80}, {"region_id": "lannisport", "preferred_order": "defense", "starred_preference": "avoid", "priority": 70}], "applied_orders": [{"region_id": "seagard", "order_id": 6, "order": "defense"}, {"region_id": "harrenhal", "order_id": 4, "order": "defense"}, {"region_id": "lannisport", "order_id": 5, "order": "defense"}]}`

Handoff: Secure our castles for victory. Use a starred Defense on Seagard to repel Stark attack from Moat Cailin. Defend Harrenhal against possible Baratheon aggression from Crackclaw Point. Defend Lannisport to protect our siege engine and maintain control of that stronghold. No March moves this round as we cannot capture additional castles without ships. Preserve power tokens for final scoring.


Previous plan: Bid 0 to keep our 2 power tokens; we cannot feasibly improve our King's Court position enough to gain extra specials that would enable capturing another castle before end of round 10. Preserving tokens is optimal as there are no further bidding opportunities.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d169"></a>

## D169 — stark — submit_orders (completed)

Run `58b41ace-0872-45e5-bd05-ee707c5c7203`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "moat-cailin", "preferred_order": "defense", "starred_preference": "avoid", "priority": 100}, {"region_id": "the-narrow-sea", "preferred_order": "support", "starred_preference": "avoid", "priority": 80}], "applied_orders": [{"region_id": "moat-cailin", "order_id": 4, "order": "defense"}, {"region_id": "the-narrow-sea", "order_id": 7, "order": "support"}]}`

Handoff: Stark aims to protect Moat Cailin castle with a Defense order and provide potential support from the ship in The Narrow Sea. No attack opportunities exist this final round, so focus is on preserving existing castles and avoiding loss.

Previous plan: Stark skips mustering this final round. With only 3 castles controlled and no realistic path to reach 7 before round end, adding units offers minimal gain. Skipping conserves available pieces and avoids potential supply issues, focusing on the inevitable end-of-game scoring where Stark is behind.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d170"></a>

## D170 — baratheon — submit_orders (completed)

Run `0f0698f1-f3af-4d2f-8c53-87603f4e57d1`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "kings-landing", "preferred_order": "defense", "starred_preference": "prefer", "priority": 90}, {"region_id": "crackclaw-point", "preferred_order": "march", "starred_preference": "prefer", "priority": 80}, {"region_id": "searoad-marches", "preferred_order": "consolidate_power", "starred_preference": "avoid", "priority": 70}, {"region_id": "shipbreaker-bay", "preferred_order": "defense", "starred_preference": "avoid", "priority": 60}, {"region_id": "dragonstone", "preferred_order": "defense", "starred_preference": "avoid", "priority": 50}], "applied_orders": [{"region_id": "kings-landing", "order_id": 6, "order": "defense"}, {"region_id": "crackclaw-point", "order_id": 3, "order": "march"}, {"region_id": "searoad-marches", "order_id": 10, "order": "consolidate_power"}, {"region_id": "shipbreaker-bay", "order_id": 4, "order": "defense"}, {"region_id": "dragonstone", "order_id": 5, "order": "defense"}]}`

Handoff: Aim to capture Lannister castle Harrenhal by a starred march from Crackclaw Point, defend our strongholds at Kings Landing and Dragonstone with defense orders, generate power at Seared Marches, and hold our fleet at Shipbreaker Bay. Use only two starred orders to stay within King’s Court limit.

Previous plan: Maintain Baratheon on King's Court (first place) to keep 3 starred orders for this final round while keeping Stark ahead of Lannister to limit Lannister's special orders and ensure they cannot disrupt our final castle capture. This ranking supports our plan to attack Lannister castles and protect our own holdings.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d171"></a>

## D171 — baratheon — replace-order (failed)

Run `5a00b219-72f0-403c-b556-471d2f24d3ff`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 1, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Use the Messenger Raven to replace the Consolidate Power order at Searoad Marches with a regular March +0 order. This enables a second attack to capture Lannister's stronghold at Stoney Sept (defended only by a Defense+1 order), adding a stronghold to our victory count while sacrificing a modest power token gain that is not needed for the final round.

Previous plan: Aim to capture Lannister castle Harrenhal by a starred march from Crackclaw Point, defend our strongholds at Kings Landing and Dragonstone with defense orders, generate power at Seared Marches, and hold our fleet at Shipbreaker Bay. Use only two starred orders to stay within King’s Court limit.

Pending: `{"type": "replace-order"}`

Guidance: `{"decision": "raven-order-replacement", "legalReplacements": [{"regionId": "crackclaw-point", "originalOrderId": 3, "availableOrderIds": [1, 2, 3, 7, 8, 9, 11, 12, 13, 14, 15]}, {"regionId": "dragonstone", "originalOrderId": 5, "availableOrderIds": [1, 2, 5, 7, 8, 9, 11, 12, 13, 14, 15]}, {"regionId": "kings-landing", "originalOrderId": 6, "availableOrderIds": [1, 2, 6, 7, 8, 9, 11, 12, 13, 14, 15]}, {"regionId": "searoad-marches", "originalOrderId": 10, "availableOrderIds": [1, 2, 7, 8, 9, 10, 11, 12, 13, 14, 15]}, {"regionId": "shipbreaker-bay", "originalOrderId": 4, "availableOrderIds": [1, 2, 4, 7, 8, 9, 11, 12, 13, 14, 15]}], "safeChoices": ["Choose skip_raven_order_replacement to keep every order.", "Choose inspect_top_wildling_card to use the Raven on the Wildling deck."]}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d172"></a>

## D172 — baratheon — skip_raven_order_replacement (completed)

Run `d929a0b7-e9da-4d36-8a6f-6fdc6c34a9ea`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Maintain current orders to keep March+1 at Crackclaw and defend strongholds; no order replacement needed.

Previous plan: Aim to capture Lannister castle Harrenhal by a starred march from Crackclaw Point, defend our strongholds at Kings Landing and Dragonstone with defense orders, generate power at Seared Marches, and hold our fleet at Shipbreaker Bay. Use only two starred orders to stay within King’s Court limit.

Pending: `{"type": "replace-order"}`

Guidance: `{"decision": "raven-order-replacement", "legalReplacements": [{"regionId": "crackclaw-point", "originalOrderId": 3, "availableOrderIds": [1, 2, 3, 7, 8, 9, 11, 12, 13, 14, 15]}, {"regionId": "dragonstone", "originalOrderId": 5, "availableOrderIds": [1, 2, 5, 7, 8, 9, 11, 12, 13, 14, 15]}, {"regionId": "kings-landing", "originalOrderId": 6, "availableOrderIds": [1, 2, 6, 7, 8, 9, 11, 12, 13, 14, 15]}, {"regionId": "searoad-marches", "originalOrderId": 10, "availableOrderIds": [1, 2, 7, 8, 9, 10, 11, 12, 13, 14, 15]}, {"regionId": "shipbreaker-bay", "originalOrderId": 4, "availableOrderIds": [1, 2, 4, 7, 8, 9, 11, 12, 13, 14, 15]}], "safeChoices": ["Choose skip_raven_order_replacement to keep every order.", "Choose inspect_top_wildling_card to use the Raven on the Wildling deck."]}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

<a id="d173"></a>

## D173 — baratheon — resolve_march (completed)

Run `504e787b-4cd1-4623-a8c9-4b703fd01ab2`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "crackclaw-point", "moves": [], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Discard the March+1 order at Crackclaw Point, leaving the footman in place and preserving our control of the castle. No movement avoids losing a control token (we have no power) and prevents risking combat at Harrenhal. Maintaining our current castle count is crucial as we approach round 10's end.

Previous plan: Maintain current orders to keep March+1 at Crackclaw and defend strongholds; no order replacement needed.

Pending: `{"type": "resolve-single-march", "houseId": "baratheon", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "crackclaw-point", "orderId": 3, "order": "March +1", "unitIds": [19], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "blackwater", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}, {"regionId": "dragonstone", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}, {"regionId": "harrenhal", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "lannister", "triggersCombat": true, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}, {"regionId": "kings-landing", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}, {"regionId": "kingswood", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}, {"regionId": "the-mountains-of-the-moon", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 0, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "moat-cailin", "port-of-white-harbor", "the-narrow-sea"]}]`

