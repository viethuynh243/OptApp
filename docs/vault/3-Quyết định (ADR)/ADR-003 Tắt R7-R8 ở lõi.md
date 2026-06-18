---
type: adr
title: ADR-003 Tắt R7-R8 ở lõi
status: accepted
amended-by: ADR-005 Bật R7-R8 trong ext không sửa lõi
tags: [adr, constraints]
---

# ADR-003 — Tắt R7 (lực ngang) & R8 (P–M) ở luồng lõi

**Bối cảnh:** đề bài chỉ R1–R6; R7/R8 ngoài đề.

**Quyết định:** `ENABLE_LATERAL_CHECK=False`, `ENABLE_PM_INTERACTION=False`
(`core/constants.py`). MCOC đã tính 3D đầy đủ nên không mất an toàn.

**Hệ quả:** R7/R8 (cột H_max, dòng [H]) **ẩn** khỏi báo cáo; bật lại = đổi cờ
thành True.

> **Bổ sung (2026-06-18):** luồng MỞ RỘNG **bật** R7/R8 mà **không** đổi cờ lõi —
> xem [[ADR-005 Bật R7-R8 trong ext không sửa lõi]]. Quyết định này vẫn đúng cho
> luồng lõi/chương trình cũ.

Liên kết: [[Ràng buộc R1–R8]] · [[Gói mở rộng (ext)]]
