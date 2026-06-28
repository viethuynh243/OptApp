# Plan 007: Design spike — parallelize MCOC evaluation (investigate, prototype, decide)

> **Executor instructions**: This is a DESIGN/SPIKE plan, not a build-everything
> plan. Your deliverable is a written findings document plus a *throwaway*
> prototype branch — NOT a merged feature. Follow the steps, run every
> verification command, and if a STOP condition occurs, stop and report. When
> done, update the status row for this plan in `plans/README.md` and attach your
> findings doc path.
>
> **Drift check (run first)**: `git diff --stat 0ec2135..HEAD -- core/nsga2_optimizer.py core/blackbox.py core/mcoc_runner.py core/ext/orchestrator.py`
> If any changed since this plan was written, re-read the "Current state"
> excerpts against live code before proceeding; on a mismatch, note it in your
> findings and adjust.

## Status

- **Priority**: P3 (direction)
- **Effort**: M–L (spike: ~1–2 days of investigation + prototype)
- **Risk**: MED (the eventual feature is risky; this spike is low-risk because
  it does not merge production code)
- **Depends on**: plans/004-mcoc-runner-robustness.md (the returncode check and
  result-isolation reasoning are prerequisites for trusting concurrent results)
- **Category**: direction / performance
- **Planned at**: commit `0ec2135`, 2026-06-20

## Why this matters

