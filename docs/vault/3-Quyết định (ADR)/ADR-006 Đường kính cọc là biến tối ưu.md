---
type: adr
title: ADR-006 Đường kính cọc là biến tối ưu
status: accepted
date: 2026-06-18
tags: [adr, diameter, ext, mcoc]
---

# ADR-006 — Đường kính cọc là biến tối ưu (MCOC chính xác)

**Bối cảnh:** người dùng muốn chương trình **đổi đường kính cọc** để tính lại
phương án tối ưu, **chấm bằng MCOC chính xác**, sức chịu tải theo TCVN 10304:2014.

**Quyết định:**
- Tập đường kính ứng viên = **các dòng bảng** `DiameterTable` người dùng nhập,
  mỗi dòng `(d, [Po], [Ct], [M], [H])` — cọc to chịu tải khỏe hơn.
- File input MCOC nhúng tiết diện theo từng cọc → `DiameterMCOCTemplate` patch
  `d`, `Fo=π·d²/4`, `Jo=π·d⁴/64`, `Po` (dò trường bằng **khớp giá trị gốc**,
  không hardcode offset). Mỗi đường kính chấm bằng MCOC thực.
- Chọn toàn cục theo chi phí vật liệu `n·π·d²/4`, đồng hạng thì ít cọc hơn.

**Hệ quả:** mỗi đường kính chạy NSGA-II riêng (params + evaluator gắn d); kết quả
gộp & xếp hạng. Xem [[Gói mở rộng (ext)]], [[Luồng MCOC]].

Liên kết: [[Tiêu chuẩn TCVN]] · [[Ràng buộc R1–R8]] · [[ADR-001 MCOC là oracle duy nhất]]
