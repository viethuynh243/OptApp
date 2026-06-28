# Plan 004: Harden the MCOC subprocess boundary (check exit code, surface failures)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 0ec2135..HEAD -- core/mcoc_runner.py core/blackbox.py tests/mcoc_stub.py`
> If any changed since this plan was written, compare the "Current state"
> excerpts against the live code before proceeding; on a mismatch, treat it as
> a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: plans/002-pytest-discovery-baseline.md (needs pytest to run
  the new MCOC-runner test)
- **Category**: bug / correctness
- **Planned at**: commit `0ec2135`, 2026-06-20

## Why this matters

Every result this app delivers flows through `MCOCRunner.run()`. Today that
method **never checks the subprocess exit code** — it decides success purely by
whether a `*_result.txt` file appeared with a recent modification time. If MCOC
exits non-zero (bad input, license error, crash) but a result file from a prior
run is still on disk, or MCOC writes a partial file before failing, the runner
can return stale or malformed numbers as if they were valid. The failure is then
further masked one layer up: `MCOCBlackbox.evaluate_layout` catches *all*
exceptions and returns `None` with a generic message. The fix is small and
high-value: assert the exit code, and make genuine failures loud and specific
instead of silent.

## Current state

`core/mcoc_runner.py` — `run()` builds the command and executes it (lines
145–166), then looks for the result file (168–187). The returncode is captured
in `proc` but never inspected:

```python
        try:
            proc = subprocess.run(
                cmd,
                input="",
                capture_output=True,
                text=True,
                cwd=workdir,
                timeout=self.timeout,
                **_no_window_kwargs()
            )
        except subprocess.TimeoutExpired:
            raise MCOCError("MCOC chay qua %ds, da dung." % self.timeout)
        except OSError as e:
            raise MCOCError("Khong chay duoc MCOC (%s): %s" % (self.exe, e))

        # Tìm file kết quả: ưu tiên <base>_result.txt, nếu không có thì tìm
        # file *_result.txt mới nhất sinh ra sau t0 trong workdir.
        if not os.path.exists(result_path):
            ...
```

Mitigations already present (do not remove): the old result file is deleted
before running (`core/mcoc_runner.py:139-143`), and the fallback scan only
accepts files with `mtime >= t0 - 1` (`:176`). These reduce — but do not
eliminate — stale-read risk, and they do nothing about a non-zero exit that
still produced a fresh-but-garbage file.

The error-swallowing layer, `core/blackbox.py:34-39`:

```python
        try:
            evaluator = MCOCBlackbox.make_real_evaluator(params, loads=loads)
            res = evaluator(coords)
            return res, "Ket qua MCOC thuc (" + os.path.basename(res.get('result_path', '')) + ")"
        except Exception as e:
            return None, "Loi goi MCOC: %s" % e
```

The CI-safe test double is `tests/mcoc_stub.py` (a `.py` invoked through the
runner as a subprocess; the runner runs `.py` files with `sys.executable` —
`core/mcoc_runner.py:112-113`). Existing MCOC-path tests
(`tests/test_nsga2_mcoc.py`, `tests/test_refine.py`) set
`params['exe_path'] = STUB` and assert a `*_result.txt` is produced — read
`tests/mcoc_stub.py` before Step 3 to learn how it parses the input filepath and
writes the result, so your new test can drive both success and failure paths.

## Commands you will need

| Purpose      | Command                                            | Expected on success |
|--------------|----------------------------------------------------|---------------------|
| Run new test | `python -m pytest -q tests/test_mcoc_runner.py`    | all pass            |
| Run MCOC path| `python -m pytest -q tests/test_nsga2_mcoc.py tests/test_refine.py` | `2 passed` |
| Full suite   | `python -m pytest -q`                              | all pass (≥ 21+new) |

## Scope

**In scope** (the only files you should modify/create):
- `core/mcoc_runner.py` — add a returncode check in `run()`
- `core/blackbox.py` — make the swallowed-error message in `evaluate_layout`
  carry the underlying diagnostic (keep returning `(None, msg)` — callers depend
  on that contract; just enrich `msg`)
- `tests/test_mcoc_runner.py` (create)

**Out of scope** (do NOT touch):
- The existing mitigations (old-file deletion, mtime fallback) — keep them.
- `tests/mcoc_stub.py` — do not change the existing stub; if you need a failing
  stub for the new test, create a NEW tiny stub file under `tests/` (e.g.
  `tests/_failing_stub.py`) or generate it inside the test with `tmp_path`.
- The `(res_dict, message)` return contract of
  `MCOCBlackbox.evaluate_layout` — callers in `ui/main_window.py` unpack a
  2-tuple; do not change the shape.
- `core/mcoc_runner.py` result-parsing logic in `parse_mcoc_result_file`
  (that lives in `io_handlers/file_io.py` and is out of scope).

## Git workflow

- Branch: `advisor/004-mcoc-runner-robustness`
- Commit per logical unit (runner change; blackbox message; test). Message
  style matches the repo, e.g. `Kiểm tra returncode MCOC + báo lỗi rõ ràng`.
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Check the subprocess exit code in `MCOCRunner.run()`

