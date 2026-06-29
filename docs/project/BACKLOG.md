# Backlog — Vấn đề & Cải tiến

> **Mã:** OA-DOC-12 · **Phiên bản:** 1.0 · **Cập nhật:** 2026-06-29 · **Trạng thái:** Living
> **Căn cứ:** nhật ký vấn đề/cải tiến (di cư từ vault Obsidian) + định hướng từ chủ dự án.

Danh sách việc đang mở (cải tiến/tái cấu trúc) và việc đã đóng. Mỗi mục nêu **mức
độ** và **căn cứ kiểm tra được** (file/hàm) để rà lại.

---

## 🚩 Định hướng lớn (mandate) — ĐANG MỞ

### M1 · Chuyển CƠ SỞ THIẾT KẾ sang **TCVN 11823:2017** (thay TCVN 10304:2014) — **mức: rất cao**

> **Yêu cầu bắt buộc của chủ dự án (2026-06-29):** toàn bộ chương trình phải dựa
> trên **TCVN 11823:2017 — Thiết kế cầu đường bộ** (bộ tiêu chuẩn theo triết lý
> **LRFD**, tương đương AASHTO LRFD; phần móng cọc ở **TCVN 11823-10**), **không**
> dùng TCVN 10304:2014 làm cơ sở nữa.

Đây là **chỉnh sửa lớn toàn bộ**, không phải vá cục bộ — triết lý chuyển từ
"sức chịu tải cho phép / hệ số riêng phần (γ)" của TCVN 10304:2014 sang
**trạng thái giới hạn LRFD** (hệ số tải `γ`, hệ số sức kháng `φ`, các tổ hợp
Strength / Service / Extreme Event). Phạm vi ảnh hưởng (sơ bộ):

| Hạng mục hiện tại (TCVN 10304:2014) | Cần làm theo TCVN 11823:2017 |
|---|---|
| Sức chịu tải `Rc,d = (γ0/γn)·(Rc,k/γk)` (`core/tcvn.py`) | Sức kháng tính toán `φ·Rn` theo TCVN 11823-10 (hệ số `φ` theo phương pháp xác định) |
| Ràng buộc R5/R5b `Pmax ≤ [Po]` (allowable) | Kiểm theo **tổ hợp tải LRFD** `ΣγᵢQᵢ ≤ φRn` |
| Tổ hợp tải nhập tay (T, T·m) | Hệ tổ hợp + hệ số tải LRFD (Strength I–V, Service I, Extreme) |
| Lún Đ.7.4.4 (TCVN 10304) + TCVN 9362 | Kiểm theo trạng thái giới hạn sử dụng (Service) của 11823-10 |
| Thiết kế đài TCVN 5574:2018 (`core/cap_design.py`) | Rà tương thích với 11823 (bê tông cốt thép cầu) |
| Báo cáo/audit ghi "TCVN 10304:2014" | Viết lại theo điều khoản TCVN 11823:2017/-10 |

**Cần trước khi thực hiện:** bản tiêu chuẩn TCVN 11823:2017 (đặc biệt **phần 10 —
Móng** và phần 3 — Tải trọng & hệ số tải) ở dạng tra cứu được; kỹ sư kết cấu/địa
kỹ thuật xác nhận ánh xạ hệ số. Xem [ADR-008](../reference/adr/ADR-008-co-so-thiet-ke-tcvn-11823.md)
(quyết định định hướng) và kế hoạch migration sẽ lập riêng.

> **Lưu ý đối chiếu tài liệu hiện hành:** mọi tài liệu trong `docs/` đang mô tả
> **trạng thái thực tế của code** (cơ sở TCVN 10304:2014). KHÔNG sửa hồi tố các
> tài liệu này thành "đã theo 11823" cho tới khi code thực sự chuyển đổi — để
> tránh tài liệu sai lệch so với phần mềm.

---

## Đang mở (open) — cải tiến kỹ thuật

| # | Cải tiến | Mức | Ghi chú |
|---|---|---|---|
| O1 | **Song song hóa lời gọi MCOC** | medium | `MCOCRunner` đang chạy tuần tự → song song nhiều lõi (mỗi tiến trình một thư mục out riêng). Tăng tốc ≈ số lõi, giữ chính xác. Càng cần khi quét nhiều đường kính. Xem [spike](spike_parallel_mcoc.md). |
| O2 | **Gieo phương án vét cạn vào NSGA-II** | low | Một lần chạy đơn có thể lệch 1 cọc ở bài khó. Gieo nghiệm vét cạn (mock, rẻ) vào quần thể khởi tạo. Xem [Báo cáo thuật toán §5.1](../reference/BAO_CAO_THUAT_TOAN.md). |

---

## Đã đóng (closed)

| Vấn đề | Tóm tắt & khắc phục |
|---|---|
| Gọi MCOC bật cửa sổ cmd | `mcoc_runner` dùng `CREATE_NO_WINDOW` + `STARTUPINFO`/SW_HIDE → chạy ngầm. |
| "Làm mới" không xóa Thông số Bài toán | `clear_loads` reset cả 6 ô thông số, file gốc, giá trị gốc nội bộ & trạng thái ext. |
| Gói ext chưa có trong UI | Đã nối vào Tab 1 (khung "Tối ưu mở rộng"): bật R7/R8, bảng đường kính, tự thu bệ; audit hiện R1–R8. |
| Báo cáo xuất thiếu R7/R8 | `build_report_text` nhận `enable_R7/R8` + `ext_info`; xuất từ ext có bảng R1–R8, cột H_max, mục 3b. |
| Công thức bệ cứng nghi bỏ dời tâm `N·x̄` | **Code đã đúng** (giữ `Mx − N·cy`); kiểm CODE == FULL (830,56). Lỗi ở tài liệu cũ → đã sửa. |
| Batch dùng mock (xấp xỉ) | Chuyển Batch sang NSGA-II + MCOC ([ADR-004](../reference/adr/ADR-004-batch-theo-mcoc.md)). |
| Demo Kiểu B bị loại oan | `optimizer.py` giảm `sy` để kéo đường chéo về `[3d, 6d]`. |
| Đơn vị báo cáo ghi kN | Sửa thành Tấn (T) / T·m. |
| R7/R8 hiện trong báo cáo khi đã tắt | Ẩn cột H_max / dòng [H] / R7 / R8. |

Liên quan: [Kiến trúc](../reference/ARCHITECTURE.md) · [ADR](../reference/adr/README.md) · [CHANGELOG](../../CHANGELOG.md)
