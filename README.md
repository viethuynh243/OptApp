# OptApp - Tối ưu hóa bố trí cọc móng cầu

**Phiên bản: v1.10.0** (2026-06-28) · xem [CHANGELOG.md](CHANGELOG.md). Nguồn version: `core/version.py`.

Ứng dụng tối ưu hóa bố trí cọc móng cầu trên bệ chữ nhật. Mục tiêu: tìm phương án có **số cọc ít nhất** mà vẫn đảm bảo điều kiện chịu lực và thi công.

> **Nguyên tắc chính xác bắt buộc:** Bên thi công **chỉ chấp nhận kết quả tính bằng phần mềm MCOC**, không nhận kết quả xấp xỉ. Vì vậy mọi phương án quyết định/giao nộp đều được chấm trực tiếp bằng **MCOC (exact)**. Tốc độ đến từ việc **giảm số lần gọi MCOC** (cache + ngân sách + dẫn hướng) và **chạy song song**, **không** phải thay MCOC bằng mô hình xấp xỉ. Xem [docs/reference/BAO_CAO_THUAT_TOAN.md §4.0](docs/reference/BAO_CAO_THUAT_TOAN.md).

## Tài liệu

Bộ tài liệu đầy đủ tổ chức theo SDLC: **[docs/README.md](docs/README.md)** (mục lục OA-DOC).
Lối tắt: [Hướng dẫn sử dụng](docs/guides/HUONG_DAN_SU_DUNG.md) · [Kiến trúc](docs/reference/ARCHITECTURE.md) · [Quyết định thiết kế (ADR)](docs/reference/adr/) · [Backlog](docs/project/BACKLOG.md).

> ⚠️ **Định hướng (2026-06-29):** chương trình sẽ **chuyển cơ sở thiết kế sang TCVN 11823:2017** (thay TCVN 10304:2014) — chỉnh sửa lớn ở pha tiếp theo. Tài liệu hiện hành mô tả trạng thái code hiện tại (cơ sở TCVN 10304:2014). Xem [ADR-008](docs/reference/adr/ADR-008-co-so-thiet-ke-tcvn-11823.md).

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
- **Tối ưu mở rộng (gói `core/ext/`)**: quét nhiều **đường kính cọc** (patch tiết diện thật vào file MCOC, chấm chính xác từng d), chọn đường kính thắng theo **chi phí vật liệu** (số cọc × diện tích), và **tự thu bệ** theo TCVN 10304:2014.
- **Ràng buộc R1–R8**: ngoài R3–R6, luồng mở rộng bật **R7** (lực ngang Hmax ≤ [H]) và **R8** (tương tác P–M N/[Po] + M/[M] ≤ 1.0).

## Cài đặt

1. Cài Python 3.9+ (đã kiểm thử trên 3.13).
2. Cài các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

> Trên Windows, `tkinter` thường đã có sẵn cùng Python. Trên Linux cần cài gói hệ thống `python3-tk`. Để đóng gói/chạy test: `pip install -r requirements-dev.txt`.

## Chạy ứng dụng

Mở terminal tại thư mục dự án và chạy:

```bash
python main.py
```

## Hướng dẫn sử dụng (quy trình chuẩn)

> Vì đánh giá **bắt buộc bằng MCOC**, cần cấu hình MCOC trước khi chạy. Mở app, các ô "Thông số Bài toán" để **trống** — bạn tự nhập hoặc nạp từ file.

**Tab 1 — Tương tác:**
1. **Cấu hình MCOC (bắt buộc):** ở mục "Cấu hình MCOC", chọn đường dẫn `MCOC Batch` (hỗ trợ `.exe/.bat/.py/.lnk`).
2. **Mở file đầu vào MCOC gốc** (`.txt`, có tọa độ cọc gốc) bằng "Mở file đầu vào" — file này làm template. *(Không phải file `_result` hay CSV.)*
3. **Nhập/kiểm tra thông số:** Lx, Ly, d, [Po] (bắt buộc > 0); [Ct], [M] tùy chọn (0 = không kiểm).
4. **Nhập tổ hợp tải:** "Thêm tổ hợp" hoặc "Dán nhiều dòng (CSV)" (đơn vị Tấn / T.m).
5. **Chọn ưu tiên:** "Tiết kiệm (bệ gọn)" hoặc "An toàn (giảm Pmax)".
6. Nhấn **► CHẠY TỐI ƯU HÓA** → mỗi phương án được chấm bằng MCOC; kết quả gồm kiến nghị, bảng tọa độ, bảng các phương án ĐẠT (kèm `Pmin` nếu có [Ct], `Mmax` nếu có [M]) và biểu đồ tổ hợp bất lợi nhất.
7. **Xuất kết quả** → TXT + báo cáo kỹ thuật `.md` (+ PNG).

**Tab 2 — Hàng loạt:** dùng đúng luồng MCOC. Cấu hình MCOC ở Tab 1, thêm nhiều file đầu vào MCOC, chọn thư mục xuất, nhấn TÍNH TOÁN → xuất Excel/PDF/PNG cho từng file.

> Nếu thiếu MCOC hoặc thiếu thông số bắt buộc, chương trình **cảnh báo và không chạy** (không dùng kết quả xấp xỉ).

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

