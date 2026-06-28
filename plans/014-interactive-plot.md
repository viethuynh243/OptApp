# Plan 014: Interactive plot — zoom/pan toolbar + hover-to-read pile force

## Status
- Priority: P2 | Effort: M | Risk: LOW (isolated to plot_canvas.py) | Depends on: 013 (base) | Category: ui

## Why
The layout plot is static (`ui/plot_canvas.py` — no `NavigationToolbar`, no `mpl_connect`). Engineers can't zoom into a dense pile layout, pan, save the figure, or read an individual pile's exact force/coords. matplotlib provides zoom/pan/save for ~5 lines via its Tk toolbar; hover read-out is a small motion handler.

## Current state
- `PlotCanvas.__init__` (`:33-44`): `self.fig, self.ax = plt.subplots(...)`; `self.canvas = FigureCanvasTkAgg(self.fig, master=master)`; `self.widget = self.canvas.get_tk_widget()`; resize handling binds `<Configure>` on `self.widget`.
- main_window packs `self.plot_canvas.widget` (do NOT change main_window — keep `.widget` packable).
- `draw_simulation(self, coords, params, forces=None, m_forces=None, view_extent=None)` (`:146`) draws the piles; `coords` and `forces` are available there.

## Scope
In scope: `ui/plot_canvas.py` ONLY. Out of scope: main_window.py (must keep working by packing `plot_canvas.widget`), core/*.

## Steps
1. **Toolbar**: import `NavigationToolbar2Tk` from `matplotlib.backends.backend_tkagg`. In `__init__`, wrap canvas + toolbar in a container Frame so main_window's `self.widget.pack(...)` still works:
   - `import tkinter as tk`
   - `self.container = tk.Frame(master)`
   - create `self.canvas = FigureCanvasTkAgg(self.fig, master=self.container)`; `canvas_w = self.canvas.get_tk_widget()`
   - `self.toolbar = NavigationToolbar2Tk(self.canvas, self.container); self.toolbar.update()`
   - pack toolbar at `side=tk.BOTTOM, fill=tk.X`; pack `canvas_w` at `side=tk.TOP, fill=tk.BOTH, expand=True`
   - set `self.widget = self.container` (what main_window packs)
   - keep the resize `<Configure>` bind on the CANVAS widget (`canvas_w`), not the container, to preserve current redraw behavior. Keep a ref `self._canvas_w = canvas_w` if needed.
2. **Hover read-out**: in `draw_simulation`, store `self._hover_coords = np.asarray(coords)` and `self._hover_forces = forces` (or None). In `__init__`, create a hidden annotation once (`self._hover_annot = self.ax.annotate("", xy=(0,0), xytext=(12,12), textcoords="offset points", bbox=dict(boxstyle="round", fc="#ffffe0", ec="#888"), fontsize=8); self._hover_annot.set_visible(False)`), and connect `self.canvas.mpl_connect("motion_notify_event", self._on_hover)`.
3. **`_on_hover(event)`**: if `event.inaxes != self.ax` or no `_hover_coords`, hide annotation + draw_idle, return. Else find the nearest pile to `(event.xdata, event.ydata)`; if within a small distance (e.g. ≤ 0.6 m or scaled), set annotation text to `"Cọc i\n(x, y)\nP=… T"` (include force if `_hover_forces` available), position it at the pile, set visible, `self.canvas.draw_idle()`; otherwise hide. Wrap in try/except so a bad event never crashes the UI (consistent with `_run_redraw`'s defensive style).

## Done criteria
- Headless build OK: constructing `MainWindow` (which builds PlotCanvas) → exit 0; `app.plot_canvas.toolbar` exists; a `motion_notify_event` connection id is stored (e.g. `app.plot_canvas._hover_cid` is not None).
- A `draw_simulation` smoke call with a few coords + forces does not raise.
- `python -m pytest -q` → no failures.
- main_window still packs `plot_canvas.widget` successfully (BUILD OK proves it).
- `git status` shows only ui/plot_canvas.py.

## STOP conditions
- Constructing MainWindow/PlotCanvas fails after the change (report traceback).
- Making the toolbar work would require editing main_window (STOP — keep `.widget` as the single packable container).
