# Plan 015: GUI panel to compute [Po]/[Ct] from TCVN 10304:2014 (Rc,d) — expose the merged feature

## Status
- Priority: P1 (expansion) | Effort: M | Risk: MED | Depends on: 014 (base) | Category: ui / feature

## Why
The merged TCVN feature (`core/tcvn.py`) can auto-compute design capacities Rc,d/Rt,d from characteristic capacity Rc,k + reliability factors, but it only activates if `params` carries `R_C_K` **via file/CSV** — there is NO GUI to enter it. Engineers using the app can't access it. Add an optional input panel so they can let the program derive `[Po]/[Ct]` per Điều 7.1.11 instead of typing raw allowables.

## Current state (param contract — verified)
`core/tcvn.apply_design_capacities(params)` reads these keys and OVERRIDES `P_LIMIT` (and `P_TENSION` if `R_T_K`) when `R_C_K>0`:
- `R_C_K` (sức chịu nén tiêu chuẩn), `R_T_K` (kéo, optional)
- `GAMMA_0` (default 1.15), `GAMMA_K` (default 1.40), `GAMMA_K_T` (default = GAMMA_K)
- `GAMMA_N` explicit, OR `IMPORTANCE_LEVEL` ∈ {I,II,III} → {1.20,1.15,1.10}
- Formula: `Po = (γ0/γn)·(Rck/γk)` via `tcvn.design_axial_capacity(R_ck, g0, gn, gk)`; `tcvn.resolve_gamma_n(params)` resolves γn.

`get_params_dict()` (`ui/main_window.py:594-625`) builds `d` from `self.params`, then ALREADY calls `tcvn.apply_design_capacities(d)` at `:623-624`. So injecting the TCVN keys into `d` before nothing else is needed — the override happens automatically.

## Scope
In scope: `ui/main_window.py` ONLY. Out of scope: `core/tcvn.py` (use it as-is), other core, plot.

## Steps
1. **Tk vars** in `__init__`: `self.var_tcvn_enable = tk.BooleanVar(value=False)`; StringVars `self.var_rck`, `self.var_rtk` (""), `self.var_g0` ("1.15"), `self.var_gk` ("1.40"), `self.var_gk_t` (""), and `self.var_imp_level` ("II").
2. **Panel** (inside the scrollable `inner`, near "Thông số Bài toán"): a `tk.LabelFrame "Sức chịu tải theo TCVN 10304:2014 (tùy chọn)"` with a checkbutton "Tự tính [Po]/[Ct] từ Rc,k" bound to `var_tcvn_enable` + a body frame (shown/hidden by a `_toggle_tcvn()` like the ext toggle at `:322`). Body fields: Rc,k (T), Rt,k (T, optional), γ0, γk, γk_t (optional), and cấp công trình (Combobox I/II/III → γn). Add brief tooltips (reuse the Tooltip helper from plan 013).
3. **Live preview**: a label in the body that, via `trace_add("write", ...)` on the TCVN vars, shows `"→ Rc,d = {Po:.1f} T" (+ "; Rt,d = {Ct:.1f} T" if Rt,k>0)` by calling `tcvn.design_axial_capacity(...)` with the current factors (resolve γn from the level via `tcvn.GAMMA_N_BY_LEVEL`). Guard against blank/invalid → show "→ nhập Rc,k để tính".
4. **Feed into get_params_dict()**: just BEFORE the existing `tcvn.apply_design_capacities(d)` call (`:623`), if `self.var_tcvn_enable.get()` and Rc,k parses >0, set `d['R_C_K']`, `d['R_T_K']` (if given), `d['GAMMA_0']`, `d['GAMMA_K']`, `d['GAMMA_K_T']` (if given), `d['IMPORTANCE_LEVEL']` (from the combobox). The existing call then overrides `P_LIMIT/P_TENSION`. Do not duplicate the apply call.
5. **UX nicety**: when `var_tcvn_enable` is on, set the `[Po]`/`[Ct]` entries (`self._param_entries['P_LIMIT'/'P_TENSION']`) to `state="readonly"` and reflect the computed value into their vars (optional but recommended so the user sees the derived number); restore `state="normal"` when off. Keep this minimal/robust.

## Done criteria
- Headless build OK (construct MainWindow) → exit 0.
- Vars exist: `app.var_tcvn_enable`, `app.var_rck`, etc.
- Behavioral: with `var_tcvn_enable=True`, `var_rck="1500"`, level "II" → `d = app.get_params_dict()` has `d['_capacity_source']=='tcvn_7.1.11'` and `abs(d['P_LIMIT'] - tcvn.design_axial_capacity(1500, 1.15, 1.15, 1.40)) < 1e-6`.
- With `var_tcvn_enable=False`: `get_params_dict()` does NOT inject R_C_K (uses the typed [Po]); `_capacity_source` is 'input' (or absent override).
- `python -m pytest -q` → no failures.
- `git status` shows only ui/main_window.py.

## STOP conditions
- MainWindow construction fails (report traceback).
- `core/tcvn.py` would need editing (STOP — the contract above is sufficient).
- The behavioral check's P_LIMIT doesn't match `design_axial_capacity` (the injection isn't reaching `apply_design_capacities` — re-check ordering in get_params_dict).
