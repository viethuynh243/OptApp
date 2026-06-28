# Plan 006: Clarify that `core/optimizer.py` (Grid Search) is a test-only legacy baseline

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 0ec2135..HEAD -- core/optimizer.py tests/ run_demo.py`
> If any changed since this plan was written, re-verify the importer list in
> Step 1 before proceeding; on a mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt / docs
- **Planned at**: commit `0ec2135`, 2026-06-20

## Why this matters

`core/optimizer.py` (the original Grid Search optimizer, 204 lines) reads like a
production module but is **not used by the live application** — the UI and core
optimization path use `core/nsga2_optimizer.run_nsga2` exclusively. It is,
however, still imported by demos and tests as a reference/baseline, including by
`tests/test_model_ext.py`, which is a collected, passing test. So it is **not
dead code** — deleting it would break a real test. The right, low-risk move is to
*label* its true status (legacy Grid Search baseline, test/demo only) so future
readers and refactorers don't mistake it for a production path, and so nobody
wastes effort re-auditing it as "dead." This plan deliberately does NOT delete it.

## Current state

`core/optimizer.py` exposes exactly one public function:

```python
def run_optimization(params, loads):
```

Verified importers (grep over the repo, excluding `.claude/worktrees/`):

```
run_demo.py:26:                from core.optimizer import run_optimization
tests/sweep_constraints.py:36:  from core.optimizer import run_optimization
tests/test_model_ext.py:17:     from core.optimizer import run_optimization
tests/validate_mcoc.py:35:      from core.optimizer import run_optimization
tests/validate_method.py:24:    from core.optimizer import run_optimization
```

- **No** import from `ui/`, `main.py`, or any other `core/` / `io_handlers/`
  module. The production optimizer is `core/nsga2_optimizer.run_nsga2`
  (`ui/main_window.py:937,946`).
- `tests/test_model_ext.py` IS collected by pytest (it appears in
  `pytest --collect-only`), so it must keep working — this is why deletion is
  off the table.

Current module docstring of `core/optimizer.py` (line 1, read it to confirm
before editing — the header may already describe Grid Search; you are adding the
"superseded / test-only" status, not rewriting the algorithm description).

## Commands you will need

| Purpose            | Command                                                    | Expected |
|--------------------|-----------------------------------------------------------|----------|
| Confirm no prod use| `grep -rn "core.optimizer\|from core import optimizer" --include=*.py ui main.py core io_handlers \| grep -v nsga2` | no matches |
| List importers     | `grep -rln "from core.optimizer import" --include=*.py . \| grep -v worktrees` | the 5 files above |
| Import still works  | `python -c "from core.optimizer import run_optimization"` | exit 0   |
| Full suite         | `python -m pytest -q`                                      | all pass |

## Scope

**In scope** (the only files you should modify):
- `core/optimizer.py` — update the module docstring only (status banner).
- `plans/README.md` — status row (as for every plan).

**Out of scope** (do NOT touch):
- Do NOT delete `core/optimizer.py` or change `run_optimization`'s code/signature.
- Do NOT modify any test or `run_demo.py` (they legitimately use it as a baseline).
- Do NOT change `core/nsga2_optimizer.py`.
- The README "Cấu trúc" mention of `core/optimizer.py` may be adjusted by Plan
  003; do not edit README here.

## Git workflow

- Branch: `advisor/006-clarify-gridsearch`
- One commit, message e.g.
  `Ghi rõ core/optimizer.py là baseline Grid Search (chỉ dùng cho test/demo)`.
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Re-confirm `core/optimizer.py` is not used in production

Run:

```
grep -rn "core.optimizer" --include=*.py ui main.py core io_handlers | grep -v "nsga2"
```

Expected: **no matches** (the only `optimizer` the production code references is
`nsga2_optimizer`). If this returns a production import, STOP — the premise is
wrong (see STOP conditions).

**Verify**: command returns nothing.

### Step 2: Add a status banner to the module docstring

Prepend a clear status note to the top of `core/optimizer.py`'s module
docstring (keep any existing description below it):

```python
"""optimizer.py — Grid Search (QUÉT LƯỚI) — BASELINE LỊCH SỬ, CHỈ DÙNG CHO TEST/DEMO.

⚠️ KHÔNG dùng trong ứng dụng thật. Đường tối ưu sản phẩm là
   core/nsga2_optimizer.run_nsga2 (xem ui/main_window.py). Module này được giữ
   lại làm phương án ĐỐI CHỨNG cho:
       - tests/test_model_ext.py, tests/sweep_constraints.py,
         tests/validate_mcoc.py, tests/validate_method.py
       - run_demo.py
   Đừng xóa khi các test/demo trên còn phụ thuộc; nếu muốn gỡ, hãy chuyển các
   phụ thuộc đó sang run_nsga2 trước.

<giữ nguyên phần mô tả cũ của module ở đây, nếu có>
"""
```

Do not change any code below the docstring.

**Verify**: `python -c "from core.optimizer import run_optimization"` → exit 0.

### Step 3: Confirm tests still pass

**Verify**: `python -m pytest -q` → all pass (unchanged count; `test_model_ext`
still imports and runs `run_optimization`).

## Test plan

No new tests. This is a documentation-in-code change. Verification:
- The module still imports (Step 2).
- The full pytest suite is unchanged and green (Step 3).
- `git diff core/optimizer.py` shows ONLY docstring lines changed (no code).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n "BASELINE\|test/demo\|CHỈ DÙNG" core/optimizer.py` returns a match
- [ ] `git diff core/optimizer.py` touches only the docstring (no lines below it)
- [ ] `python -c "from core.optimizer import run_optimization"` exits 0
- [ ] `python -m pytest -q` passes with the same count as before
- [ ] `git status` shows only `core/optimizer.py` modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Step 1 finds a production (`ui/`, `main.py`, non-test `core/`) import of
  `core.optimizer` — the "test-only" premise is false; report where it's used.
- Removing or editing the docstring breaks import (syntax error in the triple-
  quoted string).

## Maintenance notes

- If someone later wants to actually delete `core/optimizer.py`, the blocker is
  the five importers listed in the banner — port `tests/test_model_ext.py` (and
  the harness scripts / `run_demo.py`) off `run_optimization` first, then delete.
- A reviewer should confirm no code below the docstring changed.
