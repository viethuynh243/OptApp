# HƯỚNG DẪN NHANH — Làm theo từng bước (ví dụ file T7_EXT.txt)

> **Mã:** OA-DOC-09b · **Phiên bản:** 1.0 · **Cập nhật:** 2026-06-29 · **Trạng thái:** Approved · **Căn cứ:** ui/; mcoc_input_sample (nội bộ)


> Mục tiêu: chạy được một lần từ đầu đến cuối. **Bạn chỉ phải gõ tay đúng 2 thứ**:
> ① ô **Sức nén [Po]**, ② đường dẫn **MCOC Batch** (chỉ chọn 1 lần đầu). Mọi thứ
> còn lại (Lx, Ly, d, 12 tổ hợp tải) chương trình **tự điền khi mở file**.

---

## PHẦN A — Chạy cơ bản (tối ưu số cọc, giữ 1 đường kính)

### Bước 1 — Mở chương trình
Mở thư mục dự án rồi chạy:
```
python main.py
```
Cửa sổ hiện ra, đang ở tab **"1. Tương tác (Interactive)"**.

### Bước 2 — Mở file đầu vào (KHÔNG gõ gì, chỉ chọn file)
- Bấm nút **"Mở file đầu vào (hoặc kéo-thả)"** (góc trên trái).
- Chọn `mcoc_input_sample/T7_EXT.txt` (hoặc kéo file thả vào cửa sổ).

➡️ Sau bước này chương trình **tự điền**:
| Ô | Giá trị tự điền |
|---|---|
| Rộng bệ Lx (m) | **9.6** |
| Dài bệ Ly (m) | **16.8** |
| Đ.kính cọc d (m) | **1.2** |
| Bảng *Tổ hợp Tải trọng* | **12 dòng** (Hx, Hy, P, Mx, My, Mz) |

> Nếu 3 ô Lx/Ly/d trống hoặc bảng tải rỗng → file chọn sai (phải là file **input
> MCOC**, không phải file `_result.txt` hay `.csv`).

### Bước 3 — GÕ ô "Sức nén [Po]" (đây là thứ quan trọng nhất phải gõ tay)
- Vào ô **"Sức nén [Po] (T)"** → gõ sức chịu nén **THẬT** của 1 cọc theo thiết kế.
- Ví dụ làm theo: **gõ `900`**.

> ⚠️ KHÔNG để [Po] trống/500. Số trong file chỉ là mặc định; để 500 thì cọc d=1.2
> sẽ "trượt" hết. Khi thiết kế thật, thay 900 bằng Rc,d tính theo TCVN của bạn.

### Bước 4 — (Tùy chọn) [Ct], [M]
- **Sức nhổ [Ct] (T)**: nếu có cọc chịu nhổ → gõ sức chịu nhổ. Không có → **để trống**.
- **Sức uốn [M] (T·m)**: nếu kiểm uốn đầu cọc → gõ giá trị. Không kiểm → **để trống**.
- Với T7 làm thử: để **trống cả hai**.

### Bước 5 — Chọn MCOC Batch (chỉ làm 1 lần, lần sau nhớ)
- Mục **"Cấu hình MCOC (bắt buộc)"** → bấm nút **"..."**.
- Trỏ tới:
  ```
  C:\ProgramData\Microsoft\Windows\Start Menu\Programs\MCOC Python\MCOC Batch (Command Line).lnk
  ```
- Dòng **"File input gốc:"** ngay dưới sẽ hiện `T7_EXT.txt` (xác nhận đã có template).

### Bước 6 — (Không bắt buộc) Điều khiển tối ưu
Để mặc định là chạy được. Ý nghĩa nhanh:
- **Ưu tiên: Tiết kiệm (bệ gọn)** ← mặc định, ít cọc/bệ nhỏ.
- **K/c tối thiểu: 3.0 ×d** ← để nguyên (3d theo TCVN).

### Bước 7 — Bấm ▶ CHẠY TỐI ƯU HÓA
- Nút xanh lớn. Ô **"Kết quả Đánh giá"** chạy log "Đang chạy MCOC, vui lòng đợi...".
- Đợi MCOC chấm xong (vài giây–vài phút tùy số phương án).

### Bước 8 — Đọc kết quả
- Combobox **"Phương án"** (trên cùng) → chọn:
  - **Phương án đề xuất** = lời giải tối ưu (vd 10 cọc),
  - **Phương án gốc** = thiết kế ban đầu (15 cọc) để so sánh,
  - **Phương án 1, 2…** = các lời giải đạt khác.
