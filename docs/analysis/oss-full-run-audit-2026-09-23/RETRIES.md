# Exhaustive retry and failure ledger

Each D-number identifies one model-run attempt, not a game round. Requests include parent and rules-oracle responses with usage. Exploration requests are not automatically retries.

402 submissions: 158 accepted, 243 schema-invalid, and one domain-legality rejection. Of the 244 unsuccessful submissions, 94 have recorded rejection outputs; 150 are independently revalidated from their arguments because their outputs were not persisted. The latter are not fabricated tool feedback.

51 run attempts had invalid submissions or ended failed/cancelled. All 13 failed attempts ended in output exhaustion; the two cancelled attempts are the mustering loops. See the individual ledger below for every unsuccessful submission.

| Run | Round / house | Status | Responses | Submissions | Schema invalid | Domain invalid | Missing invalid outputs |
|---|---|---|---:|---:|---:|---:|---:|
| [D004](round-01.md#d004) | 1 / lannister | completed | 30 | 30 | 29 | 0 | 0 |
| [D008](round-01.md#d008) | 1 / baratheon | completed | 2 | 2 | 1 | 0 | 0 |
| [D009](round-01.md#d009) | 1 / lannister | completed | 4 | 3 | 2 | 0 | 0 |
| [D014](round-02.md#d014) | 2 / lannister | failed | 1 | 0 | 0 | 0 | 0 |
| [D017](round-02.md#d017) | 2 / lannister | completed | 2 | 2 | 1 | 0 | 0 |
| [D019](round-02.md#d019) | 2 / lannister | completed | 4 | 4 | 3 | 0 | 0 |
| [D021](round-02.md#d021) | 2 / baratheon | completed | 6 | 3 | 2 | 0 | 0 |
| [D022](round-02.md#d022) | 2 / stark | completed | 3 | 2 | 1 | 0 | 0 |
| [D024](round-03.md#d024) | 3 / baratheon | failed | 2 | 0 | 0 | 0 | 0 |
| [D027](round-03.md#d027) | 3 / baratheon | failed | 1 | 0 | 0 | 0 | 0 |
| [D029](round-03.md#d029) | 3 / lannister | failed | 1 | 0 | 0 | 0 | 0 |
| [D030](round-03.md#d030) | 3 / lannister | completed | 2 | 2 | 1 | 0 | 0 |
| [D035](round-03.md#d035) | 3 / lannister | completed | 2 | 2 | 1 | 0 | 0 |
| [D036](round-03.md#d036) | 3 / stark | completed | 26 | 26 | 24 | 1 | 0 |
| [D038](round-04.md#d038) | 4 / baratheon | failed | 1 | 0 | 0 | 0 | 0 |
| [D039](round-04.md#d039) | 4 / baratheon | failed | 1 | 0 | 0 | 0 | 0 |
| [D040](round-04.md#d040) | 4 / baratheon | cancelled | 90 | 75 | 75 | 0 | 75 |
| [D041](round-04.md#d041) | 4 / baratheon | failed | 1 | 0 | 0 | 0 | 0 |
| [D042](round-04.md#d042) | 4 / baratheon | cancelled | 80 | 73 | 73 | 0 | 73 |
| [D043](round-04.md#d043) | 4 / baratheon | completed | 3 | 2 | 1 | 0 | 0 |
| [D044](round-04.md#d044) | 4 / lannister | failed | 1 | 0 | 0 | 0 | 0 |
| [D045](round-04.md#d045) | 4 / lannister | failed | 1 | 0 | 0 | 0 | 0 |
| [D046](round-04.md#d046) | 4 / lannister | failed | 2 | 0 | 0 | 0 | 0 |
| [D047](round-04.md#d047) | 4 / lannister | failed | 1 | 0 | 0 | 0 | 0 |
| [D048](round-04.md#d048) | 4 / lannister | completed | 2 | 2 | 1 | 0 | 0 |
| [D049](round-04.md#d049) | 4 / stark | completed | 2 | 2 | 1 | 0 | 0 |
| [D056](round-04.md#d056) | 4 / lannister | completed | 2 | 2 | 1 | 0 | 0 |
| [D057](round-04.md#d057) | 4 / baratheon | completed | 4 | 2 | 1 | 0 | 0 |
| [D059](round-04.md#d059) | 4 / stark | completed | 2 | 2 | 1 | 0 | 0 |
| [D069](round-05.md#d069) | 5 / baratheon | completed | 3 | 2 | 1 | 0 | 0 |
| [D070](round-05.md#d070) | 5 / baratheon | completed | 2 | 2 | 1 | 0 | 0 |
| [D083](round-06.md#d083) | 6 / baratheon | completed | 2 | 2 | 1 | 0 | 0 |
| [D090](round-07.md#d090) | 7 / baratheon | completed | 2 | 2 | 1 | 0 | 0 |
| [D091](round-07.md#d091) | 7 / lannister | completed | 2 | 2 | 1 | 0 | 0 |
| [D092](round-07.md#d092) | 7 / stark | completed | 2 | 2 | 1 | 0 | 0 |
| [D102](round-07.md#d102) | 7 / baratheon | completed | 3 | 3 | 2 | 0 | 0 |
| [D105](round-07.md#d105) | 7 / stark | completed | 2 | 2 | 1 | 0 | 0 |
| [D107](round-08.md#d107) | 8 / baratheon | completed | 2 | 2 | 1 | 0 | 0 |
| [D108](round-08.md#d108) | 8 / lannister | completed | 3 | 3 | 2 | 0 | 0 |
| [D109](round-08.md#d109) | 8 / stark | completed | 2 | 2 | 1 | 0 | 0 |
| [D113](round-08.md#d113) | 8 / baratheon | completed | 2 | 2 | 1 | 0 | 0 |
| [D143](round-09.md#d143) | 9 / baratheon | failed | 2 | 1 | 1 | 0 | 1 |
| [D144](round-09.md#d144) | 9 / baratheon | completed | 2 | 2 | 1 | 0 | 0 |
| [D145](round-09.md#d145) | 9 / baratheon | completed | 2 | 2 | 1 | 0 | 0 |
| [D152](round-09.md#d152) | 9 / lannister | completed | 4 | 2 | 1 | 0 | 0 |
| [D156](round-09.md#d156) | 9 / stark | completed | 2 | 2 | 1 | 0 | 0 |
| [D157](round-10.md#d157) | 10 / baratheon | completed | 2 | 2 | 1 | 0 | 0 |
| [D158](round-10.md#d158) | 10 / stark | completed | 2 | 2 | 1 | 0 | 0 |
| [D159](round-10.md#d159) | 10 / lannister | completed | 2 | 2 | 1 | 0 | 0 |
| [D171](round-10.md#d171) | 10 / baratheon | failed | 2 | 1 | 1 | 0 | 1 |
| [D172](round-10.md#d172) | 10 / baratheon | completed | 2 | 2 | 1 | 0 | 0 |

## All 244 unsuccessful submissions

Call numbers are chronological within each run, including exploration calls. Error excerpts are abbreviated here; exact arguments, complete errors and original outputs are in [retry-events.json](retry-events.json). “Reconstructed” means schema validation now, not an archived response.

| Run | Call | Evidence | Error excerpt |
|---|---:|---|---|
| [D004](round-01.md#d004) | 1 | Recorded | Invalid action: 'skip_raven_order_replacement' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 2 | Recorded | Invalid action: 'skip' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 3 | Recorded | Invalid action: 'replace_raven_order' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 4 | Recorded | Invalid action: 'decision' is a required property |
| [D004](round-01.md#d004) | 5 | Recorded | Invalid action: 'replace_raven_order' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 6 | Recorded | Invalid action: 'decision' is a required property |
| [D004](round-01.md#d004) | 7 | Recorded | Invalid action: 'replace-order' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 8 | Recorded | Invalid action: 'decision' is a required property |
| [D004](round-01.md#d004) | 9 | Recorded | Invalid action: {'type': 'skip_raven_order_replacement'} is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 10 | Recorded | Invalid action: 'replace-order' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 11 | Recorded | Invalid action: {'regionId': 'lannisport', 'orderId': 3} is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 12 | Recorded | Invalid action: 'skip_raven_order_replacement' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 13 | Recorded | Invalid action: {'skip_raven_order_replacement': {}} is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 14 | Recorded | Invalid action: {'type': 'skip_raven_order_replacement'} is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 15 | Recorded | Invalid action: 'replace-order' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 16 | Recorded | Invalid action: 'replace-order' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 17 | Recorded | Invalid action: {'regionId': 'lannisport', 'orderId': 3} is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 18 | Recorded | Invalid action: 'decision' is a required property |
| [D004](round-01.md#d004) | 19 | Recorded | Invalid action: 'replace-order' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 20 | Recorded | Invalid action: 'replace-order' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 21 | Recorded | Invalid action: 'replace-order' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 22 | Recorded | Invalid action: {'regionId': 'lannisport', 'newOrderId': 3} is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 23 | Recorded | Invalid action: 'raven-order-replacement' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 24 | Recorded | Invalid action: {'type': 'skip_raven_order_replacement'} is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 25 | Recorded | Invalid action: 'replace_raven_order' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 26 | Recorded | Invalid action: {'choice': 'skip_raven_order_replacement'} is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 27 | Recorded | Invalid action: 'replace-order' is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 28 | Recorded | Invalid action: {'skip': True} is not valid under any of the given schemas |
| [D004](round-01.md#d004) | 29 | Recorded | Invalid action: 'skip_raven_order_replacement' is not valid under any of the given schemas |
| [D008](round-01.md#d008) | 1 | Recorded | Invalid action: Additional properties are not allowed ('unit_ids' was unexpected) |
| [D009](round-01.md#d009) | 2 | Recorded | Invalid action: Additional properties are not allowed ('unit_ids' was unexpected) |
| [D009](round-01.md#d009) | 3 | Recorded | Invalid action: Additional properties are not allowed ('unitIds' was unexpected) |
| [D017](round-02.md#d017) | 1 | Recorded | Invalid action: 'skip_raven_order_replacement' is not valid under any of the given schemas |
| [D019](round-02.md#d019) | 1 | Recorded | Invalid action: Additional properties are not allowed ('unit_ids' was unexpected) |
| [D019](round-02.md#d019) | 2 | Recorded | Invalid action: Additional properties are not allowed ('unitIds' was unexpected) |
| [D019](round-02.md#d019) | 3 | Recorded | Invalid action: Additional properties are not allowed ('unitIds' was unexpected) |
| [D021](round-02.md#d021) | 4 | Recorded | Invalid action: Additional properties are not allowed ('unit_ids' was unexpected) |
| [D021](round-02.md#d021) | 5 | Recorded | Invalid action: Additional properties are not allowed ('unitIds' was unexpected) |
| [D022](round-02.md#d022) | 2 | Recorded | Invalid action: Additional properties are not allowed ('unit_ids' was unexpected) |
| [D030](round-03.md#d030) | 1 | Recorded | Invalid action: 'skip_raven_order_replacement' is not valid under any of the given schemas |
| [D035](round-03.md#d035) | 1 | Recorded | Invalid action: Additional properties are not allowed ('unit_ids' was unexpected) |
| [D036](round-03.md#d036) | 1 | Recorded | Invalid action: Additional properties are not allowed ('destination_region_id', 'unit_ids' were unexpected) |
| [D036](round-03.md#d036) | 2 | Recorded | Invalid action: Additional properties are not allowed ('regionId', 'unitIds' were unexpected) |
| [D036](round-03.md#d036) | 3 | Recorded | Invalid action: Additional properties are not allowed ('destination_region_id', 'unit_ids' were unexpected) |
| [D036](round-03.md#d036) | 4 | Recorded | Invalid action: Additional properties are not allowed ('regionId', 'unitIds' were unexpected) |
| [D036](round-03.md#d036) | 5 | Recorded | Invalid action: ['winterfell', [2]] is not of type 'object' |
| [D036](round-03.md#d036) | 6 | Recorded | Invalid action: Additional properties are not allowed ('region_id', 'units' were unexpected) |
| [D036](round-03.md#d036) | 7 | Recorded | Invalid action: Additional properties are not allowed ('destinationRegionId', 'unitIds' were unexpected) |
| [D036](round-03.md#d036) | 8 | Recorded | Invalid action: Additional properties are not allowed ('winterfell' was unexpected) |
| [D036](round-03.md#d036) | 9 | Recorded | Invalid action: Additional properties are not allowed ('destination_region_id', 'unit_ids' were unexpected) |
| [D036](round-03.md#d036) | 10 | Recorded | Invalid action: Additional properties are not allowed ('regionId', 'unitId' were unexpected) |
| [D036](round-03.md#d036) | 11 | Recorded | Invalid action: Additional properties are not allowed ('destination', 'units' were unexpected) |
| [D036](round-03.md#d036) | 12 | Recorded | A control token can only be left when legally vacating this source; no move was submitted. |
| [D036](round-03.md#d036) | 13 | Recorded | Invalid action: Additional properties are not allowed ('region_id', 'unit_ids' were unexpected) |
| [D036](round-03.md#d036) | 14 | Recorded | Invalid action: Additional properties are not allowed ('regionId', 'unitId' were unexpected) |
| [D036](round-03.md#d036) | 15 | Recorded | Invalid action: Additional properties are not allowed ('destination', 'units' were unexpected) |
| [D036](round-03.md#d036) | 16 | Recorded | Invalid action: Additional properties are not allowed ('regionId', 'unitIds' were unexpected) |
| [D036](round-03.md#d036) | 17 | Recorded | Invalid action: Additional properties are not allowed ('regionId', 'unitId' were unexpected) |
| [D036](round-03.md#d036) | 18 | Recorded | Invalid action: Additional properties are not allowed ('region', 'units' were unexpected) |
| [D036](round-03.md#d036) | 19 | Recorded | Invalid action: Additional properties are not allowed ('destinationRegionId', 'unitIds' were unexpected) |
| [D036](round-03.md#d036) | 20 | Recorded | Invalid action: Additional properties are not allowed ('regionId', 'unitIds' were unexpected) |
| [D036](round-03.md#d036) | 21 | Recorded | Invalid action: Additional properties are not allowed ('region_id', 'unit_ids' were unexpected) |
| [D036](round-03.md#d036) | 22 | Recorded | Invalid action: Additional properties are not allowed ('RegionId', 'UnitIds' were unexpected) |
| [D036](round-03.md#d036) | 23 | Recorded | Invalid action: Additional properties are not allowed ('region', 'unitIds' were unexpected) |
| [D036](round-03.md#d036) | 24 | Recorded | Invalid action: Additional properties are not allowed ('starting_region_id' was unexpected) |
| [D036](round-03.md#d036) | 25 | Recorded | Invalid action: Additional properties are not allowed ('unitId' was unexpected) |
| [D040](round-04.md#d040) | 1 | Reconstructed | {'mustering_units': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region_id': 'the-reach', ' |
| [D040](round-04.md#d040) | 3 | Reconstructed | {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dr |
| [D040](round-04.md#d040) | 5 | Reconstructed | {'skip_mustering': True} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 6 | Reconstructed | {'skip_mustering': {}} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 7 | Reconstructed | {'mustering_units': [{'region_id': 'the-reach', 'unit_type': 'footman'}]} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 8 | Reconstructed | {'mustering_choices': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region_id': 'the-reach', |
| [D040](round-04.md#d040) | 9 | Reconstructed | {'mustering_units': [{'origin_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region_id': 'the-reach', 'unit_type': 'footman'}, {'origin_region_id': 'dragonstone', 'unit_type': 'footman' |
| [D040](round-04.md#d040) | 10 | Reconstructed | {'mustering': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region_id': 'the-reach', 'destin |
| [D040](round-04.md#d040) | 11 | Reconstructed | {'mustering': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region_id': 'the-reach', 'destin |
| [D040](round-04.md#d040) | 12 | Reconstructed | {'mustering_units': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone |
| [D040](round-04.md#d040) | 13 | Reconstructed | {'mustering_type': 0, 'mustering_units': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_regio |
| [D040](round-04.md#d040) | 14 | Reconstructed | {'skip_mustering': True} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 15 | Reconstructed | {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dr |
| [D040](round-04.md#d040) | 16 | Reconstructed | {'skip': True} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 17 | Reconstructed | {'skip': True} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 18 | Reconstructed | {'choose_option': {'choice_index': 0}} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 19 | Reconstructed | {'mustering_units': []} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 20 | Reconstructed | {'mustering': {'units': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region_id': 'the-reach |
| [D040](round-04.md#d040) | 21 | Reconstructed | {'mustering_units': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone |
| [D040](round-04.md#d040) | 23 | Reconstructed | {'skip': True} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 24 | Reconstructed | {'player-mustering': {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'re |
| [D040](round-04.md#d040) | 25 | Reconstructed | {'musteringType': 0, 'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': ' |
| [D040](round-04.md#d040) | 26 | Reconstructed | {'mustering_units': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone |
| [D040](round-04.md#d040) | 27 | Reconstructed | {'mustering': 'skip'} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 28 | Reconstructed | {'musteringType': 0, 'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': ' |
| [D040](round-04.md#d040) | 29 | Reconstructed | {'mustering_type': 0, 'mustering_units': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': |
| [D040](round-04.md#d040) | 30 | Reconstructed | {'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone' |
| [D040](round-04.md#d040) | 31 | Reconstructed | {'musteringType': 0, 'musteringUnits': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region_ |
| [D040](round-04.md#d040) | 32 | Reconstructed | {'mustering': {'skip': True}} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 33 | Reconstructed | {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dr |
| [D040](round-04.md#d040) | 34 | Reconstructed | {'muster_units': [{'originRegionId': 'crackclaw-point', 'destinationRegionId': 'crackclaw-point', 'unitType': 'knight'}, {'originRegionId': 'harrenhal', 'destinationRegionId': 'harrenhal', 'unitType': 'knight'}, {'originRegionId': 'the-reach', 'destinationRegi |
| [D040](round-04.md#d040) | 35 | Reconstructed | {'musteringType': 0, 'mustering_units': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region |
| [D040](round-04.md#d040) | 36 | Reconstructed | 'decision' is a required property; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D040](round-04.md#d040) | 37 | Reconstructed | {'mustering_units': [{'regionId': 'crackclaw-point', 'destinationRegionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'destinationRegionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'destinationRegionId': 'the-rea |
| [D040](round-04.md#d040) | 38 | Reconstructed | {'mustering_type': 0, 'mustering_units': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': |
| [D040](round-04.md#d040) | 39 | Reconstructed | {'musteringType': 0, 'musteringUnits': [{'originRegionId': 'crackclaw-point', 'destinationRegionId': 'crackclaw-point', 'unitType': 'knight'}, {'originRegionId': 'harrenhal', 'destinationRegionId': 'harrenhal', 'unitType': 'knight'}, {'originRegionId': 'the-re |
| [D040](round-04.md#d040) | 40 | Reconstructed | {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dr |
| [D040](round-04.md#d040) | 41 | Reconstructed | {'muster_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-drago |
| [D040](round-04.md#d040) | 43 | Reconstructed | {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dr |
| [D040](round-04.md#d040) | 44 | Reconstructed | {'player_mustering': {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'re |
| [D040](round-04.md#d040) | 45 | Reconstructed | [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region_id': 'the-reach', 'destination_region_i |
| [D040](round-04.md#d040) | 46 | Reconstructed | {'units': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region_id': 'the-reach', 'destinatio |
| [D040](round-04.md#d040) | 47 | Reconstructed | {'skip': True} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 48 | Reconstructed | {'mustering_type': 0, 'skip_mustering': True} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 49 | Reconstructed | {'musteringUnits': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dra |
| [D040](round-04.md#d040) | 50 | Reconstructed | {'mustering': {'mustering_units': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region_id':  |
| [D040](round-04.md#d040) | 51 | Reconstructed | {'musteringType': 0, 'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': ' |
| [D040](round-04.md#d040) | 52 | Reconstructed | {'mustering': {'mustering_units': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_region_id':  |
| [D040](round-04.md#d040) | 53 | Reconstructed | {'mustering_type': 0, 'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'re |
| [D040](round-04.md#d040) | 54 | Reconstructed | {'player_mustering': {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'re |
| [D040](round-04.md#d040) | 55 | Reconstructed | {'mustering': {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id |
| [D040](round-04.md#d040) | 56 | Reconstructed | {'type': 'player-mustering', 'musteringUnits': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'} |
| [D040](round-04.md#d040) | 57 | Reconstructed | {'skip_mustering': True} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 58 | Reconstructed | 'decision' is a required property; 'strategic_handoff' is a required property; Additional properties are not allowed ('action', 'arguments' were unexpected) |
| [D040](round-04.md#d040) | 59 | Reconstructed | {'mustering': {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id |
| [D040](round-04.md#d040) | 60 | Reconstructed | {'mustering': 'skip'} is not valid under any of the given schemas; 'strategic_handoff' is a required property |
| [D040](round-04.md#d040) | 61 | Reconstructed | {'mustering_units': [{'region_id': 'crackclaw-point', 'type': 'knight'}, {'region_id': 'harrenhal', 'type': 'knight'}, {'region_id': 'the-reach', 'type': 'footman'}, {'region_id': 'dragonstone', 'type': 'footman'}, {'region_id': 'port-of-dragonstone', 'type':  |
| [D040](round-04.md#d040) | 62 | Reconstructed | {'skip_mustering': True, 'mustering_type': 0} is not valid under any of the given schemas; 'strategic_handoff' is a required property |
| [D040](round-04.md#d040) | 63 | Reconstructed | {'musteringUnits': []} is not valid under any of the given schemas; 'strategic_handoff' is a required property |
| [D040](round-04.md#d040) | 64 | Reconstructed | {'musteringType': 0, 'musteringUnits': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'regi |
| [D040](round-04.md#d040) | 65 | Reconstructed | {'player_mustering': {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'re |
| [D040](round-04.md#d040) | 66 | Reconstructed | {'mustering': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dragonst |
| [D040](round-04.md#d040) | 67 | Reconstructed | {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dr |
| [D040](round-04.md#d040) | 68 | Reconstructed | {'musteringUnits': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dra |
| [D040](round-04.md#d040) | 69 | Reconstructed | {'musteringUnits': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dra |
| [D040](round-04.md#d040) | 70 | Reconstructed | {'skipMustering': True} is not valid under any of the given schemas; 'strategic_handoff' is a required property |
| [D040](round-04.md#d040) | 71 | Reconstructed | {'musteringUnits': [{'originRegionId': 'crackclaw-point', 'destinationRegionId': 'crackclaw-point', 'unitType': 'knight'}, {'originRegionId': 'harrenhal', 'destinationRegionId': 'harrenhal', 'unitType': 'knight'}, {'originRegionId': 'the-reach', 'destinationRe |
| [D040](round-04.md#d040) | 72 | Reconstructed | {'skip': True} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 73 | Reconstructed | {'skipMuster': True} is not valid under any of the given schemas |
| [D040](round-04.md#d040) | 74 | Reconstructed | {'player-mustering': {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'re |
| [D040](round-04.md#d040) | 75 | Reconstructed | {'mustering': {'mustering_type': 0, 'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'f |
| [D040](round-04.md#d040) | 76 | Reconstructed | 'decision' is a required property; 'strategic_handoff' is a required property; Additional properties are not allowed ('action', 'arguments' were unexpected) |
| [D040](round-04.md#d040) | 77 | Reconstructed | {'mustering': {'mustering_type': 0, 'units': [{'origin_region_id': 'crackclaw-point', 'destination_region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'origin_region_id': 'harrenhal', 'destination_region_id': 'harrenhal', 'unit_type': 'knight'}, {'origin_r |
| [D040](round-04.md#d040) | 78 | Reconstructed | {'musteringUnits': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dra |
| [D040](round-04.md#d040) | 80 | Reconstructed | {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'Knight'}, {'region_id': 'harrenhal', 'unit_type': 'Knight'}, {'region_id': 'the-reach', 'unit_type': 'Footman'}, {'region_id': 'dragonstone', 'unit_type': 'Footman'}, {'region_id': 'port-of-dr |
| [D042](round-04.md#d042) | 1 | Reconstructed | {'type': 'mustering', 'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'re |
| [D042](round-04.md#d042) | 2 | Reconstructed | {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dr |
| [D042](round-04.md#d042) | 3 | Reconstructed | 'mustering' is not valid under any of the given schemas; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 4 | Reconstructed | {'musteringUnits': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dra |
| [D042](round-04.md#d042) | 5 | Reconstructed | 'decision' is a required property; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 6 | Reconstructed | {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dr |
| [D042](round-04.md#d042) | 7 | Reconstructed | 'mustering_units' is not valid under any of the given schemas; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 8 | Reconstructed | {'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone' |
| [D042](round-04.md#d042) | 9 | Reconstructed | 'mustering' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 10 | Reconstructed | {'skipMustering': True} is not valid under any of the given schemas |
| [D042](round-04.md#d042) | 11 | Reconstructed | 'mustering_units' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 12 | Reconstructed | 'decision' is a required property; Additional properties are not allowed ('skip_mustering' was unexpected) |
| [D042](round-04.md#d042) | 13 | Reconstructed | 'mustering' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 14 | Reconstructed | {'skip_mustering': True} is not valid under any of the given schemas |
| [D042](round-04.md#d042) | 15 | Reconstructed | {'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone' |
| [D042](round-04.md#d042) | 16 | Reconstructed | {'type': 'mustering', 'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'re |
| [D042](round-04.md#d042) | 17 | Reconstructed | {'mustering_units': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone |
| [D042](round-04.md#d042) | 18 | Reconstructed | {'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone' |
| [D042](round-04.md#d042) | 19 | Reconstructed | {'skipMustering': True} is not valid under any of the given schemas |
| [D042](round-04.md#d042) | 20 | Reconstructed | 'mustering_units' is not valid under any of the given schemas; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 21 | Reconstructed | 'mustering' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 22 | Reconstructed | {'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone' |
| [D042](round-04.md#d042) | 23 | Reconstructed | 'decision' is a required property; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 25 | Reconstructed | 'player-mustering' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 26 | Reconstructed | 'player-mustering' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 27 | Reconstructed | {'skipMustering': True} is not valid under any of the given schemas |
| [D042](round-04.md#d042) | 28 | Reconstructed | 'skip_mustering' is not valid under any of the given schemas |
| [D042](round-04.md#d042) | 29 | Reconstructed | {'mustering': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone', 'un |
| [D042](round-04.md#d042) | 30 | Reconstructed | 'decision' is a required property; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 31 | Reconstructed | 'mustering_units' is not valid under any of the given schemas; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 32 | Reconstructed | 'mustering' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 34 | Reconstructed | {'mustering_units': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone |
| [D042](round-04.md#d042) | 35 | Reconstructed | {'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone' |
| [D042](round-04.md#d042) | 36 | Reconstructed | {'muster_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-drago |
| [D042](round-04.md#d042) | 37 | Reconstructed | {'type': 'player-mustering', 'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regi |
| [D042](round-04.md#d042) | 38 | Reconstructed | {'skipMustering': True} is not valid under any of the given schemas |
| [D042](round-04.md#d042) | 39 | Reconstructed | 'player-mustering' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 40 | Reconstructed | {'type': 'mustering', 'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'re |
| [D042](round-04.md#d042) | 41 | Reconstructed | {'muster_units': {'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'por |
| [D042](round-04.md#d042) | 42 | Reconstructed | 'decision' is a required property; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 44 | Reconstructed | {'skip_mustering': True} is not valid under any of the given schemas |
| [D042](round-04.md#d042) | 45 | Reconstructed | {'type': 'mustering', 'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId':  |
| [D042](round-04.md#d042) | 46 | Reconstructed | 'mustering' is not valid under any of the given schemas; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 47 | Reconstructed | 'skip_mustering' is not valid under any of the given schemas |
| [D042](round-04.md#d042) | 48 | Reconstructed | 'player-mustering' is not valid under any of the given schemas; Additional properties are not allowed ('arguments' was unexpected) |
| [D042](round-04.md#d042) | 49 | Reconstructed | {'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone' |
| [D042](round-04.md#d042) | 50 | Reconstructed | {'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'}, {'region_id': 'port-of-dr |
| [D042](round-04.md#d042) | 51 | Reconstructed | 'mustering' is not valid under any of the given schemas; Additional properties are not allowed ('arguments' was unexpected) |
| [D042](round-04.md#d042) | 52 | Reconstructed | 'mustering_units' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 53 | Reconstructed | 'mustering_units' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 54 | Reconstructed | 'decision' is a required property; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 55 | Reconstructed | 'skip_mustering' is not valid under any of the given schemas |
| [D042](round-04.md#d042) | 56 | Reconstructed | {'musteringType': 0, 'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': ' |
| [D042](round-04.md#d042) | 58 | Reconstructed | 'decision' is a required property; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 59 | Reconstructed | 'player-mustering' is not valid under any of the given schemas; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 60 | Reconstructed | {'mustering': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone', 'un |
| [D042](round-04.md#d042) | 61 | Reconstructed | 'mustering' is not valid under any of the given schemas; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 62 | Reconstructed | {'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone' |
| [D042](round-04.md#d042) | 63 | Reconstructed | 'mustering_units' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 64 | Reconstructed | 'decision' is a required property; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 65 | Reconstructed | 'decision' is a required property; Additional properties are not allowed ('mustering' was unexpected) |
| [D042](round-04.md#d042) | 66 | Reconstructed | 'mustering' is not valid under any of the given schemas; 'strategic_handoff' is a required property; Additional properties are not allowed ('arguments' was unexpected) |
| [D042](round-04.md#d042) | 67 | Reconstructed | {'type': 'mustering_units', 'mustering_units': [{'region_id': 'crackclaw-point', 'unit_type': 'knight'}, {'region_id': 'harrenhal', 'unit_type': 'knight'}, {'region_id': 'the-reach', 'unit_type': 'footman'}, {'region_id': 'dragonstone', 'unit_type': 'footman'} |
| [D042](round-04.md#d042) | 68 | Reconstructed | 'mustering_units' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D042](round-04.md#d042) | 69 | Reconstructed | 'mustering' is not valid under any of the given schemas; Additional properties are not allowed ('musteringType', 'mustering_units' were unexpected) |
| [D042](round-04.md#d042) | 70 | Reconstructed | {'skipMustering': True} is not valid under any of the given schemas |
| [D042](round-04.md#d042) | 71 | Reconstructed | {'type': 'player-mustering', 'musteringType': 0, 'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType' |
| [D042](round-04.md#d042) | 72 | Reconstructed | {'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone' |
| [D042](round-04.md#d042) | 73 | Reconstructed | {'musteringUnits': [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone' |
| [D042](round-04.md#d042) | 74 | Reconstructed | 'mustering' is not valid under any of the given schemas; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 75 | Reconstructed | 'mustering_units' is not valid under any of the given schemas; Additional properties are not allowed ('musteringUnits' was unexpected) |
| [D042](round-04.md#d042) | 76 | Reconstructed | [{'regionId': 'crackclaw-point', 'unitType': 'knight'}, {'regionId': 'harrenhal', 'unitType': 'knight'}, {'regionId': 'the-reach', 'unitType': 'footman'}, {'regionId': 'dragonstone', 'unitType': 'footman'}, {'regionId': 'port-of-dragonstone', 'unitType': 'ship |
| [D042](round-04.md#d042) | 77 | Reconstructed | 'player_mustering' is not valid under any of the given schemas; Additional properties are not allowed ('mustering_units' was unexpected) |
| [D043](round-04.md#d043) | 2 | Recorded | Invalid action: {'skip_mustering': True} is not valid under any of the given schemas |
| [D048](round-04.md#d048) | 1 | Recorded | Invalid action: 'skip_mustering' is not valid under any of the given schemas |
| [D049](round-04.md#d049) | 1 | Recorded | Invalid action: 'skip_mustering' is not valid under any of the given schemas |
| [D056](round-04.md#d056) | 1 | Recorded | Invalid action: 'skip_raven_order_replacement' is not valid under any of the given schemas |
| [D057](round-04.md#d057) | 3 | Recorded | Invalid action: Additional properties are not allowed ('unitIds' was unexpected) |
| [D059](round-04.md#d059) | 1 | Recorded | Invalid action: Additional properties are not allowed ('destination_region_id', 'unit_ids' were unexpected) |
| [D069](round-05.md#d069) | 2 | Recorded | Invalid action: 'skip_raven_order_replacement' is not valid under any of the given schemas |
| [D070](round-05.md#d070) | 1 | Recorded | Invalid action: Additional properties are not allowed ('unitIds' was unexpected) |
| [D083](round-06.md#d083) | 1 | Recorded | Invalid action: {'action': 'replace_raven_order', 'regionId': 'the-reach', 'orderId': 6} is not valid under any of the given schemas |
| [D090](round-07.md#d090) | 1 | Recorded | Invalid action: 'skip_mustering' is not valid under any of the given schemas |
| [D091](round-07.md#d091) | 1 | Recorded | Invalid action: 'skip_mustering' is not valid under any of the given schemas |
| [D092](round-07.md#d092) | 1 | Recorded | Invalid action: 'skip_mustering' is not valid under any of the given schemas |
| [D102](round-07.md#d102) | 1 | Recorded | Invalid action: 'replace_raven_order' is not valid under any of the given schemas |
| [D102](round-07.md#d102) | 2 | Recorded | Invalid action: 'replace_raven_order' is not valid under any of the given schemas |
| [D105](round-07.md#d105) | 1 | Recorded | Invalid action: Additional properties are not allowed ('destination_region_id', 'unit_ids' were unexpected) |
| [D107](round-08.md#d107) | 1 | Recorded | Invalid action: {'mustering': [{'regionId': 'kings-landing', 'units': ['footman', 'footman']}, {'regionId': 'dragonstone', 'units': ['knight', 'footman']}, {'regionId': 'the-reach', 'units': ['footman']}, {'regionId': 'crackclaw-point', 'units': ['footman']},  |
| [D108](round-08.md#d108) | 1 | Recorded | Invalid action: {'musterings': [['lannisport', [{'region': 'lannisport', 'from': None, 'to': 'footman'}]], ['port-of-lannisport', [{'region': 'port-of-lannisport', 'from': None, 'to': 'ship'}]], ['moat-cailin', [{'region': 'moat-cailin', 'from': 'footman', 'to |
| [D108](round-08.md#d108) | 2 | Recorded | Invalid action: {'action': 'muster_units', 'musters': [{'mustering_region_id': 'lannisport', 'recruitments': [{'unit_type': 'siege-engine', 'region_id': 'lannisport', 'upgrade_from_footman': False}]}, {'mustering_region_id': 'moat-cailin', 'recruitments': [{'u |
| [D109](round-08.md#d109) | 1 | Recorded | Invalid action: {'type': 'muster_units', 'placements': [{'regionId': 'winterfell', 'unitType': 'footman'}]} is not valid under any of the given schemas |
| [D113](round-08.md#d113) | 1 | Recorded | Invalid action: {'type': 'replace_raven_order', 'region_id': 'dragonstone', 'order_id': 10} is not valid under any of the given schemas |
| [D143](round-09.md#d143) | 1 | Reconstructed | {'regionId': 'searoad-marches', 'newOrderId': 2} is not valid under any of the given schemas |
| [D144](round-09.md#d144) | 1 | Recorded | Invalid action: 'skip_raven_order_replacement' is not valid under any of the given schemas |
| [D145](round-09.md#d145) | 1 | Recorded | Invalid action: Additional properties are not allowed ('unitIds' was unexpected) |
| [D152](round-09.md#d152) | 3 | Recorded | Invalid action: Additional properties are not allowed ('unit_ids' was unexpected) |
| [D156](round-09.md#d156) | 1 | Recorded | Invalid action: Additional properties are not allowed ('destination_region_id', 'unit_ids' were unexpected) |
| [D157](round-10.md#d157) | 1 | Recorded | Invalid action: 'skip_mustering' is not valid under any of the given schemas |
| [D158](round-10.md#d158) | 1 | Recorded | Invalid action: 'skip_mustering' is not valid under any of the given schemas |
| [D159](round-10.md#d159) | 1 | Recorded | Invalid action: 'skip_mustering' is not valid under any of the given schemas |
| [D171](round-10.md#d171) | 1 | Reconstructed | {'type': 'replace-order', 'regionId': 'searoad-marches', 'newOrderId': 2} is not valid under any of the given schemas |
| [D172](round-10.md#d172) | 1 | Recorded | Invalid action: 'skip_raven_order_replacement' is not valid under any of the given schemas |

## Exploration-tool failures

These are separate from submit-action rejection counts. They include six oracle output-limit failures, one oracle turn-limit failure, and one misspelled card ID. A later attempt may repeat the failed query; the ledger preserves every occurrence.

| Run | Call | Tool | Error |
|---|---:|---|---|
| [D010](round-02.md#d010) | 1 | ask_rules_oracle | An error occurred while running the tool. Please try again. Error: Responses API returned terminal status incomplete; incomplete_details=IncompleteDetails(reason='max_output_tokens') |
| [D010](round-02.md#d010) | 4 | ask_rules_oracle | An error occurred while running the tool. Please try again. Error: Responses API returned terminal status incomplete; incomplete_details=IncompleteDetails(reason='max_output_tokens') |
| [D012](round-02.md#d012) | 1 | ask_rules_oracle | An error occurred while running the tool. Please try again. Error: Responses API returned terminal status incomplete; incomplete_details=IncompleteDetails(reason='max_output_tokens') |
| [D012](round-02.md#d012) | 2 | ask_rules_oracle | An error occurred while running the tool. Please try again. Error: Responses API returned terminal status incomplete; incomplete_details=IncompleteDetails(reason='max_output_tokens') |
| [D023](round-03.md#d023) | 1 | ask_rules_oracle | An error occurred while running the tool. Please try again. Error: Responses API returned terminal status incomplete; incomplete_details=IncompleteDetails(reason='max_output_tokens') |
| [D120](round-08.md#d120) | 4 | inspect_house_card | An error occurred while running the tool. Please try again. Error: Unknown or ambiguous House card 'renny-baratheon'. Use an exact card ID or name from availableHouseCards or houseCardStatus. |
| [D150](round-09.md#d150) | 1 | ask_rules_oracle | An error occurred while running the tool. Please try again. Error: Responses API returned terminal status incomplete; incomplete_details=IncompleteDetails(reason='max_output_tokens') |
| [D150](round-09.md#d150) | 2 | ask_rules_oracle | An error occurred while running the tool. Please try again. Error: Max turns (3) exceeded |
