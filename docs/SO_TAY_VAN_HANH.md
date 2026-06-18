# SỔ TAY VẬN HÀNH — Tối Ưu Hóa Bố Trí Cọc Móng Cầu (OptApp v1.2.0)

> Tài liệu hướng dẫn vận hành **toàn bộ chức năng** của chương trình, kèm quy
> trình chuẩn, ý nghĩa các điều kiện R1–R8, và xử lý sự cố. Dành cho kỹ sư thiết
> kế nền móng. Cập nhật: 2026-06-18.

---

## 0. Tóm tắt nhanh (Quick start)

1. Mở chương trình: `python main.py`.
2. Bấm **"Mở file đầu vào"** → chọn file MCOC gốc (vd `mcoc_input_sample/T7_EXT.txt`).
3. **Nhập sức chịu tải THẬT** vào ô **[Po]** (và [Ct]/[M] nếu có) — *đừng dùng số
   500 mặc định của file* (xem [§6 Cảnh báo quan trọng](#6-cảnh-báo-quan-trọng-bẫy-po500)).
4. Chọn **MCOC Batch** ở mục *Cấu hình MCOC (bắt buộc)*.
5. Bấm **▶ CHẠY TỐI ƯU HÓA**.
6. Xem kết quả: chọn **Phương án** trên combobox, xem **Mặt bằng** hoặc
   **Kiểm tra điều kiện (R1–R8)**.
7. Bấm **"Xuất kết quả"** để lưu TXT (MCOC) + báo cáo `.md`/PDF + ảnh PNG.

---

## 1. Tổng quan & phạm vi mô hình

- **Mục tiêu**: tìm bố trí cọc (số cọc, lưới, khoảng cách) **ít cọc nhất** mà vẫn
  thỏa mọi điều kiện chịu lực + cấu tạo; có thể đồng thời **đổi đường kính cọc**
  và **thu nhỏ bệ** (luồng mở rộng).
- **Mô hình tính**: **bệ cứng** (rigid cap) — phân phối lực dọc trục cho từng cọc
  theo công thức giải tích, hiệu chỉnh theo MCOC thực. **CHƯA** xét Hx/Hy/Mz, hiệu
  ứng nhóm cọc, độ lún, hay kết cấu bệ. → Dùng cho **bố trí sơ bộ / tối ưu số cọc**;
  thiết kế chi tiết phải chạy **MCOC/FEM đầy đủ**.
- **Đơn vị (theo MCOC)**: lực = **Tấn (T)**, momen = **T·m**. Áp dụng cho cả tải
  trọng lẫn [Po]/[Ct]/[M].
- **Hai tab**: *(1) Tương tác (Interactive)* xử lý 1 hồ sơ; *(2) Hàng loạt (Batch)*
  chạy nhiều file/thư mục cùng lúc.

---

## 2. TAB 1 — TƯƠNG TÁC: từng chức năng

### 2.1. Thanh trên cùng (nhập/xuất hồ sơ)
| Nút | Chức năng |
|---|---|
| **Mở file đầu vào** | Chọn 1 hoặc nhiều file `.txt` (chuẩn MCOC) / `.csv`. Nạp Lx/Ly/d, tổ hợp tải, tọa độ cọc gốc. Cũng có thể **kéo-thả** file vào cửa sổ. |
| **Làm mới** | Xóa trắng toàn bộ (tải trọng, thông số, file gốc, kết quả) về như lúc mới mở. Có hỏi xác nhận. |
| **Xuất kết quả** | Lưu phương án đang có ra file (xem [§2.10](#210-xuất-kết-quả)). |

> **Nhận diện file**: nếu là *file kết quả MCOC* (`_result.txt`) chương trình tự
> đọc tọa độ + nội lực; nếu là *file input MCOC* thì dùng làm **template** sinh
> phương án mới. File `.csv` (tham số ở dòng đầu) cũng được hỗ trợ.

### 2.2. Thông số Bài toán
| Ô | Ý nghĩa | Ghi chú |
|---|---|---|
| **Rộng bệ Lx (m)** | Bề rộng bệ theo trục X | Mở khóa sửa được sau khi nạp file |
| **Dài bệ Ly (m)** | Chiều dài bệ theo trục Y | |
| **Đ.kính cọc d (m)** | Đường kính cọc | Quyết định 3d/6d (R3) và mép bệ (R4) |
| **Sức nén [Po] (T)** | Sức chịu nén dọc trục **cho phép** của 1 cọc | **BẮT BUỘC nhập thật** |
| **Sức nhổ [Ct] (T)** | Sức chịu nhổ (kéo) cho phép | Để trống/0 = không kiểm nhổ |
| **Sức uốn [M] (T·m)** | Momen đầu cọc cho phép | Để trống/0 = không kiểm uốn |

### 2.3. Tổ hợp Tải trọng
- Bảng các tổ hợp: **Hx, Hy, P(N), Mx, My, Mz** (T và T·m).
- **Thêm tổ hợp** / **Sửa dòng chọn** (hoặc nhấp đúp) / **Xóa dòng chọn**.
- **Dán nhiều dòng (CSV)**: dán nhanh nhiều tổ hợp từ Excel.
- Lưu ý: mô hình bệ cứng chỉ dùng **P, Mx, My** để phân phối lực dọc trục; Hx/Hy/Mz
  được lưu nhưng **chưa xét** (trừ R7 lực ngang ở luồng mở rộng).

### 2.4. Điều Khiển Tối Ưu
- **Chỉ phương án tối ưu** / **Hiện tất cả phương án**: chi phối **khâu XUẤT FILE**
  (xuất 1 hay tất cả phương án đạt). Trên màn hình **luôn** liệt kê đủ phương án.
- **Ưu tiên**:
  - *Tiết kiệm (bệ gọn)* — `compact`: sau khi đủ số cọc & đạt, ưu tiên bệ nhỏ gọn.
  - *An toàn (giảm Pmax)* — `pmax`: ưu tiên hạ Pmax (dự trữ lớn hơn).
- **K/c tối thiểu (×d)**: hệ số khoảng cách tim‑tim nhỏ nhất. **Mặc định 3.0 (3d
  theo TCVN)**; có thể chọn 2.75/2.5 cho cọc khoan nhồi cho phép gần hơn. Đây là
  **lựa chọn của người dùng**, không thay đổi mặc định thuật toán — để trống thì
  vẫn dùng 3d. Xem [§5b](#5b-xử-lý-bệ-chật-tùy-chọn).
- **Đề xuất nới bệ khi bệ chật** (mặc định bật): khi không tìm được phương án, in
  thêm gợi ý kích thước bệ tối thiểu (xem [§5b](#5b-xử-lý-bệ-chật-tùy-chọn)).

### 2.5. Cấu hình MCOC (bắt buộc)
- **MCOC Batch**: đường dẫn tới chương trình MCOC Batch (Command Line) — chấm điểm
  mọi phương án bằng FEM thực. Bấm **"..."** để chọn (chấp nhận `.lnk/.exe/.bat/.py`).
- **File input gốc**: hiển thị file template MCOC đang dùng (nạp ở [§2.1](#21-thanh-trên-cùng-nhậpxuất-hồ-sơ)).
- *Mọi phương án đều được chấm bằng MCOC chính xác* → cần **cả** MCOC Batch **và**
  file input MCOC gốc thì nút Chạy mới hoạt động.

### 2.6. Tối ưu mở rộng (tùy chọn)
Bật ô **"Bật tối ưu mở rộng (đổi đường kính cọc + thu bệ)"** để mở các tùy chọn:
| Tùy chọn | Ý nghĩa |
|---|---|
| **R7 lực ngang [H]** | Kiểm tra Hmax ≤ [H] (cần [H] > 0 trong bảng đường kính) |
| **R8 tương tác P–M** | Kiểm N_max/[Po] + M/[M] ≤ 1.0 (cần [M] > 0) |
| **Tự thu bệ** + *Làm tròn (m)* | Sau khi tối ưu, thu bệ vừa khít theo TCVN (mép cách tim ≥ d), làm tròn lên bội số 0.05–1.0 m |
| **Bảng đường kính...** | Khai báo nhiều đường kính ứng viên, mỗi đường kính có [Po]/[Ct]/[M]/[H] riêng. Chương trình quét tất cả rồi chọn **rẻ nhất** (chi phí = số cọc × diện tích tiết diện), đồng hạng thì ít cọc hơn. |

> Khi không khai báo bảng đường kính, luồng mở rộng dùng **đúng đường kính hiện tại**.

### 2.7. ▶ CHẠY TỐI ƯU HÓA
- Luồng chuẩn (NSGA-II + MCOC): tối ưu bố trí ở **đường kính cố định**.
- Khi bật *Tối ưu mở rộng*: quét đường kính + R7/R8 + thu bệ.
- Chạy ở luồng nền (không treo giao diện); tiến trình in ra ô **Kết quả Đánh giá**.

### 2.8. Kết quả Đánh giá (ô văn bản)
In: phương án kiến nghị (kiểu lưới, số cọc, sx/sy, Pmax/Pmin, **kích thước bệ**,
tọa độ đầu cọc), **PHƯƠNG ÁN GỐC** (số cọc, Pmax/Pmin, **kích thước bệ gốc**), và
bảng tất cả phương án đạt (Kiểu, nx, ny, n, sx, sy, Pmax…).

### 2.9. Khu mô phỏng (bên phải)
- **Combobox Phương án**: *Phương án gốc* / *Phương án đề xuất* / *Phương án 1, 2…*
  — **mỗi phương án vẽ trong bệ + đường kính + sức chịu CỦA CHÍNH NÓ** (xem [§5](#5-nguyên-tắc-mỗi-phương-án-đi-theo-chính-nó)).
- **Combobox Tổ hợp**: chọn tổ hợp tải để xem phân bố lực; mặc định mở ở tổ hợp
  **chi phối** (Nmax lớn nhất).
- **Mặt bằng**: vẽ bệ, viền giới hạn tâm cọc, từng cọc tô màu theo lực P (thang màu
  bên phải, vạch đỏ = [Po]); nhãn P từng cọc; Max Momen; tiêu đề ĐẠT/KHÔNG ĐẠT
  (theo lực: nén/nhổ/uốn).
- **Kiểm tra điều kiện (R1–R8)**: bảng kiểm toán từng tổ hợp + tổng hợp hình học
  (xem [§4](#4-các-điều-kiện-r1r8)).
- Dải KPI phía trên: **Số cọc | Hệ số sử dụng lớn nhất (TH chi phối) | Trạng thái**.

### 2.10. Xuất kết quả
Một lần bấm sinh ra (theo lựa chọn BEST/ALL):
1. **`.txt`** định dạng MCOC (nạp lại được vào MCOC),
2. **`_baocao_kythuat.md`** — báo cáo kỹ thuật (hệ số sử dụng, bảng R1–R8, phụ lục),
3. **PDF** báo cáo,
4. **PNG** ảnh mặt bằng từng phương án.
Phiên *mở rộng* còn thêm mục **"3b. Tối ưu mở rộng"** (bảng quét đường kính + thu bệ)
và cột H_max (R7).

---

## 3. TAB 2 — HÀNG LOẠT (Batch Mode)

| Khu | Chức năng |
|---|---|
| **Thêm file / Thêm thư mục** | Nạp nhiều hồ sơ vào danh sách (cũng kéo-thả được). |
| Bảng *Dữ liệu đầu vào* | Tên file, thư mục, trạng thái. **Xóa tất cả / Xóa chọn**. |
| **Thư mục xuất kết quả** | Chọn nơi lưu; để trống = lưu cạnh từng file đầu vào. |
| Tab *Xuất kết quả* | Bật/tắt: **Xuất báo cáo PDF**, **Xuất bảng Excel**, **Xuất mặt bằng PNG**, **Gộp các PDF thành một file tổng hợp**. |
| Tab *Nâng cao* | **Prefix / Suffix** tên file xuất. |
| **Tiến trình** | Thanh tiến độ + log; nút **Dừng**; nút **Mở thư mục** kết quả khi xong. |
| **▶ CHẠY HÀNG LOẠT** | Xử lý lần lượt toàn bộ danh sách. |

---

## 4. Các điều kiện R1–R8

| Mã | Tên | Công thức / tiêu chí | Khi nào kiểm |
|---|---|---|---|
| **R1** | Huy động nén | `N_max / [Po] ≤ 1` (mỗi tổ hợp) | luôn (cần [Po]>0) |
| **R2** | Huy động nhổ | `max(0, −N_min) / [Ct] ≤ 1` | khi [Ct]>0 |
| **R3** | Khoảng cách tim cọc | `3d ≤ s ≤ 6d` (kiểu so le xét **đường chéo** `√((sx/2)²+sy²)`) | luôn |
| **R4** | Mép bệ | tim cọc ngoài cùng cách mép bệ **≥ d** | khi có Lx/Ly |
| **R5/R6** | Uốn | momen đầu cọc `max(Mx,My) ≤ [M]` | khi [M]>0 |
| **R7** | Lực ngang | `Hmax ≤ [H]` | chỉ luồng **mở rộng**, [H]>0 |
| **R8** | Tương tác P–M | `N_max/[Po] + M/[M] ≤ 1.0` | khi [M]>0 và [Po]>0 |

- **Cận dưới R3** = `max(3d, d + thông thủy)` (nếu khai báo thông thủy CLEAR_MIN).
- **Trạng thái tổng** "ĐẠT" của bảng R1–R8 = đạt **tất cả** R1…R8 áp dụng được. Tiêu
  đề trên *Mặt bằng* chỉ xét lực (R1/R2/R5) nên có thể "ĐẠT" trong khi bảng R1–R8
  "KHÔNG ĐẠT" vì lỗi **hình học** (R3/R4) — hãy tin **bảng R1–R8**.

---

## 5. Nguyên tắc "mỗi phương án đi theo chính nó"

Sau khi tối ưu mở rộng, các ô *Thông số Bài toán* (d, Lx, Ly, [Po]…) được cập nhật
theo **phương án thắng** (thiết kế áp dụng). Tuy vậy, khi bạn chọn **Phương án gốc**
trên combobox, phần **mặt bằng + bảng R1–R8 + thang màu** sẽ tự dùng **đường kính,
sức chịu và kích thước bệ GỐC** — không phải của phương án thắng. Nhờ đó:

- Bệ gốc được vẽ đúng kích thước gốc (không bị "ép" vào bệ đã thu) → khoảng cách cọc
  hiển thị đúng tỉ lệ.
- Audit R3 dùng `3d` theo **đường kính gốc** → không báo *KHÔNG ĐẠT* oan.
- Thang màu hiển thị đúng `[Po]` gốc.

→ Cho phép **so sánh sự tiến hóa** giữa phương án gốc và phương án đề xuất một cách
trung thực. (Riêng các *ô nhập* luôn hiển thị thông số phương án thắng vì đó là
thiết kế áp dụng.)

---

## 5b. Xử lý BỆ CHẬT (tùy chọn)

"Bệ chật" = bệ cố định quá nhỏ để chứa đủ cọc gánh tải ở khoảng cách tối thiểu
(xung đột R3 ↔ R4 ↔ R1). Khi đó **bình thường** chương trình **không tự ý phình
bệ** (vì kích thước bệ cầu bị khống chế bởi trụ/tĩnh không), mà **chẩn đoán định
lượng + đề xuất** để kỹ sư quyết định, qua 3 cơ chế bạn **tự bật/tắt**:

1. **Lượng hóa** (luôn hiện khi vô nghiệm): *"Bệ hiện chứa tối đa N cọc (lưới
   nx×ny @ k/c ≥ s)."* → biết ngay bệ thiếu chỗ hay thiếu sức chịu.
2. **Đề xuất nới bệ** (ô *"Đề xuất nới bệ khi bệ chật"*): tính lưới ≥2×2 ít cọc
   nhất ĐẠT lực (bỏ qua mép bệ) và **bệ nhỏ nhất** chứa nó → *"Nới bệ tối thiểu ~
   A×B m (nx×ny = M cọc, Pmax ~ … ≤ [Po])."* Chỉ **đề xuất**, không tự áp dụng.
3. **Giảm k/c tối thiểu** (ô *"K/c tối thiểu ×d"*): hạ 3d → 2.75d/2.5d nếu loại cọc
   cho phép (vd khoan nhồi), để tái lập các hồ sơ dùng k/c < 3d.

> Thứ tự xử lý khuyến nghị: **(a)** xem có nới được bệ không → **(b)** tăng đường
> kính (luồng mở rộng) → **(c)** chỉ giảm k/c tối thiểu khi tiêu chuẩn/loại cọc
> cho phép. Mọi con số gợi ý dùng mô hình bệ cứng — xác nhận lại bằng MCOC.

---

## 6. CẢNH BÁO QUAN TRỌNG: bẫy [Po]=500

`[Po]/[Ct]/[M]` ghi trong file input MCOC **chỉ là giá trị MẶC ĐỊNH (thường 500 T)**,
MCOC **không dùng** để chấm. Nếu để nguyên 500:

- Với cọc lớn (vd d=2.0 m, sức chịu thật ~2000 T) **mọi phương án sẽ "trượt"** vì
  Pmax > 500 → chương trình báo *không tìm được lời giải*.

**Luôn nhập [Po] THẬT theo đường kính cọc.** Khi nạp file, nếu ô [Po] đang trống mới
được điền tạm từ file; chương trình **không ghi đè** giá trị bạn đã nhập.

> Kiểm chứng trên bộ mẫu: 35/38 file có `Pmax(gốc) > 500` chính vì lý do này.

---

## 7. Quy trình vận hành chuẩn (SOP)

```
1. Nạp file input MCOC gốc          (Mở file đầu vào / kéo-thả)
2. Kiểm Lx, Ly, d, tổ hợp tải đã đúng
3. NHẬP [Po] (và [Ct]/[M]) THẬT     ← bước hay bị bỏ sót
4. (Tùy chọn) Bật Tối ưu mở rộng + khai báo Bảng đường kính
5. Chọn MCOC Batch
6. ▶ CHẠY TỐI ƯU HÓA  → đợi MCOC chấm
7. Đọc Kết quả Đánh giá; chuyển combobox xem từng phương án
8. Mở "Kiểm tra điều kiện (R1–R8)" để duyệt từng tổ hợp
9. So sánh Phương án gốc ↔ đề xuất (số cọc, bệ, Pmax)
10. Xuất kết quả (TXT + báo cáo .md/PDF + PNG)
11. Chạy lại MCOC/FEM đầy đủ cho thiết kế chi tiết
```

---

## 8. Xử lý sự cố thường gặp

| Hiện tượng | Nguyên nhân | Cách xử lý |
|---|---|---|
| "Cần cấu hình MCOC" | Chưa chọn MCOC Batch | Mục *Cấu hình MCOC* → "..." |
| "Thiếu file MCOC gốc" | Chưa nạp file input có tọa độ cọc | Mở đúng **file input** (không phải `_result`/`.csv`) |
| Không tìm được phương án | [Po] còn 500 (bẫy §6); hoặc bệ quá chật so với R3 (3d) | Nhập [Po] thật; nới bệ hoặc xét đổi đường kính (mở rộng) |
| Phương án gốc báo *KHÔNG ĐẠT* | R3: khoảng cách gốc < 3d, hoặc R4 mép bệ | Là đặc tính hồ sơ gốc — xem bảng R1–R8 để biết điều kiện nào vi phạm |
| Mặt bằng "ĐẠT" nhưng R1–R8 "KHÔNG ĐẠT" | Tiêu đề mặt bằng chỉ xét lực | Tin **bảng R1–R8** (xét cả hình học) |
| Treo lâu | MCOC chấm nhiều phương án | Đợi; hoặc giảm bảng đường kính / ngân sách |

---

## 9. Công cụ kiểm thử nội bộ (cho người phát triển)

| Script | Mục đích |
|---|---|
| `python -m pytest tests/` | Bộ test đơn vị (lõi + mở rộng), không cần MCOC. |
| `python tests/_review_all.py` | **Duyệt toàn bộ** file `mcoc_input_sample/`: parse + kiểm R3/R4 + Pmax/Pmin bệ cứng. |
| `python tests/_test_cases.py` | **Chạy tối ưu** (mock bệ cứng) trên mọi file `*_EXT`, báo số cọc giảm/khả thi. |
| `python tests/_drive_ui.py` | Khởi chạy GUI thật, nạp mẫu, **chụp màn hình** từng trạng thái vào `tests/_ui_shots/`. |
| `python run_demo.py` | Chạy quy trình tối ưu từ dòng lệnh (không GUI). |
| `python run_validate.py` | So sánh độ chính xác Hộp đen (bệ cứng) ↔ MCOC. |

### Kết quả duyệt bộ mẫu (2026-06-18, mô hình bệ cứng)
- **38/38 file** parse được, không lỗi.
- **35 file** có `Pmax(gốc) > [Po]=500` → đúng bẫy §6 (cần nhập [Po] thật).
- **10 file** (T3–T6, T22 bản EXT/STR) có khoảng cách gốc **3.33 m < 3d=3.60 m** →
  vi phạm R3 theo tiêu chí công cụ; cũng là 5 ca *EXT* mà bộ tối ưu **không tái lập
  được** trong bệ chật khi ép `s ≥ 3d`. Đây là đặc tính **dữ liệu gốc** (thiết kế
  thật dùng k/c < 3d), không phải lỗi chương trình.
- Bộ tối ưu chạy **không treo/crash** trên toàn bộ 15 ca EXT; 10/15 ca tìm được
  phương án đạt (5 ca chật bệ như trên).

---

## 10. Giới hạn cần nhớ

- Mô hình **bệ cứng** — chỉ phân phối lực dọc trục; **chưa** xét Hx/Hy/Mz (trừ R7),
  nhóm cọc, độ lún, kết cấu bệ.
- `[Po]/[Ct]/[M]` trong file là **mặc định** — phải nhập thật.
- Min khoảng cách mặc định **3d** có thể chặt hơn thực tế ở các bệ chật; cân nhắc
  khai báo *thông thủy* hoặc đổi đường kính (luồng mở rộng).
- Kết quả là **bố trí sơ bộ / tối ưu số cọc**; thiết kế chi tiết **bắt buộc** chạy
  MCOC/FEM đầy đủ.
