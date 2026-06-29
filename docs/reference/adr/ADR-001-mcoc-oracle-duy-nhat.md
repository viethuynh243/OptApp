# ADR-001 — MCOC là oracle duy nhất, cấm xấp xỉ

> **Mã:** OA-ADR-001 · **Trạng thái:** Đã chấp nhận (accepted) · **Ngày:** 2026-06-18

**Bối cảnh:** bên thi công không nghiệm thu kết quả xấp xỉ.

**Quyết định:** mọi phương án quyết định được chấm trực tiếp bằng MCOC; thiếu cấu
hình MCOC → chương trình **từ chối chạy**. Mô hình bệ cứng chỉ dùng để dẫn
hướng/heatmap nội bộ.

**Hệ quả:** tốc độ đến từ việc *giảm số lần gọi MCOC + chạy song song* (xem
[Kiến trúc — NSGA-II](../ARCHITECTURE.md#thuật-toán-nsga-ii)), **không** từ xấp xỉ.
Ràng buộc engine ở [ADR-002](ADR-002-chon-nsga2.md).

Liên quan: [Kiến trúc — Luồng MCOC](../ARCHITECTURE.md#luồng-mcoc-đánh-giá-chính-xác)
