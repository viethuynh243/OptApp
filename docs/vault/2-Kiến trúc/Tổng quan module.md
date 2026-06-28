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
| `io_handlers/report_writer.py` | Báo cáo kỹ thuật `.md`/`.pdf` (R1–R8, lún Đ.7.4.4, ngang Phụ lục A Mục 6c) |
| `core/tcvn.py` | TCVN 10304:2014: Rc,d (Đ.7.1.11), móng khối quy ước + lún (Đ.7.4.4 — Se + Boussinesq) |
| `core/cap_design.py` | Thiết kế đài TCVN 5574:2018 (uốn, chọc thủng, cắt 1 phương Qb đầy đủ, STM) |
| `core/ssi_engine.py` | Tương tác đất–cọc thuần NumPy (dọc trục + ngang Winkler "m" + lún + nhóm) |
| `core/version.py` | Nguồn version duy nhất (**v1.10.0**) |

## Giao diện (GUI) — composition (Plan 023)
`ui/main_window.py` từ **3247 dòng (1 class)** → còn **~512 dòng**: VỎ điều phối giữ
state chia sẻ + dựng khung 2 tab/menu + tạo & nối component; giữ **delegator mỏng** cho
API ngoài. Logic tách thành (component nhận tham chiếu `app`):

| Nhóm | File | Vai trò |
|---|---|---|
| controllers | `ui/controllers/{params,loads,file_ops,results,simulation,optimization}.py` | tham số+TCVN, CRUD tải, nạp/xuất file, render kết quả+KPI, vẽ mô phỏng+audit, chạy tối ưu (thread) |
| tabs | `ui/tabs/{interactive_tab,batch_tab}.py` | dựng giao diện Tab 1 / Tab 2 (hàng loạt) |
| widgets | `ui/widgets/{tooltip,widget_utils}.py`, `ui/constants.py`, `ui/strings.py` | tiện ích GUI + hằng số + nhãn dùng chung |

## Gói mở rộng (branch riêng)
`core/ext/` + `io_handlers/mcoc_writer_ext.py` — tách biệt, không sửa lõi.
Xem [[Gói mở rộng (ext)]].

## Cạm bẫy
- `rigid_cap` phải giữ số hạng dời tâm `N·cy`/`N·cx` (Kiểu B `ny` chẵn) —
  [[Vấn đề & Cải tiến]].
- Mock cho mômen heuristic → R6 ở mock kém tin cậy (có cảnh báo).

Liên kết: [[Luồng MCOC]] · [[Thuật toán NSGA-II]] · [[Quyết định (ADR)|ADR]]
