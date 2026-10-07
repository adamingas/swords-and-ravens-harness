# Round 9: recorded decisions and state evidence

<a id="d125"></a>

## D125 — baratheon — submit_bid (completed)

Run `826dd63a-5323-431e-8a08-e919ffc64ac3`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Bid 0 power tokens to avoid being lowest bidder (Stark is lowest with 0, and as Iron Throne holder we can assign severe penalty to Stark). Preserves our 8 power tokens for final round bidding and future actions.

Previous plan: Moved footman from The Reach to Seared Marches to position forces for a future attack on Lannisport stronghold while preserving our castle in The Reach via existing control token.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 6, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["castle-black", "winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d126"></a>

## D126 — lannister — submit_bid (completed)

Run `cb59a98e-b391-4c30-a528-9a01a81717e3`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Wildlings attack strength 12 exceeds total possible Night's Watch power (Baratheon 8 + Lannister 2 =10). Outcome unavoidable: wildlings win. Bidding any tokens is wasteful as they are discarded regardless. Stark already has zero tokens and will be lowest bidder, taking severe penalty; Lannister bidding >0 wouldn't change that. Preserve our 2 power tokens for any future needs. Bid 0.

Previous plan: Play The Hound (strength 2) to ensure victory in the Harrenhal combat, capturing the castle. This secures an additional castle area, advancing us toward the 7‑castle win condition while preserving our supply and power.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 6, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["castle-black", "winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d127"></a>

## D127 — baratheon — choose_option (completed)

Run `6bea3593-5d2c-48e4-846c-b3cb488875e2`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"choice_index": 1}`

Handoff: Choose Lannister as the house to receive the severe wildling penalty. This weakens Lannister's position while preserving our power tokens and focusing on our own castle expansion toward the 7‑castle win condition.

Previous plan: Bid 0 power tokens to avoid being lowest bidder (Stark is lowest with 0, and as Iron Throne holder we can assign severe penalty to Stark). Preserves our 8 power tokens for final round bidding and future actions.

Pending: `{"type": "simple-choice", "houseId": "baratheon", "description": "The holder of the Iron Throne must choose between the lowest bidders", "choices": ["Stark", "Lannister", "Baratheon"]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 6, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["castle-black", "winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d128"></a>

## D128 — lannister — select_units (completed)

Run `1a4c3d6c-ffbe-4701-8fb7-256a5fcb4b0d`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"unit_ids": [6, 7, 26]}`

Handoff: Chosen losses: Lannister knight at Lannisport (ID 6) and ship at The Golden Sound (ID 7) to keep naval presence minimal, and siege‑engine at Harrenhal (ID 26) sacrificing that contested castle. Lannisport remains held by the remaining siege‑engine, preserving our home stronghold. Remaining castles (Riverrun, Seagard, Moat Cailin) are protected. Expect to rebuild naval capacity later with available power tokens and focus on expanding toward additional castles.

Previous plan: Wildlings attack strength 12 exceeds total possible Night's Watch power (Baratheon 8 + Lannister 2 =10). Outcome unavoidable: wildlings win. Bidding any tokens is wasteful as they are discarded regardless. Stark already has zero tokens and will be lowest bidder, taking severe penalty; Lannister bidding >0 wouldn't change that. Preserve our 2 power tokens for any future needs. Bid 0.

Pending: `{"type": "select-units", "house": "lannister", "possibleUnits": [26, 8, 6, 24, 7, 27, 25], "count": 3, "canBeSkipped": false, "selectedUnitsMustBeOfSameRegion": false}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 6, "controlledCastleAreas": 5, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "the-golden-sound", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["castle-black", "winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d129"></a>

## D129 — baratheon — select_units (completed)

Run `9fd9dd2d-108c-44ca-8a03-75bb9d4f2ae9`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"unit_ids": [10, 14]}`

Handoff: Removed two Kingswood knights to preserve castle holdings (Kings Landing, Crackclaw Point, Dragonstone) and maintain transport ships. This reduces army count safely, keeps control of our castle areas via remaining units and power tokens, and retains critical ship forces for future moves.

Previous plan: Choose Lannister as the house to receive the severe wildling penalty. This weakens Lannister's position while preserving our power tokens and focusing on our own castle expansion toward the 7‑castle win condition.

Pending: `{"type": "select-units", "house": "baratheon", "possibleUnits": [23, 10, 14, 19, 16, 11, 12, 18, 20, 21], "count": 2, "canBeSkipped": false, "selectedUnitsMustBeOfSameRegion": false}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["castle-black", "winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d130"></a>

## D130 — stark — select_units (completed)

Run `c956a8dd-8870-4d98-9d12-42298167cebb`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"unit_ids": [2, 28]}`

Handoff: Removed the unnecessary knight at Castle Black and one footman from Winterfell to preserve our defensive strength at our home castle while retaining enough troops to meet supply limits and keeping the ship for future transport and attacks.

Previous plan: Move the lone footman from White Harbor back to Winterfell, bolstering our home army without risking combat or needing a control token. This keeps us within supply limits and preserves our castle count while positioning the unit for future operations.

Pending: `{"type": "select-units", "house": "stark", "possibleUnits": [2, 28, 29, 30, 4], "count": 2, "canBeSkipped": false, "selectedUnitsMustBeOfSameRegion": false}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 3, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["castle-black", "winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d131"></a>

## D131 — baratheon — submit_bid (completed)

Run `bbdcc29d-5ec2-401d-a2f5-e8f58b8a1617`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Bid zero to conserve power tokens while retaining Iron Throne position via tie-breaking as current holder. This keeps turn order advantage for round 9 and preserves resources for upcoming bids and wildling defense.

Previous plan: Removed two Kingswood knights to preserve castle holdings (Kings Landing, Crackclaw Point, Dragonstone) and maintain transport ships. This reduces army count safely, keeps control of our castle areas via remaining units and power tokens, and retains critical ship forces for future moves.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]], "currentTrack": {"index": 0, "id": "iron-throne", "name": "Iron Throne", "meaning": "Higher position acts earlier during the Action phase. The player in first place holds the Iron Throne token and decides unresolved non-combat ties, including tied influence bids. This track does not break combat ties."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d132"></a>

## D132 — lannister — submit_bid (completed)

Run `9d1723fe-7629-4295-95fb-308683413093`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Bid 0 to preserve our two power tokens for future needs. Baratheon likely outbids us; we remain second on Iron Throne, maintaining turn order without wasting tokens.

Previous plan: Chosen losses: Lannister knight at Lannisport (ID 6) and ship at The Golden Sound (ID 7) to keep naval presence minimal, and siege‑engine at Harrenhal (ID 26) sacrificing that contested castle. Lannisport remains held by the remaining siege‑engine, preserving our home stronghold. Remaining castles (Riverrun, Seagard, Moat Cailin) are protected. Expect to rebuild naval capacity later with available power tokens and focus on expanding toward additional castles.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]], "currentTrack": {"index": 0, "id": "iron-throne", "name": "Iron Throne", "meaning": "Higher position acts earlier during the Action phase. The player in first place holds the Iron Throne token and decides unresolved non-combat ties, including tied influence bids. This track does not break combat ties."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d133"></a>

## D133 — baratheon — resolve_track_ties (completed)

Run `d1ff6205-633d-4f5e-976e-08e65b14521e`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"preferred_house_ids": ["baratheon", "stark", "lannister"], "applied_house_ids": ["baratheon", "stark", "lannister"]}`

Handoff: Maintain Baratheon as Iron Throne holder and keep turn order advantage. Rank Stark ahead of Lannister to give the weaker house earlier action, leaving Lannister to act last, limiting their ability to disrupt our castle consolidation and upcoming offensives.

Previous plan: Bid zero to conserve power tokens while retaining Iron Throne position via tie-breaking as current holder. This keeps turn order advantage for round 9 and preserves resources for upcoming bids and wildling defense.

Pending: `{"type": "resolve-ties", "bidResults": [[0, ["stark", "baratheon", "lannister"]]], "currentTrack": {"index": 0, "id": "iron-throne", "name": "Iron Throne", "meaning": "Higher position acts earlier during the Action phase. The player in first place holds the Iron Throne token and decides unresolved non-combat ties, including tied influence bids. This track does not break combat ties."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "lannister", "stark"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d134"></a>

## D134 — lannister — submit_bid (completed)

Run `7168c93c-d77c-4099-bb5d-3729f492d1d0`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Bid 0 to conserve our 2 power tokens for future needs. Baratheon likely outbids us on the Fiefdoms track, so we maintain our current position without spending tokens.

Previous plan: Bid 0 to preserve our two power tokens for future needs. Baratheon likely outbids us; we remain second on Iron Throne, maintaining turn order without wasting tokens.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]], "currentTrack": {"index": 1, "id": "fiefdoms", "name": "Fiefdoms", "meaning": "Higher position wins a tied combat total. The player in first place holds the Valyrian Steel Blade and may normally spend it once per round to add +1 to their combat strength after House cards are revealed."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d135"></a>

## D135 — baratheon — submit_bid (completed)

Run `a560de67-74bc-4c57-be26-d8d13dcfcb50`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 3}`

Handoff: Bid 3 to secure first place on the Fiefdoms track, retaining the Valyrian Steel Blade token for crucial combat in the final round while preserving most of our power tokens for upcoming bids and wildling defense.

Previous plan: Maintain Baratheon as Iron Throne holder and keep turn order advantage. Rank Stark ahead of Lannister to give the weaker house earlier action, leaving Lannister to act last, limiting their ability to disrupt our castle consolidation and upcoming offensives.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]], "currentTrack": {"index": 1, "id": "fiefdoms", "name": "Fiefdoms", "meaning": "Higher position wins a tied combat total. The player in first place holds the Valyrian Steel Blade and may normally spend it once per round to add +1 to their combat strength after House cards are revealed."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 8, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d136"></a>

## D136 — baratheon — resolve_track_ties (completed)

Run `783e57de-27f6-4af4-8956-f9afbfed0e57`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"preferred_house_ids": ["stark", "lannister"], "applied_house_ids": ["stark", "lannister"]}`

