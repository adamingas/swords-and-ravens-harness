# OSS blocked-march failure: confirmed harness bug

The original round-3 failure was enabled by incorrect legal guidance and an
incorrect `submit_action` destination enum. It cannot be treated as clean evidence
of poor model reasoning.

The server uses garrison `1000` as an impassable-area marker. The harness excluded
that value from ordinary neutral-force calculations, but failed to exclude the
area from march destinations. Consequently, Storm's End appeared in all three
places: the observation's legal destinations, the decision briefing's castle
targets, and the submission schema's destination enum. The server then rejected
the supposedly legal action. Repeated attempts eventually exhausted the
provider's response output allowance.

The fix filters blocked destinations before generating guidance and schemas,
marks blocked areas with `isBlocked` in board and neighbour observations, and
rejects blocked neutral-force attacks. A related contract bug also needed fixing:
the march split-size bound could overwrite `maxItems: 0` when no moves were legal.
The contract now preserves that bound and restores the forced empty march.

Validation on 2026-09-21:

- Ruff and all 232 tests passed, including the two real-server tests.
- Regression coverage checks ship transport to blocked Storm's End, rejection
  before any command is sent, continued availability of legal destinations, and
  a pass-only contract when direct destinations are all blocked.
- A live replay used an isolated copy of the failed board and complete private
  memory, with `openai/gpt-oss-120b` restricted to Cerebras, fallback disabled,
  reasoning high, and no harness output limit.
- The old Storm's End submission failed schema validation locally.
- The actual outgoing API schema matched the corrected contract on every parent
  request. The remaining destinations were Crackclaw Point and Kingswood.
- On the first decision attempt, OSS moved units 9 and 10 from Dragonstone to
  Crackclaw Point without spending a control token. The server accepted the
  command and advanced the authoritative state. It used three provider requests.

Replay run ID: `f3be3c56-2a3b-46e4-8890-584920bb75e7`.

Artifacts: `data/evaluations/oss-blocked-march-fix-20260921-v2/` contains
`replay.json`, `submit-action-schema.json`, `observation-before.json`,
`observation-after.json`, `model-trace.json`, the isolated SQLite database, and
the resulting game save. The original failed experiment is preserved unchanged.
This validates recovery of the stuck decision, not completion of the full game
or elimination of independent provider output-limit failures.
