## Final result: Luna wins in round eight

The game completed at **2026-09-24 09:53:47 UTC**. **Luna GPT-6 / Baratheon
won with 7 castles**, followed by DeepSeek V4.1 Flash / Lannister with **4**
and Qwen3.8-27B / Stark with **1**. The saved game's terminal state is
`game-ended`, winner `baratheon`, matching the manifest result.

| Model / provider | Castles | Completed decisions | Responses with usage | Reported cost |
| --- | ---: | ---: | ---: | ---: |
| Luna GPT-6 / OpenAI | 7 | 59 | 218 | $0.523996255 |
| DeepSeek V4.1 Flash / Morph | 4 | 52 | 123 | $0.58309531926 |
| Qwen3.8-27B / DeepInfra BF16 | 1 | 35 | 177 | $2.160324975 |
| Total | | 146 | 518 | **$3.26741654926** |

### Final cumulative verification

- **526 recorded request starts**, including parent and nested oracle requests.
  There are **518 unique returned response IDs with usage: 499 parent and 19
  oracle**. Starts and usage responses are different measures because some
  requests failed or were cancelled. The database's 512 ordinary
  `model-request-completed` events also exclude response records recovered via
  other persisted traces, so that event count alone understates returned usage.
- Read-only generation metadata confirms **all 518 responses** used the pinned
  providers: 218 OpenAI, 123 Morph, 177 DeepInfra. No fallback was observed.
- **157 decision attempts: 146 completed, nine failed, two cancelled.**
  **147 action submissions: 146 accepted plus one invalid submission**.
- The sole action-schema violation was DeepSeek/Morph's 2201-character handoff
  exceeding the offered 2000-character maximum. Its second submission was
  accepted. This remains a **provider-schema issue**; no harness workaround
  was made. There were no additional schema violations in the final segment.
- Other recorded issues: two parent output-limit failures (DeepSeek), three
  oracle output-limit failures (one Luna, two Qwen), two incorrect area IDs,
  two DeepSeek connection failures and one DeepSeek stream server error.
  Four failed attempts came from earlier account/key funding rejections.
  The previous segment's timeout caused the two cancellations. Detailed
  evidence and qualifications are retained in the historical sections below.
- The final resumed segment's **`runtimeUnchangedAtExit` is true**. All resumed
  segments used the original isolated runtime. The first segment's shared
  source drift qualification remains documented below.
- SQLite `quick_check` returned `ok`. Saves, cumulative traces, manifest history
  and checkpoints are preserved. The five-submission guard never fired.
- No production harness, prompt or schema was changed to compensate for these
  failures; provider routes, BF16 precision, blocklist, disabled fallbacks,
  reasoning and output settings remained fixed.

The cost is reported response usage, not an independently reconciled account
bill; requests without returned usage cannot be fully costed from these traces.
This is one seeded game with fixed house assignments, not a general model ranking.

The one-game monitoring automation has been removed following completion.

All sections below are historical checkpoints superseded by this completed
result. Their earlier unfinished/running statements describe those checkpoints.

## Third continuation: resumed from round eight

At the user's explicit request, the same saved game resumed at **2026-09-24
09:16:20 UTC**, after the previous segment's six-hour timeout. No duplicate game
was created. The original isolated runtime fingerprint matched exactly and all
strict resume provenance checks passed. The launcher passed its quota preflight.
Models, pinned providers, Qwen BF16, blocklist, disabled fallbacks, reasoning,
output limits, harness, prompts and schemas remain unchanged.

A checkpoint preserves the prior save/database under
`checkpoint-before-resume-20260924T091618Z`. The launcher PID is 91381,
log `resume-3-launcher.log`; the external five-submission guard is restored.
The figures and timeout below describe the previous stopped checkpoint, not
the newly resumed segment. Live cumulative counts appear in REPORT.md.

## Latest outcome: six-hour session timeout in round eight

The second continuation stopped at **2026-09-23 23:42:15 UTC** with
`Game exceeded the 6-hour timeout`. The game is **unfinished, with no winner**.
The saved game is in round-eight planning. The latest recorded observation
shows **Luna/Baratheon 6 castles, DeepSeek/Lannister 4, Qwen/Stark 1**.
These are checkpoint scores, not final standings.

