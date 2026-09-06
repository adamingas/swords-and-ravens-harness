# GPT-OSS-120B house test

## Status

This experiment is complete. All five games reached a winner without an
artificial round limit.

## Method

All six players use the `strategic-v1` harness and the exact
`openai/gpt-oss-120b` model. Request routing permits only the Cerebras backend,
and backend fallback is off. The experiment uses the six-player base game. It
does not impose a round limit.

The runner starts one game at a time. Within a game, each agent has an
independent asynchronous autoplay task. The harness does not limit concurrent
model calls. A new game-server snapshot wakes each affected agent.

The source revision for Game 1 is `b4279fb`. The source revision for Game 2 is
`11a7615`. The source revision for Game 3 is `446b444`. The source revision for
Game 4 is `7a08b11`. Game 5 records the documentation-only revision `b1b2424`
and has the same runtime fingerprint as Game 4. Each attempt stores its full
runtime provenance. The experiment base seed is 102. The five derived seeds
are 647336519, 2863619190, 2003516222, 629562040, and 3567110443. The artifact
root is
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

## Game 3

Greyjoy won at the end of turn 10.

| Place | House | Victory points | Land areas |
| ---: | --- | ---: | ---: |
| 1 | Greyjoy | 5 | 6 |
| 2 | Martell | 4 | 7 |
| 3 | Stark | 2 | 4 |
| 4 | Tyrell | 2 | 2 |
| 5 | Baratheon | 1 | 1 |
| 6 | Lannister | 0 | 0 |

The game completed in 245.046 seconds. It completed 234 agent runs and failed
two. Both failures were runaway responses that reached the 16,384-token output
limit. A fresh turn recovered each decision. There was no game-server, tool, or
oracle failure.

The metrics record 259 requests, 3,381,429 input tokens, 76,986 output tokens,
and $1.241240. The event trace contains 259 parent-model request starts and two
oracle requests, for 261 model-endpoint invocations. The metrics contain all
257 completed parent responses and both oracle responses. They omit only the
two incomplete terminal responses because the first terminal-capture fix
covered a different SDK request path. The recorded tokens and cost are lower
bounds. The corrected adapter now captures the non-streaming terminal response
object that this runner uses.

Across the first three games, 694 stored successful parent responses have a
maximum output of 1,216 tokens and a 99th percentile below 930 tokens. Games 1,
2, and 3 produced four runaway responses at the 16,384-token limit. Starting
with Game 4, the house-test runner uses a 4,096-token limit. This retains more
than three times the largest observed successful response and makes a runaway
generation fail sooner and at lower cost. The next fresh turn still retries the
unchanged game decision.

## Game 4

Lannister won at the end of turn 10.

| Place | House | Victory points | Land areas |
| ---: | --- | ---: | ---: |
| 1 | Lannister | 4 | 7 |
| 2 | Greyjoy | 3 | 4 |
| 3 | Stark | 3 | 4 |
| 4 | Tyrell | 2 | 5 |
| 5 | Martell | 2 | 3 |
| 6 | Baratheon | 1 | 2 |

The game completed in 213.333 seconds. All 274 agent runs completed. The run
made 294 model-endpoint requests. Every request start has a matching completed
response in the trace and in the metrics. There was no failed, cancelled,
oracle, tool, game-server, or terminal-response run.

The game used 3,863,113 input tokens and 80,939 output tokens. Its recorded cost
was $1.412794. The maximum response was 1,196 output tokens, so the new
4,096-token limit did not constrain a successful response.

## Game 5

Martell won at the end of turn 10.

| Place | House | Victory points | Land areas |
| ---: | --- | ---: | ---: |
| 1 | Martell | 5 | 9 |
| 2 | Lannister | 3 | 5 |
| 3 | Greyjoy | 3 | 4 |
| 4 | Stark | 2 | 4 |
| 5 | Tyrell | 2 | 3 |
| 6 | Baratheon | 1 | 1 |

The game completed in 301.654 seconds. It completed 301 agent runs and failed
one. The failed run reached the 4,096-token output limit after 4.146 seconds. A
fresh turn recovered the decision. The terminal response is present in the
metrics with its response ID, 12,268 input tokens, 4,096 output tokens, and
$0.007366 cost.