> Trước đây tài liệu ghi tải trọng là kN — **không đúng**. Bằng chứng: với phương án gốc, Pmax bệ cứng từ tải file ≈ 529.65 còn Pmax MCOC = 519.63 T (hệ số ≈ 0.98). Nếu tải ở kN thì hai số phải lệch ~10 lần; thực tế cùng bậc ⇒ tải đang ở **Tấn**.

## Mô hình bệ cứng — chỉ là bộ DẪN HƯỚNG nội bộ (không phải kết quả)

Kết quả giao nộp luôn từ MCOC. Công thức **bệ cứng** (`core/rigid_cap.py`) chỉ dùng *nội bộ* để: (1) **xếp hạng/dẫn hướng** ứng viên nào gửi MCOC trước (giảm số lần gọi MCOC); (2) tô **heatmap** tức thì trên mặt bằng. Nó **không bao giờ** là số liệu quyết định. Khi dẫn hướng dùng hệ số `K = Pmax_MCOC_gốc / Pmax_bệ_cứng_gốc` (≈ 0.98 — hiệu chỉnh sai số mô hình ~2%, không phải quy đổi đơn vị). Có thể tắt hẳn bộ dẫn hướng, chạy MCOC thuần + song song mà không đổi tính đúng đắn.

## Xuất kết quả

- Ứng dụng xuất file TXT kết quả theo định dạng tương tự MCOC
- Nếu chọn `Xuất tất cả`, ứng dụng còn sinh thêm các ảnh mô phỏng `*.png`

## Cấu trúc chính của dự án

- `main.py` - điểm khởi chạy GUI
- `ui/main_window.py` - VỎ điều phối (composition): giữ state chia sẻ, dựng khung 2 tab + menu, tạo & nối các component bên dưới (giữ delegator mỏng cho API ngoài)
- `ui/constants.py` - hằng số giao diện (geometry, preset NSGA-II)
- `ui/strings.py` - chuỗi/khóa UI dùng chung (nhãn phương án, khóa chế độ xem) — nguồn duy nhất để khớp chính xác giữa nơi đặt và nơi kiểm tra
- `ui/widgets/` - widget/tiện ích GUI dùng chung: `tooltip.py`, `widget_utils.py`
- `ui/controllers/` - logic theo trách nhiệm:
  - `params.py` - tham số bài toán + TCVN + nạp DEMO
  - `loads.py` - CRUD tổ hợp tải trọng
  - `file_ops.py` - nạp/xuất file & làm mới
  - `results.py` - render kết quả + KPI + combobox
  - `simulation.py` - vẽ mô phỏng + dữ liệu audit R1–R8
  - `optimization.py` - chạy NSGA-II / mở rộng / tinh chỉnh (thread nền)
- `ui/tabs/` - dựng giao diện từng tab: `interactive_tab.py` (Tab 1), `batch_tab.py` (Tab 2 + chạy hàng loạt)
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
- `core/cap_suggest.py` - đề xuất nới bệ tối thiểu khi bệ chật
- `core/ext/` - gói tối ưu mở rộng:
  - `pile_section.py` - bảng/đặc trưng đường kính cọc
  - `config_ext.py` - cấu hình R7/R8 + thu bệ
  - `blackbox_ext.py` - đánh giá có R7/R8
  - `nsga2_ext.py` - NSGA-II mở rộng
  - `cap_resize.py` - thu bệ theo TCVN 10304:2014
  - `orchestrator.py` - điều phối end-to-end
- `io_handlers/file_io.py` - đọc file đầu vào và xuất kết quả
- `io_handlers/mcoc_writer.py` - sinh file input MCOC từ template
- `io_handlers/mcoc_writer_ext.py` - patch tiết diện theo đường kính vào template MCOC
- `io_handlers/report_writer.py` - sinh báo cáo kỹ thuật MD/PDF
- `io_handlers/export_utils.py` - xuất Excel/PDF/PNG

## Phương pháp tối ưu hóa (MCOC chính xác)

Mô tả tóm tắt — chi tiết xem [docs/reference/METHODOLOGY.md](docs/reference/METHODOLOGY.md) và [docs/reference/BAO_CAO_THUAT_TOAN.md](docs/reference/BAO_CAO_THUAT_TOAN.md):

1. Tham số hóa bố trí thành genome `(type, nx, ny, sx, sy)` — lưới đối xứng A/B.
2. **NSGA-II** tiến hóa quần thể phương án (đa mục tiêu: số cọc + bệ gọn/Pmax).
3. Mỗi phương án được **chấm bằng MCOC chính xác** (gọi `MCOC_Batch.exe`); ràng buộc R1–R8 (R3–R6 ở luồng cơ bản, thêm R7/R8 ở luồng mở rộng) và Pmax/Pmin/M đều từ MCOC.
4. Tốc độ: **cache theo lưới** (không gọi MCOC trùng) + **trần `max_evals`** + **dẫn hướng bằng predictor rẻ** + (khuyến nghị) **song song hóa** lời gọi MCOC.
5. Trả về **mặt Pareto**; kiến nghị phương án ít cọc nhất → bệ gọn/an toàn.

## Chế độ Hàng loạt (Batch Mode)

Tab **"2. Hàng loạt"** xử lý nhiều file cùng lúc, **dùng đúng luồng chính NSGA-II + MCOC chính xác** (giống Tab 1, không xấp xỉ):

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
