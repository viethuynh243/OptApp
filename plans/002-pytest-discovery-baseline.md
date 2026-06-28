# Plan 002: Make `pytest` collect every real test (establish a green verification baseline)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 0ec2135..HEAD -- tests/test_nsga2_mcoc.py tests/test_refine.py`
> If either file changed since this plan was written, compare the "Current
> state" excerpts against the live code before proceeding; on a mismatch,
> treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tests / dx
- **Planned at**: commit `0ec2135`, 2026-06-20

## Why this matters

`python -m pytest` currently collects **19 tests** — but two real test files,
`tests/test_nsga2_mcoc.py` and `tests/test_refine.py`, contribute **zero** of
them. Both define their assertions inside a `def main()` function instead of a
`def test_*()` function, so pytest never runs them. These two are the only
tests that exercise the end-to-end MCOC pipeline (writer → runner → parser →
optimizer) via the bundled `tests/mcoc_stub.py`, so the most important
integration path silently isn't part of the "green" signal. This plan makes the
default `pytest` run actually cover them, and adds a `pytest.ini` so collection
is explicit and stable.

## Current state

`python -m pytest --collect-only -q` lists 19 tests, all from:
`tests/test_cap_suggest.py`, `tests/test_ext.py`, `tests/test_model_ext.py`,
`tests/test_nsga2.py`. **Neither `test_nsga2_mcoc.py` nor `test_refine.py`
appears.**

**Clean-checkout baseline caveat (important for verification):** the full 19
pass ONLY when the untracked sample data in `mcoc_input_sample/*.txt` is present
on disk. That data was intentionally excluded from the repo for confidentiality
(`README.md:136`), so in a fresh clone/worktree two tests —
`tests/test_ext.py::test_writer_diameter` and `::test_orchestrator` — FAIL with
`FileNotFoundError` on `mcoc_input_sample/T3_EXT.txt`. The genuine committed
baseline is therefore **`17 passed, 2 failed`**, and those 2 failures are
pre-existing and out of scope here. The two tests this plan exposes
(`test_nsga2_mcoc`, `test_refine`) build their OWN input under `tests/_work/`
and use `tests/mcoc_stub.py`, so they do NOT need the confidential sample data
and WILL pass in a clean worktree.

`tests/test_nsga2_mcoc.py` ends like this:

```python
def main():
    """Chạy NSGA-II với evaluator MCOC thực (stub) ở chế độ EXACT và kiểm tra: ..."""
    print("=" * 60)
    ...
    build_input()
    params, loads, _ = parse_input_file(INPUT_FILE)
    assert params.get('original_coords'), "parser thieu original_coords"
    ...
    print("\n  TAT CA TEST DA PASS.")


if __name__ == "__main__":
    main()
```

`tests/test_refine.py` has the same shape: a `def main()` containing the
`assert`s, ending with `if __name__ == "__main__": main()`.

Both files:
- take no arguments and need no fixtures,
- set `params['exe_path'] = STUB` where `STUB = tests/mcoc_stub.py`, so they run
  WITHOUT the proprietary MCOC solver (CI-safe),
- create scratch files under `tests/_work/` (already gitignored via `*.txt`).

There is no `pytest.ini`, `conftest.py`, `pyproject.toml`, or `tox.ini` in the
repo, so pytest uses pure default discovery (`test_*.py` files, `test_*`
functions).

The 10 harness/utility scripts named with a leading underscore
(`tests/_review_all.py`, `tests/_drive_ui.py`, `tests/_smoke_full.py`,
`tests/_smoke_ext_ui.py`, `tests/_scenarios.py`, `tests/_test_cases.py`) and the
non-`test_` scripts (`tests/sweep_constraints.py`, `tests/validate_mcoc.py`,
`tests/validate_method.py`, `tests/gen_sample_test_plan.py`) are intentionally
NOT pytest tests (many need the real MCOC solver or do interactive/manual
work). They must stay uncollected — do not rename them.

## Commands you will need

| Purpose          | Command                                       | Expected on success |
|------------------|-----------------------------------------------|---------------------|
| Collect          | `python -m pytest --collect-only -q`          | lists test ids      |
| Run all          | `python -m pytest -q`                         | all pass            |
| Run the two new  | `python -m pytest -q tests/test_nsga2_mcoc.py tests/test_refine.py` | `2 passed` |
| Run a file direct| `python tests/test_refine.py`                 | prints `TAT CA PASS.` |

## Scope

**In scope** (the only files you should modify/create):
- `tests/test_nsga2_mcoc.py` — rename `main` → `test_nsga2_mcoc`, fix the
  `__main__` call
- `tests/test_refine.py` — rename `main` → `test_refine`, fix the `__main__` call
- `pytest.ini` (create)

**Out of scope** (do NOT touch):
- Any `tests/_*.py` harness script or `tests/{sweep_constraints,validate_mcoc,validate_method,gen_sample_test_plan}.py`
  — these are deliberately not unit tests (some require the real MCOC solver).
