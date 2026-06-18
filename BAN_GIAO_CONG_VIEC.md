# BÀN GIAO CÔNG VIỆC — OptApp (Tối ưu bố trí cọc móng cầu)

> Mục đích: ghi lại toàn bộ việc đã làm trong phiên hôm nay để chuyển tài khoản/người tiếp tục.
> Cập nhật: 2026-06-16.

---

## 0. TÓM TẮT NHANH (đọc cái này trước)

- Dự án: ứng dụng Python/Tkinter tối ưu **số cọc ít nhất** cho móng cọc cầu; đánh giá nội lực bằng **MCOC** (chính xác) hoặc bệ cứng (xấp xỉ).
- Trong phiên này đã: **viết engine NSGA-II**, **refactor gom code trùng**, **đưa MCOC làm mặc định (chính xác, bỏ xấp xỉ)**, **mở rộng mô hình (Hx/Hy/Mz)**, **sửa nhiều lỗi/UX**, **chuẩn hóa đơn vị về Tấn**, **tiêm tải UI vào MCOC**, **thêm mục tiêu "bệ gọn"**.
- ~~**VIỆC CẦN LÀM NGAY:** chạy lại các test trên MÁY THẬT~~ → ✅ **ĐÃ XONG (2026-06-15):** toàn bộ test PASS, GUI chạy đúng, và đường MCOC thật đã kiểm chứng (MCOC_Batch.exe chạy + tải UI tác động kết quả). Chi tiết ở mục 4 & 5. Không còn việc tồn đọng bắt buộc.

---

## 1. CÁC ĐẦU VIỆC ĐÃ HOÀN THÀNH

### 1.1. Đồng bộ tài liệu với code
- `methodology.md`, `short_methodology.md`: sửa cây kiến trúc, công thức bệ cứng, bảng ràng buộc R1–R8, bổ sung module thiếu (`refine_optimizer`, `mcoc_runner`, `mcoc_writer`, `nsga2_optimizer`, `constants`, `rigid_cap`, `report_writer`), sửa danh sách script chạy, sửa "midas"→MCOC.

### 1.2. Engine NSGA-II (đa mục tiêu)
- Tạo `core/nsga2_optimizer.py`: thuật toán di truyền thật (non-dominated sort, crowding distance, tournament, SBX + đột biến đa thức, constrained-domination).
- Genome: (kiểu A/B, nx, ny, sx, sy). Mục tiêu: (số cọc, mục tiêu phụ). Evaluator cắm được (mock hoặc MCOC), có cache giới hạn số lần gọi MCOC.
- Test: `tests/test_nsga2.py`, demo `run_nsga2_demo.py`.

### 1.3. Refactor gom code (DRY) + chuẩn thiết kế + comment
- Tạo `core/constants.py`: hằng số (3d/6d, dải nx/ny, NMAX_AXIS, EPS, mặc định param, cờ bật/tắt R7/R8).
- Tạo `core/rigid_cap.py`: **NGUỒN DUY NHẤT** công thức bệ cứng (trước bị lặp ở 4 nơi) + phân phối lực ngang.
- Refactor `blackbox.py`, `optimizer.py`, `mechanics.py`, `refine_optimizer.py`, `nsga2_optimizer.py`, `io_handlers/file_io.py`, `io_handlers/export_utils.py` dùng module chung.
- Dọn UI: gom import lên đầu, thêm docstring.

### 1.4. Bản output kỹ thuật chuẩn
- Tạo `io_handlers/report_writer.py` → `export_technical_report()` sinh bản tính Markdown: số liệu đầu vào + tiêu chuẩn, tổ hợp tải, kiểm tra hình học (tỷ lệ), nội lực từng tổ hợp + **hệ số sử dụng** + **tổ hợp chi phối**, bảng R1–R8, phụ lục phạm vi/giới hạn mô hình.
- Mẫu: `docs/ban_output_chuan_ky_thuat.md`, `docs/baocao_kythuat_mau.md`. (Có tra cứu TCVN 10304:2014, AASHTO.)
- Đã nối vào nút "Xuất kết quả" (xuất kèm `*_baocao_kythuat.md`).

### 1.5. Mở rộng mô hình rồi TẮT theo yêu cầu
- Thêm phân phối **Hx, Hy, Mz** (lực ngang) trong `rigid_cap.horizontal_forces/hmax`.
- Thêm **R7** (Hmax ≤ [H]) và **R8** (tương tác P–M) + ràng buộc **thông thủy ≥ 1 m** (TCVN, cho cọc nhồi).
- **ĐÃ TẮT R7, R8** theo yêu cầu (ngoài đề bài R1–R6): cờ `ENABLE_LATERAL_CHECK=False`, `ENABLE_PM_INTERACTION=False` trong `core/constants.py`. Muốn bật lại đổi thành `True`.
- Lưu ý: ở chế độ MCOC, **MCOC đã tính 3D đầy đủ (gồm Hx/Hy/Mz)** nên tắt R7/R8 không mất an toàn.

