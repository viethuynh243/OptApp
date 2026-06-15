# 📗 HƯỚNG DẪN SỬ DỤNG — OptApp (Tối ưu bố trí cọc móng cầu)

> Tài liệu dành cho **người dùng** (kỹ sư thiết kế). Nếu cần hiểu thuật toán/kiến
> trúc bên trong, xem `methodology.md`.

---

## 1. OptApp làm gì?

OptApp tự động tìm **phương án bố trí cọc ít cọc nhất** mà vẫn đạt mọi điều kiện
kỹ thuật (sức chịu nén/nhổ, khoảng cách cọc, cọc nằm trong bệ…). Mỗi phương án
được **chấm bằng phần mềm MCOC** (chính xác), nên kết quả dùng được cho hồ sơ.

Tổng quan các bước sử dụng:

```mermaid
flowchart LR
    A["Cài & mở<br/>OptApp"] --> B["Cấu hình MCOC<br/>(1 lần)"]
    B --> C["Nhập số liệu:<br/>bệ, cọc, tải trọng"]
    C --> D["Bấm<br/>CHẠY TỐI ƯU HÓA"]
    D --> E["Xem kết quả<br/>& mặt bằng"]
    E --> F["Xuất kết quả<br/>(TXT, báo cáo, ảnh)"]
```

---

## 2. Cài đặt

### Cách 1 — Dùng bộ cài (khuyến nghị)

1. Chạy **`OptApp_Setup_1.0.0.exe`**.
2. Làm theo trình cài đặt (chọn thư mục, tạo shortcut Desktop nếu muốn).
3. Mở **OptApp** từ Start Menu hoặc Desktop.

> Bộ cài chỉ gồm OptApp. Phần mềm **MCOC** (`MCOC_Batch.exe`) bạn cài/đặt riêng.

### Cách 2 — Chạy từ mã nguồn

```bat
pip install numpy matplotlib openpyxl reportlab tkinterdnd2 PyPDF2
cd d:\Project\TEDI\OptApp
python main.py
```

---

## 3. Chuẩn bị trước khi chạy (quan trọng)

OptApp chấm mọi phương án bằng MCOC nên cần **2 thứ** sau (cấu hình một lần):

| Cần có                       | Là gì                                                                                        | Lấy ở đâu trong app                                |
| ------------------------------ | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **MCOC Batch**           | File `MCOC_Batch.exe` (hỗ trợ cả `.bat/.py/.lnk`)                                       | Mục *Cấu hình MCOC (bắt buộc)* → nút `...` |
| **File input MCOC gốc** | File `.txt` đầu vào của MCOC, **có sẵn tọa độ cọc gốc** (dùng làm khuôn) | Nút*Mở file đầu vào*                            |

> ⚠️ File input gốc phải là **file đầu vào MCOC** — KHÔNG phải file `_result` (kết
> quả) hay file CSV.

---

## 4. Tab 1 — Tương tác (dùng hằng ngày)

Giao diện chia 2 phần: **bên trái** nhập liệu & kết quả, **bên phải** vẽ mặt bằng cọc.

### Bước 1 — Nạp số liệu

Có 2 cách:

- **Mở file:** bấm *“Mở file đầu vào (hoặc kéo-thả)”* rồi chọn file `.txt` (MCOC)
  hoặc `.csv`. Có thể **kéo-thả** thẳng file vào cửa sổ.
- **Nhập tay:** điền trực tiếp ở khung *Thông số Bài toán* và *Tổ hợp Tải trọng*.

### Bước 2 — Thông số Bài toán

| Thông số | Ký hiệu | Ý nghĩa | Đơn vị |
|---|---|---|---|
| Rộng bệ | Lx | Chiều rộng bệ | m |
| Dài bệ | Ly | Chiều dài bệ | m |
| Đ.kính cọc | d | Đường kính cọc | m |
| Sức chịu nén | [Po] | Sức chịu nén cho phép của 1 cọc | Tấn (T) |
| Sức chịu nhổ | [Ct] | Sức chịu nhổ cho phép (0 = bỏ qua) | T |
| Sức chịu uốn | [M] | Sức chịu uốn cho phép (0 = bỏ qua) | T.m |

> 🔎 **Đơn vị (theo MCOC):** lực = **Tấn (T)**, momen = **T.m** — áp dụng cho cả
> tải trọng lẫn [Po]/[Ct]/[M]. Bắt buộc Lx, Ly, d, [Po] đều > 0.

### Bước 3 — Tổ hợp Tải trọng

Mỗi dòng là một tổ hợp: **Hx, Hy** (lực ngang), **P** (lực đứng), **Mx, My, Mz** (momen).

- **Thêm tổ hợp** — mở hộp thoại nhập 1 tổ hợp.
- **Sửa dòng chọn** (hoặc nháy đúp) / **Xóa dòng chọn**.
- **Dán nhiều dòng (CSV)** — dán nhanh nhiều tổ hợp một lúc.

### Bước 4 — Cấu hình MCOC (bắt buộc)

