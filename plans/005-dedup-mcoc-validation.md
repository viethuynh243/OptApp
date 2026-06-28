# Plan 005: Extract the duplicated MCOC-setup validation in the UI into one helper

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 0ec2135..HEAD -- ui/main_window.py`
> If it changed since this plan was written, compare the "Current state"
> excerpts against the live code before proceeding; on a mismatch, treat it as
> a STOP condition. NOTE: `ui/main_window.py` is large (2364 lines) and likely
> to drift — re-read the three target methods before editing.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `0ec2135`, 2026-06-20

## Why this matters

Three optimization entry points in the UI — `run_optimize`, `run_optimize_ext`,
and `run_refine_real` — each re-implement the same "is MCOC configured?" gate
(executable path exists, input file exists, original pile coordinates present),
with three slightly different message texts ("Cần cấu hình MCOC" vs "Thiếu MCOC",
"Thiếu file MCOC gốc" vs "Thiếu file input gốc"). Any change to the required
preconditions — or just making the wording consistent — currently means editing
three places and risks them drifting further. Consolidating the shared trio into
one helper removes the duplication without changing behavior.

## Current state

There are three near-identical validation blocks. The **common** checks across
all three are: (a) `exe_path` non-empty and exists on disk, (b) `input_filepath`
non-empty and exists, (c) `original_coords` present.

`ui/main_window.py:909-923` (`run_optimize`):

```python
        # 2) BẮT BUỘC MCOC — không chấp nhận phương án xấp xỉ
        exe = self.params['exe_path'].get().strip()
        if not exe or not os.path.exists(exe):
            messagebox.showwarning(
                "Cần cấu hình MCOC",
                "Chương trình đánh giá mọi phương án bằng MCOC (chính xác).\n"
                "Hãy chọn đường dẫn MCOC Batch ở mục \"Cấu hình MCOC (bắt buộc)\".")
            return
        if (not self.input_filepath or not os.path.exists(self.input_filepath)
                or not getattr(self, 'original_coords', None)):
            messagebox.showwarning(
                "Thiếu file MCOC gốc",
                "Cần mở FILE INPUT MCOC gốc (.txt, có tọa độ cọc gốc) làm template.\n"
                "Dùng \"Mở file đầu vào\" để nạp file input MCOC — không phải file _result hay CSV.")
            return
```

`ui/main_window.py:1285-1294` (`run_optimize_ext`):

```python
        exe = self.params['exe_path'].get().strip()
        if not exe or not os.path.exists(exe):
            messagebox.showwarning("Cần cấu hình MCOC",
                                   "Tối ưu mở rộng chấm bằng MCOC chính xác. Hãy chọn MCOC Batch.")
            return
        if (not self.input_filepath or not os.path.exists(self.input_filepath)
                or not getattr(self, 'original_coords', None)):
            messagebox.showwarning("Thiếu file MCOC gốc",
                                   "Cần mở FILE INPUT MCOC gốc (.txt, có tọa độ cọc gốc) làm template.")
            return
```

`ui/main_window.py:1466-1478` (`run_refine_real`) — slightly different: it
splits the checks and uses different titles, and it does NOT also require the
`required` params / `loads` that the other two check earlier:

```python
        exe = self.params['exe_path'].get().strip()
        if not exe:
            messagebox.showwarning("Thiếu MCOC", "Chưa chọn đường dẫn MCOC Batch (Command Line).")
            return
        if not self.input_filepath or not os.path.exists(self.input_filepath):
            messagebox.showwarning(
                "Thiếu file input gốc",
                "Chế độ MCOC thực cần file INPUT MCOC gốc làm template.\n"
                "Hãy load file input (.txt/.dat) của MCOC — không phải file _result.")
            return
        if not getattr(self, 'original_coords', None):
            messagebox.showwarning("Thiếu phương án gốc", "File input chưa có tọa độ cọc gốc.")
            return
