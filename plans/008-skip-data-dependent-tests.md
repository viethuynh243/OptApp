# Plan 008: Skip the two data-dependent `test_ext` tests when sample data is absent (green clean-checkout baseline)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan in
> `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 0ec2135..HEAD -- tests/test_ext.py`
> If `tests/test_ext.py` changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (independent of 001–007; touches only `tests/test_ext.py`)
- **Category**: tests / dx
- **Planned at**: commit `0ec2135`, 2026-06-20

## Why this matters

`python -m pytest` is not green on a fresh clone/CI: two tests in
`tests/test_ext.py` **fail** with `FileNotFoundError` because they read
`mcoc_input_sample/T3_EXT.txt`, which is intentionally untracked for
confidentiality (`README.md:136`; 0 of 38 sample `.txt` are git-tracked). A
failing test and an unrunnable-by-design test look identical in CI, so the suite
can't be used as a "does the codebase work?" signal. The fix is to **skip**
(not fail) those two tests when the sample file is absent — making a clean
checkout report `green (with skips)` while still running them fully in a
developer environment that has the data. This completes the green-baseline goal
that Plan 002 only partially achieved.

## Current state

`tests/test_ext.py` has 5 tests. Three need no external data
(`test_pile_section`, `test_diameter_table`, `test_cap_resize`). Two read the
confidential sample file via a module-level constant:

`tests/test_ext.py:34-35`:

```python
SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "mcoc_input_sample", "T3_EXT.txt")
```

`tests/test_ext.py:61-67` (`test_writer_diameter`) and `:100-102`
(`test_orchestrator`) both start by calling `parse_input_file(SAMPLE)`:

```python
def test_writer_diameter():
    """Round-trip patch duong kinh tren file MCOC mau that."""
    params, _, _ = parse_input_file(SAMPLE)
    ...

def test_orchestrator():
    """Quet duong kinh + R7/R8 + chon toan cuc + resize be (evaluator gia)."""
    params, loads, _ = parse_input_file(SAMPLE)
    ...
```

The file does **not** currently import `pytest`. It also has a standalone runner
at the bottom (`def main(): ... ; if __name__ == "__main__": main()`) that calls
all five tests directly — leave that runner as-is (developers who run the file
standalone have the sample data).

Empirically confirmed: on a clean checkout these are the **only** two failing
tests in the whole suite (verified by integrating all plans and running pytest
without the sample data → `2 failed`, both here). No other test file needs
`mcoc_input_sample/`.

## Commands you will need

| Purpose            | Command                                                  | Expected (clean worktree, no sample data) |
|--------------------|----------------------------------------------------------|-------------------------------------------|
| Baseline (before)  | `python -m pytest -q tests/test_ext.py`                  | `2 failed, 3 passed`                       |
| After (this file)  | `python -m pytest -q tests/test_ext.py`                  | `3 passed, 2 skipped`                      |
| Full suite (after) | `python -m pytest -q`                                    | `17 passed, 2 skipped` (no failures)       |
| Skip reasons shown | `python -m pytest -rs tests/test_ext.py`                 | lists 2 skipped with the reason            |

## Scope

**In scope** (the only file you should modify):
- `tests/test_ext.py` — add `import pytest` and a `skipif` marker on the two
  data-dependent tests.

**Out of scope** (do NOT touch):
- The other three tests in the file, the `SAMPLE` constant value, or the bodies
  of the two tests (only ADD a decorator above each).
- The standalone `def main()` runner at the bottom — leave it unchanged.
- `.gitignore` / `mcoc_input_sample/` — do NOT track or add the confidential
  sample data; skipping is the intended fix, not committing the data.
- Any other test file or any source module.

## Git workflow

- Branch: `advisor/008-skip-data-tests` (or commit on the reset HEAD — see Step 0
  below if you are in a fresh worktree based off the wrong branch).
- One commit, message e.g.
  `Bỏ qua (skip) 2 test_ext phụ thuộc dữ liệu mẫu khi thiếu file (CI xanh)`.
- Do NOT push or open a PR unless instructed.

