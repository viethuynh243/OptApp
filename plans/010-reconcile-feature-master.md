# Plan 010: Reconcile the diverged `feature/toiuu-mo-rong` and `master` (TCVN work)

> **Executor instructions**: This is a **merge-strategy plan for a human** (or an
> agent the operator explicitly authorizes to merge). It involves resolving git
> conflicts that require engineering judgment and a strategic decision that is the
> maintainer's to make. Do NOT dispatch a cheap executor to auto-resolve
> conflicts. Follow the steps, resolve each conflicted file per the guidance, and
> verify the unified suite is green before committing the merge.

## Status

- **Priority**: P2 (do AFTER the 8 plans are merged into `feature/toiuu-mo-rong`)
- **Effort**: M (≈half a day incl. conflict resolution + verification)
- **Risk**: MED–HIGH (the conflict in `io_handlers/report_writer.py` and
  `ui/main_window.py` combines two real feature sets; mis-resolution silently
  drops one)
- **Depends on**: the 8-plan cherry-pick sequence in `plans/README.md` applied to
  `feature/toiuu-mo-rong` first (so reconciliation happens once, against the final
  feature tree)
- **Category**: migration / tech-debt
- **Planned at**: commit `0ec2135`, 2026-06-20 (analysis valid as of `master` @ `f14053f`)

## Why this matters

`feature/toiuu-mo-rong` (@`0ec2135`) and `master` (@`f14053f`) have **diverged**
from common ancestor `6728897` (v1.2.0) and neither contains the other. They are
two parallel, overlapping lines of the same product:

- **feature** — 99 files changed: the "tối ưu mở rộng" work (gói `core/ext/`,
  quét đường kính, thu bệ, R7/R8, plus the 8 advisor plans). The active branch.
- **master** — 12 files changed: a focused PR adding **TCVN 10304:2014** design
  capacities — new `core/tcvn.py` (231 lines, `apply_design_capacities`: [Po]/[Ct]
  → Rc,d/Rt,d per Điều 7.1.11) + `tests/test_tcvn.py`, wired into a few shared
  files and a TCVN section in the PDF/MD report.

Leaving them split means every cross-cutting fix (the advisor plans, the MCOC
robustness, the dependency manifest) has to be done twice, and the TCVN design-
capacity logic never reaches the active branch. Both branches even claim version
**1.3.0** for *different* feature sets — a latent release-numbering clash.

## Current state (measured)

`master`'s entire diff vs base `6728897` (the only things to bring over):

```
 CHANGELOG.md                 |  9 ++   (TCVN changelog entry)
 core/constants.py            |  6 ++   (TCVN comments; auto-merges)
 core/mechanics.py            | 13 ++   (TCVN comment in R3 docstring)
 core/nsga2_optimizer.py      |  8 ++   (import core.tcvn; tcvn.apply_design_capacities(params))
 core/version.py              |  4 ++   (version/date header)
 io_handlers/report_writer.py | 99 ++   (TCVN report section — the big one)
 methodology.md               |  4 ++   (auto-merges)
 ui/main_window.py            |  4 ++   (from core import tcvn; tcvn.apply_design_capacities(d))
 core/tcvn.py                 | NEW 231 (the module — purely additive)
 tests/test_tcvn.py           | NEW     (purely additive)
 core/optimizer.py            | (master-only edit; auto-merges — feature kept base)
 core/refine_optimizer.py     | (master-only edit; auto-merges)
```

**Measured conflict surface** (dry-run `git merge master` into the
8-plan-integrated feature, 2026-06-20) — exactly **5 conflicted files**:

| File | Why it conflicts | Resolution difficulty |
|------|------------------|-----------------------|
| `CHANGELOG.md` | both added a top entry | trivial — keep both entries |
| `core/mechanics.py` | master added a TCVN comment in the R3 docstring | trivial — keep both |
| `core/nsga2_optimizer.py` | feature changed it; master added `import core.tcvn` + `tcvn.apply_design_capacities(params)` near line ~375 | small — keep feature's logic AND insert master's tcvn import + call |
| `io_handlers/report_writer.py` | feature added R1–R8 reporting; master added a +99-line TCVN section | **careful** — combine BOTH report sections; do not drop either |
| `ui/main_window.py` | feature's ext UI + plan 005 helper; master added `from core import tcvn; tcvn.apply_design_capacities(d)` (~line 509) | **careful** — keep feature/005 code AND insert master's tcvn call at the param-normalization point |

Auto-merged cleanly (no action): `core/constants.py`, `core/version.py`,
`core/optimizer.py`, `methodology.md`, plus the additive new files
`core/tcvn.py`, `tests/test_tcvn.py`.

`tcvn.apply_design_capacities` is described as **idempotent** (per the master
ui comment), so calling it once at the param-normalization point is safe.

## Strategy decision (recommended)

**Merge `master` INTO `feature/toiuu-mo-rong`** (feature is the far-ahead, active
superset where all plans land). After it's green, fast-forward `master` to the
unified tip so the two lines converge. Alternative strategies and why not:

- *Merge feature → master*: same conflicts, but leaves the active work on a
  branch; you'd still need to move master forward. No advantage.
- *Cherry-pick only `core/tcvn.py` + call sites onto feature*: tempting, but you'd
  hand-pick the report_writer section and risk missing the `constants/mechanics`
  comment + changelog context; a real merge is cleaner and records history.
- *Rebase*: rewrites the PR-merge history on master (`f14053f` is a merge commit) —
  avoid.

⚠️ This decision (which branch becomes canonical, and the version number) is the
maintainer's. Confirm before executing.

## Commands you will need

| Purpose | Command | Expected |
|---|---|---|
| Confirm feature has the 8 plans | `git log --oneline -10` | shows the 8 plan commits on `feature/toiuu-mo-rong` |
| Start the merge | `git merge --no-ff master` | conflicts in the 5 files above |
| See conflicts | `git diff --name-only --diff-filter=U` | the 5 files |
| Full suite | `python -m pytest -q` | green (see Done criteria) |
| Abort if needed | `git merge --abort` | clean working tree |

## Scope

**In scope**: resolving the 5 conflicts on `feature/toiuu-mo-rong`, bringing in
`core/tcvn.py` + `tests/test_tcvn.py`, and deciding the unified version number.

**Out of scope**: do NOT rewrite the ext logic or the TCVN logic — this is a
*combine*, not a redesign. Do NOT drop either side's report section. Do NOT push
or force-update `master` without the maintainer's explicit say-so.

## Steps

### Step 0: Prerequisite — integrate the 8 plans first
Apply the cherry-pick sequence from `plans/README.md` to `feature/toiuu-mo-rong`
and confirm `python -m pytest -q` → `22 passed, 2 skipped` (or `24 passed` with
sample data). Reconciling before that means doing conflict resolution twice.

### Step 1: Decide the unified version
Both sides are `1.3.0` for different features. Pick the union version (recommended
**`1.4.0`**) and the release date. You will set this in `core/version.py` during
Step 3 and add a combined `CHANGELOG.md` entry.

### Step 2: Start the merge
`git merge --no-ff master`. Expect conflicts in the 5 files listed in
"Current state".

### Step 3: Resolve each conflict
- **`CHANGELOG.md`** — keep BOTH entries; add one new `## [1.4.0]` heading that
  notes "hợp nhất: tối ưu mở rộng (ext) + TCVN 10304:2014 design capacities".
- **`core/mechanics.py`** — keep both comment lines (feature's + master's TCVN
  note). No logic change.
- **`core/nsga2_optimizer.py`** — keep feature's function body in full; ADD
  master's `from core import tcvn` and the `tcvn.apply_design_capacities(params)`
  call at the same place master put it (param normalization, ~line 375). Verify
  the call runs once before evaluation.