This stop was the launcher's time limit. It was not a funding rejection or
an intervention by the five-submission supervisor. DeepSeek and Qwen's active
planning attempts were cancelled when the session ended. No new game or manual
restart was launched, and the save and cumulative database remain intact.

### Cumulative accounting at this stop

- **147 decision attempts: 136 completed, nine failed, two cancelled.**
- **137 action submissions: 136 accepted and one schema-invalid submission**
  from DeepSeek/Morph, corrected on its second submission. No domain rejection
  or runaway submission loop was recorded.
- **488 returned responses with usage: 469 parent and 19 rules-oracle.**
  This count excludes requests that failed without returned usage and requests
  cancelled while in flight; it is not a count of every attempted HTTP request.
- **$3.129333290 reported cumulative inference cost:** Luna $0.482664335,
  DeepSeek $0.569987730, Qwen $2.076681225. Unreturned or interrupted request
  usage cannot be independently reconciled from these traces.
- SQLite `quick_check` returned `ok`. The current segment's
  **`runtimeUnchangedAtExit` is true**. The first segment's separate shared
  checkout drift qualification below remains applicable.
- Models, providers, BF16 precision, disabled fallbacks, blocklist, reasoning,
  output limits, harness, prompts and schemas were preserved.

Read-only generation metadata confirms all **488 returned responses** used the
pinned providers: **200 OpenAI, 117 Morph, 171 DeepInfra**. No fallback was
observed. The monitoring automation was removed after this terminal timeout
was identified; the game remains saved for an explicitly requested continuation.

### Failures and retries across all segments

The nine failed attempts comprise two Qwen HTTP 403 key-limit failures, two
DeepSeek HTTP 402 account-credit failures, two DeepSeek parent output-limit
failures, two DeepSeek connection errors, and one DeepSeek provider-stream
server error. The final two cancellations were caused by the session timeout.
The existing autoplay handled retries; monitoring made no compensating edits.

Additional issues include three rules-oracle output-limit failures (two Qwen,
one Luna), two incorrect area identifiers (one each Luna and Qwen), and the
DeepSeek/Morph schema violation documented below. The first-segment Qwen oracle
failure is captured in a partial response but omitted from the audit's explicit
tool-error list because its failed parent did not retain that tool exchange.

The later DeepSeek stream failure occurred in round-seven march run
`45b91266-1b48-4642-ab8a-6c7da64d694c`: the API reported `server_error`,
`stream closed with reason: error`. Autoplay subsequently progressed.
Round-eight planning run `6a71dafd-52b2-445c-ad08-0c2618b4d17d` exhausted
**40,960 output tokens**, returning `incomplete` / `max_output_tokens`.
Its retry was still active when the session timed out.

The schema-invalid action remains classified as a **provider-schema issue**;
no harness workaround was made. The five-submission guard never fired.

Earlier sections below preserve historical checkpoints and are superseded by
this latest outcome wherever they describe the game as running.

## Second continuation: resumed from the same round-four save

At the user's explicit request, the same game resumed again at **2026-09-23
17:42:13 UTC**. Funding checks returned approximately $19.89 account credits
and $7.18 remaining under the existing key limit. No limits were changed.

The original isolated runtime fingerprint was verified again, strict resume
provenance checks passed, and the save/database were checkpointed under
`checkpoint-before-resume-20260923T174212Z`. All models, routes, BF16 precision
for Qwen, reasoning/output settings, prompts and tool schemas remain unchanged.
The five-submission supervisor and ten-minute monitoring schedule were restored.

The account-credit stop and figures below are the **previous segment's outcome**,
not a claim that the newly resumed game has stopped or finished. Live cumulative
counts appear at the top of REPORT.md.

## Cumulative outcome: stopped again for account credits

The resumed game stopped at **2026-09-23 17:15:53 UTC**, during round-four
march resolution. **The game is unfinished; there is no winner.** The saved
position has **Luna/Baratheon 4 castles, DeepSeek/Lannister 4, Qwen/Stark 3**.

