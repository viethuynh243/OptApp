---
type: note
title: Tiêu chuẩn TCVN
tags: [reference, tcvn, standard]
---

# Tiêu chuẩn TCVN 10304:2014 — Móng cọc

Các điều khoản đang được dùng trong OptApp (toàn văn: `../../words_dict/tieu_chuan.md`).

## Điều khoản áp dụng
| Điều | Nội dung | Dùng ở đâu |
|---|---|---|
| **§7.1.11** | Cọc chịu nén `Nc,d ≤ Rc,d`; chịu kéo `Nt,d ≤ Rt,d` | [[Ràng buộc R1–R8\|R5, R5b]] |
| **§7.1.13** | Tải trọng lên cọc thứ j: `Nj = N/n + My·xj/Σx² + Mx·yj/Σy²` | công thức bệ cứng ([[Bài toán & Mô hình]]) |
| **§7.1.14** | Tải ngang phân bố đều cho các cọc thẳng đứng cùng tiết diện | [[Ràng buộc R1–R8\|R7]] |
| **Điều 8 (cấu tạo)** | Khoảng cách tim cọc ≥ 3d; cọc cách mép bệ an toàn | [[Ràng buộc R1–R8\|R3, R4]], [[ADR-007 Đổi kích thước bệ theo TCVN]] |
| **§6.6** | Cọc khoan nhồi (đường kính) | [[ADR-006 Đường kính cọc là biến tối ưu]] |

## Sức chịu tải theo đường kính
Bản mở rộng dùng **bảng đường kính** do người dùng nhập (mỗi d có [Po]/[Ct]/[M]
riêng theo TCVN — cọc to chịu khỏe hơn), thay vì suy 1 công thức cứng. Xem
[[Gói mở rộng (ext)]] và [[ADR-006 Đường kính cọc là biến tối ưu]].

## Tiết diện cọc tròn
- `Fo = π·d²/4` (diện tích) · `Jo = π·d⁴/64` (mômen quán tính).
- Khớp đúng giá trị MCOC nhúng trong file input ([[Luồng MCOC]]).

Liên kết: [[Ràng buộc R1–R8]] · [[Thuật ngữ]]
