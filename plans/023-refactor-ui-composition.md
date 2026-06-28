# Plan 023 — Tái cấu trúc UI theo composition + dọn hạ tầng (giữ nguyên hành vi)

## Mục tiêu
Tách `ui/main_window.py` (**3247 dòng, 1 class, 7 trách nhiệm**) thành các
module/component cohesive theo kiến trúc **composition (controller + view)**, và
dọn hạ tầng package để "chuẩn chỉ, dễ kiểm soát lỗi, nâng cấp, mở rộng".

**INVARIANT TUYỆT ĐỐI:** giữ NGUYÊN hành vi 1:1. Mỗi pha xong phải PASS cả 3
cổng an toàn dưới đây — golden KHÔNG được đổi (mọi lệch = hồi quy phải sửa).

## Lưới an toàn (chạy sau MỖI pha)
```
python -m pytest -q                       # 54 passed (backend)
python tests/_ui_regression.py 2>/dev/null # [PASS] snapshot KHOP golden
python tests/_smoke_full.py               # 16/16 PASS (bắt crash toàn app)
```
- `tests/_ui_regression.py` (mới, Plan 023): tự chứa, dựng MainWindow thật, chạy
  luồng thường + mở rộng có seed, chụp snapshot hành vi (ô kết quả, combobox,
  KPI audit, digest config) so với `_ui_regression_golden.json`.
- KHÔNG `--update` golden trừ khi thay đổi hành vi là CỐ Ý (refactor này thì không).

## Kiến trúc đích (ui/)
```
ui/
  main_window.py        — MainWindow: vỏ mỏng. Giữ state chia sẻ + tạo & nối
                          component, menu, notebook, status bar; ủy quyền.
  constants.py          — magic numbers UI (geometry, preset NSGA-II, màu, view keys)
  strings.py            — nhãn/chuỗi tiếng Việt (tên phương án, tên chế độ xem)
  widgets/
    __init__.py
    tooltip.py          — class Tooltip (rê chuột)
    text_logger.py      — append + autoscroll cho Text widget
    form_builder.py     — build_form_grid(): label+entry lặp lại
    widget_utils.py     — set_state_recursive(), safe_float/safe_int
  controllers/
    __init__.py
    params.py           — ParamsController: get_params_dict, _pget, validate,
                          TCVN toggle/preview, _load_demo_geotech
    loads.py            — LoadsController: CRUD tải, paste CSV, refresh_loads_ui
    file_ops.py         — FileController: load/drop/process_multiple_files/save/clear
    optimization.py     — OptimizationController: run_optimize(_ext), refine,
                          threading, progress, cancel, validate MCOC
    results.py          — ResultsView: render kết quả, show_nsga2/ext/refine,
                          populate_comboboxes, _update_kpi, _maybe_suggest_cap
    simulation.py       — SimulationView: update_simulation, _build_constraint_data,
                          _config_fully_ok, _global_view_extent
  tabs/
    __init__.py
    interactive_tab.py  — InteractiveTab: dựng Tab 1 (giữ widget refs)
    batch_tab.py        — BatchTab: dựng Tab 2 + run_batch + quản lý danh sách file
  plot_canvas.py        — (giữ nguyên)
```
**Cơ chế chia sẻ state:** MainWindow là "shared context". Component nhận tham
chiếu `app` (MainWindow) và thao tác qua nó (`app.params`, `app.loads`,
`app.current_config`, `app.txt_result`, ...). Đây là composition giữ-hành-vi:
thân hàm gần như không đổi, chỉ `self.x` → `self.app.x` cho state/widget chia sẻ,
và lời gọi chéo → `self.app.<component>.<method>()`. Widget do component nào dựng
thì component đó giữ ref; truy cập chéo đi qua `app`.

## Các pha (làm tuần tự, mỗi pha 1 commit, verify trước khi sang pha sau)

### Pha 0 — Lưới an toàn ✅ (đã xong trong session này)
`tests/_ui_regression.py` + golden. Baseline: pytest 54 passed, smoke 16/16.

### Pha 1 — Dọn hạ tầng (rủi ro THẤP, không đụng logic)
- Thêm `__init__.py` rỗng (có docstring 1 dòng) vào `core/`, `ui/`, `io_handlers/`,
  `tests/` → package tường minh thay vì namespace ngầm (PEP 420).
- `.gitignore`: thêm `tests/*.log`, `tests/_ui_shots/`, `tests/_work/`,
  `packaging/*.zip`, `tests/_ui_regression_golden.json` (golden là cục bộ máy dev).
  → cân nhắc giữ golden trong repo nếu muốn CI; mặc định KHÔNG track.
- Kiểm tra `packaging/OptApp.spec` còn build được sau khi thêm `__init__.py`
  (hidden imports / pathex không đổi → an toàn).
- Verify: 3 cổng PASS.

### Pha 2 — Widgets lá (rủi ro THẤP, trích thuần)
Trích các tiện ích KHÔNG phụ thuộc state MainWindow:
`Tooltip`, `TextLogger`, `form_builder`, `widget_utils` (set_state_recursive,
safe_float/int), `ui/constants.py`, `ui/strings.py`. Thay usage trong main_window.
- Verify: 3 cổng PASS.

