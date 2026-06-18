# BỘ ĐIỀU KIỆN TEST THỦ CÔNG — mcoc_input_sample/

> Sinh tự động bởi `tests/gen_sample_test_plan.py` (đọc bằng chính parser của app nên luôn khớp dữ liệu thật). Chạy lại để cập nhật khi đổi file mẫu.

**Quy ước đơn vị:** lực = Tấn (T), momen = T.m. **[Po] đọc từ file = 500 T.** File mẫu KHÔNG có [Ct]/[M] nên R2/R5b/R6 mặc định *không kiểm* (nhập tay nếu cần). **R7** chỉ kiểm khi bật *Tối ưu mở rộng* + khai [H].

**Cấu hình bắt buộc trước khi chạy:** MCOC Batch + đúng file input gốc (các trị Pmax/Pmin trị tuyệt đối do MCOC quyết định; mục B4 chỉ là dự báo bệ cứng).

## Bảng tổng quan

| File | Lx×Ly (m) | d (m) | #TH | #cọc gốc | k/c min (m) | R3 gốc | R4 gốc | TH chi phối | Pmax dự báo* |
|---|---|---:|---:|---:|---:|:--:|:--:|:--:|---:|
| T10_EXT.txt | 34.0×28.0 | 2.00 | 12 | 24 | 6.00 | ✓ | ✓ | TH9 | 1993.9 |
| T10_SER.txt | 34.0×28.0 | 2.00 | 12 | 24 | 6.00 | ✓ | ✓ | TH3 | 1311.3 |
| T10_STR.txt | 34.0×28.0 | 2.00 | 12 | 24 | 6.00 | ✓ | ✓ | TH6 | 1853.4 |
| T11_EXT.txt | 34.0×28.0 | 2.00 | 12 | 26 | 6.00 | ✓ | ✓ | TH9 | 1940.6 |
| T11_SER.txt | 34.0×28.0 | 2.00 | 12 | 26 | 6.00 | ✓ | ✓ | TH4 | 1358.0 |
| T11_STR.txt | 34.0×28.0 | 2.00 | 12 | 26 | 6.00 | ✓ | ✓ | TH5 | 1856.5 |
| T12_EXT.txt | 34.0×28.0 | 2.00 | 12 | 26 | 6.00 | ✓ | ✓ | TH9 | 2171.4 |
| T12_SER.txt | 34.0×28.0 | 2.00 | 12 | 26 | 6.00 | ✓ | ✓ | TH4 | 1478.7 |
| T12_STR.txt | 34.0×28.0 | 2.00 | 12 | 26 | 6.00 | ✓ | ✓ | TH7 | 1873.2 |
| T13_EXT.txt | 34.0×28.0 | 2.00 | 12 | 26 | 6.00 | ✓ | ✓ | TH9 | 1993.1 |
| T13_SER.txt | 34.0×28.0 | 2.00 | 12 | 26 | 6.00 | ✓ | ✓ | TH12 | 1617.7 |
| T13_STR.txt | 34.0×28.0 | 2.00 | 12 | 26 | 6.00 | ✓ | ✓ | TH9 | 1937.1 |
| T14_EXT.txt | 34.0×22.0 | 2.00 | 12 | 22 | 6.00 | ✓ | ✓ | TH9 | 2092.8 |
| T14_SER.txt | 34.0×22.0 | 2.00 | 12 | 22 | 6.00 | ✓ | ✓ | TH3 | 1402.0 |
| T14_STR.txt | 34.0×22.0 | 2.00 | 12 | 22 | 6.00 | ✓ | ✓ | TH1 | 1863.5 |
| T1_EXT.txt | 6.0×9.6 | 1.20 | 10 | 6 | 3.60 | ✓ | ✓ | TH1 | 529.7 |
| T1_STR.txt | 6.0×9.6 | 1.20 | 11 | 6 | 3.60 | ✓ | ✓ | TH1 | 664.8 |
| T22_EXT.txt | 8.0×9.6 | 1.20 | 10 | 8 | 3.33 | ✗ | ✓ | TH1 | 487.8 |
| T22_STR.txt | 8.0×9.6 | 1.20 | 11 | 8 | 3.33 | ✗ | ✓ | TH1 | 550.4 |
| T2_EXT.txt | 6.0×9.6 | 1.20 | 10 | 6 | 3.60 | ✓ | ✓ | TH7 | 457.4 |
| T2_STR.txt | 6.0×9.6 | 1.20 | 11 | 6 | 3.60 | ✓ | ✓ | TH1 | 622.9 |
| T3_EXT.txt | 8.0×9.6 | 1.20 | 10 | 8 | 3.33 | ✗ | ✓ | TH1 | 496.3 |
| T3_STR.txt | 8.0×9.6 | 1.20 | 11 | 8 | 3.33 | ✗ | ✓ | TH1 | 606.8 |
| T4_EXT.txt | 8.0×9.6 | 1.20 | 10 | 8 | 3.33 | ✗ | ✓ | TH7 | 517.4 |
| T4_STR.txt | 8.0×9.6 | 1.20 | 11 | 8 | 3.33 | ✗ | ✓ | TH9 | 620.9 |
| T5_EXT.txt | 8.0×9.6 | 1.20 | 10 | 8 | 3.33 | ✗ | ✓ | TH1 | 583.3 |
| T5_STR.txt | 8.0×9.6 | 1.20 | 11 | 8 | 3.33 | ✗ | ✓ | TH9 | 674.8 |
| T6_EXT.txt | 8.0×9.6 | 1.20 | 10 | 8 | 3.33 | ✗ | ✓ | TH1 | 614.5 |
| T6_STR.txt | 8.0×9.6 | 1.20 | 11 | 8 | 3.33 | ✗ | ✓ | TH9 | 752.4 |
| T7_EXT.txt | 9.6×16.8 | 1.20 | 12 | 15 | 3.60 | ✓ | ✓ | TH12 | 623.7 |
| T7_SER.txt | 9.6×16.8 | 1.20 | 12 | 15 | 3.60 | ✓ | ✓ | TH1 | 637.1 |
| T7_STR.txt | 9.6×16.8 | 1.20 | 12 | 15 | 3.60 | ✓ | ✓ | TH4 | 570.0 |
| T8_EXT.txt | 34.0×22.0 | 2.00 | 12 | 22 | 6.00 | ✓ | ✓ | TH12 | 1982.9 |
| T8_SER.txt | 34.0×22.0 | 2.00 | 12 | 22 | 6.00 | ✓ | ✓ | TH11 | 1736.5 |
| T8_STR.txt | 34.0×22.0 | 2.00 | 12 | 22 | 6.00 | ✓ | ✓ | TH12 | 1752.4 |
| T9_EXT.txt | 34.0×28.0 | 2.00 | 12 | 24 | 6.00 | ✓ | ✓ | TH12 | 1859.7 |
| T9_SER.txt | 34.0×28.0 | 2.00 | 12 | 24 | 6.00 | ✓ | ✓ | TH3 | 1376.7 |
| T9_STR.txt | 34.0×28.0 | 2.00 | 12 | 24 | 6.00 | ✓ | ✓ | TH5 | 1803.7 |

