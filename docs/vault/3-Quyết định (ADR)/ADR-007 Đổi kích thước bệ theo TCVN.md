---
type: adr
title: ADR-007 Đổi kích thước bệ theo TCVN
status: accepted
date: 2026-06-18
tags: [adr, cap, ext, tcvn]
---

# ADR-007 — Đổi kích thước bệ sau tối ưu theo TCVN

**Bối cảnh:** sau khi ra phương án tối ưu (bố trí + đường kính), bệ ban đầu
thường còn dư; người dùng muốn thu bệ cho phù hợp, theo TCVN 10304:2014.

**Quyết định:** `core/ext/cap_resize.py` tính
`L = (span tọa độ cọc) + 2·SAFE_D`, với `SAFE_D = d` (tim cọc cách mép ≥ d — cấu
tạo Điều 8, đúng ràng buộc [[Ràng buộc R1–R8|R4]]), rồi **làm tròn lên** bội số
thi công (`ExtConfig.cap_round_to`, mặc định 0.1 m). `cap_resize=False` → chỉ đề
xuất, không tự ghi đè `L_X/L_Y`.

**Hệ quả:** không bao giờ làm bệ nhỏ hơn mức để cọc còn nằm trong bệ (an toàn R4);
báo cáo `cap_report` kèm % diện tích tiết kiệm.

Liên kết: [[Tiêu chuẩn TCVN]] · [[Gói mở rộng (ext)]] · [[Ràng buộc R1–R8]]
