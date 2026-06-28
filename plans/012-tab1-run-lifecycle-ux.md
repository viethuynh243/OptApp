# Plan 012: Tab 1 run-lifecycle UX — lock the Run button, show live progress, allow Stop

## Status
- Priority: P1 | Effort: M | Risk: MED (touches the 3 run workers + worker threading)
- Depends on: none (base = unified feature tip 08d1c3f) | Category: dx / ui

## Why
The interactive tab is the primary workflow but during a multi-minute MCOC run it shows only the text "Đang chạy MCOC, vui lòng đợi..." (`ui/main_window.py:946`). The app looks frozen: no progress, no live call count, no Stop — and the Run button is NOT disabled, so a second click spawns a second optimization thread into the same `_opt_runs` dir. Tab 2 (batch) already has a Progressbar + Stop + status (`:1976-2015`); Tab 1 should reach parity.

## Current state
- `self.btn_run_opt` created at `:162-165`; never disabled.
- `run_optimize` (`:910`), `run_optimize_ext` (`:1286`), `run_refine_real` (`:1469`) each end with `threading.Thread(target=worker, daemon=True).start()`.
- The real evaluator (`core/blackbox.py make_real_evaluator`) exposes `evaluator.runner` whose `MCOCRunner.n_calls` increments per MCOC call — a free live progress signal.
- Results are marshalled back via `self.root.after(0, lambda: self._show_*(...))`.

## Scope
In scope: `ui/main_window.py` only.
Out of scope: `core/*` (do NOT modify the optimizer/runner — cancellation is cooperative via wrapping the evaluator); Tab 2 batch code; plot code.

## Steps
1. **Add run-state widgets** in the interactive left pane, just under the Run button (`:165`): a `ttk.Progressbar(mode="indeterminate")` (hidden/stopped by default) and a small `ttk.Label` (`self.lbl_run_status`) for "Đã gọi MCOC: N lần". Keep references on `self`.
2. **Add `self._run_cancel = threading.Event()`** in `__init__`. Add a Stop button (`self.btn_stop_opt`, initially `state="disabled"`) next to/under Run.
3. **Add helpers**:
   - `_set_running(True/False)`: disables `btn_run_opt` (+ the ext/refine triggers) and enables `btn_stop_opt` when running; starts/stops the indeterminate progressbar; clears `_run_cancel`. Reverse on False.
   - `_poll_run_progress(evaluator)`: via `root.after(250, ...)`, read `evaluator.runner.n_calls` and update `lbl_run_status`; reschedule while running.
   - `_request_stop_opt()`: sets `self._run_cancel`; updates status to "Đang dừng...".
4. **Wrap the evaluator for cooperative cancel**: before each MCOC call, if `self._run_cancel.is_set()` raise `MCOCError("Đã dừng theo yêu cầu")`. Implement by wrapping the evaluator the worker uses (do NOT change core). The worker catches that and reports "Đã dừng".
5. **Wire all 3 workers**: call `_set_running(True)` + start polling before `Thread.start()`; in the worker's `finally` (via `root.after`), call `_set_running(False)` and stop polling. Guard against double-run: if already running, the Run handlers return early (the button is disabled, but also check a `self._is_running` flag).

## Done criteria
- MainWindow still builds headless (`import` + construct with mocked messagebox) — exit 0.
- `python -m pytest -q` → no failures (31 passed on a machine with sample data; or 29 passed/2 skipped without).
- Widgets exist: `app.btn_stop_opt`, `app.progress_run` (or chosen name), `app.lbl_run_status`.
- Behavioral smoke: calling `_set_running(True)` disables `btn_run_opt` and enables `btn_stop_opt`; `_set_running(False)` reverses.
- `git status` shows only `ui/main_window.py`.

## STOP conditions
- Constructing MainWindow fails after the change (report traceback).
- Any core file would need editing to implement cancel — STOP (must stay in main_window via evaluator wrapping).
