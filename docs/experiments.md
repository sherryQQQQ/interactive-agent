# Running controlled experiments

Start with `interactive-agent catalog` and `interactive-agent plan information-gain`.
These commands, the synthetic demo and paired scoring require no external data.

## External inputs

MediQ adapters require the separately obtained `all_dev_good.jsonl` source and
the MedRAG Textbooks SQLite FTS5 index. Neither data nor checkpoints ship here.
Respect upstream terms; never commit patient records, raw provider responses or
credentials. Frozen selections are in `graphrag/eval/specs`. The stage archive
contains historical corpus-preparation commands.

Use an editable checkout and inspect each adapter's options:

```bash
interactive-agent experiment handoff -- --help
interactive-agent experiment compaction -- --help
interactive-agent experiment information-gain -- --help
interactive-agent experiment information-gain -- --set dev --source /data/all_dev_good.jsonl --index /data/textbooks.sqlite --dry-run
```

Only `--execute` authorizes new calls. Inspect the dry-run first. `--reuse-only`
never fills missing checkpoints with new provider calls. It requires matching
data, model, prompts and checkpoint. Historical adapters may record missing
calls as failures; fairness-v2 IG stops. Distractors do not yet expose supported
replay through the public CLI.

## Information-gain amendment: fairness-v2

New checkpoint filenames prevent mixing corrected behavior with earlier calls.
Every arm receives a fresh instance of the same patient simulator. Oracle probes
use independent patient copies. Freeform processes the final patient answer
before diagnosis. Frozen case IDs are unchanged.

With three questions and three candidates, full-question no-retry cost planning
uses 43 calls/case: dev20 = 860 calls, holdout40 = 1,720 calls. At an illustrative
$0.0015/call these are $1.29 and $2.58. These are not provider quotes or upper
bounds: retries and token lengths change cost. Inspect guards and cumulative
spending before authorization. Offline fixes establish no new paid results.

## Paired scoring

`interactive-agent compare records.json --baseline transcript --candidate handoff`
accepts a JSON array:

```json
[
  {"case_id":"synthetic-1","arm":"transcript","correct":false,"valid":true},
  {"case_id":"synthetic-1","arm":"handoff","correct":true,"valid":true}
]
```

This toy schema is not experimental evidence. Duplicate records and unmatched
case sets are rejected. Output includes Wilson intervals, exact paired McNemar,
wins/losses, validity and selective accuracy. Retain failed attempts in the
primary denominator; report exclusions separately. Existing adapters supply
richer latency/token traces; the generic scorer does not infer missing telemetry.
