---
type: adr
title: ADR-004 Batch theo MCOC
status: accepted
tags: [adr, mcoc, batch]
---

# ADR-004 — Tab Hàng loạt theo đúng luồng MCOC

**Bối cảnh:** Batch trước đây chạy mock bệ cứng → xuất kết quả xấp xỉ (trái
[[ADR-001 MCOC là oracle duy nhất]]).

**Quyết định:** Batch dùng NSGA-II + MCOC như Tab 1; bắt buộc cấu hình MCOC.

**Hệ quả:** `optimizer.run_optimization` chỉ còn cho `run_demo.py`
([[Tổng quan module]]).

Liên kết: [[Luồng MCOC]] · [[ADR-001 MCOC là oracle duy nhất]]