- **`io_handlers/report_writer.py`** — the careful one. Keep feature's R1–R8
  reporting AND master's TCVN section; place them as adjacent sections, not
  one-replacing-the-other. Read both sides of the conflict markers fully before
  deleting any line.
- **`ui/main_window.py`** — keep feature's code (including plan 005's
  `_validate_mcoc_setup` and the ext UI) AND insert master's
  `from core import tcvn; tcvn.apply_design_capacities(d)` at the param-
  normalization point (master had it ~line 509, where `d` is the params dict).
- **`core/version.py`** — git auto-merges this, but OVERRIDE it to the Step 1
  unified version + date.

Confirm `core/tcvn.py` and `tests/test_tcvn.py` arrived (they're additive):
`ls core/tcvn.py tests/test_tcvn.py`.

### Step 4: Verify the unified tree is green
- `python -m pytest -q` → **no failures**. Expected with no sample data:
  the feature tests (incl. plan 002's MCOC tests, plan 004's runner tests) PLUS
  master's `tests/test_tcvn.py` all pass; the 2 `test_ext` data tests are
  *skipped* (plan 008). With sample data present, all pass.
- `python -c "import core.tcvn, ui.main_window, core.nsga2_optimizer"` → exit 0
  (the tcvn integration imports cleanly into the feature code).
- `grep -n "apply_design_capacities" core/nsga2_optimizer.py ui/main_window.py`
  → a call in each (master's integration survived the merge).
- `grep -n "R1\|R8\|TCVN\|Rc,d" io_handlers/report_writer.py` → BOTH the R1–R8
  reporting and the TCVN section are present (neither was dropped).

### Step 5: Commit the merge (do not push without sign-off)
`git commit` the merge with a message naming both feature sets and the new
version. Do NOT fast-forward/update `master` until the maintainer approves.

## Done criteria

- [ ] `git merge` completed; the 5 conflicts resolved.
- [ ] `core/tcvn.py` and `tests/test_tcvn.py` present on the unified branch.
- [ ] `python -m pytest -q` → no failures (feature + tcvn tests pass; 2 `test_ext`
      skipped without sample data).
- [ ] `apply_design_capacities` is called in both `core/nsga2_optimizer.py` and
      `ui/main_window.py` (master's integration preserved).
- [ ] `io_handlers/report_writer.py` contains BOTH the R1–R8 and the TCVN report
      sections.
- [ ] `core/version.py` shows the unified version (recommended `1.4.0`), and
      `CHANGELOG.md` has a combined entry.
- [ ] `plans/README.md` status row updated.

## ⛔ STOP conditions

- The dry-run conflict set differs from the 5 files in "Current state" — `master`
  or `feature` advanced since this plan was written (`f14053f` / `0ec2135`).
  Re-run `git merge --abort`, re-measure with the analysis commands, and refresh
  this plan before resolving.
- After resolution, `tests/test_tcvn.py` fails — the TCVN integration didn't land
  correctly (likely the `apply_design_capacities` call site or an import was lost
  in the `nsga2_optimizer`/`ui` conflict). Re-examine those two resolutions.
- You cannot tell which lines to keep in `report_writer.py` — STOP and get the
  author's intent rather than guessing; dropping a report section is a silent
  data-loss bug.

## Maintenance notes

- After this lands and the maintainer approves, fast-forward `master` to the
  unified tip so the branches reconverge; then future work has one line.
- The 8 advisor plans assumed the feature branch; once merged, master inherits
  them. Re-check that `requirements.txt`, `pytest.ini`, and the MCOC returncode
  guard are present on the unified branch (they should be, via feature).
- `tcvn.apply_design_capacities` is idempotent — safe even though it may now be
  invoked from both the UI normalization and the optimizer entry; confirm it
  isn't double-counting if you later add more call sites.
