# Plan 016: Color-code the results panel for at-a-glance scannability

## Status
- Priority: P3 | Effort: S | Risk: LOW | Depends on: 015 (base) | Category: ui

## Why
Results render as flat monospace text in `self.txt_result` (`_render_results`, `ui/main_window.py:1057-1140`). It's information-dense but hard to scan: pass/fail status, the recommendation, and the options table all look the same. Adding color tags (ĐẠT green, KHÔNG ĐẠT red, headers bold/blue) makes status pop without restructuring the (carefully formatted, multi-case) output. NOTE: a full sortable Treeview of the options was deliberately deferred — it needs a result-pane layout split and is higher risk; this plan is the safe scannability win.

## Current state
- `self.txt_result = tk.Text(..., font=("Consolas", 10))` created at `:347`.
- `_render_results` (`:1057`) writes via `ins = lambda s="": self.txt_result.insert(tk.END, s + "\n")`.
- Status markers in the text: `"DAT"` / `"KHONG DAT"` (`:1098`), section headers like `"  PHUONG AN KIEN NGHI"` and `"="*60` / `"-"*60` rules, `"Khong tim thay phuong an..."` / `"Khong co phuong an nao DAT..."` (`:1093,1138`).
- All three result paths (`_show_nsga2_results`, `_show_ext_results`, `_show_refine_results`) funnel through `_render_results`.

## Scope
In scope: `ui/main_window.py` ONLY. Out of scope: core/*, plot, restructuring the result pane into a Treeview (deferred).

## Steps
1. **Define tags** once (e.g. in `setup_interactive_ui` right after `txt_result` is created, `:347`):
   - `self.txt_result.tag_config("ok",   foreground="#1e8449")`  (xanh = ĐẠT)
   - `self.txt_result.tag_config("bad",  foreground="#b03a2e")`  (đỏ = KHÔNG ĐẠT / không có nghiệm)
   - `self.txt_result.tag_config("head", foreground="#1a3c5e", font=("Consolas", 10, "bold"))`
   - `self.txt_result.tag_config("muted", foreground="#888")`
2. **Tagged insert helper**: in `_render_results`, replace the bare `ins` with one that optionally takes a tag and applies it to the inserted line, e.g.:
   ```python
   def ins(s="", tag=None):
       start = self.txt_result.index(tk.END)
       self.txt_result.insert(tk.END, s + "\n")
       if tag:
           self.txt_result.tag_add(tag, start, self.txt_result.index(tk.END))
   ```
3. **Apply tags** (minimal, targeted):
   - The three header blocks ("PHUONG AN KIEN NGHI", "PHUONG AN GOC : ...", "CAC PHUONG AN DAT ... N phuong an") and their `=`/`-` rules → `"head"`.
   - The `PHUONG AN GOC` status line: pass `"ok"` when `orig['ok']`, else `"bad"` (currently `:1100`).
   - "Khong tim thay phuong an thoa man." (`:1093`) and "Khong co phuong an nao DAT..." (`:1138`) → `"bad"`.
   - The recommendation block when `rec` exists → leave default (or the "Kieu/So coc" lines optionally `"ok"`). The limits note line (`:1136`) → `"muted"`.
   - Keep all existing text/format/columns EXACTLY — only add tags, change nothing about the strings or numbers.

## Done criteria
- Headless build OK (construct MainWindow) → exit 0.
- Behavioral: after building, the tags exist — `"ok" in app.txt_result.tag_names()` etc. And rendering a small fake results dict (with `original_config={'ok':True,'n':6,'pmax':400,'pmin':0}` and `all_valid_configs=[]`) via `app._render_results({...})` does not raise and produces tagged ranges (`app.txt_result.tag_ranges("head")` non-empty).
- `python -m pytest -q` → no failures.
- The result text content is unchanged except for coloring (diff shows only tag plumbing + the `ins` helper, no string/number edits).
- `git status` shows only ui/main_window.py.

## STOP conditions
- MainWindow construction or a sample `_render_results` call fails (report traceback).
- You find the result strings differ from "Current state" (drift) — re-read before tagging.