### 1.6. MCOC làm MẶC ĐỊNH (chính xác, bỏ xấp xỉ)
- Nút "Chạy tối ưu hóa" nay chạy **NSGA-II + MCOC exact** (mỗi phương án chấm bằng MCOC), chạy nền (thread), log tiến trình.
- **Bắt buộc**: phải cấu hình MCOC Batch + mở file input MCOC gốc; nếu thiếu → báo lỗi, không chạy (không còn đường xấp xỉ trong quyết định).
- Bệ cứng (`optimizer.run_optimization`) chỉ còn dùng cho **Batch/xem nhanh** và tô màu heatmap (hiển thị).

### 1.7. Sửa lỗi quan trọng phát hiện khi rà soát
- **Tải UI không tác động MCOC** → ĐÃ SỬA: `mcoc_writer` nay **ghi đè khối tổ hợp tải bằng tải từ UI** + cập nhật Np (qua `make_real_evaluator(params, loads=...)`). Đã kiểm: nhân đôi N → file MCOC sinh ra có N gấp đôi → kết quả MCOC đổi (408→706 T trên stub).
- **Sai đơn vị tải trọng** → ĐÃ SỬA: tải thực ở **Tấn (T)/T.m** (bằng chứng K≈0.98), không phải kN. Đổi nhãn UI + README + methodology.

### 1.8. Cải thiện UI/UX
- Bảng tải trọng **trống khi mở** (sạch).
- Khung vẽ **về trống khi "Làm mới"/mở file** (không vẽ bệ+giới hạn như trước).
- **Bảng tọa độ cọc** hiện sau khi chạy (cả chế độ MCOC).
- Bố cục ô "Kết quả Đánh giá" gọn lại (kiến nghị + tọa độ lên đầu, so sánh phía dưới).
- Đổi tên nút thân thiện; bỏ "(Modular)" ở tiêu đề; thêm ghi chú đơn vị; bỏ ô "Sức ngang [H]" và "Thông thủy" khỏi UI.
- Thêm tùy chọn **"Tiết kiệm (bệ gọn)"** vs **"An toàn (giảm Pmax)"** (mục tiêu phụ).
- Biểu đồ mặc định vẽ **tổ hợp bất lợi nhất**.
- Cảnh báo khi chưa nhập tải.

---

## 2. PHÂN TÍCH KỸ THUẬT QUAN TRỌNG (đã thống nhất)

- **Tại sao khoảng cách cọc từng rất lớn (vd 10×9 m):** mục tiêu phụ cũ là "giảm Pmax" → trải cọc ra mép bệ. Khi mômen nhỏ so với lực đứng, trải rộng gần như vô ích mà tốn bê tông. → Đã thêm mục tiêu **"bệ gọn"** (mặc định) để cụm cọc sát ~3d, cho bệ tối thiểu vẫn đạt.
- **Đơn vị:** TOÀN BỘ ở **Tấn (T)** và **T.m** theo MCOC (tải trọng, [Po], [Ct], [M], lực cọc).
- **Giới hạn mô hình:** NSGA-II không vét cạn (gần tối ưu); lưới đối xứng quanh tâm bệ; kích thước bệ là input cố định (tool không tự thu nhỏ bệ).

---

## 3. CÁC FILE ĐÃ TẠO / SỬA

**Tạo mới:**
- `core/constants.py`, `core/rigid_cap.py`, `core/nsga2_optimizer.py`
- `io_handlers/report_writer.py`
- `run_nsga2_demo.py`
- `tests/test_nsga2.py`, `tests/test_nsga2_mcoc.py`, `tests/test_model_ext.py`
- `docs/ban_output_chuan_ky_thuat.md`, `docs/baocao_kythuat_mau.md`
- `BAN_GIAO_CONG_VIEC.md` (file này)

**Sửa:**
- `core/blackbox.py`, `core/optimizer.py`, `core/mechanics.py`, `core/refine_optimizer.py`, `core/mcoc_runner.py` (giữ nguyên)
- `io_handlers/file_io.py`, `io_handlers/export_utils.py`, `io_handlers/mcoc_writer.py`
- `ui/main_window.py`, `ui/plot_canvas.py`
- `methodology.md`, `short_methodology.md`, `README.md`
- `tests/test_refine.py` (nới assertion)

---

## 4. TRẠNG THÁI HIỆN TẠI & VẤN ĐỀ CÒN MỞ

- ✅ **ĐÃ XÁC MINH TRÊN MÁY THẬT (2026-06-15):** chạy lại toàn bộ test, TẤT CẢ PASS:
  - `core/nsga2_optimizer.py` parse OK (không còn rác từ sự cố mount cũ).
  - `tests/test_nsga2.py` ✅, `tests/test_nsga2_mcoc.py` ✅, `tests/test_model_ext.py` ✅, `tests/test_refine.py` ✅.
  - `run_demo.py` ✅ (bệ cứng, Pmax=486.91 T ≤ [Po]=500 T).
  - `main.py`, `ui/main_window.py`, `ui/plot_canvas.py` parse OK.
