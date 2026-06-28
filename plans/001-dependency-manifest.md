# Plan 001: Add a dependency manifest so installs and builds are reproducible

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 0ec2135..HEAD -- README.md io_handlers/export_utils.py packaging/`
> If any of those files changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dependencies / dx
- **Planned at**: commit `0ec2135`, 2026-06-20

## Why this matters

The repo has **no `requirements.txt`, `pyproject.toml`, or `setup.py`**. The
README's install line lists only `numpy matplotlib tkinterdnd2`, but the code
actually imports three more third-party packages at runtime (`openpyxl`,
`reportlab`, `Pillow`) plus build-time tools (`pyinstaller`, `markdown`). A
fresh `pip install` per the README produces an app that crashes the moment a
user exports an Excel/PDF report or the icon code runs. Pinning the real
dependency set makes installs, CI, and PyInstaller builds reproducible.

## Current state

The full set of third-party imports, verified by grepping the repo (excluding
`.claude/worktrees/`):

- **Runtime** (imported by `core/`, `io_handlers/`, `ui/`, `main.py`):
  - `numpy` — everywhere (e.g. `core/blackbox.py:13`)
  - `matplotlib` — `ui/plot_canvas.py`, `io_handlers/export_utils.py`
  - `tkinterdnd2` — `main.py:19` (drag-and-drop)
  - `openpyxl` — `io_handlers/export_utils.py` (Excel export)
  - `reportlab` — `io_handlers/export_utils.py` (PDF export)
  - `Pillow` (imported as `PIL`) — `io_handlers/export_utils.py`, `packaging/make_icon.py`
- **Build/dev only** (not needed to run the app):
  - `pyinstaller` — `packaging/OptApp.spec`, `packaging/build_installer.bat`
  - `markdown` — `packaging/md_to_pdf.py:19` (docs→PDF tooling)
  - `pytest` — the test suite

`tkinter` itself is part of the Python standard library — do NOT list it as a
pip dependency (it is a system package on Linux, bundled on Windows).

Versions currently installed in the dev environment (use as the pin baseline):

```
numpy==2.3.0
matplotlib==3.10.8
tkinterdnd2  (no __version__ attribute; pin to the version `pip show tkinterdnd2` reports)
openpyxl==3.1.5
reportlab==4.5.1
Pillow==11.2.1
markdown==3.10.2
pyinstaller==6.21.0
pytest==9.1.0
```

Current README install section (`README.md:24-33`):

```
## Cài đặt

1. Cài Python 3.9+ hoặc 3.10/3.11.
2. Cài các thư viện cần thiết:

