# OptApp - Tối ưu hóa bố trí cọc móng cầu

Ứng dụng này hỗ trợ tối ưu hóa bố trí cọc móng cầu trên bệ móng dạng chữ nhật. Mục tiêu là tìm phương án bố trí có **số cọc ít nhất** mà vẫn đảm bảo các điều kiện chịu lực và thi công.

## Tính năng chính

- Giao diện đồ họa tương tác (Tkinter) với:
  - kéo thả hoặc chọn file đầu vào
  - hiển thị cấu hình cọc tối ưu
  - xuất file kết quả và bản vẽ mô phỏng
- Hỗ trợ cả chế độ xử lý hàng loạt và chế độ tương tác
- Tự động sinh lưới cọc 2 kiểu:
  - `A` (trực giao)
  - `B` (sò le)
- Kiểm tra các điều kiện chịu lực:
  - giới hạn nén `P_LIMIT`
  - giới hạn nhổ `P_TENSION`
  - kiểm tra momen `M_LIMIT` (nếu bật)
- Mô phỏng lực cọc bằng phương pháp bệ cứng + hiệu chỉnh nhanh

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

Ứng dụng dùng **hai hệ đơn vị khác nhau** cho đầu vào và đầu ra — cần nắm rõ để đọc kết quả đúng:

| Đại lượng | Đơn vị | Ghi chú |
|-----------|--------|---------|
| Tải trọng nhập vào: `N` (lực đứng), `Hx`, `Hy` | **kN** | Theo tổ hợp tải trọng người dùng nhập |
| Momen: `Mx`, `My`, `Mz` | **kNm** | |
| Giới hạn sức nén `[Po]`, sức nhổ `[Ct]` | **Tấn (T)** | Lấy từ chuẩn MCOC |
| Giới hạn uốn `[M]` | **T.m** | 0 = không kiểm tra |
| Lực cọc kết quả `Pmax`, `Pmin` hiển thị/xuất file | **Tấn (T)** | Đã hiệu chỉnh (xem dưới) |

## Hiệu chỉnh (Calibration)

Lực cọc tính nhanh bằng công thức **bệ cứng** cho ra đơn vị thô (theo `N`, tức kN). Để so sánh được với
giới hạn `[Po]` (đơn vị T) và để bám sát kết quả MCOC thực, ứng dụng nhân một **hệ số hiệu chỉnh**:

```
calib = Pmax_thực_MCOC (T) / Pmax_lý_thuyết_bệ_cứng (kN)
```

Hệ số này lấy từ phương án gốc trong file (`orig_pmax` đọc từ bảng tổng kết nội lực), rồi áp dụng cho mọi
phương án lưới. Nhờ vậy mọi `Pmax`/`Pmin` hiển thị trên biểu đồ, bảng Excel và báo cáo đều **đồng nhất ở đơn vị Tấn**.

## Xuất kết quả

- Ứng dụng xuất file TXT kết quả theo định dạng tương tự MCOC
- Nếu chọn `Xuất tất cả`, ứng dụng còn sinh thêm các ảnh mô phỏng `*.png`

## Cấu trúc chính của dự án

- `main.py` - điểm khởi chạy GUI
- `ui/main_window.py` - giao diện người dùng và điều khiển chính
- `ui/plot_canvas.py` - vẽ mô phỏng bố trí cọc
- `core/generator.py` - sinh tọa độ lưới cọc
- `core/mechanics.py` - kiểm tra điều kiện chịu lực và khoảng cách
- `core/optimizer.py` - chạy thuật toán tìm cấu hình tối ưu
- `io_handlers/file_io.py` - đọc file đầu vào và xuất kết quả

## Phương pháp tối ưu hóa

Mô tả tóm tắt:

1. Sinh các lưới cọc khả thi với hai kiểu bố trí (`A` và `B`).
2. Tính nhanh nội lực cọc bằng phương pháp bệ cứng.
3. Hiệu chỉnh mô phỏng dựa trên dữ liệu gốc để đạt độ chính xác cao.
4. Lọc bỏ ngay các phương án không thoả mãn ràng buộc và chọn phương án ít cọc nhất.

## Chế độ Hàng loạt (Batch Mode)

Tab **"2. Hàng loạt"** cho phép xử lý nhiều file cùng lúc:

- Thêm từng file hoặc cả thư mục (hoặc kéo–thả vào danh sách).
- Chọn thư mục xuất (để trống = xuất cùng thư mục file đầu vào).
- Tùy chọn xuất: báo cáo **PDF**, bảng **Excel**, mặt bằng **PNG**, và **gộp** tất cả PDF thành một file tổng hợp.
- Tùy chọn nâng cao: ghi đè thông số cọc (`d`, `Po`, `Ct`, `M`) từ Tab 1 lên tất cả file để so sánh cùng một giới hạn.
- Có thanh tiến trình, log màu và nút **Dừng**.

## Lưu ý

- Dữ liệu đầu vào và các file kết quả đã bị loại khỏi repo gốc để bảo mật.
- Mô hình bệ cứng + hiệu chỉnh là **ước lượng nhanh**; với bài toán quan trọng nên đối chiếu lại bằng phần mềm MCOC.
- Kiểm tra `M_LIMIT` đã được tích hợp (đặt `> 0` để bật).