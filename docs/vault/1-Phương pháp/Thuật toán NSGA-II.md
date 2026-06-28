---
type: note
title: Thuật toán NSGA-II
tags: [algorithm, method]
---

# Thuật toán NSGA-II

Engine chính (`core/nsga2_optimizer.py`). Di truyền đa mục tiêu (Deb et al. 2002).

## 4 thành phần cốt lõi
1. **Fast non-dominated sorting** → xếp hạng Pareto (rank).
2. **Crowding distance** → giữ đa dạng trên mặt Pareto.
3. **Crowded-comparison tournament** → chọn lọc.
4. **SBX crossover + polynomial mutation + elitism (μ+λ)**.

## Xử lý ràng buộc — constrained-domination
- khả thi **>** bất khả thi;
- 2 bất khả thi → `cv` nhỏ hơn trội hơn;
- 2 khả thi → Pareto trên mục tiêu.

Xem định nghĩa CV ở [[Ràng buộc R1–R8]].

## Chính xác bắt buộc nhưng vẫn nhanh
Tốc độ KHÔNG từ xấp xỉ ([[ADR-001 MCOC là oracle duy nhất]]) mà từ **giảm số lần
gọi MCOC** + **song song**:
1. cache theo lưới (không gọi trùng) · 2. trần `max_evals` (≈50) ·
3. predictor bệ cứng xếp thứ tự gửi MCOC · 4. song song hóa *(backlog)* ·
5. cache bền *(backlog)*.

1 lần gọi ≈ 0.1–1 s; mặc định ≤50 lần ≈ 50 s (song song 8 lõi ≈ 7 s).

## Số neo kiểm thử (oracle hồi quy)
- `tests/test_nsga2.py` → Kiểu A 2×3, 6 cọc, **Pmax=486.91 T**.
- `tests/test_refine.py` → 8 cọc, **Pmax=408.34 T**.
- `tests/test_nsga2_mcoc.py` → 8 cọc, **Pmax=398.80 T**, **25 lần gọi MCOC**.

Liên kết: [[Bài toán & Mô hình]] · [[Tổng quan module]] · [[Luồng MCOC]]