### Step 0 (only if running in a fresh isolated worktree)
If your worktree may be based on the wrong branch, first run
`git reset --hard 0ec2135` and verify `git rev-parse --short HEAD` → `0ec2135`
and `ls tests/test_ext.py` exists. The clean baseline here is
`17 passed, 2 failed` for the full suite (the 2 failures are the tests this plan
fixes). If the base is wrong, STOP.

## Steps

### Step 1: Import pytest

Add `import pytest` to the imports near the top of `tests/test_ext.py` (after the
existing `import numpy as np` is fine).

**Verify**: `grep -n "^import pytest" tests/test_ext.py` → one match.

### Step 2: Add a shared skip condition and mark the two tests

After the `SAMPLE = ...` definition (line ~35), add a reusable marker:

```python
_needs_sample = pytest.mark.skipif(
    not os.path.exists(SAMPLE),
    reason="Thiếu dữ liệu mẫu bảo mật %s (không track trong repo) — bỏ qua." % SAMPLE,
)
```

Then place `@_needs_sample` immediately above `def test_writer_diameter():` and
above `def test_orchestrator():`. Do not change either test body.

**Verify**: `grep -n "@_needs_sample" tests/test_ext.py` → exactly 2 matches.

### Step 3: Confirm the two tests now skip (clean worktree) or still pass (data present)

**Verify (clean worktree, no sample data)**:
`python -m pytest -q tests/test_ext.py` → `3 passed, 2 skipped` (was `2 failed, 3 passed`).

If your environment HAS `mcoc_input_sample/T3_EXT.txt` present, instead expect
`5 passed` (the skip condition is false, tests run normally). Both outcomes are
correct — confirm which applies and report it.

### Step 4: Confirm the full suite has no failures

**Verify (clean worktree)**: `python -m pytest -q` → `17 passed, 2 skipped`
(zero failed). With sample data present: `19 passed`.

## Test plan

No new test cases — this plan changes how two existing tests behave when their
required data is missing (fail → skip). Verification is the count change:
- `tests/test_ext.py`: `2 failed, 3 passed` → `3 passed, 2 skipped` (clean) or
  `5 passed` (data present).
- Full suite: no `failed` line in a clean checkout.
- `python -m pytest -rs tests/test_ext.py` shows the skip reason text mentioning
  the missing sample file.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n "^import pytest" tests/test_ext.py` → one match
- [ ] `grep -c "@_needs_sample" tests/test_ext.py` → `2`
- [ ] `python -m pytest -q tests/test_ext.py` → `3 passed, 2 skipped` (clean
      worktree) OR `5 passed` (if sample data present) — and in NEITHER case any `failed`
- [ ] `python -m pytest -q` → no `failed` (i.e. `17 passed, 2 skipped` clean, or
      `19 passed` with data)
- [ ] `git diff tests/test_ext.py` shows only the import, the `_needs_sample`
      definition, and two decorator lines added (no test body changes)
- [ ] `git status` shows only `tests/test_ext.py` modified
- [ ] `plans/README.md` status row updated (unless a reviewer maintains it)

## STOP conditions

Stop and report back (do not improvise) if:

- `tests/test_ext.py` doesn't match the "Current state" excerpts (drift —
  re-read; line numbers may have moved, but the two `parse_input_file(SAMPLE)`
  call sites must exist).
- After the change a clean-worktree run still shows ANY `failed` test — there is
  a third data-dependent test the audit missed; report which one (`pytest -rf`).
- Adding `import pytest` or the marker breaks import/collection of the file
  (report the traceback).

## Maintenance notes

- If new tests are added that read files under `mcoc_input_sample/` (or any other
  untracked confidential data), they should reuse the `_needs_sample` marker (or
  an equivalent `skipif`) so a clean checkout / CI stays green.
- A reviewer should confirm the two tests still actually RUN (and pass) in a
  developer environment that has the sample data — skipping must be conditional,
  never unconditional.
- Follow-up (separate, optional): a CI workflow could provision a small
  non-confidential fixture so even CI exercises these two paths; out of scope here.
