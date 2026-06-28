---
type: note
title: Gói mở rộng (ext)
tags: [code, architecture, ext]
---

# Gói mở rộng (ext)

Branch **`feature/toiuu-mo-rong`**. Ba tính năng mở rộng, **tách biệt hoàn toàn**
module lõi cũ (không sửa `nsga2_optimizer.py`, `constants.py`, `mcoc_writer.py`,
`blackbox.py`). Tài liệu repo: `../ext_toiuu_mo_rong.md`.

## Module
| File | Vai trò |
|---|---|
| `core/ext/pile_section.py` | Tiết diện TCVN `Fo=π·d²/4`, `Jo=π·d⁴/64`; `DiameterTable`/`DiameterOption` (bảng d → [Po],[Ct],[M],[H]) |
| `core/ext/config_ext.py` | `ExtConfig` — bật R7/R8, chính sách resize bệ (`cap_round_to`) |
| `io_handlers/mcoc_writer_ext.py` | `DiameterMCOCTemplate` — patch d/Fo/Jo/Po theo đường kính (dò trường bằng **khớp giá trị**, không hardcode offset) |
| `core/ext/blackbox_ext.py` | Evaluator MCOC thực gắn từng đường kính |
| `core/ext/nsga2_ext.py` | `constraints_enabled(cfg)` — bật/khôi phục R7/R8 không sửa lõi |
| `core/ext/cap_resize.py` | Thu bệ vừa khít theo TCVN R4 + làm tròn thi công |
| `core/ext/orchestrator.py` | Gộp: quét d → tối ưu (R7/R8) → chọn toàn cục → resize bệ |

## Ba tính năng
1. **Bật R7 + R8** — [[ADR-005 Bật R7-R8 trong ext không sửa lõi]].
2. **Đổi đường kính cọc** (biến tối ưu, MCOC chính xác toàn bộ) —
   [[ADR-006 Đường kính cọc là biến tối ưu]].
3. **Đổi kích thước bệ** sau tối ưu — [[ADR-007 Đổi kích thước bệ theo TCVN]].

## Chọn toàn cục giữa các đường kính
Chi phí vật liệu mặc định `material_cost(n, d) = n·π·d²/4` (thể tích bê tông cọc /
1 m dài); đồng hạng thì ưu tiên ít cọc hơn.

## Điểm vào
```python
from core.ext.orchestrator import run_extended_optimization
from core.ext.pile_section import DiameterTable
from core.ext.config_ext import ExtConfig

table = DiameterTable([(1.0, 400), (1.2, 600), (1.5, 950)])  # (d, [Po][, Ct, M, H])
out = run_extended_optimization(params, loads, table,
                                cfg=ExtConfig(enable_R7=True, enable_R8=True))
```

## Kiểm thử
`python tests/test_ext.py` (chạy không cần MCOC, dùng evaluator giả).

## Đã nối vào UI (Tab 1)
Khung **"Tối ưu mở rộng (tùy chọn)"** trong Tab 1: checkbox bật, R7/R8, tự thu bệ
+ làm tròn, nút **"Bảng đường kính..."**. Khi bật, nút CHẠY route sang
`run_optimize_ext` → `_show_ext_results`: cập nhật ô D_PILE/[Po]/[Ct]/[M]/L_X/L_Y
theo đường kính thắng, bảng audit hiện **R1–R8** (thêm dòng R7/R8). Smoke test:
`tests/_smoke_ext_ui.py`.

Liên kết: [[Tổng quan module]] · [[Luồng MCOC]] · [[Ràng buộc R1–R8]] · [[Tiêu chuẩn TCVN]]
