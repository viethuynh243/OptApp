# Plan 013: Input guidance & safety — tooltips, inline validation, status bar, shortcuts, workflow hint

## Status
- Priority: P1 | Effort: M | Risk: MED | Depends on: 012 (base) | Category: ui/dx

## Why
The form gives no inline help and validates only on Run via modal popups (`run_optimize:892-907`). Engineers (esp. new ones) must consult external docs for `[Po]/[Ct]/[M]`, `R7/R8`, "bệ gọn", and get no as-you-type feedback. No status bar, no keyboard shortcuts, no in-app workflow guidance.

## Current state
- Param entries built at `:202-211` (`self._param_entries[k]`), vars `self.params[k]` (StringVar). Required: L_X, L_Y, D_PILE, P_LIMIT.
- Labels for [Po]/[Ct]/[M] at `:199-200`; R7/R8 checkbuttons `:303-306`; secondary radios `:279-282`; k/c combobox `:288`.
- No Tooltip class, no status bar, no `root.bind` shortcuts, no trace/validatecommand anywhere.
- Frames in order: "Thông số Bài toán", "Tổ hợp Tải trọng", "Điều Khiển Tối Ưu", "Cấu hình MCOC (bắt buộc)".

## Scope
In scope: `ui/main_window.py` ONLY. Out of scope: core/*, plot, Tab 2 internals (status bar may be global at root bottom — that's fine).

## Steps
1. **Tooltip helper**: add a small `class Tooltip` (hover → Toplevel label, show on `<Enter>`, hide on `<Leave>`), or a `def _tip(widget, text)` helper. Attach concise Vietnamese tooltips to: the [Po]/[Ct]/[M] labels (`:199-200`), D_PILE label, R7/R8 checkbuttons, the two "Ưu tiên" radios, the "K/c tối thiểu" combobox, and the "Tự thu bệ" checkbox. Keep text short (1 sentence each).
2. **Inline validation (FocusOut + as-you-type)**: add `_validate_inputs()` that checks the 4 required vars (L_X, L_Y, D_PILE, P_LIMIT) are numeric and > 0; red-tint invalid entries (e.g. `entry.config(...)` background or a red `*` marker) and write a one-line summary to the status bar ("Thiếu/không hợp lệ: Lx, [Po]"). Bind via `trace_add("write", ...)` on the 4 vars and/or `<FocusOut>` on the entries. Keep the existing Run-time messagebox gate as the final guard (do not remove it; do not fully disable Run to avoid clashing with plan 012's running-state).
3. **Status bar (global, bottom of root)**: add `self.lbl_status` (a `tk.Label`, anchor w) packed at the bottom of the root window (below the Notebook). Update it from: file load ("Đã nạp <file>: N cọc, M tổ hợp"), validation summary, run start/stop. Default "Sẵn sàng.".
4. **Keyboard shortcuts** (root.bind): `<Control-o>` → load_file, `<Control-r>` → run_optimize, `<Control-s>` → save_file, `<F1>` → a help messagebox summarizing the 4-step workflow + units. Guard `<Control-r>` so it no-ops when `self._is_running`.
5. **Workflow hint banner**: at the very top of the scrollable input area (inside `inner`, before "Thông số Bài toán"), add a compact muted label: "Quy trình: ① Cấu hình MCOC  →  ② Mở file đầu vào  →  ③ Nhập thông số & tải  →  ④ ▶ Chạy". 1 line, foreground "#666".

## Done criteria
- Headless build OK (mock messagebox; construct MainWindow) → exit 0.
- `python -m pytest -q` → no failures.
- Exists: a Tooltip helper (class or `_tip`); `app.lbl_status`; `_validate_inputs` method; `root.bind` for Control-o/r/s and F1 (check `root.bind()` returns non-empty for these).
- Behavioral smoke: set `params['P_LIMIT']` to "0" → `_validate_inputs()` reports it invalid (status text mentions [Po] or returns False); set all 4 valid → reports OK.
- `git status` shows only ui/main_window.py.

## STOP conditions
- MainWindow construction fails (report traceback).
- A change would require editing core/* (STOP).