- **MCOC Batch:** bấm `...` chọn `MCOC_Batch.exe`.
- **File input gốc:** đã nạp ở Bước 1 (dòng *“File input gốc: …”* hiện tên file).

### Bước 5 — Tùy chọn tối ưu

- **Phạm vi xuất:** *Chỉ phương án tối ưu* hoặc *Hiện tất cả phương án*.
- **Ưu tiên** (khi đã đủ số cọc & đạt [Po]):
  - **Tiết kiệm (bệ gọn)** — gom cọc sát nhau, bệ nhỏ nhất *(mặc định)*.
  - **An toàn (giảm Pmax)** — trải cọc để giảm lực đầu cọc.

### Bước 6 — Chạy

Bấm nút lớn **▶ CHẠY TỐI ƯU HÓA**. App chạy MCOC ở chế độ nền (có log tiến trình
ở khung *Kết quả Đánh giá*); chờ một lát tuỳ số phương án.

### Bước 7 — Đọc kết quả & xem mặt bằng

- Khung **Kết quả Đánh giá** (trái): phương án kiến nghị, số cọc, Pmax/Pmin, lý do chọn.
- Bên phải: chọn **Phương án** và **Tổ hợp** ở 2 ô combobox để xem **mặt bằng cọc**
  tô màu nhiệt theo mức tải:
  - 🟢 thấp (an toàn) · 🟡 gần giới hạn · 🔴 vượt [Po] · 🟣 nhổ vượt [Ct].

### Bước 8 — Xuất kết quả

Bấm **Xuất kết quả**, chọn nơi lưu. App tạo:

| File                                                          | Nội dung                                                                 |
| ------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `*.txt`                                                     | Kết quả định dạng MCOC (tọa độ cọc, nội lực)                   |
| `*_baocao_kythuat.md`                                       | Báo cáo kỹ thuật: hệ số sử dụng, tổ hợp chi phối, bảng R1–R6 |
| `*_De_xuat.png` (hoặc nhiều ảnh nếu chọn “tất cả”) | Ảnh mặt bằng bố trí cọc                                             |

> *Làm mới* để xoá số liệu/kết quả và bắt đầu lại.

---

## 5. Tab 2 — Hàng loạt (Batch Mode)

Dùng khi cần chạy **nhiều file** cùng lúc (mỗi file là một template MCOC riêng).

1. Cấu hình **MCOC Batch** ở Tab 1 trước (bắt buộc).
2. Sang Tab 2, khung *Dữ liệu đầu vào*: **Thêm file** / **Thêm thư mục** (và *Xóa
   chọn* / *Xóa tất cả* nếu cần).
3. Khung *Thiết lập chạy*: chọn **thư mục lưu kết quả**, đặt **tiền tố/hậu tố** tên file.
4. Bấm **TÍNH TOÁN** — app chạy ngầm, hiện log ở khung *Tiến trình* (bấm **Dừng**
   để hủy). Mỗi file được xuất **Excel + PDF + PNG** tự động.
5. Bấm **Mở thư mục kết quả** để xem.

---

## 6. Các thông báo thường gặp & cách xử lý

| Thông báo                           | Nguyên nhân                                        | Cách xử lý                                         |
| ------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------- |
| **Chưa nhập đủ thông số** | Thiếu Lx/Ly/d/[Po] (phải > 0)                      | Điền đủ ở*Thông số Bài toán*               |
| **Chưa có tải trọng**       | Chưa nhập tổ hợp tải                            | Thêm tổ hợp / Dán CSV / mở file                  |
| **Cần cấu hình MCOC**        | Chưa chọn `MCOC_Batch.exe`                       | Chọn ở*Cấu hình MCOC* → `...`                |
| **Thiếu file MCOC gốc**       | Chưa nạp file input MCOC (có tọa độ cọc gốc) | *Mở file đầu vào* nạp file `.txt` input MCOC |
| **LỖI TEMPLATE**               | File input gốc không khớp tọa độ cọc          | Kiểm tra lại đúng file input MCOC gốc            |

---

## 7. Chạy nhanh không cần giao diện (tuỳ chọn)

Dành cho người dùng nâng cao / kiểm thử:

```bat
python run_nsga2_demo.py   REM Demo NSGA-II (mock), tự xuất nsga2_result.txt
python run_demo.py         REM Demo quét nhanh bằng bệ cứng (không cần MCOC)
```

---

## 8. Mẹo dùng hiệu quả

- Luôn để **đơn vị Tấn (T)** cho cả tải trọng và sức chịu tải — nhầm kN sẽ ra sai số lớn.
- Bắt đầu với ưu tiên **Tiết kiệm (bệ gọn)**; nếu lo lực đầu cọc cao thì đổi sang
  **An toàn (giảm Pmax)** và chạy lại.
- Muốn báo cáo đầy đủ để thẩm tra: chọn xuất và mở file `*_baocao_kythuat.md`.
- Với nhiều mố/trụ: dùng **Tab Hàng loạt** để xuất đồng loạt PDF/Excel/PNG.

---

*Phiên bản OptApp 1.0.0 — cập nhật 2026-06-15.*
