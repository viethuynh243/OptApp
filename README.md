# OptApp - Tối ưu hóa bố trí cọc móng cầu

Ứng dụng này hỗ trợ tối ưu hóa bố trí cọc móng cầu trên bệ móng dạng chữ nhật. Mục tiêu là tìm phương án bố trí có **số cọc ít nhất** mà vẫn đảm bảo các điều kiện chịu lực và thi công.

> **Nguyên tắc chính xác bắt buộc:** Bên thi công **chỉ chấp nhận kết quả chính xác tính bằng phần mềm MCOC**, không chấp nhận kết quả xấp xỉ. Vì vậy mọi phương án quyết định/giao nộp đều được chấm trực tiếp bằng **MCOC (exact)**. Tốc độ đạt được bằng cách **giảm số lần gọi MCOC** (cache + ngân sách + dẫn hướng) và **chạy song song**, **không** bằng cách thay MCOC bằng mô hình xấp xỉ. Xem [docs/BAO_CAO_THUAT_TOAN.md §4.0](docs/BAO_CAO_THUAT_TOAN.md).

## Tính năng chính

- Giao diện đồ họa tương tác (Tkinter) với:
  - kéo thả hoặc chọn file đầu vào
  - hiển thị cấu hình cọc tối ưu
  - xuất file kết quả và bản vẽ mô phỏng
- **Tối ưu đa mục tiêu NSGA-II + đánh giá MCOC chính xác** (đường mặc định): cực tiểu đồng thời *số cọc* và *mục tiêu phụ* (bệ gọn / Pmax), trả về **mặt Pareto**.
- Tự động sinh lưới cọc 2 kiểu:
  - `A` (trực giao)
  - `B` (so le / hoa mai)
- Kiểm tra các điều kiện chịu lực (số liệu lấy từ MCOC):
  - giới hạn nén `P_LIMIT`
  - giới hạn nhổ `P_TENSION`
  - kiểm tra momen `M_LIMIT` (nếu bật)

## Cài đặt

1. Cài Python 3.9+ hoặc 3.10/3.11.
2. Cài các thư viện cần thiết:

```bash
pip install numpy matplotlib tkinterdnd2
```

> Trên Windows, `tkinter` thường đã có sẵn cùng Python. Nếu chạy trên Linux, cần cài thêm gói hệ thống `python3-tk`.

## Chạy ứng dụng

Mở terminal tại thư mục dự án và chạy:

```bash
python main.py
```

## Đầu vào

Ứng dụng hỗ trợ:

- File CSV có định dạng:
  - dòng 1: tên trường (`L_X, L_Y, D_PILE, SAFE_D, P_LIMIT, P_TENSION`)
  - dòng 2: giá trị tương ứng
  - các dòng tiếp theo: tổ hợp tải `Hx, Hy, P, Mx, My, Mz`
- File TXT theo chuẩn MCOC / mô phỏng tải trọng

Sau khi load file, người dùng có thể sửa tham số cọc hoặc tổ hợp tải trong giao diện.

## ⚠️ Quy ước đơn vị (quan trọng)

Ứng dụng dùng **một hệ đơn vị thống nhất theo MCOC** — toàn bộ ở **Tấn (T)** và **T.m**:

| Đại lượng                                                | Đơn vị          | Ghi chú                                      |
| ------------------------------------------------------------ | ------------------ | --------------------------------------------- |
| Tải trọng:`N` (lực đứng), `Hx`, `Hy`            | **Tấn (T)** | Theo tổ hợp tải trọng (đúng quy ước MCOC) |
| Momen:`Mx`, `My`, `Mz`                                 | **T.m**      |                                               |
| Giới hạn sức nén `[Po]`, sức nhổ `[Ct]`            | **Tấn (T)** |                                               |
| Giới hạn uốn `[M]`                                      | **T.m**      | 0 = không kiểm tra                          |
| Lực cọc kết quả `Pmax`, `Pmin`                       | **Tấn (T)** | Lấy trực tiếp từ MCOC                      |

> Trước đây tài liệu ghi tải trọng là kN — **không đúng**. Bằng chứng: với phương án gốc, Pmax bệ cứng tính từ tải file ≈ 529.65 còn Pmax MCOC = 519.63 T (hệ số ≈ 0.98). Nếu tải ở kN thì hai số phải lệch ~10 lần; thực tế chúng cùng bậc ⇒ tải đang ở **Tấn**.

## Mô hình bệ cứng — chỉ là bộ DẪN HƯỚNG nội bộ (không phải kết quả)

