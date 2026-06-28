# Số liệu đầu vào bổ sung — OptApp

Các file `mcoc_input_sample/*.txt` đã chứa tọa độ cọc, đường kính d, chiều dài cọc Lc,
mô đun bê tông Eb, hệ số nền m, tổ hợp tải (Hx, Hy, N, Mx, My, Mz) và kích thước đài.
Chương trình tự đọc các thông số này khi mở file.

Hai nhóm số liệu sau không có trong file MCOC, cần nhập thêm:

- Trụ địa chất — để tính lún móng khối quy ước (TCVN 10304:2014, Điều 7.4).
- Tiết diện trụ và vật liệu đài — để thiết kế kết cấu đài (TCVN 5574:2018).

Đơn vị theo MCOC: lực Tấn (T), kích thước mét, mô đun E theo T/m², dung trọng γ theo T/m³.

## 1. Trụ địa chất tham khảo

Ba kiểu nền điển hình. Mỗi lớp gồm bề dày h, dung trọng γ, góc ma sát trong φ, lực dính
c, mô đun biến dạng E và chỉ số SPT. Dải giá trị theo TCVN 9362; E ước lượng từ SPT
(cát E ≈ 1–2·N MPa, sét E ≈ 3–8·cu).

### Kiểu A — nền yếu (sét mềm dày)

| Độ sâu (m) | Mô tả | γ | φ | c | E | SPT |
|---|---|---|---|---|---|---|
| 0–10 | Sét mềm chảy dẻo | 1.65 | 5 | 0.8 | 250 | 2 |
| 10–20 | Sét dẻo mềm | 1.80 | 10 | 1.5 | 600 | 5 |
| 20–28 | Sét pha dẻo cứng | 1.90 | 16 | 2.5 | 1500 | 12 |
| 28–36 | Cát pha chặt vừa | 1.95 | 28 | 0 | 3000 | 22 |

### Kiểu B — nền trung bình (sét cứng + cát chặt)

| Độ sâu (m) | Mô tả | γ | φ | c | E | SPT |
|---|---|---|---|---|---|---|
| 0–6 | Sét pha dẻo mềm | 1.80 | 8 | 1.2 | 400 | 4 |
| 6–14 | Sét pha dẻo cứng | 1.90 | 14 | 2.5 | 1200 | 9 |
| 14–23 | Cát pha chặt vừa | 1.95 | 24 | 0.8 | 2500 | 18 |
| 23–30 | Cát hạt trung chặt | 2.00 | 32 | 0 | 4500 | 32 |
| 30–40 | Cát hạt thô rất chặt | 2.05 | 36 | 0 | 8000 | 50 |

### Kiểu C — nền tốt (cát/cuội chặt gần mặt)

| Độ sâu (m) | Mô tả | γ | φ | c | E | SPT |
|---|---|---|---|---|---|---|
| 0–5 | Sét pha nửa cứng | 1.90 | 16 | 2.0 | 1500 | 12 |
| 5–15 | Cát hạt trung chặt | 2.00 | 32 | 0 | 5000 | 30 |
| 15–25 | Cát–cuội rất chặt | 2.10 | 38 | 0 | 12000 | 55 |
| 25–35 | Đá phong hóa | 2.20 | 40 | 5 | 25000 | 80 |

Quy đổi sang các ô nhập trong khung "Trụ địa chất & lún":

- φ tb dọc cọc: trung bình φ có trọng số bề dày, lấy từ mặt đất đến mũi cọc.
- Độ sâu đáy đài: đáy khối quy ước nằm ở cao độ bằng độ sâu đáy đài cộng Lc.
- γ' trên đáy khối: dung trọng đẩy nổi trung bình, xấp xỉ γ trừ 1.0. Bỏ trống thì cộng
  lún toàn bộ các lớp khai báo (thiên về an toàn).
- Lớp đất dưới mũi cọc: nhập từng lớp theo định dạng `h, E, γ`.

## 2. Vật liệu và tiết diện đài

| Tham số | Đài cầu vừa và nhỏ | Đài cầu lớn |
|---|---|---|
| Mác bê tông | B25–B30 | B30–B35 |
| Nhóm cốt thép | CB400-V | CB400-V hoặc CB500-V |
| Lớp bảo vệ | 0.10–0.15 m | 0.15 m |
| Chiều cao đài | lấy từ file | lấy từ file |
| Tiết diện trụ | theo hồ sơ kết cấu (xem mục 3) | theo hồ sơ kết cấu |

Cường độ tính toán dùng trong chương trình (TCVN 5574:2018): B25 — Rb 14.5, Rbt 1.05;
B30 — 17.0, 1.15; CB400-V — Rs 350; CB500-V — Rs 435 (MPa).

## 3. Số liệu đầy đủ cho T1–T22

Bộ số liệu dưới đây đã kiểm tra: mọi trụ đạt các điều kiện nén (R1), nhổ (R2), chọc
thủng, uốn và lún. Vật liệu mặc định B25 và CB400-V, lớp bảo vệ 0.10 m, γ' bỏ trống,
lún giới hạn 0.08 m. Chiều cao đài lấy đủ để chọc thủng đạt.

