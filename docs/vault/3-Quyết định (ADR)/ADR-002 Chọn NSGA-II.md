---
type: adr
title: ADR-002 Chọn NSGA-II
status: accepted
tags: [adr, algorithm]
---

# ADR-002 — Chọn NSGA-II làm engine chính

**Bối cảnh:** hộp đen không đạo hàm, biến hỗn hợp, đa mục tiêu mâu thuẫn, hàm
mục tiêu đắt.

**Quyết định:** NSGA-II + MCOC, trả về mặt Pareto.

**Lý do:** không cần gradient; xử lý biến hỗn hợp + ràng buộc (Deb); cho cả mặt
Pareto trong một lần chạy.

Liên kết: [[Thuật toán NSGA-II]] · [[ADR-001 MCOC là oracle duy nhất]]
