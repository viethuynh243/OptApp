# Plan 011: Stop the MCOC runner from returning a different input's result (stale-result bug)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving on. Touch
> only the files listed as in scope. If a STOP condition occurs, stop and
> report. When done, update the status row in `plans/README.md` unless a
> reviewer maintains it.

## Status

- **Priority**: P1 (silent wrong data on the only delivery-grade path)
- **Effort**: S
- **Risk**: MED (touches the result-lookup on the critical MCOC path; mitigated by a regression test + keeping the deterministic primary path)
- **Depends on**: plan 004 (returncode check) — builds on top of it; ideally executed on the unified branch that already contains 004
- **Category**: bug / correctness
- **Planned at**: commit `0ec2135`, 2026-06-20
- **Discovered by**: running the REAL `MCOC Batch` solver during plan 009 Part A
  (2026-06-20). Reproduced below.

## Why this matters

`MCOCRunner.run()` decides which `*_result.txt` belongs to the run it just made.
Its fallback path scans the WHOLE working directory for any `*_result.txt` with a
recent mtime and returns the newest. Observed real-solver behavior makes this
unsafe:

- **`MCOC_Batch.exe` ALWAYS exits 0**, even when it rejects an input (it prints
  `Ket qua: 0 OK / 1 LOI` + `LOI: ...` to stdout but returns code 0). So plan
  004's `returncode != 0` guard never fires for this solver — failure is only
  detectable by the absence of the expected result file.
- When an input is rejected, no `<base>_result.txt` is produced, so `run()` hits
  the dir-wide fallback scan. If a DIFFERENT input produced a `*_result.txt`
  less than ~1s earlier (normal in the optimization loop, where each MCOC call
  takes ≈1s and all evaluations share one `_opt_runs` dir), the scan picks up
  **that other input's result** and returns its forces as if they were this
  input's. The optimization is silently fed wrong, delivery-grade numbers, with
  no error surfaced.

**Reproduction (real solver, observed):** running a good input then a garbage
input in the same dir made `run(garbage)` return `Nmax=481.56` — identical to the
good input's result — instead of raising. Running the garbage input alone in a
clean dir correctly raised `MCOCError "khong sinh file ket qua"`.

## Current state

`core/mcoc_runner.py`, inside `MCOCRunner.run()` (line numbers approximate; on the
unified branch the returncode guard from plan 004 sits just above this). The
primary path is deterministic and correct:

```python
        workdir = os.path.dirname(input_filepath)
        base = os.path.splitext(os.path.basename(input_filepath))[0]
        result_path = os.path.join(workdir, base + "_result.txt")
        ...
        # (plan 004) raise if proc.returncode != 0   <-- inert for this solver (always 0)
        ...
        if not os.path.exists(result_path):
            cands = []
            for fn in os.listdir(workdir):
                if fn.lower().endswith("_result.txt"):          # <-- BUG: any result file
                    fp = os.path.join(workdir, fn)
                    if os.path.getmtime(fp) >= t0 - 1:
                        cands.append(fp)
            if cands:
                result_path = max(cands, key=os.path.getmtime)  # <-- can be ANOTHER input's
            else:
                tail = (proc.stdout or "")[-400:] + (proc.stderr or "")[-400:]
                raise MCOCError("MCOC khong sinh file ket qua cho %s.\nOutput cuoi:\n%s"
                                % (base, tail))
```

Confirmed real behavior: MCOC names output deterministically as
`<base>_result.txt` (e.g. `good.txt` → `good_result.txt`). So the dir-wide
fallback is not needed for the common case and is the source of cross-input
contamination.

The CI-safe stub is `tests/mcoc_stub.py`; the existing runner tests live in
`tests/test_mcoc_runner.py` (created by plan 004) — add the regression there.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Runner tests | `python -m pytest -q tests/test_mcoc_runner.py` | all pass (incl. the new one) |
| MCOC-path tests | `python -m pytest -q tests/test_nsga2_mcoc.py tests/test_refine.py` | `2 passed` |
| Full suite | `python -m pytest -q` | no failures |

## Scope

**In scope**:
- `core/mcoc_runner.py` — constrain the fallback scan so it only accepts a
  result file belonging to THIS input.
- `tests/test_mcoc_runner.py` — add a regression test for the stale-pickup.

**Out of scope**:
- The plan-004 returncode guard — leave it (harmless; useful for solvers that DO
  signal via exit code). Do not remove it.
- The deterministic primary `result_path` and the old-file deletion at the top of
  `run()` — keep them.
- Parsing MCOC's `X OK / Y LOI` stdout summary — a nice-to-have noted in
  Maintenance, not required here.