```

Note `run_refine_real`'s first check is `if not exe:` (no `os.path.exists`).
The unified helper should use the stricter `not exe or not os.path.exists(exe)`
form — this is a deliberate, safe tightening (refine would otherwise proceed
with a non-existent exe and fail deeper). Call this out in your commit message.

The class uses `messagebox` (imported at top of `ui/main_window.py`) and reads
`self.params['exe_path']` (a Tk variable), `self.input_filepath`, and
`self.original_coords`.

## Commands you will need

| Purpose        | Command                                              | Expected on success |
|----------------|-----------------------------------------------------|---------------------|
| Syntax check   | `python -c "import ast; ast.parse(open('ui/main_window.py',encoding='utf-8').read())"` | exit 0 |
| Import module  | `python -c "import ui.main_window"`                 | exit 0, no error    |
| Full suite     | `python -m pytest -q`                               | all pass            |
| Count helper   | `grep -n "_validate_mcoc_setup" ui/main_window.py`  | 1 def + 3 calls = 4 |

NOTE: the test suite does NOT import or exercise the GUI, so it will pass
regardless. The real verification here is an import-time/AST check plus a manual
read; do NOT claim behavior is verified by the unit tests.

## Scope

**In scope** (the only file you should modify):
- `ui/main_window.py` — add one private method and replace the three blocks
  above with calls to it.

**Out of scope** (do NOT touch):
- The `required` params check and the `if not self.loads:` check that precede
  the MCOC block in `run_optimize` (`:892-907`) and `run_optimize_ext`
  (`:1275-1284`) — those are NOT shared by `run_refine_real`; leave each method's
  own param/loads checks where they are. The helper covers ONLY the exe/input/
  coords trio.
- Any threading, evaluator, or `worker()` logic in the three methods.
- All other methods of `MainWindow`. This is not the place to refactor the
  god-object more broadly (that is a separate, larger effort).

## Git workflow

- Branch: `advisor/005-dedup-mcoc-validation`
- One commit, message e.g.
  `Gộp kiểm tra cấu hình MCOC vào _validate_mcoc_setup (đồng nhất thông báo)`.
  Mention the refine tightening (exe existence now checked).
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Add the helper method

Add a private method on `MainWindow` (place it near the three callers, e.g. just
above `run_optimize`). It returns `True` when setup is valid, and shows the
appropriate warning + returns `False` otherwise:

```python
    def _validate_mcoc_setup(self):
        """Kiểm tra cấu hình MCOC bắt buộc (exe + file input gốc + tọa độ cọc gốc).

        Trả về True nếu hợp lệ; nếu thiếu thì hiện cảnh báo phù hợp và trả về False.
        Dùng chung cho run_optimize / run_optimize_ext / run_refine_real.
        """
        exe = self.params['exe_path'].get().strip()
        if not exe or not os.path.exists(exe):
            messagebox.showwarning(
                "Cần cấu hình MCOC",
                "Mọi phương án được chấm bằng MCOC (chính xác).\n"
                "Hãy chọn đường dẫn MCOC Batch ở mục \"Cấu hình MCOC (bắt buộc)\".")
            return False
        if (not self.input_filepath or not os.path.exists(self.input_filepath)
                or not getattr(self, 'original_coords', None)):
            messagebox.showwarning(
                "Thiếu file MCOC gốc",
                "Cần mở FILE INPUT MCOC gốc (.txt, có tọa độ cọc gốc) làm template.\n"
                "Dùng \"Mở file đầu vào\" để nạp file input MCOC — không phải file _result hay CSV.")
            return False
        return True
```

**Verify**: `python -c "import ui.main_window"` → exit 0.

### Step 2: Replace the block in `run_optimize`

Replace lines `909-923` (the two `if`-blocks shown in Current state) with:

```python
        # 2) BẮT BUỘC MCOC — không chấp nhận phương án xấp xỉ
        if not self._validate_mcoc_setup():
            return
```

Keep the surrounding `required`/`loads` checks and the `params = self.get_params_dict()`
line that follows.

**Verify**: `grep -n "_validate_mcoc_setup" ui/main_window.py` now shows the def + 1 call.

### Step 3: Replace the block in `run_optimize_ext`

Replace lines `1285-1294` with:

```python
        if not self._validate_mcoc_setup():
            return
```

**Verify**: the call count rises to 2.

### Step 4: Replace the block in `run_refine_real`

Replace lines `1466-1478` (all three `if`-blocks) with:

```python
        if not self._validate_mcoc_setup():
            return
```

This is where the behavior tightens slightly: refine now also requires the exe
to exist on disk (previously only non-empty). This is intended.

**Verify**: `grep -n "_validate_mcoc_setup" ui/main_window.py` shows exactly the
def line + 3 call sites (4 matches total).

### Step 5: Confirm nothing broke at import/parse time and tests still pass

**Verify**:
- `python -c "import ast; ast.parse(open('ui/main_window.py',encoding='utf-8').read())"` → exit 0
- `python -c "import ui.main_window"` → exit 0
- `python -m pytest -q` → all pass (unchanged count)

## Test plan

The GUI is not unit-tested, so there are no automated assertions for this
behavior. Verification is:
- The module parses and imports cleanly (Step 5).
- The helper is defined once and called from exactly the three methods (grep
  count = 4).
- A manual smoke check is recommended but optional: run `python main.py`, click
  "CHẠY TỐI ƯU HÓA" with no MCOC configured, and confirm the warning appears
  (note in your report whether you were able to do this).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -c "_validate_mcoc_setup" ui/main_window.py` returns `4` (1 def + 3 calls)
- [ ] The three original duplicated blocks are gone: `grep -c "Hãy chọn MCOC Batch" ui/main_window.py` returns `0` (the ext-specific wording removed)
- [ ] `python -c "import ui.main_window"` exits 0
- [ ] `python -m pytest -q` passes with the same count as before this plan
- [ ] `git status` shows only `ui/main_window.py` modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The three methods no longer match the "Current state" excerpts (the file
  drifted — re-read before editing; the line numbers will have moved).
- `import ui.main_window` fails (e.g. a paste indentation error) and you cannot
  resolve it in one fix.
- You find a fourth caller doing the same validation inline — report it; it can
  join the helper, but confirm its message expectations first.

## Maintenance notes

- New optimization entry points should call `_validate_mcoc_setup()` rather than
  re-inlining the checks.
- A reviewer should confirm `run_refine_real` still behaves correctly with the
  now-stricter exe-existence check (it should: a missing exe would have failed
  later anyway).
- This is a deliberately narrow refactor; the broader `main_window.py`
  god-object cleanup (extracting orchestration out of the UI) is a separate,
  higher-risk effort not attempted here.
