# GPT-OSS-120B House Test

## Purpose

This test checks the first-round results for the six houses when every seat
uses the same model and harness. It removes differences between models from
the comparison.

The test does not prove that one house is stronger for a complete game. It has
only five samples, and each game stops after round 1. Use the results as a
short harness and opening-position check.

## Configuration

- Model for all 30 seats: `openai/gpt-oss-120b`.
- Harness for all 30 seats: `strategic-v1`.
- Harness source commit: `6713d20a9c9803110ec4c8a3be6e0b65415ff345`.
- Game-server source commit: `002978aa46343d7eb5e289c27d6e90752cdff041`.
- Players per game: 6.
- Games: 5.
- Maximum rounds per game: 1.
- Concurrent games: 5.
- Base random seed: 102. The runner derived one stable seed for each game.
- Requested backend: Cerebras, with fallback disabled.
- Artifact directory: `data/evaluations/gpt-oss-120b-house-bias-5x-v1`.

The runner called `raven_harness.evaluation.run_game()` once for each game.
Each call used the same six-seat model list, the same six-house list,
`max_rounds=1`, ports 5121 through 5125, and seeds derived with
`derive_game_seed(102, game_number)`. Each game used its own artifact directory
and `harness.db` file.

## Results

| Game | Seed | Winner | Time |
|---:|---:|---|---:|
| 1 | 647336519 | Greyjoy | 25.251 s |
| 2 | 2863619190 | Stark | 14.896 s |
| 3 | 2003516222 | Tyrell | 14.792 s |
| 4 | 629562040 | Lannister | 20.799 s |
| 5 | 3567110443 | Tyrell | 23.541 s |

The five games ran at the same time and finished in 25.289 seconds of wall
time. The average game time was 19.856 seconds, and the median was 20.799
seconds. The slowest game took 25.251 seconds. Every game finished within the
required one minute.

## House statistics

| House | Wins | Win rate | Average place | Average victory points | Average land areas |
|---|---:|---:|---:|---:|---:|
| Baratheon | 0 | 0% | 2.6 | 1.4 | 2.4 |
| Greyjoy | 1 | 20% | 4.6 | 1.2 | 2.2 |
| Lannister | 1 | 20% | 3.0 | 1.4 | 2.6 |
| Martell | 0 | 0% | 4.4 | 1.2 | 2.2 |
| Stark | 1 | 20% | 2.4 | 2.2 | 2.2 |
| Tyrell | 2 | 40% | 4.0 | 1.4 | 2.6 |

Tyrell won most often in this sample. Stark had the best average place and the
highest average victory-point count. These measures disagree because five
games are too few for stable estimates and the game uses several tie-breakers
at the forced end of round 1. The zero-win results for Baratheon and Martell
must not be treated as evidence that they cannot win.

## Requests, cost, and reliability

The harness recorded 61 decision runs: 60 completed runs and one failed run.
Some decision runs made an additional model request, so the total was 65 model
requests. The requests used 709,339 input tokens and 19,061 output tokens, for
728,400 total tokens. Of the input tokens, 90,112 were reported as cached. The
recorded cost was USD 0.262564.

The full model-request duration averaged 1,970 ms. The median was 1,510 ms,
the 90th percentile was 3,321 ms, and the maximum was 5,035 ms. A separate
post-game reporting lookup found all 65 response IDs. For this specific test,
all 65 records reported the exact model ID `openai/gpt-oss-120b` and the
Cerebras backend. The backend latency field averaged 506 ms, with a range from
191 ms to 1,300 ms.

The single failed decision run occurred in game 4 for Lannister. The model
returned prose without a game-action tool call for state
`0890b66c-3b3e-421d-8242-c370df6f3fb4`. The harness saved that failure and
retried the same state from the pre-call checkpoint with earlier history
removed. The retry called `resolve_march` and completed 1.53 seconds later.
No game state was lost, no duplicate action was sent, and the game completed.

## Interpretation

The test confirms that six identical GPT-OSS-120B agents can run in parallel,
that the recovery path handles an isolated no-action response, and that all
five game processes stop cleanly. It also confirms the one-minute performance
target for one-round games on the tested machine and endpoint.

A credible estimate of full-game house advantage needs more games without the
one-round limit. This five-game test is suitable as a pre-tournament harness
check, not as a final balance study.
