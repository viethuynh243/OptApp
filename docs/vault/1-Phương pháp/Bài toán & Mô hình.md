---
type: note
title: Bài toán & Mô hình
tags: [model, method]
---

# Bài toán & Mô hình hóa

## Mục tiêu
Tìm **bố trí cọc tối ưu** (số cọc ít / vật liệu rẻ) cùng vị trí từng cọc, thỏa
mọi [[Ràng buộc R1–R8]], trên bệ `Lx × Ly`.

## Biến quyết định (genome)
`(type, nx, ny, sx, sy)`:
- `type` ∈ {A trực giao, B hoa mai/so le} — rời rạc.
- `nx, ny` — số cột/hàng, rời rạc.
- `sx, sy` ∈ `[3d, 6d]` — bước lưới, liên tục.
- Tọa độ luôn **đối xứng quanh tâm bệ** (cx=cy=0).

> Bản mở rộng thêm **đường kính d** thành biến (quét theo bảng) — xem
> [[Gói mở rộng (ext)]] và [[ADR-006 Đường kính cọc là biến tối ưu]].

## Hai mục tiêu (đều cực tiểu) → mặt Pareto
- `f1` = số cọc (tiết kiệm vật liệu/thi công).
- `f2` = bệ gọn (footprint, mặc định) **hoặc** Pmax (an toàn) — chọn qua
  `secondary`.

Lời giải là **mặt Pareto** (tập không bị thống trị), không phải một điểm.

## Đánh giá nội lực — bắt buộc MCOC
Mỗi phương án chấm bằng `MCOC_Batch.exe` (oracle duy nhất, [[Luồng MCOC]]).
Mô hình **bệ cứng** chỉ dẫn hướng nội bộ + heatmap, không phải kết quả giao nộp:

`P_i = N/n + (Mx − N·cy)(y_i − cy)/Ix + (My − N·cx)(x_i − cx)/Iy`

(dời mômen về trọng tâm — đúng cả khi tâm lệch, vd Kiểu B `ny` chẵn; xem
[[Vấn đề & Cải tiến]]).

Liên kết: [[Ràng buộc R1–R8]] · [[Thuật toán NSGA-II]] · [[Thuật ngữ]]
