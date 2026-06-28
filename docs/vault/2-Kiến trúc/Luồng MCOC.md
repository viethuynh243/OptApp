---
type: note
title: Luồng MCOC
tags: [code, architecture, mcoc]
---

# Luồng MCOC (đánh giá chính xác)

Tab 1 (Tương tác) và Tab 2 (Hàng loạt) dùng **cùng** luồng:

```
file input MCOC + tham số UI
   → nsga2_optimizer.run_nsga2()
   → evaluator = MCOCBlackbox.make_real_evaluator()
   → mcoc_writer (sinh input) → MCOC_Batch.exe → *_result.txt   [EXACT]
   → recommended + pareto_front
```

## Định dạng file input MCOC
Mỗi **khối cọc** nhúng đặc trưng tiết diện:
- đường kính `Bpx/Bpy` (2 dòng) = d;
- `Fo = π·d²/4` (diện tích);
- `Jo = π·d⁴/64` (mômen quán tính);
- `Po` (sức chịu nén cho phép);
- toạ độ `X, Y`.

> Kiểm chứng trên `mcoc_input_sample/T3_EXT.txt`: d=1.2 → Fo=1.1309733552923256,
> Jo=0.10178760197630929. Nhờ đó **đổi đường kính** = patch các trường này
> ([[Gói mở rộng (ext)]], [[ADR-006 Đường kính cọc là biến tối ưu]]).

## Gọi tiến trình (chạy ngầm)
`core/mcoc_runner.py` gọi `MCOC_Batch.exe` (.exe/.bat/.py/.lnk) bằng subprocess,
**không bật cửa sổ cmd** (`CREATE_NO_WINDOW` + `STARTUPINFO`/SW_HIDE) — xem
[[2026-06-18]].

Liên kết: [[Tổng quan module]] · [[Bài toán & Mô hình]] · [[Gói mở rộng (ext)]]
