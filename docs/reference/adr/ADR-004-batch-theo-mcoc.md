# ADR-004 — Tab Hàng loạt theo đúng luồng MCOC

> **Mã:** OA-ADR-004 · **Trạng thái:** Đã chấp nhận (accepted) · **Ngày:** 2026-06-16

**Bối cảnh:** Tab Hàng loạt trước đây chạy mock bệ cứng → xuất kết quả xấp xỉ,
trái với [ADR-001](ADR-001-mcoc-oracle-duy-nhat.md).

**Quyết định:** Tab Hàng loạt dùng NSGA-II + MCOC như Tab 1; **bắt buộc** cấu
hình MCOC.

**Hệ quả:** `optimizer.run_optimization` (quét lưới bệ cứng) chỉ còn dùng cho
`run_demo.py`, không nằm trên luồng quyết định.

Liên quan: [Kiến trúc — Luồng MCOC](../ARCHITECTURE.md#luồng-mcoc-đánh-giá-chính-xác) · [ADR-001](ADR-001-mcoc-oracle-duy-nhat.md)