The game made 346 model-endpoint requests. The trace has 346 request starts,
345 normal completions, and one captured terminal response. All 346 usage
records are present. The game used 4,774,195 input tokens and 108,623 output
tokens. Its recorded cost was $1.752436.

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

Game 3 also reached six concurrent calls. Its 257 completed parent-model calls
had a mean duration of 1.211 seconds, a median of 1.090 seconds, a 95th
percentile of 1.877 seconds, and a maximum of 9.302 seconds. At least one
completed request was active for 204.821 seconds. The game had 36.672 seconds
between completed request intervals. Its largest accumulated request times were
order placement at 92.427 seconds, march resolution at 70.399 seconds, bidding
at 42.494 seconds, and mustering at 38.275 seconds.

Game 4 reached six concurrent calls for 18.482 seconds. Its 294 calls had a
mean duration of 1.188 seconds, a median of 1.084 seconds, a 95th percentile of
1.916 seconds, and a maximum of 2.831 seconds. At least one request was active
for 192.852 seconds. The game had 17.445 seconds between completed request
intervals.

Game 5 reached six concurrent calls for 16.493 seconds. Its 345 normal
completions had a mean duration of 1.184 seconds, a median of 1.085 seconds, a
95th percentile of 2.000 seconds, and a maximum of 2.773 seconds. At least one
normal request was active for 269.469 seconds. The game had 28.765 seconds
between normal request intervals. The incomplete request used another 4.146
seconds.

All five games exceeded the expected one-to-two-minute duration. The 1,218.588
seconds of active game time are 20 minutes and 18.588 seconds. The average was
243.718 seconds per game. The calls themselves were fast, but each complete
ten-turn game required hundreds of model decisions. Removing decisions would
change the harness behavior and the model comparison.

## Aggregate requests, failures, and cost

The five games made 1,452 model-endpoint requests. The aggregate metrics store
1,439 requests, 19,076,843 input tokens, 418,069 output tokens, and $6.990447.
This aggregate is a lower bound because Games 1 through 3 ran before terminal
accounting was complete. Their traces show 13 additional requests: eight
completed parent responses in Game 2 and five incomplete or cancelled terminal
responses across Games 1 through 3. The eight recoverable responses add
121,040 input tokens, 2,628 output tokens, and $0.044335. Therefore, the proven
minimum is 19,197,883 input tokens, 420,697 output tokens, and $7.034782. The
exact usage and cost of the five old terminal responses are not recoverable
from the saved data.

The games completed 1,306 agent runs. Six agent runs failed, and one was
cancelled during the deliberate Game 1 shutdown test. Five failures were
output-limit responses. One failure followed six repeated illegal march
attempts after the rules oracle gave an incorrect answer. Every failed or
cancelled decision resumed from the last durable boundary. All five games
reached a winner.

Games 4 and 5 used the final accounting code. Together they made 640 endpoint
requests, and all 640 have stored usage and cost. Game 5 also proves that an
incomplete terminal response is now counted.

## House statistics

| House | Wins | Win rate | Average place | Average victory points | Average land areas |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stark | 0 | 0% | 3.6 | 2.0 | 4.0 |
| Greyjoy | 1 | 20% | 3.0 | 3.0 | 3.6 |
| Lannister | 3 | 60% | 2.2 | 3.4 | 5.4 |
| Tyrell | 0 | 0% | 4.2 | 2.0 | 3.4 |
| Martell | 1 | 20% | 2.4 | 3.4 | 6.2 |
| Baratheon | 0 | 0% | 5.6 | 1.0 | 1.2 |

Lannister won three games. Greyjoy and Martell won one game each. Martell had
the best average land-area count at 6.2 and tied Lannister for the best average
victory-point count at 3.4. Martell also had the second-best average placement,
2.4, behind Lannister at 2.2.

## Interpretation

The result proves that the harness can run complete six-player games, issue
simultaneous model calls when the game permits them, persist game and agent
state, resume an interrupted game, recover individual failed decisions, and
retain usage for new failed terminal responses. It also shows that the model
endpoint is not the source of the four-to-five-minute game time: normal calls
usually finish in about one second, while the rules expose many decisions in
sequence.

Five games are a small sample. The Lannister result is evidence from this test,
not proof that Lannister is generally the strongest house. The mixed-model
tournament must rotate every model through every house so that house strength
does not become model strength.