OpenRouter rejected DeepSeek's next request with HTTP 402. Its metadata explicitly
identifies `limit_source: openrouter_credits`: the available account credits
could cover 40,144 output tokens, below the unchanged 40,960-token request.
The existing autoplay retried once and received the same rejection, then stopped.
This differs from the first segment's HTTP 403 key-spending-limit failure.
Neither error is a schema failure. No further restart, provider substitution,
spending-limit change or reduction in output allowance was made by monitoring.

### Cumulative accounting and validation

- **64 decision attempts: 59 completed and five failed.** Failures comprise the
  two original Qwen HTTP 403 attempts, one DeepSeek output-limit failure, and
  the two final DeepSeek HTTP 402 attempts.
- **59 action submissions, all schema-valid and accepted first time.** No
  malformed tool JSON, exploration-schema violations or domain rejections were
  recorded. There was no action-schema repair loop.
- **219 returned responses with usage: 206 parent and 13 oracle**, plus four
  HTTP-rejected requests without returned usage. Thus 223 request outcomes are
  represented by the saved responses and terminal HTTP errors.
- **$1.4711403823 cumulative reported inference cost**: Luna $0.1598325700,
  DeepSeek $0.2162385873, Qwen $1.0950692250. This game's usage does not establish
  the account's total spending or explain other activity against its balance.
- Read-only generation metadata confirms all **219** returned responses: **76
  OpenAI, 55 Morph and 88 DeepInfra**, matching the pinned routes; no fallback
  provider was observed.
- SQLite `quick_check` returns `ok`. The same game save and cumulative traces
  are preserved in the experiment directory.
- The resumed segment's **`runtimeUnchangedAtExit` is true**. The original
  segment's separate source-integrity qualification remains documented below.
- The external five-submission guard did not fire. The one-game monitoring
  automation was removed after this terminal funding failure was identified.

### Additional observations in the resumed segment

1. DeepSeek exhausted the parent output allowance during round-four Raven order
   replacement (`01adb76c-9566-465e-866b-2eff53e86663`). Its response ended
   `incomplete` with `max_output_tokens`; the existing autoplay retried the
   decision and subsequently progressed. This is an output-limit failure,
   not a malformed action or schema retry.
2. Qwen used `mountains-of-the-moon` instead of the canonical
   `the-mountains-of-the-moon` in a neighbour lookup. This is a schema-valid
   but incorrect area identifier. It recovered and submitted an accepted action.
3. Qwen's round-four planning decision took about **64 minutes**, returning
   **15 responses** and making **31 tool calls including its one accepted
   submission**. The other 30 calls explored the map, cards and history.
   That decision alone reported **$0.351777225** and **74,935 output tokens**.
   This was prolonged deliberation, not rejected-action repair.
4. The first segment's two oracle output-limit failures and Luna area-ID error
   remain part of the cumulative record below. No production prompt, schema
   or harness adjustment was made to compensate for any of these issues.

## First segment: interrupted by the OpenRouter key limit

The section below preserves the first segment's outcome and accounting.
The cumulative outcome above supersedes its interim status.

The game stopped at **2026-09-23 13:32:23 UTC**, approximately two hours after
launch, during round-three planning. There is **no winner**. OpenRouter returned
HTTP 403 with `Key limit exceeded (total limit)` while Qwen was still deciding
its orders. The existing autoplay logic attempted the decision once more about
two seconds later and received the same 403, then the launcher stopped. No
manual restart, provider switch, limit increase or new game was performed.

At the stop, the recorded castle counts were **Luna/Baratheon 3,
DeepSeek/Lannister 4, Qwen/Stark 4**. These are an unfinished position, not final
standings. The game save and SQLite database are retained; SQLite `quick_check`
returns `ok`.

### First-segment accounting

- **30 attempts: 28 completed decisions and two failed attempts**, both Qwen HTTP 403 errors.
- **28 action submissions, all schema-valid and accepted on the first submission.** No action-schema repair loop occurred.
- All retained exploration-call arguments also validated against their respective parent/oracle schemas. No malformed tool JSON was recorded.
- **102 returned responses with usage: 93 parent and nine oracle.** These include successful exploration requests and output-incomplete oracle responses. The two HTTP 403 requests did not return response usage.
- **$0.6162830152 reported inference cost**: Luna $0.0617635750; DeepSeek $0.0664647402; Qwen $0.4880547000. This is this game's returned usage, not the account's total spending or an independently reconciled bill. The key-limit error does not establish what other activity consumed that limit.
- Read-only generation metadata confirms **OpenAI for all 32 Luna responses, Morph for all 26 DeepSeek responses, and DeepInfra for all 44 Qwen responses**. No provider fallback was used.

