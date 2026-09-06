# Harness guide review record

This record shows how independent reviewers checked `HARNESS_GUIDE.md`. The
guide remains the stand-alone system description. This file records the review
method, findings, and corrections.

## Initial review basis

The reviewers inspected root commit `590a7ed` and the matching upstream commit
`12269cc`. They compared the guide with the Python source, model-visible tool
registries, API routes, state lifecycle, persistence layer, reconnect logic,
and dashboard.

Each reviewer inspected the source and guide independently and returned
evidence with exact file and line references.

The current review used root commit `6a7e5bb`, upstream commit `1a1c4434`, and
the exact proposed changes that became root commit `fdda17d`. Independent Sol
and Luna reviewers compared those changes with the source, tests, saved trace
evidence, API behavior, and dashboard code. Neither reviewer used Terra.

## Reviewer 1: documentation and operator view

This reviewer checked the complete guide against the source and counted every
model-visible tool. The guide contained all 27 tools. The reviewer found these
other problems:

- The reconnect text did not say that rejected authentication ends retry.
- The event metadata list omitted the model, phase, tool list, item counts, and
  occurrence time.
- The privacy paragraph used raw field names and long passive sentences.
- The dashboard repeatedly announced the complete agent grid to screen
  readers.
- The dialogs and tabs did not have complete accessible names and keyboard
  behavior.
- Poll failures left a stale ready status.
- One narrow viewport range could overflow, and the activity pulse did not
  respect reduced-motion settings.

Commit `a62ee71` corrects these findings. Browser-based visual verification is
still required because the in-app browser was not available during this review.

## Reviewer 2: lifecycle and completion

This reviewer traced each roadmap requirement to source, tests, artifacts, and
guide sections. The reviewer confirmed that the guide explains the rules
oracle, current-state replacement, context history, all tool groups, trace
fields, reconnect behavior, and the same-model evaluation. The reviewer found
these missing assumptions or weak claims:

- The guide did not have a reproducible source-to-tool-catalog check.
- The deterministic server smoke covered only planning and Raven skip actions.
- `submit_orders` is a multi-message action and cannot guarantee rollback after
  an ambiguous connection failure.
- Lobby launch and automatic ready events prove a send, not server completion.
- A built wheel did not contain the dashboard assets.

The review added an automated tool-catalog contract in
`tests/test_documentation.py`. The dashboard assets now live inside the Python
package. `tests/test_packaging.py` builds and installs a wheel in isolation,
then verifies the dashboard and writable data paths. Lobby launch and ready
responses now use fresh authoritative snapshots. Planning submission now uses
one server-validated request and a private correlated response. The
provider-free real-server smoke runs two rounds and saves its actual tool
coverage. It also checks atomic rejection and planning-order privacy through
two player-scoped snapshots.

## Reviewer 3: canonical implementation

This reviewer searched for compatibility paths, unsupported variants, repeated
work, loose interfaces, and unused code. The review found that unsupported
lobby variants could pass API validation, missing game settings enabled tools,
turn preparation derived the same legal actions several times, and the
evaluator silently upgraded one legacy manifest shape.

Commits `e6b5bea` and `4b81262` make these paths fail closed. They restrict the
lobby to the supported six-player base game, require the setup and player count
in authoritative snapshots, remove the legacy manifest upgrade, replace loose
turn metadata with required fields, and derive legal actions once per decision.
The real TypeScript server omits false and default-valued settings, so the
harness normalizes only those documented serializer defaults before it checks
the lobby response.

## Reviewer 4: saved state and evidence

This reviewer checked the saved-state dashboard design and the evidence for the
rules oracle. The first proposed implementation could combine an old in-memory
observation with a different stored snapshot after a connection failure. It
could also report the wrong game-owner status. The evidence report contained
correct counts, but its first SQL example selected unrelated failed runs and
did not explain player pseudonyms.

Commit `fdda17d` makes every non-live monitor view use one complete stored
snapshot. It adds `stateStatus.actionable`, which is false for saved state. It
also adds a reconnecting-session test. The tracked evidence JSON now contains
the seven sanitized source rows. The report contains the exact SQL filter and
the deterministic pseudonym procedure. A test checks the evidence categories
and counts.

The same review found that the guide listed an old provider order. The guide,
configuration, README, and environment example now put Reka first. A test
derives that sentence from the configured default. The reviewer found no
remaining medium- or high-severity issue after these corrections.

## Reviewer 5: dashboard and tracing

This reviewer checked the saved-state user interface and OpenTelemetry proof.
The dashboard labels a stopped agent's state as saved and does not highlight an
old required decision as actionable. The Available tools tab now tells the
operator to reconnect instead of presenting an empty saved-state tool list as
current legality.

The review requested tests for successful and failed decision spans. The tests
now use an in-memory OpenTelemetry exporter. They verify agent, game, model,
run, action, token, cost, and failure-status data. Decision spans now include
sanitized model-run, provider-request, and tool lifecycle events. They do not
include prompts, observations, tool arguments, tool results, or credentials.
The reviewer found no high-severity issue.

The in-app browser still could not initialize for this revision. Automated
desktop and narrow-width visual verification remains incomplete. Static
JavaScript checks, API tests, and responsive-source review passed.

## Reviewer 6: deterministic evaluation seeds

An independent Sol reviewer checked root commit `7377514` and upstream commit
`99f68768`. The manifest, verifier, per-game seed derivation, retry reuse,
same-model enforcement, provider fallback, and private-save exclusion were
consistent. The reviewer found that two presentation paths still consumed the
seeded gameplay stream: the Westeros deck broadcast and Iron Bank client
serialization. A follow-up source audit found the same issue in the Iron Bank
update broadcast.

Upstream commit `1f5e9671` sends all three concealment-only shuffles through
the secure random source. Gameplay shuffles remain on the seeded stream. The
reviewer used Sol, not Terra.

## Continuing contract

`tests/test_documentation.py` derives the expected names from all four
model-visible registries: strategic gameplay, protocol gameplay, memory, and
the rules oracle. It derives documented names from the guide tables and support
tool headings. A tool addition, removal, or rename now fails the test until the
guide and source agree.
