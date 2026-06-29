# ADR-003 — Tắt R7 (lực ngang) & R8 (P–M) ở luồng lõi

> **Mã:** OA-ADR-003 · **Trạng thái:** Đã chấp nhận (accepted) · **Ngày:** 2026-06-16
> **Bổ sung bởi:** [ADR-005](ADR-005-bat-r7-r8-trong-ext.md)

**Bối cảnh:** đề bài gốc chỉ yêu cầu R1–R6; R7/R8 nằm ngoài đề.

**Quyết định:** đặt `ENABLE_LATERAL_CHECK=False`, `ENABLE_PM_INTERACTION=False`
trong [`core/constants.py`](../../../core/constants.py). MCOC đã tính 3D đầy đủ nên
không mất an toàn.

**Hệ quả:** R7/R8 (cột `H_max`, dòng `[H]`) **ẩn** khỏi báo cáo; bật lại = đổi
cờ thành `True`.

> **Bổ sung (2026-06-18):** luồng MỞ RỘNG **bật** R7/R8 mà **không** đổi cờ lõi —
> xem [ADR-005](ADR-005-bat-r7-r8-trong-ext.md). Quyết định này vẫn đúng cho luồng
> lõi / chương trình cũ.

Liên quan: [Kiến trúc — Ràng buộc R1–R8](../ARCHITECTURE.md#ràng-buộc-r1r8) · [Gói mở rộng (ext)](../EXT_TOIUU_MO_RONG.md)
