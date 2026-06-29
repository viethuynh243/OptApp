# Thuật ngữ & ký hiệu

> **Mã:** OA-DOC-09d · **Phiên bản:** 1.0 · **Cập nhật:** 2026-06-29 · **Trạng thái:** Approved
> **Căn cứ:** `core/constants.py`, `core/rigid_cap.py`, `core/ext/`.

Quy ước đơn vị thống nhất theo MCOC: **lực = Tấn (T)**, **mômen = T·m**, **chiều dài = m**.

| Ký hiệu | Nghĩa | Đơn vị |
|---|---|---|
| **MCOC** | Phần mềm tính móng cọc — oracle chính xác (xem [ADR-001](../reference/adr/ADR-001-mcoc-oracle-duy-nhat.md)) | — |
| **NSGA-II** | Giải thuật di truyền đa mục tiêu — engine chính | — |
| `N` | Lực dọc trục tại đáy bệ | T |
| `Mx, My, Mz` | Mômen quanh X/Y, xoắn quanh Z | T·m |
| `Hx, Hy` | Lực ngang theo X/Y | T |
| `[Po]` (P_LIMIT) | Sức chịu nén cho phép của 1 cọc | T |
| `[Ct]` (P_TENSION) | Sức chịu nhổ cho phép (0 = không kiểm) | T |
| `[M]` (M_LIMIT) | Sức chịu uốn (0 = không kiểm) | T·m |
| `[H]` (H_LIMIT) | Sức chịu lực ngang (0 = không kiểm; dùng cho R7) | T |
| **Pmax / Pmin** | Lực nén lớn nhất / nhổ (âm) trên một cọc | T |
| **Hmax** | Lực ngang tổng hợp lớn nhất trên một cọc (R7) | T |
| **footprint** | Bề rộng + bề cao cụm cọc (đo "bệ gọn") | m |
| **K** | Hệ số hiệu chỉnh `Pmax_MCOC / Pmax_bệ_cứng` (dùng khi dẫn hướng) | — |
| **diag** | Khoảng cách chéo Kiểu B `= √((sx/2)² + sy²)` | m |
| **3d–6d** | Dải khoảng cách tim cọc cho phép | m |
| **Kiểu A / B** | Lưới trực giao / hoa mai (so le) | — |
| **CV** | Constraint Violation — mức vi phạm ràng buộc đã chuẩn hóa | — |
| `d` (D_PILE) | Đường kính cọc | m |
| `SAFE_D` | Khoảng cách an toàn tim cọc → mép bệ (mặc định = d) | m |
| **Fo** | Diện tích tiết diện cọc `= π·d²/4` | m² |
| **Jo** | Mômen quán tính tiết diện cọc `= π·d⁴/64` | m⁴ |
| **DiameterTable** | Bảng đường kính ứng viên + sức chịu tải (xem [ext](../reference/EXT_TOIUU_MO_RONG.md)) | — |
| **material_cost** | Chi phí vật liệu `n·π·d²/4` (chọn toàn cục giữa các đường kính) | m²/m |
| **bệ / đài cọc** | Pile cap — dùng đồng nghĩa theo quy ước công trình cầu | — |

Xem thêm: [Bài toán & mô hình](../reference/ARCHITECTURE.md#bài-toán--mô-hình) · [Ràng buộc R1–R8](../reference/ARCHITECTURE.md#ràng-buộc-r1r8)