Immediately after the `try/except` block that runs `subprocess.run(...)` (i.e.
right before the `# Tìm file kết quả` comment at `core/mcoc_runner.py:168`), add
a returncode guard. On a non-zero exit, raise `MCOCError` with the tail of
stdout/stderr for diagnosis — mirroring the existing diagnostic style used in
the "no result file" branch (`:182-187`):

```python
        # MCOC báo lỗi (exit code != 0): coi như thất bại, KHÔNG đọc file cũ/dở.
        if proc.returncode != 0:
            tail = (proc.stdout or "")[-400:] + (proc.stderr or "")[-400:]
            raise MCOCError(
                "MCOC ket thuc voi ma loi %d cho %s.\nOutput cuoi:\n%s"
                % (proc.returncode, base, tail)
            )
```

Rationale for placement: the old result file was already deleted at
`:139-143`, so failing here cannot return a stale value, and a still-running
solver case is already covered by the timeout branch.

**Verify**: `python -m pytest -q tests/test_nsga2_mcoc.py tests/test_refine.py`
→ `2 passed` (the success path is unaffected — the stub exits 0).

### Step 2: Make the blackbox error message carry the cause

In `core/blackbox.py`, the `except Exception as e:` at `:38` already includes
`e` in the message. Confirm the message is specific enough; if `e` is an
`MCOCError`, its text now contains the returncode + output tail from Step 1, so
no shape change is needed — only verify the message propagates. If you find the
message is truncated or generic, widen it to include `type(e).__name__`:

```python
        except Exception as e:
            return None, "Loi goi MCOC (%s): %s" % (type(e).__name__, e)
```

Keep the 2-tuple return contract.

**Verify**: `python -m pytest -q` → full suite still green.

### Step 3: Add `tests/test_mcoc_runner.py`

Create a pytest file (model its structure on `tests/test_refine.py` for ROOT
setup and stub usage). Cover:

1. **Success path** — point `MCOCRunner` at `tests/mcoc_stub.py`, run a minimal
   valid input file (build one the way `tests/test_refine.py::build_demo_input`
   does, or reuse a fixture), and assert `run()` returns a dict with `pmax`.
2. **Non-zero exit is raised** — create a tiny failing stub (a `.py` that prints
   to stderr and calls `sys.exit(1)` without writing any `*_result.txt`), point
   the runner at it, and assert `run()` raises `MCOCError` whose message
   contains the exit code. Use `pytest.raises(MCOCError)`.
3. **No-result-file is raised** — a stub that exits 0 but writes nothing; assert
   `run()` raises `MCOCError` mentioning no result file (this guards the
   existing behavior so Step 1 didn't regress it).

Import target: `from core.mcoc_runner import MCOCRunner, MCOCError`. Write
scratch files under `tests/_work/` or a pytest `tmp_path` fixture.

**Verify**: `python -m pytest -q tests/test_mcoc_runner.py` → all pass (3 tests).

### Step 4: Confirm the whole suite is green

**Verify**: `python -m pytest -q` → all pass; count = previous baseline (21
after Plan 002) + 3 new = `24 passed` (adjust if Plan 002 not yet landed; then
the two MCOC-path files won't be collected and you'll see fewer — note this in
your report rather than forcing a number).

## Test plan

- New file `tests/test_mcoc_runner.py` with three cases: success, non-zero
  exit raises `MCOCError`, missing-result raises `MCOCError`. Model ROOT/path
  and stub setup after `tests/test_refine.py`.
- Verification: `python -m pytest -q tests/test_mcoc_runner.py` → 3 passed, and
  the full suite stays green.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n "returncode" core/mcoc_runner.py` returns a match inside `run()`
- [ ] `tests/test_mcoc_runner.py` exists and contains a `pytest.raises(MCOCError)` assertion
- [ ] `python -m pytest -q tests/test_mcoc_runner.py` → 3 passed
- [ ] `python -m pytest -q tests/test_nsga2_mcoc.py tests/test_refine.py` → `2 passed` (success path unbroken)
- [ ] `python -m pytest -q` → full suite green
- [ ] `git status` shows only `core/mcoc_runner.py`, `core/blackbox.py`,
      `tests/test_mcoc_runner.py` (and any new helper stub) changed
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Adding the returncode check makes `tests/test_nsga2_mcoc.py` or
  `tests/test_refine.py` fail — that would mean the stub exits non-zero on the
  success path; report it instead of weakening the check.
- The real result-file naming differs from `<base>_result.txt` in a way that
  the returncode check interferes with the fallback scan (report the case).
- You discover a caller that depends on `evaluate_layout` returning something
  other than a `(dict-or-None, str)` tuple — do not change the contract; report.

## Maintenance notes

- If/when Plan 007 (parallel MCOC) lands, each concurrent call must get an
  isolated working directory or a unique result filename; the mtime-based
  fallback scan in `run()` is not safe under concurrency. The returncode check
  added here is a prerequisite for trusting parallel results.
- A reviewer should confirm the old result file is still deleted before the run
  (the stale-read mitigation) and that the new test's failing stub does not
  leave `*_result.txt` artifacts that pollute `tests/_work/`.
