---
type: note
title: Ràng buộc R1–R8
tags: [constraints, method]
---

# Ràng buộc R1–R8

Kiểm trong `core/mechanics.py::check_layout` (gom lỗi, không dừng ở lỗi đầu) và
`core/nsga2_optimizer.py::evaluate` (chuẩn hóa thành CV — Constraint Violation).
`d` = đường kính cọc; `SAFE_D` = khoảng cách an toàn tới mép (mặc định = d).

| Mã      | Ràng buộc                                          | Ghi chú                                    |
| ------- | -------------------------------------------------- | ------------------------------------------ |
| **R1**  | có ≥ 1 cọc                                         | tiền đề                                    |
| **R2**  | có ≥ 1 tổ hợp tải                                  | tiền đề                                    |
| **R3**  | `s_min ≤ s ≤ 6d`, `s_min = max(3d, d+thông thủy)`  | Kiểu B xét **đường chéo** `√((sx/2)²+sy²)` |
| **R4**  | cọc trong bệ: `max\|x\|+SAFE_D ≤ Lx/2` (và theo Y) | TCVN cấu tạo (Điều 8)                      |
| **R5**  | `Pmax ≤ [Po]`                                      | nén                                        |
| **R5b** | `Pmin ≥ −[Ct]` (khi `[Ct]>0`)                      | nhổ                                        |
| **R6**  | `Mx, My ≤ [M]` (khi `[M]>0`)                       | uốn; mock heuristic kém tin cậy            |
| **R7**  | `Hmax ≤ [H]` (khi `[H]>0`)                         | lực ngang — **mặc định TẮT ở lõi**         |
| **R8**  | `Pmax/[Po] + max(Mx,My)/[M] ≤ 1`                   | tương tác P–M — **mặc định TẮT ở lõi**     |

## R7 / R8 — trạng thái
- **Lõi:** `ENABLE_LATERAL_CHECK=False`, `ENABLE_PM_INTERACTION=False`
  (`core/constants.py`). Lý do: [[ADR-003 Tắt R7-R8 ở lõi]] (MCOC đã tính 3D).
- **Bản mở rộng:** **BẬT** cả R7 và R8 qua context manager, không sửa lõi —
  xem [[ADR-005 Bật R7-R8 trong ext không sửa lõi]] và [[Gói mở rộng (ext)]].
- R7 cần `[H]>0`, R8 cần `[M]>0` mới thực sự chặn.

## Cơ chế CV (constrained-domination)
Mỗi vi phạm cộng vào `cv` đã chuẩn hóa (vd `max(0, Pmax−[Po])/[Po]`); `ok = cv≈0`.
So sánh cá thể: khả thi > bất khả thi; 2 bất khả thi xét `cv` nhỏ hơn; 2 khả thi
xét Pareto. Chi tiết: [[Thuật toán NSGA-II]].

Liên kết: [[Bài toán & Mô hình]] · [[Tiêu chuẩn TCVN]] · [[Quyết định (ADR)|ADR]]