MCOC subprocess calls dominate wall-clock time: every NSGA-II individual and
every diameter in the extended sweep is one external solver invocation, run
**strictly serially** today (no `ThreadPoolExecutor`, `multiprocessing`, or
`concurrent.futures` anywhere in the codebase). The project's own backlog
(`docs/vault/4-Vấn đề & Cải tiến/Vấn đề & Cải tiến.md`, item "Song song hóa lời
gọi MCOC", priority *medium*) and ADR-001 both name parallelization as the
intended speedup — "tốc độ đến từ giảm số lần gọi + song song" — yet it is
unimplemented. On an 8-core machine a population batch could plausibly run
several times faster. This spike determines **whether** to build it, **how**, and
**what must be fixed first** (chiefly: the result-file lookup is not concurrency-
safe), so the maintainer can decide with evidence instead of guessing.

## Current state

The natural parallelization point is `_eval_pop` in `core/nsga2_optimizer.py:466-481`,
which evaluates a batch of individuals in a plain serial loop:

```python
    def _eval_pop(individuals):
        """Đánh giá cả một nhóm cá thể, tôn trọng trần max_evals và cache."""
        out = []
        for ind in individuals:
            if max_evals is not None and counters['n_evals'] >= max_evals:
                spec, _ = decode(ind, params)
                rec = cache.get(_spec_key(spec))
                if rec is None:
                    continue
            else:
                rec = evaluate(ind, params, loads, evaluator, cache, counters)
            ...
```

Shared mutable state that any parallel version must handle carefully:
- `cache` (dict keyed by `_spec_key(spec)`) and `counters['n_evals']` — read and
  written inside `evaluate()` (`core/nsga2_optimizer.py:100-128`). Under
  concurrency these need locking or a per-batch dedup-then-merge strategy. The
  `max_evals` budget semantics ("seeds get the budget first") must be preserved.

The evaluator that actually calls MCOC, `MCOCBlackbox.make_real_evaluator`
(`core/blackbox.py:44-77`), is the concurrency hazard:

```python
        workdir = os.path.join(os.path.dirname(os.path.abspath(input_file)), "_opt_runs")
        os.makedirs(workdir, exist_ok=True)
        base = os.path.splitext(os.path.basename(input_file))[0]
        counter = [0]

        def evaluator(coords):
            counter[0] += 1
            in_path = os.path.join(workdir, "%s_opt%03d.txt" % (base, counter[0]))
            template.write(coords, in_path, name_suffix="OPT%03d" % counter[0], loads=loads)
            return runner.run(in_path)
```

- `counter[0] += 1` is not atomic → two threads can pick the same index / file.
- All runs share ONE `workdir` (`_opt_runs`). `MCOCRunner.run()`
  (`core/mcoc_runner.py:122-197`) derives the result path as
  `<base>_result.txt` in that shared dir and, on the fallback path, scans the
  whole dir for the newest `*_result.txt` by mtime — under concurrency, call A
  can pick up call B's result. **This is the prerequisite to fix before any
  parallelism** (it is the downgraded-to-LOW "race" finding; LOW only because
  it is unreachable while execution is serial).

The extended flow funnels through `core/ext/orchestrator.py`
(`run_extended_optimization`), which loops over diameters and calls the NSGA-II
path per diameter — a second, coarser-grained parallelization candidate.

## Commands you will need

| Purpose            | Command                                                  | Expected |
|--------------------|---------------------------------------------------------|----------|
| Confirm serial today| `grep -rn "ThreadPoolExecutor\|multiprocessing\|concurrent.futures\|Pool(" core io_handlers ui` | no matches |
| Run MCOC-path tests | `python -m pytest -q tests/test_nsga2_mcoc.py tests/test_refine.py` | `2 passed` |
| Full suite          | `python -m pytest -q`                                   | all pass |
| CPU count           | `python -c "import os; print(os.cpu_count())"`          | prints an int |

## Scope

**In scope** (deliverables of the spike):
- A findings/design document at `docs/spike_parallel_mcoc.md` (create) — see
  "Done criteria" for required contents.
- A **throwaway prototype** on a branch named `spike/parallel-mcoc` that proves
  the concept end-to-end against the stub. The prototype MAY modify
  `core/blackbox.py`, `core/nsga2_optimizer.py`, and `core/mcoc_runner.py`, but
  it is NOT to be merged from this plan — merging is a separate, future decision.

**Out of scope** (do NOT do in this plan):
- Do NOT merge parallel execution into `master`/the working branch.
- Do NOT change the UI threading model (`ui/main_window.py` already runs each
  optimization in a background thread; nested parallelism interaction is a
  finding to document, not to wire up here).
- Do NOT change result formats, the `(res_dict, message)` blackbox contract, or
  the NSGA-II algorithm itself.

## Git workflow

- Branch: `spike/parallel-mcoc` (clearly a spike; not `advisor/...`).
- Commit the findings doc separately from prototype code so the doc can be
  cherry-picked even if the prototype is discarded.
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Establish a baseline timing with the stub

Using the existing stub harness (`tests/test_nsga2_mcoc.py` builds an input and
runs `run_nsga2` against `tests/mcoc_stub.py`), measure wall-clock for a
representative run (e.g. `pop_size=20, n_gen=10, max_evals=140`). Record
`n_evals` and elapsed seconds. The stub is fast, so to make parallelism
observable, add an artificial per-call delay in a *local copy* of the stub (e.g.
`time.sleep(0.1)`) to simulate real MCOC latency — document the delay you used.

**Verify**: you have a baseline number (serial elapsed, with the simulated delay).

### Step 2: Fix result isolation (the prerequisite)

Prototype per-call working-directory or unique-filename isolation so two
concurrent MCOC calls cannot read each other's result:
- Option A: each evaluator call writes into its own subdir
  `_opt_runs/run_<uuid>/` and `MCOCRunner.run()` looks only there.
- Option B: pass a unique `--out-dir` per call and key the result strictly by
  the input basename (no dir-wide mtime scan).

Make `counter[0] += 1` thread-safe (a lock) or replace the counter with a
`uuid`/thread-id suffix. Confirm the serial tests still pass with the isolation
change.

**Verify**: `python -m pytest -q tests/test_nsga2_mcoc.py tests/test_refine.py`
→ `2 passed` with the isolation change applied serially.

### Step 3: Prototype parallel batch evaluation

Replace the serial loop in `_eval_pop` with a thread pool
(`concurrent.futures.ThreadPoolExecutor`, max_workers = `min(os.cpu_count(),
batch_size)`), preserving:
- the `max_evals` budget (decide and document a policy: e.g. submit at most the
  remaining budget, evaluate seeds before random as today),
- cache correctness (dedup specs within a batch before submitting; lock the
  shared `cache`/`counters`).

Threads (not processes) are the likely right choice because the work is an
external subprocess (releases the GIL) and the data is shared in-memory — but
record the reasoning and any contraindication you find.

**Verify**: prototype run reproduces the same `recommended` solution as the
serial baseline (same seed) and is faster with the simulated delay; capture both
numbers.

### Step 4: Write the findings/design document

Create `docs/spike_parallel_mcoc.md` capturing the results and a go/no-go
recommendation (see Done criteria for the required sections).

**Verify**: the doc exists and contains all required sections.

## Test plan

This spike does not add permanent tests. For the prototype, use the existing
stub-based tests as a correctness oracle:
- Same-seed runs must yield the same `recommended` result serial vs parallel
  (determinism check — note if NSGA-II ordering makes this hard and how you
  controlled for it).
- `python -m pytest -q` must still pass with the isolation change (Step 2) even
  before parallelism is added, proving the prerequisite is safe on its own.

## Done criteria

The spike is complete when `docs/spike_parallel_mcoc.md` exists and contains:

- [ ] **Baseline vs prototype timing** with the simulated per-call delay stated,
      and the speedup factor on this machine (`os.cpu_count()` recorded).
- [ ] **Correctness evidence**: same-seed serial vs parallel produce the same
      recommended solution (or an explanation of any nondeterminism and how to
      bound it).
- [ ] **The result-isolation design** (Option A/B chosen, with rationale) — this
      is the mandatory prerequisite and must be described even if parallelism is
      ultimately declined.
- [ ] **Budget & cache policy** under concurrency (how `max_evals` and the spec
      cache stay correct).
- [ ] **Interaction with the UI background thread** and the extended-flow
      per-diameter loop (`core/ext/orchestrator.py`) — which level to parallelize.
- [ ] **Go/No-Go recommendation** with a rough effort estimate for the real
      (mergeable) implementation, and the list of files it would touch.
- [ ] The prototype lives on branch `spike/parallel-mcoc` and is NOT merged.
- [ ] `plans/README.md` status row updated (and, if Go, a follow-up build plan is
      recommended in the findings doc).

## STOP conditions

Stop and report back (do not improvise) if:

- Plan 004 has not landed (no returncode check in `core/mcoc_runner.py`) — the
  spike depends on failures being detectable; flag this and either run 004 first
  or note the gap prominently.
- The prototype shows parallel runs giving *different/wrong* results that you
  cannot trace to ordering nondeterminism — that is a finding worth stopping on;
  document the reproduction.
- Result isolation (Step 2) cannot be made to pass the serial tests — the shared
  `_opt_runs` assumption may be load-bearing elsewhere (e.g. the UI reads those
  files); report what depends on the current naming.

## Maintenance notes

- The real implementation (if Go) should land as its own plan, gated on Plan
  004, and must keep `MCOCRunner`'s old-result deletion + returncode check.
- A reviewer of the eventual feature should scrutinize: thread-safety of the
  spec cache, the `max_evals` budget under concurrency (no over-spend), and that
  every concurrent MCOC call has a provably unique result path.
- If the spike concludes No-Go, record why in the findings doc and in
  `plans/README.md` so the backlog item can be closed rather than re-opened.
