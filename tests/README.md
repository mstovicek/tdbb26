# Tests

No dependencies: Python's `unittest` and Node's built-in test runner.

```
python3 -m unittest discover -s tests/python     # validate.py, summary.py, embed.py, the real data, the cross-check
node --test tests/js/                            # the page, run against a stand-in for the browser
```

- `tests/python/` tests the scripts as subprocesses, the way you run them. `test_real_data.py` validates the real `data/`.
- `tests/js/` runs the real `index.html` script with data embedded and checks what it renders (`harness.mjs`).
- `tests/python/test_crosscheck.py` runs the same data through `summary.py` and the page and compares every rank and
  score as text. Scores are rounded half up to two decimals in both.
- **Test data is built inside the tests** (temporary folders, `tests/js/fixtures.mjs`). Never add fake ratings to `data/`.
- CI runs both on every push to `master` and on pull requests (`.github/workflows/tests.yml`).