## Steps

### Step 1: Constrain the fallback scan to this input's base name

In `core/mcoc_runner.py`, change the fallback filter so a candidate must ALSO
start with the input's `base`:

```python
            for fn in os.listdir(workdir):
                fl = fn.lower()
                # CHỈ nhận file kết quả CỦA CHÍNH input này (tránh nhặt nhầm
                # kết quả của input khác vừa sinh <1s trước trong cùng thư mục).
                if fl.endswith("_result.txt") and fl.startswith(base.lower()):
                    fp = os.path.join(workdir, fn)
                    if os.path.getmtime(fp) >= t0 - 1:
                        cands.append(fp)
```

This keeps the "MCOC named the result slightly differently but for THIS base"
case working, while making it impossible to return another input's result. The
deterministic `<base>_result.txt` primary path is unchanged.

**Verify**: `python -m pytest -q tests/test_nsga2_mcoc.py tests/test_refine.py`
→ `2 passed` (stub still produces `<base>_result.txt`, so the happy path is intact).

### Step 2: Add a regression test (stub-based, CI-safe)

Add to `tests/test_mcoc_runner.py` a test that reproduces the bug with the stub
(no real MCOC):

1. Create a `tmp_path` workdir.
2. Pre-create a stale result for a DIFFERENT input:
   `(<workdir>/other_result.txt)` with valid MCOC summary content, and ensure its
   mtime is recent (it is, since just written).
3. Build a valid input file `target.txt` in the same dir.
4. Use a stub that exits 0 but writes NO `target_result.txt` (model it on the
   "noop" stub already used by `test_run_no_result_file_raises`; it simulates
   MCOC rejecting the input while exiting 0 — the real solver's behavior).
5. Assert `MCOCRunner(noop_stub).run(target_path)` **raises `MCOCError`** (it must
   NOT return `other_result.txt`'s content).

For step 2's stale file content, reuse the minimal `BANG TONG KET NOI LUC`
snippet that `parse_mcoc_result_file` accepts (look at how `tests/mcoc_stub.py`
writes its result, or at a sample under `mcoc_input_sample/_opt_runs/*_result.txt`
if present) — it only needs to be parseable so that, WITHOUT the fix, the old code
would have returned it.

**Verify**: `python -m pytest -q tests/test_mcoc_runner.py` → all pass; the new
test FAILS if you revert Step 1 (confirm by temporarily reverting, then restore).

### Step 3: Full suite

**Verify**: `python -m pytest -q` → no failures (the 2 `test_ext` data tests are
skipped without sample data per plan 008; everything else passes).

## Test plan

- New regression test in `tests/test_mcoc_runner.py`: a failed run (exit 0, no
  own result file) in a dir containing a recent OTHER `*_result.txt` must raise,
  not return the stranger's result.
- Confirm the test is meaningful: it must fail against the pre-fix code (dir-wide
  scan) and pass after Step 1.

## Done criteria

- [ ] `core/mcoc_runner.py` fallback requires `fn.startswith(base.lower())`
- [ ] New regression test exists and asserts `pytest.raises(MCOCError)` for the
      stale-other-result scenario
- [ ] `python -m pytest -q tests/test_mcoc_runner.py` → all pass
- [ ] `python -m pytest -q tests/test_nsga2_mcoc.py tests/test_refine.py` → `2 passed`
- [ ] `python -m pytest -q` → no failures
- [ ] `git status` shows only `core/mcoc_runner.py` and `tests/test_mcoc_runner.py`

## STOP conditions

- The fallback code no longer matches the "Current state" excerpt (drift): STOP.
- The new regression test passes even before Step 1's fix (then it isn't actually
  exercising the bug — fix the test to pre-create the stale OTHER result with a
  recent mtime and a parseable body): STOP and report.
- Constraining the scan makes `test_nsga2_mcoc`/`test_refine` fail (the stub must
  be producing `<base>_result.txt`; if it names it differently, report): STOP.

## Maintenance notes

- The real `MCOC_Batch.exe` signals per-file failure ONLY via stdout
  (`Ket qua: N OK / M LOI`) and always exits 0. A stronger future guard is to
  parse that summary and raise when `M LOI > 0` for the submitted file — clearer
  than relying on result-file absence. Deferred from this plan (kept minimal).
- This fix is also the prerequisite the plan-007 parallel-MCOC spike calls out:
  with per-input result isolation, concurrent evaluations in a shared workdir no
  longer risk cross-contamination via the mtime scan.
- A reviewer should confirm the deterministic `<base>_result.txt` primary path is
  untouched and that the regression test fails without Step 1.
