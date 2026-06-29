# Gói tối ưu MỞ RỘNG (branch `feature/toiuu-mo-rong`)

> **Mã:** OA-DOC-07 · **Phiên bản:** 1.0 · **Cập nhật:** 2026-06-29 · **Trạng thái:** Approved · **Căn cứ:** core/ext/, io_handlers/mcoc_writer_ext.py


Ba tính năng mở rộng, **tách biệt hoàn toàn** module lõi cũ (không sửa
`core/nsga2_optimizer.py`, `core/constants.py`, `io_handlers/mcoc_writer.py`,
`core/blackbox.py`). Toàn bộ nằm trong `core/ext/` + `io_handlers/mcoc_writer_ext.py`.

## 1. Bật R7 (lực ngang) và R8 (tương tác P-M)

Lõi đã có sẵn 2 cờ `ENABLE_LATERAL_CHECK` (R7) và `ENABLE_PM_INTERACTION` (R8)
nhưng để **tắt**. Luồng mở rộng bật chúng qua context manager
`core/ext/nsga2_ext.py::constraints_enabled(cfg)` — tạm gán cờ ở cấp module rồi
**khôi phục nguyên trạng** trong `finally`. Không sửa file lõi, không rò trạng thái.

- R7 chỉ chặn khi `[H] > 0` (H_LIMIT). R8 chỉ chặn khi `[M] > 0` (M_LIMIT).

## 2. Thay đổi đường kính cọc để tính lại tối ưu

- Tập đường kính ứng viên = **các dòng bảng** người dùng nhập:
  `DiameterTable` gồm `DiameterOption(d, Po, Ct, M, H)` — mỗi đường kính có sức
  chịu tải riêng (TCVN 10304:2014; cọc to chịu khỏe hơn).
- File input MCOC **nhúng tiết diện cọc** theo từng khối: đường kính (Bpx/Bpy),
  `Fo = π·d²/4`, `Jo = π·d⁴/64`, `Po`. `DiameterMCOCTemplate`
  (`io_handlers/mcoc_writer_ext.py`) dò các trường này bằng **khớp giá trị gốc**
  rồi patch theo đường kính mới → **MCOC chấm chính xác** cho từng đường kính.
- `core/ext/blackbox_ext.py::make_diameter_evaluator` tạo evaluator MCOC gắn với
  một đường kính (file tạm tách theo `_opt_runs/d<mm>/`).

## 3. Đổi kích thước bệ sau tối ưu (TCVN)

`core/ext/cap_resize.py`: `L = (span tọa độ cọc) + 2·SAFE_D`, với `SAFE_D = d`
(tim cọc cách mép ≥ d — cấu tạo Điều 8 / ràng buộc R4), làm tròn **lên** bội số
thi công (`ExtConfig.cap_round_to`, mặc định 0.1 m). Đặt `cap_resize=False` để
chỉ đề xuất mà không tự ghi đè `L_X/L_Y`.

## Điểm vào

```python
from core.ext.orchestrator import run_extended_optimization
from core.ext.pile_section import DiameterTable
from core.ext.config_ext import ExtConfig

table = DiameterTable([(1.0, 400), (1.2, 600), (1.5, 950)])  # (d, [Po][, Ct, M, H])
cfg = ExtConfig(enable_R7=True, enable_R8=True, cap_round_to=0.1)

out = run_extended_optimization(params, loads, table, cfg=cfg,
                                pop_size=16, n_gen=10, max_evals=50)
# out['recommended']      -> phương án tối ưu toàn cục
# out['winner_diameter']  -> đường kính thắng
# out['cap_report']       -> báo cáo đổi kích thước bệ
# out['params_final']     -> params đã cập nhật L_X/L_Y
```

Chọn toàn cục giữa các đường kính theo chi phí vật liệu mặc định
`material_cost(n, d) = n · π·d²/4` (thể tích bê tông cọc / 1 m dài), đồng hạng
thì ưu tiên ít cọc hơn.

## Kiểm thử

```
python tests/test_ext.py
```

Chạy không cần MCOC (dùng evaluator giả). Bao phủ: công thức tiết diện, bảng
đường kính, patch đường kính round-trip trên file mẫu thật, resize bệ, và luồng
orchestrator đầu-cuối (gồm kiểm tra R7/R8 được bật rồi khôi phục).

## Chưa làm

Chưa nối vào giao diện Tkinter (`ui/main_window.py`) — hiện là module lõi + test.
Sẽ thống nhất với người dùng trước khi sửa `main_window.py` để tránh nhập nhằng.
