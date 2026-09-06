# GPT-OSS-120B house test

## Status

This experiment is in progress. Two of five games are complete. Do not use two
games to estimate house strength.

## Method

All six players use the `strategic-v1` harness and the exact
`openai/gpt-oss-120b` model. Request routing permits only the Cerebras backend,
and backend fallback is off. The experiment uses the six-player base game. It
does not impose a round limit.

The runner starts one game at a time. Within a game, each agent has an
independent asynchronous autoplay task. The harness does not limit concurrent
model calls. A new game-server snapshot wakes each affected agent.

The source revision for Game 1 is `b4279fb`. The source revision for Game 2 is
`11a7615`. Each attempt stores its full runtime provenance. The experiment base
seed is 102. Game 1 uses derived seed 647336519. Game 2 uses derived seed
2863619190. The artifact root is
`data/evaluations/gpt-oss-120b-house-test-b4279fb`.

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

The old metrics code recorded 245 model requests, 3,224,890 input tokens, and
70,396 output tokens. The recorded cost was $1.181509. The active runtime was
198.336 seconds. This time excludes the interval when the harness process was
stopped.

I stopped the process after 130.209 active seconds because the game exceeded
the two-minute investigation threshold without a winner. The saved game was at
turn 8. The same attempt resumed from the saved game and agent checkpoints and
then completed. One response reached its output-token limit after the resume.
The unchanged decision was retried and succeeded. The final attempt metrics
contain 232 completed agent runs, one failed run, and one run cancelled by the
manual stop.

The event trace contains 244 parent-model request starts and 242 completed
parent-model responses. Three oracle responses are also stored. Therefore, the
game invoked the model endpoint 247 times. The old failed-turn accounting
omitted the usage of the incomplete request and the request that was active
during manual shutdown. The recorded tokens and cost are lower bounds.

## Game 2

Lannister won at the end of turn 10.

| Place | House | Victory points | Land areas |
| ---: | --- | ---: | ---: |
| 1 | Lannister | 5 | 7 |
| 2 | Martell | 3 | 6 |
| 3 | Stark | 2 | 5 |
| 4 | Tyrell | 2 | 4 |
| 5 | Baratheon | 1 | 1 |
| 6 | Greyjoy | 1 | 1 |

The game completed in one uninterrupted process segment. The active runtime
was 260.219 seconds. It completed 265 agent runs and failed two agent runs. A
fresh turn recovered from each failure and the game continued to a winner.

The first failed run spent six model turns on the same illegal march. The model
tried to move a Ship unit from Shipbreaker Bay to Blackwater Bay. The rules
oracle incorrectly approved that move although the section it read says that
Ship units cannot move by ship transport. The oracle instructions now require
it to check prohibitions, to treat facts in a question as unverified, and to
separate rules from current board facts.

The second failed run made two completed parent-model requests and two oracle
requests. Its third parent-model response then reached the output-token limit.
A fresh run completed the decision.

The old metrics code recorded 295 requests, 3,833,216 input tokens, 81,125
output tokens, and $1.402469. The event trace proves 298 parent-model request
starts and six oracle requests, for 304 model-endpoint invocations. Eight
completed parent responses inside the two failed runs were absent from the old
metrics. Those eight responses add 121,040 input tokens, 2,628 output tokens,
and $0.044335 at the price reported for the other responses. The final
incomplete response is also absent, and its exact usage is not recoverable from
the saved run. Therefore, Game 2 used at least 3,954,256 input tokens, 83,753
output tokens, and $1.446804. The failed-turn accounting now retains completed
and terminal Responses API payloads for subsequent games.

## Latency investigation

For Game 1, the completed request intervals account for the active runtime as
follows.

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

Game 2 confirms the same result. Its 297 completed parent-model calls had a
mean duration of 1.163 seconds, a median of 1.066 seconds, a 95th percentile of
1.976 seconds, and a maximum of 2.443 seconds. At least one request was active
for 223.218 seconds. The completed request intervals had these concurrency
levels:

| Concurrent model requests | Wall time |
| ---: | ---: |
| 1 | 184.847 seconds |
| 2 | 10.982 seconds |
| 3 | 4.937 seconds |
| 4 | 1.861 seconds |
| 5 | 6.905 seconds |
| 6 | 13.686 seconds |
| 0, between requests | 33.791 seconds |

The longest accumulated request times were order placement at 101.066 seconds,
march resolution at 79.990 seconds, bidding at 50.622 seconds, and mustering at
38.354 seconds. Simultaneous decisions did run concurrently. Most wall time was
in decisions that the game rules expose one after another. The trace does not
show a harness-side concurrency limit or a polling delay.

Both games exceeded the expected one-to-two-minute duration. The calls
themselves were fast, but a complete ten-turn game required hundreds of model
decisions. Removing decisions would change the harness behavior and the model
comparison.

## Provisional house statistics

| House | Wins | Win rate | Average place | Average victory points | Average land areas |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stark | 0 | 0% | 4.0 | 1.5 | 4.0 |
| Greyjoy | 0 | 0% | 4.5 | 2.0 | 2.0 |
| Lannister | 2 | 100% | 1.0 | 5.0 | 7.5 |
| Tyrell | 0 | 0% | 4.0 | 2.0 | 3.5 |
| Martell | 0 | 0% | 2.0 | 3.0 | 6.0 |
| Baratheon | 0 | 0% | 5.5 | 1.0 | 1.0 |

These values are descriptive only. Two games are not enough to make a claim
about house balance.

## Remaining work

Three more complete games are required. The final report must replace this
provisional interpretation with five-game house win-rate and placement
statistics.