> `*` Pmax dự báo theo **đơn vị tải trong file** (bệ cứng, chưa hiệu chỉnh MCOC) — chỉ để so sánh tương đối; trị Tấn chính thức do MCOC tính. `R3/R4 gốc` là kiểm hình học TẤT ĐỊNH theo TCVN (đúng không cần MCOC).

**Đọc nhanh:** các bố trí gốc có **R3 ✗** (vd T3–T6, T22: k/c 3.33 m < 3d=3.6 m) → bảng audit PHẢI báo *KHÔNG ĐẠT* cho phương án gốc; phần tối ưu phải tìm bố trí đạt 3d–6d. `[Po]=500 T` lấy từ file — với trụ lớn (T10–T14) nếu tối ưu báo vô nghiệm thì chỉnh [Po]/đơn vị cho đúng thực tế.
## Thẻ test từng file

### `T10_EXT.txt` — Tru Mcoc-T10 EXT(max)+EXT(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 24 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10 | 0 | 34901 | -94 | -2250 | 0 |
| 2 | -6 | 0 | 24524 | -60 | -2824 | 0 |
| 3 | -1116 | 0 | 34706 | -93 | -6112 | 0 |
| 12 | 98 | 0 | 24730 | -62 | 60382 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH9** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1993.9` / `481.6`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 24** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T10_SER.txt` — Tru Mcoc-T10 SER(max)+SER(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 24 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | -18 | 0 | 28187 | -77 | -1208 | 0 |
| 2 | 13 | 0 | 27415 | -70 | -4591 | 0 |
| 3 | -445 | 0 | 27792 | -75 | -21302 | 0 |
| 12 | 412 | 0 | 27857 | -74 | 15218 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH3** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1311.3` / `1001.8`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 24** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T10_STR.txt` — Tru Mcoc-T10 STR(max)+STR(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 24 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 62 | 0 | 41271 | -107 | 1146 | 0 |
| 2 | -77 | 0 | 24487 | -61 | -7395 | 0 |
| 3 | -643 | 0 | 34543 | -92 | -30757 | 0 |
| 12 | 668 | 0 | 24621 | -60 | 27235 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH6** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1853.4` / `626.2`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 24** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T11_EXT.txt` — Tru Mcoc-T11 EXT(max)+EXT(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 26 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 76 | 0 | 36499 | -91 | 2962 | 0 |
| 2 | 78 | 0 | 25659 | -57 | 3524 | 0 |
| 3 | -951 | 0 | 36294 | -90 | -666 | 0 |
| 12 | 169 | 0 | 25875 | -59 | 61894 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH9** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1940.6` / `447.8`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 26** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T11_SER.txt` — Tru Mcoc-T11 SER(max)+SER(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 26 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 246 | 0 | 29467 | -80 | 19241 | 0 |
| 2 | -117 | 0 | 28678 | -48 | -14240 | 0 |
| 3 | -552 | 0 | 29058 | -52 | -30588 | 0 |
| 12 | 669 | 0 | 29135 | -78 | 35533 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH4** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1358.0` / `883.4`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 26** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T11_STR.txt` — Tru Mcoc-T11 STR(max)+STR(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 26 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 268 | 0 | 43179 | -104 | 16549 | 0 |
| 2 | -89 | 0 | 25629 | -59 | -8343 | 0 |
| 3 | -661 | 0 | 36130 | -88 | -31983 | 0 |
| 12 | 880 | 0 | 25768 | -57 | 43089 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH5** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1856.5` / `517.0`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 26** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T12_EXT.txt` — Tru Mcoc-T12 EXT(max)+EXT(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 26 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 78 | 0 | 36617 | -108 | 4212 | 0 |
| 2 | 91 | 0 | 25784 | -74 | 5249 | 0 |
| 3 | -960 | 0 | 36439 | -107 | 433 | 0 |
| 12 | 184 | 0 | 25974 | -76 | 64880 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH9** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `2171.4` / `220.6`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 26** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T12_SER.txt` — Tru Mcoc-T12 SER(max)+SER(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 26 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 492 | -1 | 29596 | -31 | 37330 | 0 |
| 2 | -340 | 2 | 28770 | -279 | -29702 | 0 |
| 3 | -767 | 2 | 29148 | -283 | -45498 | 0 |
| 12 | 896 | -1 | 29268 | -29 | 52916 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH4** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1478.7` / `772.8`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 26** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T12_STR.txt` — Tru Mcoc-T12 STR(max)+STR(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 26 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 417 | 0 | 43372 | -122 | 28411 | 0 |
| 2 | -195 | 0 | 25718 | -76 | -15427 | 0 |
| 3 | -768 | 0 | 36261 | -106 | -38835 | 0 |
| 12 | 1051 | 0 | 25884 | -75 | 56342 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH7** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1873.2` / `446.8`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 26** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T13_EXT.txt` — Tru Mcoc-T13 EXT(max)+EXT(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 26 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 319 | 0 | 36912 | -103 | 9619 | 0 |
| 2 | 360 | 0 | 25931 | -70 | 13740 | 0 |
| 3 | -649 | 0 | 36690 | -103 | 7661 | 0 |
| 12 | 405 | 0 | 26172 | -71 | 70522 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH9** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1993.1` / `413.9`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 26** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T13_SER.txt` — Tru Mcoc-T13 SER(max)+SER(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 26 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | -518 | -3 | 29709 | 185 | -46943 | 0 |
| 2 | 1089 | 9 | 29026 | -953 | 65416 | 0 |
| 3 | -727 | 9 | 29416 | -955 | -55763 | 0 |
| 12 | 1268 | -3 | 29384 | 186 | 73029 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH12** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1617.7` / `642.6`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 26** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T13_STR.txt` — Tru Mcoc-T13 STR(max)+STR(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 26 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 61 | 0 | 43623 | -117 | -13093 | 0 |
| 2 | 993 | 0 | 25957 | -78 | 56623 | 0 |
| 3 | -583 | 0 | 36554 | -100 | -39526 | 0 |
| 12 | 1399 | 0 | 26014 | -78 | 73489 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH9** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1937.1` / `456.6`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 26** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T14_EXT.txt` — Tru Mcoc-T14 EXT(max)+EXT(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 22.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 22 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | -31 | 0 | 30918 | -13 | -1558 | 0 |
| 2 | 30 | 0 | 22016 | -9 | 3896 | 0 |
| 3 | -802 | 0 | 30779 | -12 | -2071 | 0 |
| 12 | 34 | 0 | 22114 | -9 | 58987 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `11.00` ≤ Ly/2 = `11.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH9** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `2092.8` / `301.6`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 22** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T14_SER.txt` — Tru Mcoc-T14 SER(max)+SER(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 22.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 22 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | -452 | -7 | 24839 | 703 | -36528 | 0 |
| 2 | 409 | 2 | 24441 | -228 | 34688 | 0 |
| 3 | -462 | -7 | 24750 | 703 | -37554 | 0 |
| 12 | 418 | 2 | 24459 | -228 | 35543 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `11.00` ≤ Ly/2 = `11.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH3** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1402.0` / `847.9`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 22** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T14_STR.txt` — Tru Mcoc-T14 STR(max)+STR(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 22.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 22 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | -292 | 0 | 36760 | -5 | -26571 | 0 |
| 2 | 550 | 0 | 21998 | -6 | 46266 | 0 |
| 3 | -832 | 0 | 30742 | -7 | -51989 | 0 |
| 12 | 917 | 0 | 22022 | -5 | 62454 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `11.00` ≤ Ly/2 = `11.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH1** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1863.5` / `548.4`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 22** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T1_EXT.txt` — T1 EXT

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 6.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 10 |
| Số cọc (gốc) | 6 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 83 | 105 | 2025 | -1499 | 951 | 0 |
| 2 | 159 | 32 | 2025 | -592 | 1509 | 0 |
| 3 | 20 | 0 | 2577 | -94 | 170 | 0 |
| 10 | 41 | 0 | 1811 | -204 | 643 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.60` m; yêu cầu ≥ 3d = `3.60` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `3.00` ≤ Lx/2 = `3.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH1** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `529.7` / `0.0`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 6** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T1_STR.txt` — T1 STR&SER

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 6.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 11 |
| Số cọc (gốc) | 6 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 97 | 0 | 2825 | -713 | 1560 | 0 |
| 2 | 97 | 0 | 2059 | -713 | 1558 | 0 |
| 3 | 88 | 0 | 2746 | -550 | 1334 | 0 |
| 11 | 102 | 13 | 2124 | -602 | 1319 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.60` m; yêu cầu ≥ 3d = `3.60` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `3.00` ≤ Lx/2 = `3.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH1** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `664.8` / `147.3`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 6** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T22_EXT.txt` — T22 EXT

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 8.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 10 |
| Số cọc (gốc) | 8 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 39 | 93 | 2517 | -2129 | 701 | 0 |
| 2 | 105 | 28 | 2517 | -781 | 1502 | 0 |
| 3 | 11 | 0 | 3209 | -94 | 169 | 0 |
| 10 | 11 | 0 | 2254 | -203 | 357 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.33` m; yêu cầu ≥ 3d = `3.60` m → **KHÔNG ĐẠT ✗**
- **R4** mép bệ: max|x|+d = `4.00` ≤ Lx/2 = `4.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH1** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `487.8` / `0.0`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 8** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái (GỐC vốn vi phạm hình học → KHÔNG ĐẠT, khớp audit).

---

### `T22_STR.txt` — T22 STR&SER

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 8.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 11 |
| Số cọc (gốc) | 8 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 37 | 0 | 3457 | -709 | 1251 | 0 |
| 2 | 37 | 0 | 2502 | -709 | 1251 | 0 |
| 3 | 29 | 0 | 3378 | -547 | 965 | 0 |
| 11 | 29 | 14 | 2616 | -725 | 859 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.33` m; yêu cầu ≥ 3d = `3.60` m → **KHÔNG ĐẠT ✗**
- **R4** mép bệ: max|x|+d = `4.00` ≤ Lx/2 = `4.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH1** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `550.4` / `176.9`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 8** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái (GỐC vốn vi phạm hình học → KHÔNG ĐẠT, khớp audit).

---

### `T2_EXT.txt` — T2 EXT

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 6.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 10 |
| Số cọc (gốc) | 6 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 | 46 | 1939 | -1041 | 589 | 0 |
| 2 | 88 | 14 | 1939 | -456 | 1034 | 0 |
| 3 | 14 | 0 | 2450 | -95 | 186 | 0 |
| 10 | 14 | 0 | 1734 | -205 | 376 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.60` m; yêu cầu ≥ 3d = `3.60` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `3.00` ≤ Lx/2 = `3.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH7** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `457.4` / `0.0`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 6** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T2_STR.txt` — T2 STR&SER

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 6.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 11 |
| Số cọc (gốc) | 6 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 52 | 0 | 2701 | -717 | 1328 | 0 |
| 2 | 52 | 0 | 1985 | -717 | 1328 | 0 |
| 3 | 42 | 0 | 2621 | -553 | 1045 | 0 |
| 11 | 47 | 14 | 2039 | -694 | 966 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.60` m; yêu cầu ≥ 3d = `3.60` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `3.00` ≤ Lx/2 = `3.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH1** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `622.9` / `143.8`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 6** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T3_EXT.txt` — T3 EXT

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 8.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 10 |
| Số cọc (gốc) | 8 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 61 | 71 | 2488 | -1714 | 1335 | 0 |
| 2 | 100 | 21 | 2488 | -657 | 1851 | 0 |
| 3 | 17 | 0 | 3162 | -95 | 295 | 0 |
| 10 | 38 | 0 | 2228 | -205 | 1012 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.33` m; yêu cầu ≥ 3d = `3.60` m → **KHÔNG ĐẠT ✗**
- **R4** mép bệ: max|x|+d = `4.00` ≤ Lx/2 = `4.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH1** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `496.3` / `0.0`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 8** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái (GỐC vốn vi phạm hình học → KHÔNG ĐẠT, khớp audit).

---

### `T3_STR.txt` — T3 STR&SER

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 8.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 11 |
| Số cọc (gốc) | 8 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 83 | 0 | 3413 | -717 | 2284 | 0 |
| 2 | 83 | 0 | 2479 | -717 | 2284 | 0 |
| 3 | 74 | 0 | 3332 | -553 | 1977 | 0 |
| 11 | 87 | 15 | 2588 | -774 | 2048 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.33` m; yêu cầu ≥ 3d = `3.60` m → **KHÔNG ĐẠT ✗**
- **R4** mép bệ: max|x|+d = `4.00` ≤ Lx/2 = `4.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH1** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `606.8` / `110.9`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 8** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái (GỐC vốn vi phạm hình học → KHÔNG ĐẠT, khớp audit).

---

### `T4_EXT.txt` — T4 EXT

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 8.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 10 |
| Số cọc (gốc) | 8 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 45 | 0 | 2646 | -205 | 1416 | 0 |
| 2 | 45 | 0 | 2646 | -205 | 1416 | 0 |
| 3 | 3 | 0 | 3364 | -95 | 5 | 0 |
| 10 | 45 | 0 | 2371 | -205 | 1416 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.33` m; yêu cầu ≥ 3d = `3.60` m → **KHÔNG ĐẠT ✗**
- **R4** mép bệ: max|x|+d = `4.00` ≤ Lx/2 = `4.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH7** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `517.4` / `0.0`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 8** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái (GỐC vốn vi phạm hình học → KHÔNG ĐẠT, khớp audit).

---

### `T4_STR.txt` — T4 STR&SER

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 8.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 11 |
| Số cọc (gốc) | 8 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 53 | 0 | 3615 | -717 | 1903 | 0 |
| 2 | 53 | 0 | 2621 | -717 | 1903 | 0 |
| 3 | 50 | 0 | 3535 | -553 | 1747 | 0 |
| 11 | 55 | 15 | 2747 | -837 | 1731 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.33` m; yêu cầu ≥ 3d = `3.60` m → **KHÔNG ĐẠT ✗**
- **R4** mép bệ: max|x|+d = `4.00` ≤ Lx/2 = `4.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH9** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `620.9` / `108.7`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 8** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái (GỐC vốn vi phạm hình học → KHÔNG ĐẠT, khớp audit).

---

### `T5_EXT.txt` — T5 EXT

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 8.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 10 |
| Số cọc (gốc) | 8 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 57 | 74 | 2787 | -2201 | 1664 | 0 |
| 2 | 113 | 22 | 2787 | -804 | 2699 | 0 |
| 3 | 11 | 0 | 3541 | -95 | 306 | 0 |
| 10 | 32 | 0 | 2497 | -205 | 1195 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.33` m; yêu cầu ≥ 3d = `3.60` m → **KHÔNG ĐẠT ✗**
- **R4** mép bệ: max|x|+d = `4.00` ≤ Lx/2 = `4.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH1** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `583.3` / `0.0`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 8** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái (GỐC vốn vi phạm hình học → KHÔNG ĐẠT, khớp audit).

---

### `T5_STR.txt` — T5 STR&SER

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 8.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 11 |
| Số cọc (gốc) | 8 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 62 | 0 | 3791 | -717 | 2449 | 0 |
| 2 | 62 | 0 | 2748 | -717 | 2449 | 0 |
| 3 | 53 | 0 | 3711 | -553 | 2072 | 0 |
| 11 | 57 | 16 | 2887 | -904 | 2010 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.33` m; yêu cầu ≥ 3d = `3.60` m → **KHÔNG ĐẠT ✗**
- **R4** mép bệ: max|x|+d = `4.00` ≤ Lx/2 = `4.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH9** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `674.8` / `110.5`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 8** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái (GỐC vốn vi phạm hình học → KHÔNG ĐẠT, khớp audit).

---

### `T6_EXT.txt` — T6 EXT

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 8.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 10 |
| Số cọc (gốc) | 8 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 32 | 70 | 3325 | -2275 | 982 | 0 |
| 2 | 77 | 21 | 3325 | -825 | 1898 | 0 |
| 3 | 11 | 0 | 4246 | -95 | 372 | 0 |
| 10 | 11 | 0 | 2981 | -204 | 565 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.33` m; yêu cầu ≥ 3d = `3.60` m → **KHÔNG ĐẠT ✗**
- **R4** mép bệ: max|x|+d = `4.00` ≤ Lx/2 = `4.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH1** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `614.5` / `0.0`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 8** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái (GỐC vốn vi phạm hình học → KHÔNG ĐẠT, khớp audit).

---

### `T6_STR.txt` — T6 STR&SER

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 8.00 |
| Dài bệ Ly (m) | 9.60 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 11 |
| Số cọc (gốc) | 8 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 41 | 0 | 4497 | -713 | 2001 | 0 |
| 2 | 41 | 0 | 3232 | -713 | 2004 | 0 |
| 3 | 32 | 0 | 4416 | -550 | 1566 | 0 |
| 11 | 39 | 16 | 3425 | -1008 | 1606 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.33` m; yêu cầu ≥ 3d = `3.60` m → **KHÔNG ĐẠT ✗**
- **R4** mép bệ: max|x|+d = `4.00` ≤ Lx/2 = `4.00`; max|y|+d = `4.80` ≤ Ly/2 = `4.80` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH9** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `752.4` / `151.9`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 8** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái (GỐC vốn vi phạm hình học → KHÔNG ĐẠT, khớp audit).

---

### `T7_EXT.txt` — Tru Mcoc-T7 EXT(max)+EXT(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 9.60 |
| Dài bệ Ly (m) | 16.80 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 15 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | -4 | 0 | 4549 | -7 | -131 | 0 |
| 2 | -47 | 0 | 2918 | -5 | -1589 | 0 |
| 3 | -409 | 0 | 3059 | -5 | -1635 | 0 |
| 12 | -2 | 0 | 4357 | -6 | 11992 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.60` m; yêu cầu ≥ 3d = `3.60` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `4.80` ≤ Lx/2 = `4.80`; max|y|+d = `8.40` ≤ Ly/2 = `8.40` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH12** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `623.7` / `-176.2`.
- ⚠ Có cọc bị **KÉO** (Pmin < 0) ở ít nhất một tổ hợp → nên khai **[Ct]** để kiểm R2/R5b.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 15** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T7_SER.txt` — Tru Mcoc-T7 SER(max)+SER(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 9.60 |
| Dài bệ Ly (m) | 16.80 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 15 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 409 | -13 | 3774 | 422 | 13596 | 0 |
| 2 | -396 | 4 | 3289 | -137 | -13134 | 0 |
| 3 | -399 | 4 | 3290 | -137 | -13225 | 0 |
| 12 | 414 | -13 | 3670 | 423 | 13750 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.60` m; yêu cầu ≥ 3d = `3.60` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `4.80` ≤ Lx/2 = `4.80`; max|y|+d = `8.40` ≤ Ly/2 = `8.40` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH1** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `637.1` / `-150.6`.
- ⚠ Có cọc bị **KÉO** (Pmin < 0) ở ít nhất một tổ hợp → nên khai **[Ct]** để kiểm R2/R5b.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 15** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T7_STR.txt` — Tru Mcoc-T7 STR(max)+STR(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 9.60 |
| Dài bệ Ly (m) | 16.80 |
| Đ.kính cọc d (m) | 1.20 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 15 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 149 | 0 | 5120 | -3 | 5097 | 0 |
| 2 | -445 | 0 | 2956 | -3 | -13368 | 0 |
| 3 | -445 | 0 | 2956 | -3 | -13368 | 0 |
| 12 | 347 | 0 | 4372 | -2 | 10025 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `3.60` m; yêu cầu ≥ 3d = `3.60` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `4.80` ≤ Lx/2 = `4.80`; max|y|+d = `8.40` ≤ Ly/2 = `8.40` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH4** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `570.0` / `-174.3`.
- ⚠ Có cọc bị **KÉO** (Pmin < 0) ở ít nhất một tổ hợp → nên khai **[Ct]** để kiểm R2/R5b.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 15** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T8_EXT.txt` — Tru Mcoc-T8 EXT(max)+EXT(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 22.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 22 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | -457 | 0 | 29841 | -110 | -9569 | 0 |
| 2 | -555 | 0 | 20876 | -75 | -15722 | 0 |
| 3 | -2503 | 0 | 21115 | -77 | -15575 | 0 |
| 12 | -414 | 0 | 29645 | -110 | 87582 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `11.00` ≤ Ly/2 = `11.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH12** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1982.9` / `141.7`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 22** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T8_SER.txt` — Tru Mcoc-T8 SER(max)+SER(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 22.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 22 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1023 | -4 | 24113 | 183 | 63077 | 0 |
| 2 | -1894 | 15 | 23350 | -989 | -84595 | 0 |
| 3 | -2167 | -5 | 23738 | 189 | -89901 | 0 |
| 12 | 1225 | 15 | 23836 | -998 | 72298 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `11.00` ≤ Ly/2 = `11.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH11** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1736.5` / `398.0`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 22** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T8_STR.txt` — Tru Mcoc-T8 STR(max)+STR(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 22.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 22 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 56 | 0 | 35175 | -126 | 20523 | 0 |
| 2 | -1714 | 0 | 20854 | -83 | -74260 | 0 |
| 3 | -2233 | 0 | 20906 | -82 | -95092 | 0 |
| 12 | 934 | 0 | 29526 | -109 | 56519 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `11.00` ≤ Ly/2 = `11.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH12** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1752.4` / `257.3`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 22** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T9_EXT.txt` — Tru Mcoc-T9 EXT(max)+EXT(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 24 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 5 | 0 | 33936 | -102 | -3373 | 0 |
| 2 | -23 | 0 | 23806 | -69 | -4500 | 0 |
| 3 | -1272 | 0 | 24033 | -71 | -8126 | 0 |
| 12 | 106 | 0 | 33717 | -101 | 63257 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH12** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1859.7` / `486.9`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 24** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T9_SER.txt` — Tru Mcoc-T9 SER(max)+SER(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 24 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | -396 | 0 | 27382 | -83 | -25298 | 0 |
| 2 | 376 | 0 | 26652 | -76 | 17319 | 0 |
| 3 | -678 | 0 | 27080 | -81 | -34533 | 0 |
| 12 | 625 | 0 | 26993 | -80 | 26188 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH3** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1376.7` / `875.1`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 24** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---

### `T9_STR.txt` — Tru Mcoc-T9 STR(max)+STR(min)

**B1. Nạp file → kiểm thông số parse (ô bên trái):**

| Thông số | Giá trị kỳ vọng |
|---|---:|
| Rộng bệ Lx (m) | 34.00 |
| Dài bệ Ly (m) | 28.00 |
| Đ.kính cọc d (m) | 2.00 |
| Sức nén [Po] (T) | 500 |
| Số tổ hợp tải | 12 |
| Số cọc (gốc) | 24 |

> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.

**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**

| TH | Hx | Hy | P | Mx | My | Mz |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | -177 | 0 | 40097 | -112 | -14343 | 0 |
| 2 | 95 | 0 | 23789 | -71 | 2873 | 0 |
| 3 | -839 | 0 | 23906 | -64 | -41931 | 0 |
| 12 | 767 | 0 | 33571 | -102 | 31024 | 0 |

**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**

- **R3** k/c tim-tim nhỏ nhất = `6.00` m; yêu cầu ≥ 3d = `6.00` m → ĐẠT ✓
- **R4** mép bệ: max|x|+d = `17.00` ≤ Lx/2 = `17.00`; max|y|+d = `14.00` ≤ Ly/2 = `14.00` → ĐẠT ✓

**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**

- **Tổ hợp CHI PHỐI dự kiến: TH5** (nội lực nén lớn nhất — bất biến theo đơn vị, dùng đối chiếu "TH… chi phối" trên KPI/bảng audit).
- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa các tổ hợp): `1803.7` / `584.2`.

**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**

- Phương án kiến nghị có **số cọc ≤ 24** (gốc) và **Pmax ≤ [Po]**.
- Chuyển radio **"Kiểm tra điều kiện (R1–R8)"**: tiêu đề bảng ghi *R1–R8*; mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.
- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).
- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).

---
