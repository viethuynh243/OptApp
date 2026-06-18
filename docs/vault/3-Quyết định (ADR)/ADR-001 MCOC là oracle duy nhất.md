---
type: adr
title: ADR-001 MCOC là oracle duy nhất
status: accepted
tags: [adr, mcoc]
---

# ADR-001 — MCOC là oracle duy nhất, cấm xấp xỉ

**Bối cảnh:** bên thi công không nghiệm thu kết quả xấp xỉ.

**Quyết định:** mọi phương án quyết định chấm trực tiếp bằng MCOC; thiếu MCOC →
từ chối chạy. Bệ cứng chỉ dẫn hướng/heatmap.

**Hệ quả:** tốc độ đến từ *giảm số lần gọi + song song* ([[Thuật toán NSGA-II]]),
không từ xấp xỉ. Ràng buộc engine (xem [[ADR-002 Chọn NSGA-II]]).

Liên kết: [[Luồng MCOC]] · [[Bài toán & Mô hình]]