| Trụ | n | d | Lc | [Po] | [Ct] | Trụ bx×by | H đài | φ tb | Đáy đài | Lún (mm) | Chọc thủng η |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | 6 | 1.2 | 20 | 590 | 180 | 2.5×4 | 2.0 | 18 | 3.0 | 26 | 0.32 |
| T2 | 6 | 1.2 | 20 | 520 | 160 | 2.5×4 | 2.0 | 18 | 3.0 | 25 | 0.39 |
| T3 | 8 | 1.2 | 20 | 550 | 170 | 2.5×4 | 2.0 | 18 | 3.0 | 28 | 0.45 |
| T4 | 8 | 1.2 | 20 | 570 | 180 | 2.5×4 | 2.0 | 18 | 3.0 | 30 | 0.60 |
| T5 | 8 | 1.2 | 20 | 650 | 200 | 2.5×4 | 2.0 | 18 | 3.0 | 31 | 0.50 |
| T6 | 8 | 1.2 | 20 | 680 | 210 | 2.5×4 | 2.5 | 18 | 3.0 | 37 | 0.43 |
| T7 | 15 | 1.2 | 12 | 690 | 230 | 2.5×4 | 2.5 | 22 | 4.0 | 24 | 0.70 |
| T8 | 22 | 2.0 | 12 | 2200 | 660 | 8×16 | 5.0 | 22 | 4.0 | 56 | 0.53 |
| T9 | 24 | 2.0 | 12 | 2200 | 660 | 8×16 | 5.5 | 22 | 4.0 | 53 | 0.63 |
| T10 | 24 | 2.0 | 12 | 2200 | 660 | 8×16 | 5.5 | 22 | 4.0 | 55 | 0.65 |
| T11 | 26 | 2.0 | 12 | 2200 | 660 | 8×16 | 6.0 | 22 | 4.0 | 57 | 0.62 |
| T12 | 26 | 2.0 | 12 | 2390 | 720 | 8×16 | 6.0 | 22 | 4.0 | 57 | 0.62 |
| T13 | 26 | 2.0 | 12 | 2200 | 660 | 8×16 | 6.0 | 22 | 4.0 | 58 | 0.62 |
| T14 | 22 | 2.0 | 12 | 2310 | 700 | 8×16 | 5.5 | 22 | 4.0 | 58 | 0.49 |
| T22 | 8 | 1.2 | 20 | 540 | 170 | 2.5×4 | 2.0 | 18 | 3.0 | 28 | 0.45 |

Lớp đất dưới mũi cọc, phân theo chiều dài cọc:

- Lc = 20 m (T1–T6, T22): φ tb 18, đáy đài 3.0; ba lớp `7, 4500, 2.05`, `10, 8000, 2.05`,
  `12, 12000, 2.05`.
- Lc = 12 m (T7–T14): φ tb 22, đáy đài 4.0; ba lớp `6, 5000, 2.00`, `10, 9000, 2.05`,
  `12, 14000, 2.10`.

## 4. Trình tự nhập

1. Mở file đầu vào. Lc, d, m, kích thước đài và tổ hợp tải được nạp tự động.
2. Nhập sức chịu tải cọc [Po], [Ct]. Nhập trực tiếp, hoặc khai báo Rc,k trong khung
   TCVN 10304 để chương trình tính Rc,d.
3. Khung "Nền & đài cọc": nhập tiết diện trụ, mác bê tông, nhóm thép, lớp bảo vệ.
4. Khung "Trụ địa chất & lún": nhập φ tb, độ sâu đáy đài, lún giới hạn và bảng lớp đất.
5. Chạy tối ưu, sau đó xem kết quả ở các chế độ: mặt bằng, 3D, SSI đất–cọc, thiết kế đài.

Để điền nhanh, dùng nút "Nạp DEMO đầy đủ". Chương trình tự điền các ô còn trống ([Po],
[Ct], tiết diện trụ, chiều cao đài, trụ địa chất) theo tải của từng file và không ghi đè
giá trị đã nhập.

## 5. Một số trường hợp kiểm tra

Lấy T7 với bộ số liệu ở mục 3 làm trường hợp gốc (đạt mọi điều kiện), thay đổi một vài
thông số để kiểm tra từng điều kiện riêng.

| Trường hợp | Thay đổi so với gốc | Kết quả |
|---|---|---|
| A. Gốc | giữ nguyên | Đạt mọi điều kiện |
| B. Nền yếu | lớp đất `8, 300, 1.7`, `10, 600, 1.8`, `12, 1200, 1.9`; Sgh 0.05 | Lún 467 mm, vượt giới hạn |
| C. Trụ nhỏ | tiết diện trụ 1.0×1.0 | Chọc thủng η 1.08, không đạt |
| D. Đài mỏng | chiều cao đài 1.0 | Chọc thủng η 2.39, không đạt |
| E. [Po] thấp | [Po] 250 | Vượt nén (lực cọc 624 lớn hơn [Po] 250) |

Lún chỉ hiện giá trị khác 0 khi để trống γ'. Khi khai báo γ' (xấp xỉ 0.95), ứng suất bản
thân được trừ đi nên lún của móng cọc sâu thường rất nhỏ.
