# BẢNG TÍNH KIỂM TRA & TỐI ƯU BỐ TRÍ MÓNG CỌC

> **Mã:** OA-DOC-06 · **Phiên bản:** 1.0 · **Cập nhật:** 2026-06-29 · **Trạng thái:** Approved · **Căn cứ:** io_handlers/report_writer.py, io_handlers/file_io.py

### (Đề xuất định dạng OUTPUT chuẩn kỹ thuật cho OptApp)

> Mẫu dưới điền **số liệu thật** từ phương án khuyến nghị của bộ dữ liệu demo
> (bệ 6.0 × 9.6 m, cọc khoan nhồi Ø1.2 m, [Po] = 500 T). Minh họa một bản tính
> đủ thông tin để kỹ sư thẩm tra ký duyệt.

---

## 1. THÔNG TIN CHUNG

| Mục | Nội dung |
|---|---|
| Công trình | Cầu …  — Mố/Trụ T… |
| Hạng mục | Móng cọc bệ thấp |
| Tiêu chuẩn áp dụng | TCVN 10304:2014 (móng cọc); TCVN 11823:2017 (cầu, LRFD); 22 TCN 18 (nếu dùng) |
| Phần mềm | OptApp v1.10.0 (nội lực tính bằng MCOC) |
| Người tính / KT / ngày | … / … / 2026‑06‑14 |

## 2. SỐ LIỆU ĐẦU VÀO

**Bệ móng & cọc**

| Thông số | Ký hiệu | Giá trị | Đơn vị |
|---|---|---|---|
| Chiều rộng bệ | Lx | 6.00 | m |
| Chiều dài bệ | Ly | 9.60 | m |
| Đường kính cọc | d | 1.20 | m |
| K.cách tim cọc → mép bệ tối thiểu | c_min | 1.20 (= 1.0 d) | m |
| Sức chịu nén cho phép | [Po] | 500.0 | T |
| Sức chịu nhổ cho phép | [Ct] | 0.0 (không kiểm) | T |
| Sức chịu uốn đầu cọc cho phép | [M] | 0.0 (không kiểm) | T·m |

**Tổ hợp tải trọng** *(đáy bệ, hệ trục tâm bệ)*

| TH | Tên tổ hợp¹ | Hx | Hy | N | Mx | My | Mz |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | Cường độ I | 0 | 0 | 2577 | 1500 | 1500 | 0 |
| 2 | Cường độ II | 0 | 0 | 2400 | 800 | 2000 | 0 |
| 3 | Cường độ III | 0 | 0 | 2800 | 1800 | 1200 | 0 |

> Đơn vị: lực **Tấn (T)**, momen **T·m** (theo quy ước MCOC). ¹Tên tổ hợp do người dùng đặt theo trạng thái giới hạn.

## 3. PHƯƠNG ÁN KHUYẾN NGHỊ

| Mục | Giá trị |
|---|---|
| Kiểu bố trí | A – Trực giao (lưới đều) |
| Số cọc | **6** (lưới 2 × 3) |
| Bước cọc | sx = 3.60 m;  sy = 3.60 m |
| Tọa độ cọc (m) | (−1.8, −3.6) (1.8, −3.6) (−1.8, 0) (1.8, 0) (−1.8, 3.6) (1.8, 3.6) |

## 4. KIỂM TRA HÌNH HỌC

| Mã | Điều kiện | Giá trị | Giới hạn | Tỷ lệ | Kết luận |
|---|---|---:|---:|---:|:--:|
| R3a | Bước cọc ≥ 3d | 3.60 m | 3.60 m | 100% | ĐẠT |
| R3b | Bước cọc ≤ 6d | 3.60 m | 7.20 m | 50% | ĐẠT |
| R4x | max\|x\| + c_min ≤ Lx/2 | 3.00 m | 3.00 m | 100% | ĐẠT |
| R4y | max\|y\| + c_min ≤ Ly/2 | 4.80 m | 4.80 m | 100% | ĐẠT |

## 5. KIỂM TRA NỘI LỰC CỌC (theo từng tổ hợp)

Lực dọc cọc theo mô hình **bệ cứng + hiệu chỉnh K** (đối chiếu MCOC); quy đổi về **Tấn** để so với [Po].

| TH | N_max (T) | Cọc | N_min (T) | Cọc | N_max/[Po] | Kết luận |
|---|---:|:--:|---:|:--:|---:|:--:|
| 1 | 466.0 | biên | 129.2 | trong | 93.2% | ĐẠT |
| 2 | 443.9 | biên | 110.3 | trong | 88.8% | ĐẠT |
| 3 | **486.9** | biên | 159.7 | trong | **97.4%** | ĐẠT (chi phối) |

**Tổng kết:** N_max = 486.9 T (TH3) / [Po] = 500 T → **hệ số sử dụng 0.974 < 1.0 ⇒ ĐẠT.**
N_min = 110.3 T > 0 ⇒ không có cọc chịu nhổ.

## 6. BẢNG TỔNG HỢP RÀNG BUỘC R1–R6

| Mã | Nội dung | Trạng thái | Ghi chú |
|---|---|:--:|---|
| R1 | N_max ≤ [Po] | ĐẠT | 0.974 |
| R2 | N_min ≥ −[Ct] | – | [Ct] = 0, không kiểm |
| R3 | 3d ≤ bước ≤ 6d | ĐẠT | tại cận dưới 3d |
| R4 | tim cọc cách mép ≥ c_min | ĐẠT | sát giới hạn |
| R5 | Mx ≤ [M] | – | [M] = 0, không kiểm |
| R6 | My ≤ [M] | – | [M] = 0, không kiểm |

## 7. KẾT LUẬN & KIẾN NGHỊ

Phương án **6 cọc Ø1.2 m, lưới trực giao 2×3, bước 3.6 m** thỏa mãn toàn bộ ràng
buộc, hệ số sử dụng lớn nhất 0.974, tiết kiệm hơn các phương án nhiều cọc.
Đề nghị thẩm tra lại bằng MCOC trước khi phát hành.

---

## PHỤ LỤC A — PHẠM VI & GIỚI HẠN MÔ HÌNH *(bắt buộc ghi rõ trong bản tính)*

Bản tính dùng mô hình **bệ cứng — chỉ phân phối lực DỌC TRỤC**:
`P_i = N/n + Mx·(y_i−cy)/Ix + My·(x_i−cx)/Iy`. Do đó **chưa** xét:

- **Lực ngang Hx, Hy** và **momen xoắn Mz** (bỏ qua dù input có nhập) →
  cần phân tích ngang riêng (p‑y / chuyển vị ngang) khi Hx, Hy hoặc Mz đáng kể.
- **Tương tác nén–uốn** trong thân cọc (kiểm [Po] và [M] tách rời, chưa kiểm đồng thời).
- **Hiệu ứng nhóm cọc, độ lún, điều kiện đóng/hạ cọc, kết cấu bệ** (chọc thủng, uốn bệ).

→ Kết quả dùng cho **bố trí sơ bộ / tối ưu số cọc**; bước thiết kế chi tiết phải
chạy MCOC/FEM đầy đủ.