```bash
pip install numpy matplotlib tkinterdnd2
```
```

There is also a stale reference: `packaging/OptApp.spec` mentions `PyPDF2`
in a comment, but `PyPDF2` is imported nowhere in current code (verify with the
grep in Step 3 before touching the spec — out of scope to edit the spec here).

## Commands you will need

| Purpose        | Command                                            | Expected on success |
|----------------|----------------------------------------------------|---------------------|
| Confirm import | `python -c "import numpy,matplotlib,openpyxl,reportlab,PIL,tkinterdnd2"` | exit 0, no output |
| Get a pin      | `pip show <pkg>`                                    | prints Version line |
| Verify install | `pip install -r requirements.txt`                  | exit 0              |
| Tests          | `python -m pytest -q`                              | `19 passed`         |

## Scope

**In scope** (the only files you should create/modify):
- `requirements.txt` (create)
- `requirements-dev.txt` (create)
- `README.md` — only the "Cài đặt" section (lines ~24-33)
- `.gitignore` — add negation lines so the two new manifests are trackable
  (the repo's `.gitignore` has a blanket `*.txt` rule at line ~7 that would
  otherwise ignore `requirements.txt` / `requirements-dev.txt`)

**Out of scope** (do NOT touch):
- `packaging/OptApp.spec` — the stale `PyPDF2` comment is real but a separate
  cleanup; editing the build spec risks breaking the installer and needs a
  build to verify.
- Any source `.py` file — this plan only adds manifests and edits README prose.
- Do NOT run `pip freeze > requirements.txt` (it would capture the entire
  environment, including transitive and unrelated packages).

## Git workflow

- Branch: `advisor/001-dependency-manifest`
- One commit. Message style matches the repo's Vietnamese commit log, e.g.
  `Thêm requirements.txt + requirements-dev.txt; cập nhật hướng dẫn cài đặt`.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Create `requirements.txt` (runtime deps)

Create `requirements.txt` in the repo root with the runtime packages only.
Pin each to the installed version (run `pip show <pkg>` for `tkinterdnd2`'s
version). Use `>=` lower bounds so the app still installs on slightly newer
releases, but record the tested versions in a comment:

```
# OptApp runtime dependencies. Cài: pip install -r requirements.txt
# (tkinter là thư viện chuẩn của Python — KHÔNG cài qua pip;
#  trên Linux cài gói hệ thống python3-tk.)
numpy>=2.3.0
matplotlib>=3.10.0
tkinterdnd2>=0.4.0          # đổi theo `pip show tkinterdnd2`
openpyxl>=3.1.5            # xuất Excel (io_handlers/export_utils.py)
reportlab>=4.5.1          # xuất PDF (io_handlers/export_utils.py)
Pillow>=11.2.0            # xử lý ảnh/icon (export_utils, packaging/make_icon.py)
```

**Verify**: `python -c "import numpy,matplotlib,openpyxl,reportlab,PIL,tkinterdnd2"` → exit 0, no output.

### Step 2: Create `requirements-dev.txt` (build + test deps)

```
# OptApp dev/build dependencies. Cài: pip install -r requirements-dev.txt
-r requirements.txt
pytest>=8.0
pyinstaller>=6.21.0       # đóng gói (packaging/OptApp.spec)
markdown>=3.10.0          # chuyển tài liệu .md -> PDF (packaging/md_to_pdf.py)
```

**Verify**: `pip install -r requirements-dev.txt` → exit 0 (all already satisfied in dev env).

### Step 3: Confirm no other third-party deps were missed

Run this grep and confirm every non-stdlib top-level import is already covered
by the two manifests:

```
grep -rhoE "^(import|from) [a-zA-Z_][a-zA-Z0-9_]*" --include=*.py core io_handlers ui main.py packaging tests | sort -u
```

Expected: every third-party name in the output is one of
`numpy, matplotlib, tkinterdnd2, openpyxl, reportlab, PIL, markdown, PyInstaller`
(plus standard-library modules like `os, sys, subprocess, tkinter, threading,
re, json, math, time, tempfile, dataclasses, typing` and first-party packages
`core, io_handlers, ui`). If you find an uncovered third-party import, STOP and
report it (see STOP conditions).

**Verify**: no third-party import outside the listed set.

### Step 4: Update the README install section

Replace the install instructions at `README.md:24-33` so users install from the
manifest. Keep the existing Python-version note and the Linux `python3-tk`
note. Target shape:

```
## Cài đặt

1. Cài Python 3.9+ (đã kiểm thử trên 3.13).
2. Cài các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

> Trên Windows, `tkinter` thường đã có sẵn cùng Python. Trên Linux cần cài gói
> hệ thống `python3-tk`. Để đóng gói/chạy test: `pip install -r requirements-dev.txt`.
```

**Verify**: `grep -n "requirements.txt" README.md` → at least one match.

### Step 5: Confirm nothing broke

**Verify**: `python -m pytest -q` → `19 passed`.

## Test plan

No new automated tests (this plan adds manifests + docs only). Verification is:
- `pip install -r requirements.txt` exits 0.
- The import smoke command in Step 1 exits 0.
- `python -m pytest -q` still reports `19 passed`.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `requirements.txt` exists and lists numpy, matplotlib, tkinterdnd2, openpyxl, reportlab, Pillow
- [ ] `requirements-dev.txt` exists and references `-r requirements.txt` plus pytest, pyinstaller, markdown
- [ ] `python -c "import numpy,matplotlib,openpyxl,reportlab,PIL,tkinterdnd2"` exits 0
- [ ] `grep -n "requirements.txt" README.md` returns a match
- [ ] `python -m pytest -q` reports `19 passed`
- [ ] `git status` shows only `requirements.txt`, `requirements-dev.txt`, `README.md` modified/created
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Step 3's grep reveals a third-party import not in the known set (a dependency
  this plan didn't account for — report which module and where).
- `python -c "import ..."` fails for any package (the dev environment is
  missing a dep — report which one; do NOT `pip install` new packages to "fix" it).
- The README install section no longer matches the "Current state" excerpt
  (README drifted since this plan was written).

## Maintenance notes

- When a new third-party package is added to the code, it must be added to
  `requirements.txt` (runtime) or `requirements-dev.txt` (build/test).
- A reviewer should check that no stdlib module (especially `tkinter`) leaked
  into `requirements.txt`.
- Deferred: the stale `PyPDF2` comment in `packaging/OptApp.spec` and pinning
  in the `.spec`/installer are intentionally left out of this plan.