### Pha 3 — Controller logic (rủi ro TRUNG BÌNH)
Tách lần lượt, MỖI controller 1 commit + verify:
1. `ParamsController` (get_params_dict, _pget, validate, TCVN, demo geotech)
2. `LoadsController` (CRUD tải, paste CSV)
3. `FileController` (load/process/save/clear)
4. `ResultsView` (render + show_* + populate_comboboxes + KPI)
5. `SimulationView` (update_simulation + build_constraint_data)
6. `OptimizationController` (run_optimize(_ext) + refine + threading)
MainWindow tạo các component trong `__init__`; UI `command=` trỏ tới
`self.<component>.<method>`. Lời gọi chéo qua `app`.

### Pha 4 — Tab components (rủi ro TRUNG BÌNH–CAO)
1. `BatchTab` (setup_batch_ui + run_batch + quản lý file) — độc lập hơn, làm trước.
2. `InteractiveTab` (setup_interactive_ui) — dựng widget Tab 1, gắn command vào
   các controller đã tách ở Pha 3.
MainWindow.setup_ui chỉ còn tạo notebook + 2 tab component + menu + status bar.
- Verify: 3 cổng PASS + soi mắt app thật (chạy `python main.py`).

### Pha 5 — Xác minh cuối + tài liệu
- 3 cổng PASS; chạy `python main.py` soi 2 tab + cả 2 luồng.
- Cập nhật `CHANGELOG.md`, `core/version.py` (→ minor bump), `README.md` (cây thư mục).
- Cập nhật `docs/vault/2-Kiến trúc/Tổng quan module.md` nếu cần.

## STOP conditions
- Bất kỳ cổng nào FAIL sau 1 pha → DỪNG, sửa cho xanh trước khi đi tiếp. KHÔNG
  `--update` golden để "vá".
- Nếu một pha quá rủi ro để giữ hành vi (vd state đan xen sâu) → chia nhỏ hơn,
  KHÔNG gộp.

## Ghi chú
- Trước đây refactor này bị xếp "NOT PLANNED" (L effort, HIGH risk — threading +
  Tk event loop) trong plans/README.md (mục "considered/rejected"). Nay làm có chủ
  đích, với lưới an toàn snapshot mới nên rủi ro đã giảm đáng kể.
- Backend (`core/`, `core/ext/`, `io_handlers/`) đã sạch — KHÔNG nằm trong phạm vi
  pha này (cleanup backend có thể là plan riêng sau).

## Trạng thái thực thi (DONE — 2026-06-28, v1.9.1)
- Pha 0 (lưới an toàn): DONE — `tests/_ui_regression.py` + golden; baseline pytest 54 passed, smoke 16/16.
- Pha 1 (hạ tầng): DONE — `__init__.py` cho core/ui/io_handlers; `.gitignore` (+`*.log`, golden, `tests/_work/`).
- Pha 2 (widgets lá): DONE — `ui/widgets/{tooltip,widget_utils}.py`, `ui/constants.py` (+preset NSGA-II).
- Pha 3 (controllers): DONE — `ui/controllers/{params,loads,file_ops,results,simulation,optimization}.py`.
- Pha 4 (tabs): DONE — `ui/tabs/{interactive_tab,batch_tab}.py`.
- Pha 5 (xác minh + dọn import + tài liệu): DONE.

**Kết quả:** `ui/main_window.py` 3247 → **515 dòng** (vỏ điều phối + delegator). Mọi pha
PASS cả 3 cổng; golden KHÔNG đổi với 2 luồng gốc (chỉ MỞ THÊM mục `after_clear` để
phủ `clear_loads`). App khởi động OK theo đường dẫn `main.py`. version → 1.9.1.

**Bug bắt được nhờ lưới an toàn (đã sửa hết):**
1. Tool sinh controller bỏ sót `delattr(self, ...)` → `clear_loads` lỗi; `_smoke_full`
   bắt; sửa tool + thêm bước `after_clear` vào golden.
2. Kiểm SÂU (rà nhánh chưa chạy): `ui/tabs/batch_tab.py` thiếu import `re`/`subprocess`/
   `numpy` → kéo-thả batch / mở thư mục KQ / chạy hàng loạt sẽ lỗi `NameError`.
   Phát hiện bằng deep-drive + quét AST tên-chưa-định-nghĩa; đã thêm 3 import +
   mở rộng `_smoke_full` lên 18 bước (phủ 3D/SSI/capdesign + drag-drop batch).

**Phép kiểm tĩnh đã chạy (đều sạch):** (a) mọi `self.X` trong controllers/tabs là
`app` hoặc method cùng class — 0 rò rỉ; (b) mọi `self.app.X` đọc đều có định nghĩa
trên MainWindow; (c) không tên chưa định nghĩa (kiểu pyflakes); (d) không method
trùng. App khởi động OK theo đường dẫn `main.py`.

**Đã làm thêm (sau yêu cầu "kiểm kỹ + tiếp tục"):**
- `ui/strings.py` — gom nhãn phương án (`CFG_GOC/CFG_DEXUAT/CFG_PREFIX`) + khóa chế độ
  xem (`VIEW_LAYOUT/AUDIT/MODEL3D/SSI/CAPDESIGN`); thay ở results/simulation/file_ops/
  interactive_tab → nơi ĐẶT == nơi KIỂM (không thể lệch). Golden + smoke 18/18 xác nhận.
- Untrack 3 log tạm (`tests/*.log`) + sửa bug `.gitignore` (comment cùng dòng) cho
  `*_tmp.html`/`_*.png`/`*.log`.

**Còn lại (ngoài phạm vi — plan riêng nếu cần):** cleanup backend (report_writer
dùng lại `mechanics`, `blackbox_ext` kế thừa `MCOCBlackbox`); cân nhắc bỏ
`run_refine_real` (legacy, không còn nơi gọi).
