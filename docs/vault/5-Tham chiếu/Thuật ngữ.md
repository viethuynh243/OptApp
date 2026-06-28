---
type: note
title: Thuật ngữ
tags: [glossary, reference]
---

# Thuật ngữ

| Ký hiệu | Nghĩa | Đơn vị |
|---|---|---|
| **MCOC** | Phần mềm tính móng cọc (oracle chính xác) | — |
| **NSGA-II** | Giải thuật di truyền đa mục tiêu — engine chính | — |
| `N` | Lực dọc trục tại đáy bệ | T |
| `Mx, My, Mz` | Mômen quanh X/Y, xoắn Z | T·m |
| `Hx, Hy` | Lực ngang | T |
| `[Po]` (P_LIMIT) | Sức chịu nén cho phép | T |
| `[Ct]` (P_TENSION) | Sức chịu nhổ cho phép | T |
| `[M]` (M_LIMIT) | Sức chịu uốn (0 = không kiểm) | T·m |
| `[H]` (H_LIMIT) | Sức chịu lực ngang (0 = không kiểm, dùng cho R7) | T |
| **Pmax / Pmin** | Lực nén lớn nhất / nhổ (âm) | T |
| **Hmax** | Lực ngang tổng hợp lớn nhất trên một cọc (R7) | T |
| **footprint** | Bề rộng + bề cao cụm cọc (đo "bệ gọn") | m |
| **K** | Hệ số hiệu chỉnh `Pmax_MCOC / Pmax_bệ_cứng` (dẫn hướng) | — |
| **diag** | Khoảng cách chéo Kiểu B = `√((sx/2)²+sy²)` | m |
| **3d–6d** | Dải khoảng cách tim cọc cho phép | m |
| **Kiểu A / B** | Lưới trực giao / hoa mai (so le) | — |
| **CV** | Constraint Violation — mức vi phạm chuẩn hóa | — |
| `d` (D_PILE) | Đường kính cọc | m |
| `SAFE_D` | Khoảng cách an toàn tim cọc → mép bệ (mặc định = d) | m |
| **Fo** | Diện tích tiết diện cọc `= π·d²/4` | m² |
| **Jo** | Mômen quán tính tiết diện cọc `= π·d⁴/64` | m⁴ |
| **DiameterTable** | Bảng đường kính ứng viên + sức chịu tải ([[Gói mở rộng (ext)]]) | — |
| **material_cost** | Chi phí vật liệu `n·π·d²/4` (chọn toàn cục giữa đường kính) | m²/m |

Liên kết: [[Bài toán & Mô hình]] · [[Ràng buộc R1–R8]] · [[Gói mở rộng (ext)]]