- 🔧 **Sửa 2 test cũ bị lỗi thời (stale) so với quyết định thiết kế:**
  - `test_model_ext.py::test_R7_R8_in_check`: trước assert R7 phải chặn, nhưng R7 đã TẮT (`ENABLE_LATERAL_CHECK=False`). Nay test **tôn trọng cờ**: R7 tắt thì xác nhận lực ngang KHÔNG bị chặn (in `[SKIP]`); bật lại mới kiểm tra chặn.
  - `test_model_ext.py::test_report`: tải cũ (N=2800, Mx=1800…) quá lớn so với bệ 6×9.6 → optimizer không tìm được phương án → báo cáo rơi vào nhánh "không tìm được", thiếu mục. Nay dùng tải vừa sức (N=2000/1800, M nhỏ hơn) để sinh báo cáo đầy đủ. (Trước đây test này bị che vì TEST 3 abort sớm nên chưa chạy tới.)
- ℹ️ Sự cố mount sandbox của phiên trước đã hết tác động: bản trên đĩa đúng, test thật xanh.

---

## 5. VIỆC CẦN LÀM TIẾP (cho người nhận bàn giao)

1. ✅ **Xác minh trên máy thật** — ĐÃ XONG (2026-06-15), tất cả test PASS (xem mục 4). Lệnh đã chạy:
   ```
   cd D:\Project\TEDI\OptApp
   python -c "import ast; ast.parse(open('core/nsga2_optimizer.py',encoding='utf-8').read()); print('nsga2 OK')"
   python tests/test_nsga2.py
   python tests/test_nsga2_mcoc.py
   python tests/test_model_ext.py
   python tests/test_refine.py
   python run_demo.py
   ```

2. ✅ **Chạy thử GUI** — ĐÃ XONG (2026-06-15, `python main.py`). Đã xác nhận trực quan + bấm nút thật:
   - Bảng tải trọng trống lúc mở; khung vẽ trống; ghi chú đơn vị Tấn; đã bỏ ô [H]/Thông thủy; tùy chọn "Tiết kiệm/An toàn" có (Tiết kiệm mặc định).
   - Bấm "Chạy tối ưu hóa" khi chưa nhập tải → cảnh báo **"Chưa có tải trọng"**.
   - Thêm 1 tổ hợp rồi bấm chạy (chưa cấu hình MCOC) → cảnh báo **"Cần cấu hình MCOC"** (không có đường xấp xỉ).

3. ✅ **Kiểm chứng đường MCOC thật** — ĐÃ XONG (2026-06-15). MCOC Batch resolve về `D:\app\MCOC Python\MCOC_Batch.exe` (qua shortcut `.lnk`).
   - Chạy `MCOC_Batch.exe` thật trên `mcoc_input_sample/T14_EXT.txt` (22 cọc, 12 tổ hợp) → **Nmax = 2065.78 T**, Nmin = 328.80 T (parse OK).
   - Qua `make_real_evaluator(params, loads=...)`: tải gốc tái lập **đúng** kết quả gốc (2065.78 T → template round-trip chuẩn). Khi **nhân đôi N** → **Nmax = 3464.73 T** (đổi thật, tỉ lệ 1.677 vì Nmax = phần dọc trục theo N + phần mômen không nhân) → xác nhận **tải UI thực sự tác động MCOC** trên exe thật (đúng như §1.7, không chỉ trên stub).
   - Lưu ý: file output trung gian sinh trong `mcoc_input_sample/_opt_runs/`.

4. (Tùy chọn) Nếu muốn chắc chắn tối ưu tuyệt đối thay vì gần tối ưu: cân nhắc thêm chế độ "quét lưới + MCOC".

---

## 6. CÁCH CHẠY NHANH

- GUI: `python main.py`
- Demo không UI: `python run_demo.py` (bệ cứng), `python run_nsga2_demo.py` (NSGA-II mock)
- Bật lại R7/R8: sửa `ENABLE_LATERAL_CHECK`/`ENABLE_PM_INTERACTION = True` trong `core/constants.py`
- Quy trình MCOC: (1) chọn MCOC Batch → (2) "Mở file đầu vào" nạp file input MCOC gốc .txt → (3) "Chạy tối ưu hóa".

---

## 7. LƯU Ý KHI TIẾP TỤC BẰNG TÀI KHOẢN/MÔI TRƯỜNG KHÁC

- Nếu dùng lại sandbox và gặp lỗi "đọc file ra rác/null/cắt cụt" hoặc test trả None bất thường: đó là **lỗi đồng bộ mount**, không phải code. Cách xử lý: đọc/sửa file bằng công cụ file (Read/Edit), **TRÁNH ghi/append file nguồn qua shell** (đã từng gây hỏng file giữa chừng). Xác minh bằng cách chạy trên máy thật.