Handoff: Rank Stark ahead of Lannister to keep Lannister lower on the Fiefdoms track, preserving our Valyrian Steel Blade advantage and limiting Lannister combat tie‑breaks. This supports our goal of consolidating castles and preparing for the final round.

Previous plan: Bid 3 to secure first place on the Fiefdoms track, retaining the Valyrian Steel Blade token for crucial combat in the final round while preserving most of our power tokens for upcoming bids and wildling defense.

Pending: `{"type": "resolve-ties", "bidResults": [[3, ["baratheon"]], [0, ["stark", "lannister"]]], "currentTrack": {"index": 1, "id": "fiefdoms", "name": "Fiefdoms", "meaning": "Higher position wins a tied combat total. The player in first place holds the Valyrian Steel Blade and may normally spend it once per round to add +1 to their combat strength after House cards are revealed."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "lannister", "stark"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 5, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d137"></a>

## D137 — lannister — submit_bid (completed)

Run `c6b5445d-ad8e-44c7-b543-7dc145cd8ca8`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 0}`

Handoff: Bid 0 to conserve our 2 power tokens for future needs. Accept possible loss of a starred order on King's Court, retaining at least one special order while preserving resources for upcoming bids and wildling defense.

Previous plan: Bid 0 to conserve our 2 power tokens for future needs. Baratheon likely outbids us on the Fiefdoms track, so we maintain our current position without spending tokens.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]], "currentTrack": {"index": 2, "id": "kings-court", "name": "King's Court", "meaning": "Your position determines how many starred special Order tokens you may place each round; higher positions receive more. The player in first place holds the Messenger Raven and, after orders are revealed, may replace one of their orders or inspect the top Wildling card."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 5, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d138"></a>

## D138 — baratheon — submit_bid (completed)

Run `e5c70d0c-3229-4408-ac10-02a80ac931fe`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"amount": 2}`

Handoff: Bid 2 power tokens to retain first place on King's Court track (using Iron Throne tie-breaking). This conserves tokens for potential wildling defense and final-round bids while preserving our special order advantage.

Previous plan: Rank Stark ahead of Lannister to keep Lannister lower on the Fiefdoms track, preserving our Valyrian Steel Blade advantage and limiting Lannister combat tie‑breaks. This supports our goal of consolidating castles and preparing for the final round.

Pending: `{"type": "bidding", "participatingHouses": ["baratheon", "lannister", "stark"], "bids": [["stark", -1]], "currentTrack": {"index": 2, "id": "kings-court", "name": "King's Court", "meaning": "Your position determines how many starred special Order tokens you may place each round; higher positions receive more. The player in first place holds the Messenger Raven and, after orders are revealed, may replace one of their orders or inspect the top Wildling card."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 5, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d139"></a>

## D139 — baratheon — resolve_track_ties (completed)

Run `7e929dad-64c6-4c5a-9ce9-bc6177a1ba92`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"preferred_house_ids": ["stark", "lannister"], "applied_house_ids": ["stark", "lannister"]}`

Handoff: Maintain Baratheon on Iron Throne and Valyrian Blade positions; rank Stark ahead of Lannister on King's Court tie to give weaker house earlier turn order, limiting Lannister's ability to disrupt our castle consolidation and preserving our special order advantage.

Previous plan: Bid 2 power tokens to retain first place on King's Court track (using Iron Throne tie-breaking). This conserves tokens for potential wildling defense and final-round bids while preserving our special order advantage.

Pending: `{"type": "resolve-ties", "bidResults": [[2, ["baratheon"]], [0, ["stark", "lannister"]]], "currentTrack": {"index": 2, "id": "kings-court", "name": "King's Court", "meaning": "Your position determines how many starred special Order tokens you may place each round; higher positions receive more. The player in first place holds the Messenger Raven and, after orders are revealed, may replace one of their orders or inspect the top Wildling card."}, "bidFieldMeaning": "A bid value of -1 for another house means that house has submitted a secret bid whose amount is hidden from you. It does not mean zero, pass, or withdrawal."}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "lannister", "stark"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d140"></a>

## D140 — lannister — submit_orders (completed)

Run `8f82f6bc-acc0-4435-b973-8ce1020938ee`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "riverrun", "preferred_order": "march", "starred_preference": "prefer", "priority": 100}, {"region_id": "moat-cailin", "preferred_order": "march", "starred_preference": "avoid", "priority": 90}, {"region_id": "lannisport", "preferred_order": "defense", "starred_preference": "avoid", "priority": 80}, {"region_id": "seagard", "preferred_order": "defense", "starred_preference": "avoid", "priority": 70}], "applied_orders": [{"region_id": "riverrun", "order_id": 3, "order": "march"}, {"region_id": "moat-cailin", "order_id": 2, "order": "march"}, {"region_id": "lannisport", "order_id": 4, "order": "defense"}, {"region_id": "seagard", "order_id": 5, "order": "defense"}]}`

Handoff: Aim to capture Harrenhal via a starred March from Riverrun (increase combat strength), capture White Harbor via a March from Moat Cailin (displace Stark power token without combat), and defend Lannisport and Seagard to protect our castles. No support orders are used due to current restriction. Preserve power tokens for future bids.

Previous plan: Bid 0 to conserve our 2 power tokens for future needs. Accept possible loss of a starred order on King's Court, retaining at least one special order while preserving resources for upcoming bids and wildling defense.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d141"></a>

## D141 — stark — submit_orders (completed)

Run `a0857eb0-9ab7-44a7-9a7c-3203a2855a6d`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "winterfell", "preferred_order": "march", "starred_preference": "avoid", "priority": 100}, {"region_id": "the-shivering-sea", "preferred_order": "march", "starred_preference": "avoid", "priority": 90}], "applied_orders": [{"region_id": "winterfell", "order_id": 2, "order": "march"}, {"region_id": "the-shivering-sea", "order_id": 1, "order": "march"}]}`