- Combobox **"Tổ hợp"** → xem phân bố lực từng tổ hợp (mặc định mở ở tổ hợp chi phối).
- Nút **"Mặt bằng"** / **"Kiểm tra điều kiện (R1–R8)"** → đổi giữa hình vẽ và bảng kiểm.
- Dải chữ trên hình: **Số cọc | Hệ số sử dụng | Trạng thái (ĐẠT/KHÔNG ĐẠT)**.

### Bước 9 — Xuất kết quả
- Bấm **"Xuất kết quả"** → đặt tên file → OK.
- Sinh ra: `.txt` (MCOC) + `_baocao_kythuat.md` + PDF + ảnh PNG mặt bằng.

✅ **Xong phần cơ bản.** Tóm lại bạn chỉ gõ: **[Po]=900** và chọn **MCOC Batch**.

---

## PHẦN B — Chạy MỞ RỘNG (để chương trình tự đổi đường kính + thu bệ)

Làm hết Bước 1–5 ở trên, rồi:

### Bước B1 — Bật tối ưu mở rộng
- Tick ô **"Bật tối ưu mở rộng (đổi đường kính cọc + thu bệ)"**.
- Hiện thêm: R7/R8, *Tự thu bệ*, *Bảng đường kính…*

### Bước B2 — Khai báo Bảng đường kính (các đường kính muốn so sánh)
- Bấm **"Bảng đường kính..."** → cửa sổ bảng.
- Thêm từng dòng, mỗi đường kính kèm sức chịu **riêng** (cọc to chịu khỏe hơn). Ví dụ:

  | d (m) | [Po] (T) | [Ct] (T) | [M] (T·m) | [H] (T) |
  |---|---|---|---|---|
  | 1.0 | 650 | 0 | 0 | 0 |
  | 1.2 | 900 | 0 | 0 | 0 |
  | 1.5 | 1400 | 0 | 0 | 0 |

  > Nếu không khai báo bảng, chương trình dùng đúng đường kính + [Po] hiện tại.

### Bước B3 — Tùy chọn
- **Tự thu bệ** ☑ + *Làm tròn (m)* = 0.1 → sau khi tối ưu, bệ thu vừa khít, làm tròn 0.1 m.
- R7/R8: chỉ bật nếu có khai báo [H]/[M] tương ứng.

### Bước B4 — ▶ CHẠY TỐI ƯU HÓA
- Chương trình quét từng đường kính, chọn phương án **rẻ nhất**, thu bệ.
- Kết quả in bảng so sánh các đường kính + đường kính THẮNG (đánh dấu `*`).
- Các ô d / [Po] / Lx / Ly tự cập nhật theo phương án thắng.

> Khi xem **Phương án gốc** lúc này, hình vẽ vẫn dùng **bệ + đường kính GỐC** (để
> so sánh đúng), còn các ô nhập hiển thị thông số phương án thắng.

---

## PHẦN C — Khi báo "Không tìm được phương án" (bệ chật)

Ô Kết quả sẽ in ngay phần **"GỢI Ý XỬ LÝ BỆ CHẬT"**, ví dụ:
```
Bệ hiện tại 8 x 9.6 m chứa TỐI ĐA 6 cọc (lưới 2x3 @ k/c ≥ 3.60 m).
Để đạt ở k/c tối thiểu, NỚI bệ tối thiểu ~ 6.0 x 13.2 m (lưới 2x4 = 8 cọc...).
Hoặc: tăng đường kính cọc, hoặc giảm k/c tối thiểu nếu loại cọc cho phép.
```
Làm theo thứ tự:
1. **Nới bệ**: sửa ô **Lx/Ly** theo số gợi ý → bấm chạy lại.
2. **Tăng đường kính**: bật mở rộng + thêm đường kính lớn hơn (Phần B).
3. **Giảm k/c tối thiểu** (chỉ khi loại cọc cho phép, vd khoan nhồi): đổi ô
   **"K/c tối thiểu"** từ 3.0 → 2.75 hoặc 2.5 → chạy lại.

---

## Bảng "phải gõ gì" (rút gọn)

| Bước | Thao tác | Gõ/chọn |
|---|---|---|
| 2 | Mở file | chọn `T7_EXT.txt` |
| 3 | Sức nén [Po] | **900** (sức chịu thật của bạn) |
| 4 | [Ct], [M] | để trống (trừ khi có) |
| 5 | MCOC Batch | chọn file `.lnk` (1 lần) |
| 7 | Chạy | bấm nút xanh |

Mọi giá trị Lx, Ly, d, 12 tổ hợp tải: **không gõ — tự điền từ file.**
