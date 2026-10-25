# Tests

Run from the repository root:

```
python tests/run_tests.py            # all my tests (hand cases, witnesses, random, big inputs)
python tests/run_tests.py --quick    # without the big inputs
python tests/route_demo.py           # route helper calls with checks
python tools/run.py --input tests/my_cases.jsonl   # print raw outputs of my cases
```

- `cases.json` - inputs, expected answers and why they are correct
- `my_cases.jsonl` - the same inputs as JSON Lines
- `actual_outputs.jsonl` - actual outputs (rewritten by `run_tests.py`)
- `validators.py` - independent checkers for non-unique answers
