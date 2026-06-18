---
type: note
title: Tổng quan module
tags: [code, architecture]
---

# Tổng quan module

## Engine
| Engine | File | Vai trò |
|---|---|---|
| **NSGA-II** | `core/nsga2_optimizer.py` | **Chính** — di truyền đa mục tiêu + MCOC exact ([[Thuật toán NSGA-II]]) |
| Refine | `core/refine_optimizer.py` | Tinh chỉnh Pareto *dự báo→kiểm chứng MCOC→hiệu chỉnh*; rất ít lần gọi MCOC |
| Quét lưới | `core/optimizer.py` | Bệ cứng (xấp xỉ) — **chỉ cho `run_demo.py`**, không quyết định ([[ADR-004 Batch theo MCOC]]) |

## Module lõi
| Module | Vai trò |
|---|---|
| `core/rigid_cap.py` | **Nguồn duy nhất** công thức bệ cứng (lực dọc dời tâm, `min_spacing`, K) |
| `core/blackbox.py` | Cầu nối: MCOC thực (`make_real_evaluator`) hoặc mock |
| `core/mcoc_runner.py` | Gọi `MCOC_Batch.exe` (subprocess), parse `*_result.txt`; hỗ trợ `.lnk`; **chạy ngầm không cửa sổ cmd** (xem [[2026-06-18]]) |
| `io_handlers/mcoc_writer.py` | Sinh file input MCOC từ template (ghi đè tải từ UI) |
| `io_handlers/report_writer.py` | Báo cáo kỹ thuật `.md` (R1–R6, hệ số sử dụng) |
| `ui/main_window.py` | GUI Tkinter (Tab Tương tác + Hàng loạt) |
| `core/version.py` | Nguồn version duy nhất (**v1.2.0**) |

## Gói mở rộng (branch riêng)
`core/ext/` + `io_handlers/mcoc_writer_ext.py` — tách biệt, không sửa lõi.
Xem [[Gói mở rộng (ext)]].

## Cạm bẫy
- `rigid_cap` phải giữ số hạng dời tâm `N·cy`/`N·cx` (Kiểu B `ny` chẵn) —
  [[Vấn đề & Cải tiến]].
- Mock cho mômen heuristic → R6 ở mock kém tin cậy (có cảnh báo).

Liên kết: [[Luồng MCOC]] · [[Thuật toán NSGA-II]] · [[Quyết định (ADR)|ADR]]