- `tests/mcoc_stub.py` — the stub is correct as-is.
- Any `core/`, `io_handlers/`, `ui/` source file — this is a test-wiring change only.

## Git workflow

- Branch: `advisor/002-pytest-discovery`
- One commit, message e.g. `Cho pytest thu thập test_nsga2_mcoc/test_refine + thêm pytest.ini`.
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Expose `tests/test_nsga2_mcoc.py` to pytest

Rename the function `def main():` to `def test_nsga2_mcoc():` (keep the body
unchanged). Update the bottom of the file so the script still runs standalone:

```python
def test_nsga2_mcoc():
    """Chạy NSGA-II với evaluator MCOC thực (stub) ở chế độ EXACT và kiểm tra: ..."""
    ...  # body unchanged


if __name__ == "__main__":
    test_nsga2_mcoc()
```

Do NOT change any assertion or the test body.

**Verify**: `python -m pytest -q tests/test_nsga2_mcoc.py` → `1 passed`.

### Step 2: Expose `tests/test_refine.py` to pytest

Same change: rename `def main():` to `def test_refine():`, leave the body
unchanged, and update the `__main__` block to call `test_refine()`.

**Verify**: `python -m pytest -q tests/test_refine.py` → `1 passed`.

### Step 3: Add an explicit `pytest.ini`

Create `pytest.ini` in the repo root to pin discovery and document the test
command:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -q
```

This restricts collection to `tests/` and to `test_*` files/functions, which
keeps the underscore-prefixed harness scripts out (they don't match
`python_files = test_*.py`).

**Verify**: `python -m pytest --collect-only -q | tail -5` shows the new
`test_nsga2_mcoc` and `test_refine` node ids and does NOT list any `_*.py`
harness file.

### Step 4: Confirm the suite grew by exactly 2 passing tests

The primary, data-independent check — the two newly-exposed tests pass:

**Verify**: `python -m pytest -q tests/test_nsga2_mcoc.py tests/test_refine.py`
→ `2 passed`.

Then the full suite. In a clean worktree (no confidential sample data) expect
**`19 passed, 2 failed`** — the 2 failures are the pre-existing, data-dependent
`test_ext.py` tests described in "Current state" (NOT caused by this change);
the 19 = the 17 that passed before + the 2 newly-collected stub tests. If you
happen to run where `mcoc_input_sample/*.txt` IS present, expect `21 passed`.

**Verify**: `python -m pytest -q` → `19 passed, 2 failed` (clean worktree) or
`21 passed` (data present). Confirm the ONLY failures are
`test_ext.py::test_writer_diameter` and `::test_orchestrator`; any other failure
is a STOP condition.

## Test plan

No brand-new test cases — this plan makes two existing, asserting tests
runnable by pytest. Verification:
- Each newly-exposed file passes individually (Steps 1–2).
- Full suite goes from 19 → 21 passing (Step 4).
- No `_*.py` harness script is collected (Step 3).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `pytest.ini` exists with `testpaths = tests` and `python_functions = test_*`
- [ ] `grep -n "def test_nsga2_mcoc" tests/test_nsga2_mcoc.py` returns a match
- [ ] `grep -n "def test_refine" tests/test_refine.py` returns a match
- [ ] `grep -n "def main" tests/test_nsga2_mcoc.py tests/test_refine.py` returns NO matches
- [ ] `python -m pytest -q tests/test_nsga2_mcoc.py tests/test_refine.py` → `2 passed`
- [ ] `python -m pytest -q` → `19 passed, 2 failed` (clean worktree; the 2 failures are ONLY `test_ext.py::test_writer_diameter` + `::test_orchestrator`) or `21 passed` if sample data is present
- [ ] `python -m pytest --collect-only -q` lists no `tests/_*.py` file
- [ ] `git status` shows only the two test files + `pytest.ini` changed/created
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Either renamed test FAILS when run under pytest (it passed as a script before
  — a failure means an environment/import difference; report the traceback, do
  not edit the test body to force a pass).
- The full suite shows failures OTHER than the two known data-dependent ones
  (`test_ext.py::test_writer_diameter`, `::test_orchestrator`) — report the
  actual count and which tests failed. (Do NOT treat those two as a STOP; they
  are pre-existing and by design, per "Current state".)
- Adding `pytest.ini` causes previously-passing tests to drop out of collection
  (report the before/after collect-only lists).

## Maintenance notes

- This is a prerequisite for Plan 004 (MCOC runner robustness), which adds a
  new `test_mcoc_runner.py`; that plan relies on `pytest` actually running the
  MCOC-path tests.
- A reviewer should confirm no harness script got swept into collection and
  that the two converted files still run standalone (`python tests/test_refine.py`).
- Follow-up deferred: wiring a CI workflow (e.g. GitHub Actions) to run
  `pytest` on push is a natural next step but is out of scope here.
