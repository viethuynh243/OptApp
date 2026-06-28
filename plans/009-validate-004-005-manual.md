# Plan 009: Validate plan 004 against the REAL MCOC solver and smoke-test plan 005 in the GUI

> **Executor instructions**: This is a **MANUAL validation plan for a human**
> with (a) the proprietary `MCOC Batch` solver installed and (b) a desktop with
> the Tkinter GUI. It CANNOT be run by a headless executor subagent — the real
> MCOC binary is not in the repo, and the validation is behavioral (GUI + real
> solver), not a code change. Do every check, record the actual observed result
> next to each box, and if a ⛔ STOP appears, halt and report.

## Status

- **Priority**: P1 (gate before relying on plan 004 in production)
- **Effort**: S (≈1 hour with MCOC + GUI available)
- **Risk**: LOW (validation only — no code changes; but it GATES a MED-risk change)
- **Depends on**: plans 004 (`20393af`) and 005 (`ce47461`) integrated/merged into
  the branch under test (or checked out in a worktree that has both)
- **Category**: tests / verification
- **Planned at**: commit `0ec2135`, 2026-06-20

## Why this matters

Plans 004 and 005 were verified only structurally — 004 against the Python
**stub** (`tests/mcoc_stub.py`), 005 by import/AST/grep (the test suite never
loads the GUI). Two residual risks remain that only a real run can settle:

1. **004 could over-reject.** The new guard raises `MCOCError` whenever the MCOC
   subprocess exits non-zero. Some engineering CLIs return a non-zero code on
   *success-with-warnings*. If the real `MCOC Batch` ever does that, plan 004
   turns a previously-working optimization into a hard failure. The stub always
   exits 0, so this was untestable in CI.
2. **005 changed live UI control flow.** It replaced three inline validation
   blocks with one `_validate_mcoc_setup()` helper and *tightened*
   `run_refine_real` (now requires the exe to exist on disk, not just be
   non-empty). No automated test exercises the GUI, so the warning dialogs and
   the three run paths are behaviorally unverified.

## Current state (what changed, for context)

- 004 — `core/mcoc_runner.py`, `MCOCRunner.run()`, immediately after the
  `subprocess.run(...)` try/except:
  ```python
  if proc.returncode != 0:
      tail = (proc.stdout or "")[-400:] + (proc.stderr or "")[-400:]
      raise MCOCError("MCOC ket thuc voi ma loi %d cho %s.\nOutput cuoi:\n%s"
                      % (proc.returncode, base, tail))
  ```
  Plus `core/blackbox.py` `evaluate_layout` now returns
  `(None, "Loi goi MCOC (%s): %s" % (type(e).__name__, e))` on failure.
- 005 — `ui/main_window.py` has a new `_validate_mcoc_setup()` called by
  `run_optimize`, `run_optimize_ext`, and `run_refine_real` (the last now also
  checks `os.path.exists(exe)`).

## Preparation

1. Check out a tree that contains BOTH plan 004 and plan 005 (e.g. after the
   `plans/README.md` cherry-pick sequence is applied to `feature/toiuu-mo-rong`).
2. `pip install -r requirements.txt` (per plan 001).
3. Have a known-good MCOC input file (`.txt` with original pile coords) and the
   `MCOC Batch` executable path ready. Have the sample/working data you normally
   use.

## Part A — Validate plan 004 against real MCOC

### A1. Normal run still succeeds (the over-rejection risk)
- [ ] Launch: `python main.py`. Configure the real `MCOC Batch` path, open a
      valid MCOC input file, enter valid params + at least one load combo, and
      run **► CHẠY TỐI ƯU HÓA** (standard NSGA-II path).
- [ ] **Expected**: the optimization completes and shows results, exactly as
      before plan 004. Record: did it complete? ____
- ⛔ **STOP** if the run now fails with "MCOC ket thuc voi ma loi N" on inputs
      that worked before plan 004. That means the real solver returns a non-zero
      code on success — plan 004's guard is too strict. Report the exit code `N`
      and the tail text; the fix is to treat that specific non-zero code as
      success (or to require BOTH non-zero exit AND no result file before
      raising). Do not edit code here — report back so the plan can be revised.

### A2. Confirm the guard catches a genuine failure
- [ ] Point the app at a deliberately invalid MCOC input (or a path that makes
      MCOC error out) and run.
- [ ] **Expected**: a clear error surfaces in the log — message contains
      "MCOC ket thuc voi ma loi" (from `mcoc_runner`) or "Loi goi MCOC (...)"
      (from `blackbox`), not a silent wrong number or a cryptic crash. Record the
      message shown: ____
- [ ] **Expected**: the app does NOT report a successful/optimized result from a
      failed solver run.

### A3. (If you can) characterize the real solver's exit codes
- [ ] Note whether `MCOC Batch` is known to ever return non-zero on
      success-with-warnings. If yes, record the code(s) — this directly informs
      whether A1's STOP applies and what the tolerated set should be.

## Part B — Smoke-test plan 005 (UI validation helper)

For each of the three run paths, with MCOC **NOT** configured (clear the exe
path), confirm the warning appears and the run is blocked:

- [ ] **Standard** (`► CHẠY TỐI ƯU HÓA`, ext toggle OFF) → warning
      "Cần cấu hình MCOC"; run is blocked. Record: ____
- [ ] **Extended** (ext toggle ON, then run) → same "Cần cấu hình MCOC" warning;
      blocked. Record: ____
- [ ] **Refine** (the MCOC-thực / tinh chỉnh path) → warning appears; blocked.
      (Note: 005 *tightened* this path — a non-existent exe path that previously
      slipped through should now be caught.) Record: ____

Then, with MCOC and a valid input file properly configured:

- [ ] Each of the three paths proceeds past validation (no false warning) and
      starts running. Record any path that wrongly warns: ____
- [ ] Missing-file case: configure a valid exe but no input file → "Thiếu file
      MCOC gốc" warning; blocked.

## Done criteria

- [ ] A1 passed: a known-good real-MCOC optimization completes unchanged (or the
      A1 STOP was triggered and reported).
- [ ] A2 passed: a genuine MCOC failure now produces a clear error and no false
      "success".
- [ ] B: all three run paths warn-and-block when MCOC is unconfigured, and all
      three proceed when properly configured.
- [ ] Results recorded next to each box; any STOP reported with exit code +
      output tail.
- [ ] `plans/README.md` status row updated with PASS / STOP outcome.

## ⛔ STOP conditions

- A1: a previously-working real-MCOC run now hard-fails on a non-zero exit code →
  plan 004 needs revision (report the code; candidate fix: tolerate that code, or
  require non-zero-exit AND missing-result before raising).
- B: any run path either fails to warn when MCOC is missing, or wrongly warns
  when MCOC is correctly configured → report which path and the dialog text.

## Maintenance notes

- If A1's STOP fires, the durable fix is to make the returncode guard
  configurable or to combine it with the result-file check (only raise when
  exit≠0 AND no fresh result file). Capture the real solver's success exit codes
  in a comment near the guard so the next maintainer knows why.
- Re-run Part B after any future refactor of the three `run_*` entry points or of
  `_validate_mcoc_setup()`.