Handoff: Goal: Capture the empty Castle Black from Winterfell using a March order, adding a new castle to our control. Move our lone ship from The Shivering Sea toward The Narrow Sea via a March order to improve future transport options. No support orders allowed this round.

Previous plan: Removed the unnecessary knight at Castle Black and one footman from Winterfell to preserve our defensive strength at our home castle while retaining enough troops to meet supply limits and keeping the ship for future transport and attacks.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d142"></a>

## D142 — baratheon — submit_orders (completed)

Run `6ca34d1e-7a35-4348-b46f-13a33e80bc9b`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"assignments": [{"region_id": "kings-landing", "preferred_order": "defense", "starred_preference": "prefer", "priority": 100}, {"region_id": "crackclaw-point", "preferred_order": "march", "starred_preference": "prefer", "priority": 90}, {"region_id": "searoad-marches", "preferred_order": "consolidate_power", "starred_preference": "avoid", "priority": 70}, {"region_id": "shipbreaker-bay", "preferred_order": "raid", "starred_preference": "avoid", "priority": 60}, {"region_id": "dragonstone", "preferred_order": "defense", "starred_preference": "avoid", "priority": 80}], "applied_orders": [{"region_id": "kings-landing", "order_id": 6, "order": "defense"}, {"region_id": "crackclaw-point", "order_id": 3, "order": "march"}, {"region_id": "searoad-marches", "order_id": 10, "order": "consolidate_power"}, {"region_id": "shipbreaker-bay", "order_id": 13, "order": "raid"}, {"region_id": "dragonstone", "order_id": 4, "order": "defense"}]}`

Handoff: Goal: Capture Harrenhal by marching from Crackclaw Point, protect the stronghold Kings Landing with a starred defense, hold Dragonstone with defense, generate power tokens via Consolidate Power at Seared Marches, and use a raid from Shipbreaker Bay to disrupt opponent orders while staying within three starred orders limit.

Previous plan: Maintain Baratheon on Iron Throne and Valyrian Blade positions; rank Stark ahead of Lannister on King's Court tie to give weaker house earlier turn order, limiting Lannister's ability to disrupt our castle consolidation and preserving our special order advantage.

Pending: `{"type": "place-orders", "readyHouses": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d143"></a>

## D143 — baratheon — replace-order (failed)

Run `e6c6ef2f-9747-4f97-85e2-3c902c8e048f`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 1, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Replace Consolidate Power at Seared Marches with a March +0 order to move our footman from Seared Marches into adjacent Crackclaw Point, strengthening our force for a potential attack on Harrenhal. This sacrifices a power token gain but improves our offensive position toward the 7‑castle win condition.

Previous plan: Goal: Capture Harrenhal by marching from Crackclaw Point, protect the stronghold Kings Landing with a starred defense, hold Dragonstone with defense, generate power tokens via Consolidate Power at Seared Marches, and use a raid from Shipbreaker Bay to disrupt opponent orders while staying within three starred orders limit.

Pending: `{"type": "replace-order"}`

Guidance: `{"decision": "raven-order-replacement", "legalReplacements": [{"regionId": "crackclaw-point", "originalOrderId": 3, "availableOrderIds": [1, 2, 3, 5, 7, 8, 9, 11, 12, 14, 15]}, {"regionId": "dragonstone", "originalOrderId": 4, "availableOrderIds": [1, 2, 4, 5, 7, 8, 9, 11, 12, 14, 15]}, {"regionId": "kings-landing", "originalOrderId": 6, "availableOrderIds": [1, 2, 5, 6, 7, 8, 9, 11, 12, 14, 15]}, {"regionId": "searoad-marches", "originalOrderId": 10, "availableOrderIds": [1, 2, 5, 7, 8, 9, 10, 11, 12, 14, 15]}, {"regionId": "shipbreaker-bay", "originalOrderId": 13, "availableOrderIds": [1, 2, 5, 7, 8, 9, 11, 12, 13, 14, 15]}], "safeChoices": ["Choose skip_raven_order_replacement to keep every order.", "Choose inspect_top_wildling_card to use the Raven on the Wildling deck."]}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d144"></a>

## D144 — baratheon — skip_raven_order_replacement (completed)

Run `7c6631c2-9b73-418e-a143-39a1900fe30d`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{}`

Handoff: Keep current orders unchanged: defense at Kings Landing (starred), march+1 at Crackclaw Point for future Harrenhal attack, raid at Shipbreaker Bay to disrupt opponents, consolidate power at Searoad Marches to gain power, defense at Dragonstone. No order replacement needed, preserving our limited starred orders.

Previous plan: Goal: Capture Harrenhal by marching from Crackclaw Point, protect the stronghold Kings Landing with a starred defense, hold Dragonstone with defense, generate power tokens via Consolidate Power at Seared Marches, and use a raid from Shipbreaker Bay to disrupt opponent orders while staying within three starred orders limit.

Pending: `{"type": "replace-order"}`

Guidance: `{"decision": "raven-order-replacement", "legalReplacements": [{"regionId": "crackclaw-point", "originalOrderId": 3, "availableOrderIds": [1, 2, 3, 5, 7, 8, 9, 11, 12, 14, 15]}, {"regionId": "dragonstone", "originalOrderId": 4, "availableOrderIds": [1, 2, 4, 5, 7, 8, 9, 11, 12, 14, 15]}, {"regionId": "kings-landing", "originalOrderId": 6, "availableOrderIds": [1, 2, 5, 6, 7, 8, 9, 11, 12, 14, 15]}, {"regionId": "searoad-marches", "originalOrderId": 10, "availableOrderIds": [1, 2, 5, 7, 8, 9, 10, 11, 12, 14, 15]}, {"regionId": "shipbreaker-bay", "originalOrderId": 13, "availableOrderIds": [1, 2, 5, 7, 8, 9, 11, 12, 13, 14, 15]}], "safeChoices": ["Choose skip_raven_order_replacement to keep every order.", "Choose inspect_top_wildling_card to use the Raven on the Wildling deck."]}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d145"></a>

## D145 — baratheon — resolve_march (completed)

Run `a2b9b008-4d18-4e74-862a-4e26f945efa4`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "crackclaw-point", "moves": [{"destination_region_id": "harrenhal", "unit_ids": [19]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Capture Harrenhal castle via footman from Crackclaw Point, adding a castle area without combat, preserving supply and advancing toward 7-castle victory.

Previous plan: Keep current orders unchanged: defense at Kings Landing (starred), march+1 at Crackclaw Point for future Harrenhal attack, raid at Shipbreaker Bay to disrupt opponents, consolidate power at Searoad Marches to gain power, defense at Dragonstone. No order replacement needed, preserving our limited starred orders.

Pending: `{"type": "resolve-single-march", "houseId": "baratheon", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "crackclaw-point", "orderId": 3, "order": "March +1", "unitIds": [19], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "blackwater", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}, {"regionId": "dragonstone", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}, {"regionId": "harrenhal", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}, {"regionId": "kings-landing", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}, {"regionId": "kingswood", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "baratheon", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}, {"regionId": "the-mountains-of-the-moon", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[19]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d146"></a>

## D146 — stark — resolve_march (completed)

Run `c3d6d0d1-72f7-452b-b13e-4cefb5dde647`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "winterfell", "moves": [{"destination_region_id": "moat-cailin", "unit_ids": [29, 30]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Capture Moat Cailin stronghold by moving both footmen from Winterfell, winning combat on tie (Fiefdoms track) and killing Lannister knight using Greatjon Umber card. Gain a stronghold, increase castle count to 3, maintain supply. Ship move deferred to later turn.

Previous plan: Goal: Capture the empty Castle Black from Winterfell using a March order, adding a new castle to our control. Move our lone ship from The Shivering Sea toward The Narrow Sea via a March order to improve future transport options. No support orders allowed this round.

Pending: `{"type": "resolve-single-march", "houseId": "stark", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "the-shivering-sea", "orderId": 1, "order": "March -1", "unitIds": [4], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "the-narrow-sea", "type": "sea", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[4]]}], "canLeavePowerToken": false}, {"regionId": "winterfell", "orderId": 2, "order": "March +0", "unitIds": [29, 30], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "castle-black", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[29], [30], [29, 30]]}, {"regionId": "karhold", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[29], [30], [29, 30]]}, {"regionId": "moat-cailin", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "lannister", "triggersCombat": true, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[29], [30], [29, 30]]}, {"regionId": "the-stony-shore", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[29], [30], [29, 30]]}, {"regionId": "white-harbor", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "stark", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[29], [30], [29, 30]]}, {"regionId": "widows-watch", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[29], [30], [29, 30]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 8, "controlledCastleAreas": 5, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d147"></a>

## D147 — lannister — choose_combat_house_card (completed)

Run `4b72d88f-a101-4227-bf60-892a0133a6c2`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"house_card_id": "tyrion-lannister", "force_valyrian_blade_decision": false}`

Handoff: We are defending Moat Cailin with a knight against Stark footmen. No support present, so defender would lose tie. Playing Tyrion provides +1 combat strength, raising defender to 3 vs attacker 2, securing the area. Kevan's ability only helps when attacking with footmen, so we preserve Kevan for future offensives. No Valyrian Blade available.

Previous plan: Aim to capture Harrenhal via a starred March from Riverrun (increase combat strength), capture White Harbor via a March from Moat Cailin (displace Stark power token without combat), and defend Lannisport and Seagard to protect our castles. No support orders are used due to current restriction. Preserve power tokens for future bids.

Pending: `{"type": "choose-house-card", "choosableHouseCards": [["stark", ["ser-rodrick-cassel", "the-blackfish", "roose-bolton", "greatjon-umber", "robb-stark"]], ["lannister", ["ser-kevan-lannister", "tyrion-lannister"]]], "houseCards": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 8, "controlledCastleAreas": 5, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d148"></a>

## D148 — stark — choose_combat_house_card (completed)

Run `1c129d0b-9845-45de-b8d8-15c7d073cfd4`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"house_card_id": "greatjon-umber", "force_valyrian_blade_decision": false}`

Handoff: We win the combat at Moat Cailin on tie (Fiefdoms) and use Greatjon Umber to add strength and a sword icon, killing Lannister knight. This secures the stronghold, increasing our castle count to 3 and moving us closer to victory threshold. With supply unchanged (2 footmen used), we maintain army limits. Next we will consider reinforcing Moat Cailin or advancing toward nearby targets, and preserve remaining strong cards for future combats.

Previous plan: Capture Moat Cailin stronghold by moving both footmen from Winterfell, winning combat on tie (Fiefdoms track) and killing Lannister knight using Greatjon Umber card. Gain a stronghold, increase castle count to 3, maintain supply. Ship move deferred to later turn.

Pending: `{"type": "choose-house-card", "choosableHouseCards": [["stark", ["ser-rodrick-cassel", "the-blackfish", "roose-bolton", "greatjon-umber", "robb-stark"]], ["lannister", ["ser-kevan-lannister", "tyrion-lannister"]]], "houseCards": []}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 8, "controlledCastleAreas": 5, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d149"></a>

## D149 — lannister — choose_option (completed)

Run `32e20937-368f-41b6-b92c-43e86bfc6ee6`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"choice_index": 0}`

Handoff: Activate Tyrion Lannister ability (+1 combat strength) to turn defender advantage at Moat Cailin, securing the area against Stark footmen.

Previous plan: We are defending Moat Cailin with a knight against Stark footmen. No support present, so defender would lose tie. Playing Tyrion provides +1 combat strength, raising defender to 3 vs attacker 2, securing the area. Kevan's ability only helps when attacking with footmen, so we preserve Kevan for future offensives. No Valyrian Blade available.

Pending: `{"type": "simple-choice", "houseId": "lannister", "description": "", "choices": ["Activate", "Ignore"]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 8, "controlledCastleAreas": 5, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d150"></a>

## D150 — stark — select_house_card (completed)

Run `06b3c375-2ae3-48d4-b05a-6b89570f7c90`. Requests: 8; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"house_card_id": "ser-rodrick-cassel"}`

Handoff: Discard the low‑strength Rodrick Cassel (strength 1, 2 towers) to draw a new card. Keep the higher‑strength Robb Stark and Roose Bolton for upcoming combats, and retain The Blackfish for its defensive ability.

Previous plan: We win the combat at Moat Cailin on tie (Fiefdoms) and use Greatjon Umber to add strength and a sword icon, killing Lannister knight. This secures the stronghold, increasing our castle count to 3 and moving us closer to victory threshold. With supply unchanged (2 footmen used), we maintain army limits. Next we will consider reinforcing Moat Cailin or advancing toward nearby targets, and preserve remaining strong cards for future combats.

Pending: `{"type": "select-house-card", "house": "stark", "houseCards": ["ser-rodrick-cassel", "the-blackfish", "roose-bolton", "robb-stark"]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 8, "controlledCastleAreas": 5, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d151"></a>

## D151 — lannister — select_region (completed)

Run `c47570be-3f09-443d-87ec-a718c21dff6b`. Requests: 1; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"region_id": "seagard"}`

Handoff: Retreat the surviving knight from Moat Cailin to Seagard, keeping a defender on our castle and maintaining control of a stronghold. This preserves our castle count and positions the unit for future defense or support.

Previous plan: Activate Tyrion Lannister ability (+1 combat strength) to turn defender advantage at Moat Cailin, securing the area against Stark footmen.

Pending: `{"type": "select-region", "house": "lannister", "regions": ["seagard", "the-twins", "greywater-watch"]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 8, "controlledCastleAreas": 5, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard", "moat-cailin"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 2, "controlledLandAreas": 2, "controlledCastleAreas": 2, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "port-of-white-harbor"]}]`

<a id="d152"></a>

## D152 — lannister — resolve_march (completed)

Run `cb9e0e24-16a0-45e5-8dd1-be05b2bc81cf`. Requests: 4; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "riverrun", "moves": [{"destination_region_id": "harrenhal", "unit_ids": [8]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Capture Harrenhal castle by moving the footman from Riverrun, increasing our castle count and weakening Baratheon. No control token needed as Riverrun stays under our control via existing control token/home symbol. This move stays within supply limits and improves position toward victory.

Previous plan: Retreat the surviving knight from Moat Cailin to Seagard, keeping a defender on our castle and maintaining control of a stronghold. This preserves our castle count and positions the unit for future defense or support.

Pending: `{"type": "resolve-single-march", "houseId": "lannister", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "riverrun", "orderId": 3, "order": "March +1", "unitIds": [8], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "harrenhal", "type": "land", "castleLevel": 1, "castleAreasGainedIfCaptured": 1, "garrison": 0, "controller": "baratheon", "triggersCombat": true, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "lannisport", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 2, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "seagard", "type": "land", "castleLevel": 2, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}, {"regionId": "stoney-sept", "type": "land", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": "lannister", "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[8]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 8, "controlledCastleAreas": 5, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d153"></a>

## D153 — baratheon — choose_combat_house_card (completed)

Run `8456e438-1103-460c-80d2-64b616985dc9`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"house_card_id": "brienne-of-tarth", "force_valyrian_blade_decision": true}`

Handoff: Play Brienne of Tarth (strength 2, Sword 1) as defender and use Valyrian Steel Blade (+1) to ensure victory at Harrenhal, eliminating Lannister footman and solidifying our castle count toward the 7‑castle win condition.

Previous plan: Capture Harrenhal castle via footman from Crackclaw Point, adding a castle area without combat, preserving supply and advancing toward 7-castle victory.

Pending: `{"type": "choose-house-card", "choosableHouseCards": [["lannister", ["ser-kevan-lannister"]], ["baratheon", ["salladhor-saan", "ser-davos-seaworth", "brienne-of-tarth"]]], "houseCards": [["lannister", null]]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 8, "controlledCastleAreas": 5, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d154"></a>

## D154 — baratheon — use_valyrian_steel_blade (completed)

Run `5ebf3d60-b1d5-4e52-95ba-eee63b47101b`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"use": false}`

Handoff: Baratheon wins the Harrenhal combat without needing the Valyrian Steel Blade (combat totals tie at 3, and Baratheon holds the Fiefdoms lead). Preserving the Blade for a later battle this round improves our chance to secure additional castles and reach the 7‑castle win condition.

Previous plan: Play Brienne of Tarth (strength 2, Sword 1) as defender and use Valyrian Steel Blade (+1) to ensure victory at Harrenhal, eliminating Lannister footman and solidifying our castle count toward the 7‑castle win condition.

Pending: `{"type": "use-valyrian-steel-blade", "houseId": "baratheon", "forNewTidesOfBattleCard": false}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 8, "controlledCastleAreas": 5, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d155"></a>

## D155 — baratheon — select_region (completed)

Run `44e0f653-e9a2-49a8-af48-8e3132659e5a`. Requests: 2; counts: `{"submissions": 1, "explicitRejections": 0, "schemaInvalidSubmissions": 0, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"region_id": "crackclaw-point"}`

Handoff: Retreat survivors to Crackclaw Point as the only legal retreat for the attacking army after losing at Harrenhal. This preserves our remaining footman unit (now routed) and keeps our controlled areas intact for future actions.

Previous plan: Baratheon wins the Harrenhal combat without needing the Valyrian Steel Blade (combat totals tie at 3, and Baratheon holds the Fiefdoms lead). Preserving the Blade for a later battle this round improves our chance to secure additional castles and reach the 7‑castle win condition.

Pending: `{"type": "select-region", "house": "baratheon", "regions": ["crackclaw-point", "blackwater"]}`

Guidance: `null`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 5, "controlledLandAreas": 8, "controlledCastleAreas": 5, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "harrenhal", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 3, "controlledLandAreas": 4, "controlledCastleAreas": 3, "controlledSupplyIcons": 4, "controlledRegions": ["stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

<a id="d156"></a>

## D156 — stark — resolve_march (completed)

Run `26ea69a8-5cd5-4fce-a1f7-de297e3c72b0`. Requests: 2; counts: `{"submissions": 2, "explicitRejections": 1, "schemaInvalidSubmissions": 1, "reconstructedInvalidWithoutOutput": 0, "nonSchemaRejections": 0}`.

Action: `{"starting_region_id": "the-shivering-sea", "moves": [{"destination_region_id": "the-narrow-sea", "unit_ids": [4]}], "leave_power_token": false, "omitted_supply_unsafe_move_groups": 0, "omitted_illegal_power_token": false}`

Handoff: Move Stark ship from The Shivering Sea to The Narrow Sea to expand naval reach for future transport without combat. No power token needed.

Previous plan: Discard the low‑strength Rodrick Cassel (strength 1, 2 towers) to draw a new card. Keep the higher‑strength Robb Stark and Roose Bolton for upcoming combats, and retain The Blackfish for its defensive ability.

Pending: `{"type": "resolve-single-march", "houseId": "stark", "supportersAgainstNeutralForce": null}`

Guidance: `{"decision": "march", "legalOrderRegions": [{"regionId": "the-shivering-sea", "orderId": 1, "order": "March -1", "unitIds": [4], "castleAreasLostIfEmptiedWithoutToken": 0, "reachableRegions": [{"regionId": "the-narrow-sea", "type": "sea", "castleLevel": 0, "castleAreasGainedIfCaptured": 0, "garrison": 0, "controller": null, "triggersCombat": false, "neutralForce": null, "supplySafeUnitIdGroupsWhenChosenAlone": [[4]]}], "canLeavePowerToken": false}], "constraints": ["Each unit ID may be moved at most once.", "At most one destination may trigger combat.", "Use only destinations listed for the selected starting region.", "Move groups are processed in list order. Every group must fit Supply after the earlier groups."], "safePass": "An empty moves list discards the selected March order without moving units or spending a control token."}`

Tracks: `{"ironThrone": ["baratheon", "stark", "lannister"], "fiefdoms": ["baratheon", "stark", "lannister"], "kingsCourt": ["baratheon", "stark", "lannister"]}`

Houses: `[{"id": "baratheon", "name": "Baratheon", "powerTokens": 3, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 7, "controlledCastleAreas": 4, "controlledSupplyIcons": 5, "controlledRegions": ["blackwater", "kings-landing", "the-reach", "kingswood", "crackclaw-point", "searoad-marches", "shipbreaker-bay", "dragonstone", "port-of-dragonstone"]}, {"id": "lannister", "name": "Lannister", "powerTokens": 2, "supply": 4, "currentVictoryPoints": 4, "controlledLandAreas": 5, "controlledCastleAreas": 4, "controlledSupplyIcons": 4, "controlledRegions": ["harrenhal", "stoney-sept", "riverrun", "lannisport", "port-of-lannisport", "seagard"]}, {"id": "stark", "name": "Stark", "powerTokens": 0, "supply": 2, "currentVictoryPoints": 3, "controlledLandAreas": 3, "controlledCastleAreas": 3, "controlledSupplyIcons": 1, "controlledRegions": ["winterfell", "port-of-winterfell", "white-harbor", "the-shivering-sea", "moat-cailin", "port-of-white-harbor"]}]`

