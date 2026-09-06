# GPT-OSS-120B house test

## Status

This experiment is in progress. One of five games is complete. Do not use one
game to estimate house strength.

## Method

All six players use the `strategic-v1` harness and the exact
`openai/gpt-oss-120b` model. Request routing permits only the Cerebras backend,
and backend fallback is off. The experiment uses the six-player base game. It
does not impose a round limit.

The runner starts one game at a time. Within a game, each agent has an
independent asynchronous autoplay task. The harness does not limit concurrent
model calls. A new game-server snapshot wakes each affected agent.

The source revision for game 1 is `b4279fb`. The experiment base seed is 102.
Game 1 uses derived seed 647336519. Its artifacts are in
`data/evaluations/gpt-oss-120b-house-test-b4279fb/game-01/attempt-01`.

## Game 1

Lannister won at the end of turn 10.

| Place | House | Victory points | Land areas |
| ---: | --- | ---: | ---: |
| 1 | Lannister | 5 | 8 |
| 2 | Martell | 3 | 6 |
| 3 | Greyjoy | 3 | 3 |
| 4 | Tyrell | 2 | 3 |
| 5 | Stark | 1 | 3 |
| 6 | Baratheon | 1 | 1 |

The game used 245 model requests, 3,224,890 input tokens, and 70,396 output
tokens. The recorded cost was $1.181509. The active runtime was 198.336 seconds.
This time excludes the interval when the harness process was stopped.

I stopped the process after 130.209 active seconds because the game exceeded
the two-minute investigation threshold without a winner. The saved game was at
turn 8. The same attempt resumed from the saved game and agent checkpoints and
then completed. One response reached its output-token limit after the resume.
The unchanged decision was retried and succeeded. The final attempt metrics
contain 232 completed agent runs, one failed run, and one run cancelled by the
manual stop.

## Latency investigation

The completed request intervals account for the active runtime as follows.

| Concurrent model requests | Wall time |
| ---: | ---: |
| 1 | 131.697 seconds |
| 2 | 9.399 seconds |
| 3 | 4.201 seconds |
| 4 | 3.841 seconds |
| 5 | 8.222 seconds |
| 6 | 11.630 seconds |
| 0, between requests | 24.459 seconds |

At least one model request was active for 168.990 seconds. The harness reached
six concurrent requests during simultaneous decisions. Most model time was
serial because the next legal decision depended on the result of the preceding
game action. The prior shared model semaphore and the 0.75-second autoplay poll
were not present in this run.

The request phases with the most accumulated model time were order placement
(98.435 seconds), bidding (55.443 seconds), and march resolution (54.853
seconds). Order placement and bidding permit concurrency. March resolution is
mostly sequential under the game rules.

The game did not meet the expected one-to-two-minute duration. The trace does
not show a remaining local concurrency queue or polling delay. Reducing the
runtime further requires faster model responses or fewer model-controlled game
decisions. Removing decisions would change the harness behavior and the model
comparison.

## Remaining work

Four more complete games are required. The final report must replace this
provisional interpretation with five-game house win-rate and placement
statistics.
