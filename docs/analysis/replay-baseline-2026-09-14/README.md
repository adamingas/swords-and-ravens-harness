# Historical decision replays

**Current ten-case test set:** [selection and new replay results](TEST_SET.md)
· [runnable manifest](test-set.json). The original screening results follow.

**Five decisions repeated exactly, four changed, and GLM was blocked by its
original provider's rate limit on both attempts.** The action-equality assertion
failed, while all ten reconstructed SDK inputs passed their historical hashes.

| # | Player / round | Replay result |
|---|---|---|
| 1 | OSS Stark / 1 | Changed Karhold destination to Winterfell; still abandoned White Harbor without a token. |
| 2 | OSS Stark / 5 | Exact same orders: no marches, two sea consolidations. |
| 3 | OSS Stark / 7 | Discarded the march instead of reinforcing Castle Black; still missed White Harbor. |
| 4 | OSS Stark / 10 | Exact same abandonment of Moat Cailin. |
| 5 | GLM Stark / 9 | Novita returned HTTP 429 twice; no decision obtained. |
| 6 | OSS Martell / 3 | Exact same return to Storm's End, missing the Reach. |
| 7 | OSS Martell / 7 | Recruited at three origins instead of only upgrading at Sunspear. |
| 8 | OSS Greyjoy / 6 | Exact same reinforcement of Greywater Watch, missing White Harbor. |
| 9 | OSS Greyjoy / 7 | Mustered a footman and ship instead of skipping. |
| 10 | DeepSeek Martell / 3 | Exact same discarded march, missing Starfall. |

Used `StrategicHarness.run_turn` → `OpenAIAgentRunner.run_once`, restoring the
historical observation prefix, selected conversation history, instructions,
tool schemas, model ID and recorded provider/generation settings. Assertions
checked full SDK input hashes before HTTP and tool schemas in outgoing bodies.
The current context filter was overridden locally in the replay process.

This compares **requested tool names and parsed arguments**, stopping before
tool execution. It does not replay server acceptance or action normalization.
GLM's original requested move and its normalized empty march are kept separate.

The offline control fed all ten original responses through the same replay path:
**10/10 matched**. Two additional tests confirmed that input corruption blocks
HTTP and changed decisions fail equality. All 12 tests passed.

Different live decisions alone do **not** demonstrate faulty storage or harness
code. No seed or temperature was pinned. Historical HTTP bodies were not saved;
the complete provider request cannot be independently certified byte-for-byte.
DeepSeek's reported input tokens changed from 15,706 to 16,457 despite matching
SDK input hashes and the same reported model/provider. All eight OSS input-token
counts matched. Provider-side processing remains an uncontrolled variable.

Recorded live cost: **$0.04576**. Current SDKs: OpenAI 3.8.0, Agents 0.22.0.

[Results and exact operation comparisons](results/summary.json) ·
[GLM retry](results-retry-1/summary.json) · [Replay script](replay.py)

```sh
# Validate stored inputs without calling models:
.venv/bin/python docs/analysis/replay-baseline-2026-09-14/replay.py
# Offline controls:
.venv/bin/pytest -q docs/analysis/replay-baseline-2026-09-14/test_replay.py
# New paid replay; requires a fresh output directory:
.venv/bin/python docs/analysis/replay-baseline-2026-09-14/replay.py --live --output tmp/new-baseline-replay
```
