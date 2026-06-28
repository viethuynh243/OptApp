---
type: home
title: OptApp — Bản đồ tri thức (MOC)
updated: 2026-06-18
tags: [optapp, moc]
---

# 🧭 OptApp — Bản đồ tri thức

Vault tri thức cho **OptApp v1.10.0** (tối ưu bố trí cọc móng cầu). Tổ chức theo
chủ đề; mỗi note một việc; liên kết `[[...]]` thể hiện nguyên nhân → hệ quả.

> Mở vault: Obsidian → **Open folder as vault** → chọn `docs/vault`.

## 🗺️ Bản đồ theo chủ đề

### 1 · Phương pháp
- [[Bài toán & Mô hình]] — mục tiêu, biến (genome), 2 mục tiêu Pareto.
- [[Ràng buộc R1–R8]] — toàn bộ ràng buộc; R7/R8 (tắt ở lõi, **bật ở ext**).
- [[Thuật toán NSGA-II]] — di truyền đa mục tiêu + constrained-domination.

### 2 · Kiến trúc
- [[Tổng quan module]] — engine, module lõi, cạm bẫy.
- [[Luồng MCOC]] — đánh giá chính xác bằng `MCOC_Batch.exe`.
- [[Gói mở rộng (ext)]] — R7/R8 + đổi đường kính + resize bệ (branch riêng).

### 3 · Quyết định (ADR)
- [[ADR-001 MCOC là oracle duy nhất]] · [[ADR-002 Chọn NSGA-II]]
- [[ADR-003 Tắt R7-R8 ở lõi]] · [[ADR-004 Batch theo MCOC]]
- [[ADR-005 Bật R7-R8 trong ext không sửa lõi]]
- [[ADR-006 Đường kính cọc là biến tối ưu]]
- [[ADR-007 Đổi kích thước bệ theo TCVN]]

### 4 · Vấn đề & Cải tiến
- [[Vấn đề & Cải tiến]] — issue đã đóng + backlog đang mở.

### 5 · Tham chiếu
- [[Thuật ngữ]] — ký hiệu Pmax, [Po], footprint, K…
- [[Tiêu chuẩn TCVN]] — TCVN 10304:2014 (điều khoản đang dùng).
- [[Hướng dẫn AI]] — nối Claude suy luận trên vault.

### 9 · Nhật ký
- [[2026-06-18]] — chạy ngầm không cửa sổ cmd + gói mở rộng ext.

## Một câu tóm tắt
Tìm **bố trí cọc tối ưu** (ít/rẻ vật liệu) thỏa ràng buộc, chấm **bắt buộc bằng
MCOC (chính xác)**, tối ưu bằng **NSGA-II**. Bản mở rộng còn **bật R7/R8**, **đổi
đường kính cọc** và **thu bệ vừa khít** — xem [[Gói mở rộng (ext)]].

## Tài liệu đầy đủ (repo)
`../../methodology.md` · `../BAO_CAO_THUAT_TOAN.md` · `../ext_toiuu_mo_rong.md` · `../../CHANGELOG.md`
