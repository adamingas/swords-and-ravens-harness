# Harness guide review record

This record shows how independent reviewers checked `HARNESS_GUIDE.md`. The
guide remains the stand-alone system description. This file records the review
method, findings, and corrections.

## Review basis

The reviewers inspected root commit `590a7ed` and the matching upstream commit
`12269cc`. They compared the guide with the Python source, model-visible tool
registries, API routes, state lifecycle, persistence layer, reconnect logic,
and dashboard.

Each reviewer inspected the source and guide independently and returned
evidence with exact file and line references.

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

## Continuing contract

`tests/test_documentation.py` derives the expected names from all four
model-visible registries: strategic gameplay, protocol gameplay, memory, and
the rules oracle. It derives documented names from the guide tables and support
tool headings. A tool addition, removal, or rename now fails the test until the
guide and source agree.