Kết quả giao nộp luôn từ MCOC. Công thức **bệ cứng** (`core/rigid_cap.py`) chỉ dùng *nội bộ* để: (1) **xếp hạng/dẫn hướng** xem nên gửi ứng viên nào cho MCOC trước (giúp giảm số lần gọi MCOC); (2) tô **heatmap** tức thì trên mặt bằng. Nó **không bao giờ** là số liệu quyết định. Khi dùng làm dẫn hướng có hệ số `K = Pmax_MCOC_gốc / Pmax_bệ_cứng_gốc` (≈ 0.98 — hiệu chỉnh sai số mô hình ~2%, không phải quy đổi đơn vị). Có thể tắt hoàn toàn bộ dẫn hướng và chạy MCOC thuần + song song mà không đổi tính đúng đắn.

## Xuất kết quả

- Ứng dụng xuất file TXT kết quả theo định dạng tương tự MCOC
- Nếu chọn `Xuất tất cả`, ứng dụng còn sinh thêm các ảnh mô phỏng `*.png`

## Cấu trúc chính của dự án

- `main.py` - điểm khởi chạy GUI
- `ui/main_window.py` - giao diện người dùng và điều khiển chính
- `ui/plot_canvas.py` - vẽ mô phỏng bố trí cọc
- `core/constants.py` - hằng số & giá trị mặc định dùng chung
- `core/rigid_cap.py` - mô hình bệ cứng (nguồn duy nhất của công thức nội lực cọc)
- `core/generator.py` - sinh tọa độ lưới cọc
- `core/mechanics.py` - kiểm tra điều kiện chịu lực và khoảng cách
- `core/blackbox.py` - hộp đen đánh giá nội lực (mock bệ cứng / gọi MCOC thực)
- `core/optimizer.py` - quét lưới tìm cấu hình tối ưu (Grid Search)
- `core/refine_optimizer.py` - tinh chỉnh Pareto + gọi MCOC thực
- `core/nsga2_optimizer.py` - tối ưu đa mục tiêu NSGA-II
- `core/mcoc_runner.py` - gọi MCOC_Batch.exe qua subprocess
- `io_handlers/file_io.py` - đọc file đầu vào và xuất kết quả
- `io_handlers/mcoc_writer.py` - sinh file input MCOC từ template
- `io_handlers/export_utils.py` - xuất Excel/PDF/PNG

## Phương pháp tối ưu hóa (MCOC chính xác)

Mô tả tóm tắt — chi tiết xem `methodology.md` và `docs/BAO_CAO_THUAT_TOAN.md`:

1. Tham số hóa bố trí thành genome `(type, nx, ny, sx, sy)` — lưới đối xứng A/B.
2. **NSGA-II** tiến hóa quần thể phương án (đa mục tiêu: số cọc + bệ gọn/Pmax).
3. Mỗi phương án được **chấm bằng MCOC chính xác** (gọi `MCOC_Batch.exe`); ràng buộc R3–R6 và Pmax/Pmin/M đều từ MCOC.
4. Tốc độ: **cache theo lưới** (không gọi MCOC trùng) + **trần `max_evals`** + **dẫn hướng bằng predictor rẻ** + (khuyến nghị) **song song hóa** lời gọi MCOC.
5. Trả về **mặt Pareto**; kiến nghị phương án ít cọc nhất → bệ gọn/an toàn.

## Chế độ Hàng loạt (Batch Mode)

Tab **"2. Hàng loạt"** cho phép xử lý nhiều file cùng lúc, **dùng đúng luồng chính NSGA-II + MCOC chính xác** (giống Tab 1, không xấp xỉ):

- **Bắt buộc cấu hình MCOC Batch** (ở Tab 1) — thiếu thì từ chối chạy. Mỗi file đầu vào chính là template MCOC của nó.
- Thêm từng file hoặc cả thư mục (hoặc kéo–thả vào danh sách).
- Chọn thư mục xuất (để trống = xuất cùng thư mục file đầu vào).
- Tùy chọn xuất: báo cáo **PDF**, bảng **Excel**, mặt bằng **PNG**, và **gộp** tất cả PDF thành một file tổng hợp.
- Tùy chọn nâng cao: ghi đè thông số cọc (`d`, `Po`, `Ct`, `M`) từ Tab 1 lên tất cả file để so sánh cùng một giới hạn.
- Có thanh tiến trình, log màu và nút **Dừng**.

## Lưu ý

- Dữ liệu đầu vào và các file kết quả đã bị loại khỏi repo gốc để bảo mật.
- **Đường quyết định bắt buộc dùng MCOC** (cần cấu hình MCOC Batch + file input gốc); nếu thiếu, chương trình từ chối chạy thay vì rơi về xấp xỉ.
- Mô hình bệ cứng chỉ là **dẫn hướng nội bộ + heatmap**, không phải kết quả giao nộp.
- Kiểm tra `M_LIMIT` đã được tích hợp (đặt `> 0` để bật).
