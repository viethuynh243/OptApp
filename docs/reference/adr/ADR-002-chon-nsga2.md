# ADR-002 — Chọn NSGA-II làm engine chính

> **Mã:** OA-ADR-002 · **Trạng thái:** Đã chấp nhận (accepted) · **Ngày:** 2026-06-18

**Bối cảnh:** hàm đánh giá là hộp đen không đạo hàm, biến hỗn hợp (rời rạc +
liên tục), đa mục tiêu mâu thuẫn, và đắt (mỗi lần gọi MCOC tốn thời gian).

**Quyết định:** dùng NSGA-II + MCOC, trả về **mặt Pareto**.

**Lý do:** không cần gradient; xử lý được biến hỗn hợp + ràng buộc (Deb et al.
2002); cho cả mặt Pareto chỉ trong một lần chạy.

Liên quan: [Kiến trúc — NSGA-II](../ARCHITECTURE.md#thuật-toán-nsga-ii) · [ADR-001](ADR-001-mcoc-oracle-duy-nhat.md)
