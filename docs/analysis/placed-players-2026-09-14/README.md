# Did the second- and third-place players play well?

**Higher placement often concealed poor play.** These players made some successful early captures, but struggled to sustain expansion.

Across 11 completed games:

| Placement | Final victory points | Average net land gained |
| --- | --- | ---: |
| Second | 3–4 | +3.55 |
| Third | 2–3 | +1.64 |

I examined 116 decisions from three higher-placed players, verifying their original inputs against recorded hashes. References below identify runs in [evidence.json](evidence.json).

## What went wrong

- **Second-place GPT-OSS Martell:** overlooked an empty castle at the Reach (**D10**), confused order-placement locations with movement destinations (**D06**), and under-recruited because it imagined a power-token cost (**D21**). After combat and Wildling losses, it **finished with no units**, yet retained second place through controlled territory: three VP and six land areas.
- **Third-place GPT-OSS Greyjoy:** reached four VP, then ignored an uncontested fifth castle at White Harbor (**E20**). It skipped legal recruitment because it misunderstood supply (**E21**) and spent later turns shuffling ships between sea and port. It finished with **only two ships**, three VP, and three land areas.
- **Second-place Luna Greyjoy:** attempted contested expansion but **lost all six battles**. After losing its ships, it kept reinforcing Pyke without rebuilding transport, leaving three knights stranded on the island. Ship recruitment was explicitly available (**F11**). It finished with three VP and three land areas. Its traces contain no readable reasoning, so its motivation is uncertain.

## What to improve

The map and legal options were present. The models struggled to connect them to useful decisions. The harness should make these consequences clearer:

1. Separate order-placement regions from movement destinations.
2. Show available castle gains, control lost when leaving, and transport routes.
3. Explain recruitment costs and supply limits together.
4. Highlight isolated armies, enemy support, and repeated ineffective moves.

Measure retained territory and productive actions alongside placement. A March order can simply move ships back and forth; second place can survive the loss of an entire army.

These cases demonstrate avoidable mistakes, but proposed fixes still need controlled testing. There is no human baseline here.

[Full trace evidence](evidence.json) · [Reproduction script](extract_evidence.py) · [Earlier Stark investigation](../stark-expansion-2026-09-14/README.md)