### Other observed issues

1. **Two oracle output-limit failures:** one under Luna and one under Qwen. Both nested agents retained the production 900-token output allowance. The Luna error was returned in a saved tool result. The Qwen error is visible in a captured `partial_model_response` with scope `rules-oracle`, status `incomplete` and reason `max_output_tokens`; its failing parent run did not retain the corresponding tool-output exchange. The main audit's explicit tool-error list therefore does not count that second oracle error.
2. **One semantic lookup error:** Luna supplied `king's-landing` to `check_neighbours`; the canonical ID is `kings-landing`. The argument satisfied the string schema, so this is an area-identifier error, not a schema-shape failure. Luna's eventual action was accepted first time.
3. **Very long deliberation:** Qwen's interrupted round-three planning attempt lasted **49.3 minutes**, with ten returned responses including nested oracle work, before the next request hit the key limit. Its last successful parent response alone took **17.2 minutes**, returning 11,730 output tokens. It had made no action submission in that attempt. Earlier Qwen planning and marching decisions also took many minutes. This was exploration/generation time, not a rejected-action loop.
4. **One additional request after the key-limit failure:** the unchanged autoplay logic retried once before stopping. This is recorded as an account-limit retry, not a schema retry. No further retries were launched by monitoring.

No provider-compatibility changes to production code, prompts or tool schemas
were made by this experiment. The external five-submission guard did not fire.

### Source-integrity qualification

`runtimeUnchangedAtExit` is **false**. Comparison with the startup source archive
found three source files changed on disk during the run:

- `src/raven_harness/harness/decision.py`
- `src/raven_harness/harness/decision_briefing.py`
- `src/raven_harness/harness/protocol_tools.py`

The current working tree also has changes in `pyproject.toml` and `uv.lock`,
which are included in the runtime fingerprint. These were not edits performed
by this experiment or its monitoring turns. The shared checkout changed while
the already-running process was active; the exit hash measures files on disk,
not a fresh fingerprint of Python objects already loaded into that process.
Do not describe this as a verified unchanged checkout or infer a hot reload
solely from the hash mismatch. The startup source archive and per-decision
schemas/inputs remain available. Source differences are recorded in
`data/evaluations/luna-deepseek-qwen-20260923/runtime-drift.json`.

### Funded continuation

The resumed segment uses the saved game, agents, memory and cumulative database.
Its runtime was restored into an isolated directory from `runtime-source.tar.gz`,
with `pyproject.toml` and `uv.lock` taken from the original recorded commit and
dependencies installed using `uv sync --frozen`. The restored runtime's complete
fingerprint matches the original exactly:
`07dcd8e8db81ecf1aa418fbfe0b0d45ca1fdb1401f9a8b97c80c2fcf398d6ae8`.
The unchanged launcher passed its resume checks for harness, rules, model
routing, evaluation settings and launcher provenance. No shared source files
were rolled back or changed, and no provider was substituted.

A checkpoint of the stopped game and database is preserved in
`data/evaluations/luna-deepseek-qwen-20260923/checkpoint-before-funded-resume/`.
Preparation details are in `funded-resume.json`; the manifest retains the prior
failed segment. The external five-submission guard was restarted, and scheduled
monitoring was restored to check every ten minutes and report completion or
actionable failures.


### Round-seven provider-schema violation

During the second continuation, DeepSeek through Morph produced the first
schema-invalid action of this experiment. Run
`ed8325e7-6c1d-48b1-9d29-db25064b9544` submitted a
`strategic_handoff` of **2201 characters**, exceeding the recorded offered
schema's `maxLength: 2000`. The existing validation rejected it. The next
submission shortened the handoff to **1299 characters** and was accepted.
This is a **provider-schema issue**, not a game-legality rejection. There were
two submissions in this decision; the five-submission guard did not fire.
No harness, prompt, schema, provider or settings changes were made. The game
continued. Earlier zero-schema-retry statements describe earlier checkpoints.
