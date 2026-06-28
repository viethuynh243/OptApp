---
type: note
title: Vấn đề & Cải tiến
tags: [issues, backlog]
---

# Vấn đề & Cải tiến

## Đã sửa (closed)
| Vấn đề | Tóm tắt & khắc phục |
|---|---|
| Gọi MCOC bật cửa sổ cmd | `mcoc_runner` dùng `CREATE_NO_WINDOW` + `STARTUPINFO`/SW_HIDE → chạy ngầm ([[2026-06-18]]). |
| "Làm mới" không xóa Thông số Bài toán | `clear_loads` nay reset cả 6 ô thông số, file gốc, giá trị gốc nội bộ & trạng thái ext ([[2026-06-18]]). |
| Gói ext chưa có trong UI | Đã nối vào Tab 1 (khung "Tối ưu mở rộng"): bật R7/R8, bảng đường kính, tự thu bệ; audit hiện R1–R8 ([[Gói mở rộng (ext)]]). |
| Báo cáo xuất thiếu R7/R8 | `build_report_text` nhận `enable_R7/R8` + `ext_info`; xuất từ ext có bảng R1–R8, cột H_max, mục 3b (quét đường kính + thu bệ). |
| Công thức bệ cứng bỏ dời tâm `N·x̄`? | **Code đã đúng** (giữ `Mx−N·cy`); kiểm CODE==FULL (830.56). Lỗi ở tài liệu cũ → đã sửa. |
| Batch dùng mock (xấp xỉ) | Chuyển Batch sang NSGA-II + MCOC ([[ADR-004 Batch theo MCOC]]). |
| Demo Kiểu B bị loại oan | `optimizer.py` giảm `sy` để kéo đường chéo về [3d,6d]. |
| Đơn vị báo cáo ghi kN | Sửa thành Tấn (T)/T.m. |
| R7/R8 hiện trong báo cáo khi đã tắt | Ẩn cột H_max/dòng [H]/R7/R8. |

## Đang mở (open)
| Cải tiến | Mức | Ghi chú |
|---|---|---|
| **Song song hóa lời gọi MCOC** | medium | `MCOCRunner` đang tuần tự → song song nhiều lõi (mỗi tiến trình out-dir riêng). Tăng tốc ≈ số lõi, giữ chính xác. Càng cần khi quét nhiều đường kính. |
| **Gieo phương án vét cạn vào NSGA-II** | low | 1 run đơn có thể lệch 1 cọc ở bài khó. Gieo nghiệm vét cạn (mock, rẻ) vào quần thể khởi tạo. Xem `../BAO_CAO_THUAT_TOAN.md` §5.1. |

Liên kết: [[Tổng quan module]] · [[Gói mở rộng (ext)]] · [[Quyết định (ADR)|ADR]]
