# Changelog — OptApp

Tất cả thay đổi đáng kể của ứng dụng. Phiên bản theo [SemVer](https://semver.org/lang/vi/).
Nguồn version duy nhất: `core/version.py`.

## [1.3.0] — 2026-06-18

### Bám sát TCVN 10304:2014 (Móng cọc – Tiêu chuẩn thiết kế)
- **Sức chịu tải thiết kế theo Điều 7.1.11.** Thêm `core/tcvn.py` tính `Rc,d = (γ0/γn)·(Rc,k/γk)`. Khi khai báo `R_C_K` (+ `GAMMA_0`, `GAMMA_N`/`IMPORTANCE_LEVEL`, `GAMMA_K`), `[Po]`/`[Ct]` được tự chuẩn hóa thành `Rc,d`/`Rt,d` (idempotent) qua `apply_design_capacities`, cắm tại `run_nsga2`, `run_optimization`, `run_pareto_refinement` và UI. Không khai báo → giữ `[Po]` nhập tay và coi đó đã là Rc,d (nguồn = 'input').
- **Cận trên 6d hạ cấp thành CẢNH BÁO MỀM.** 6d không phải giới hạn TCVN (chỉ 3d cọc ma sát là cận dưới bắt buộc). Thêm cờ `ENFORCE_SPACING_MAX=False`: 6d vẫn là cận tìm kiếm nhưng **không loại** phương án vượt 6d (`mechanics`, `nsga2` không phạt; báo cáo ghi "CANH BAO").
- **Kiểm móng khối quy ước & lún (Điều 7.4).** `core/tcvn.py` thêm `equivalent_block` (mở rộng góc φ_tb/4) và `settlement` (cộng lún từng lớp, Phụ lục C, β=0,8). Báo cáo có mục **6b**; thiếu số liệu địa chất → ghi rõ "CHƯA KIỂM".
- **Báo cáo nêu rõ phạm vi & nghĩa vụ TCVN.** Hiển thị nguồn `Rc,d` + bảng γ; phụ lục liệt kê các kiểm toán phải làm riêng: sức chịu tải theo vật liệu (7.1.11+7.2), nhóm cọc/lún (7.4), tải ngang (Phụ lục A); nhắc tải N, M phải là nội lực tính toán.
- Thêm `tests/test_tcvn.py`.

## [1.2.0] — 2026-06-16

### Giao diện (UI/UX)
- Panel phải thêm **chế độ hiển thị "Kiểm tra điều kiện R1–R6"** (nút radio đổi qua lại với "Mặt bằng"):
  - **Bảng kiểm tra điều kiện R1–R6 theo từng tổ hợp tải**: cột R1 nén `N_max/[Po]`, R2 nhổ `|N_min|/[Ct]`; tô màu **nhị phân ĐẠT (xanh) / KHÔNG ĐẠT (đỏ)**; **tổ hợp chi phối viền đỏ**; có chú thích màu (legend).
  - Tổng hợp hình học **R3/R4** và uốn **R5/R6** ở chân bảng.
- Thêm **dải KPI** luôn hiển thị: `Số cọc | Hệ số sử dụng lớn nhất (THx chi phối) | Trạng thái` (đổi màu theo ĐẠT/KHÔNG ĐẠT).
- Thêm **ghi chú phạm vi & giới hạn mô hình** dưới khung vẽ (chuẩn tư vấn thiết kế).

### Báo cáo / Xuất
- **Xuất báo cáo kỹ thuật dạng PDF** (`*_baocao_kythuat.pdf`) song song bản `.md`: cùng nội dung (hệ số sử dụng, tổ hợp chi phối, bảng R1–R6, phụ lục), render bằng `reportlab` với **font có dấu tiếng Việt** (DejaVu). Nguồn duy nhất `build_report_text` → PDF và `.md` luôn khớp.

## [1.1.0] — 2026-06-16

### Thay đổi quan trọng (Breaking / hành vi)
- **MCOC là đường tính toán BẮT BUỘC, cấm xấp xỉ.** Mọi phương án quyết định/giao nộp chấm trực tiếp bằng `MCOC_Batch.exe`. Thiếu cấu hình MCOC → chương trình **từ chối chạy** (không rơi về bệ cứng).
- **Tab "Hàng loạt (Batch)" nay theo đúng luồng chính** (NSGA-II + MCOC exact) như Tab 1; bắt buộc cấu hình MCOC. (Trước đây Batch chạy mock bệ cứng → đã bỏ.)
- `optimizer.run_optimization` (quét lưới bệ cứng) **chỉ còn dùng cho `run_demo.py`**, không nằm trên luồng quyết định.

### Tính năng
- Tối ưu đa mục tiêu **NSGA-II + MCOC** mặc định; trả về **mặt Pareto** (số cọc × bệ gọn/Pmax).
- Bảng kết quả thêm **cột `Pmin`** (khi có `[Ct]`) và **cột `Mmax`** (khi có `[M]`) + chú thích giới hạn, để dễ đối chiếu sức nhổ/uốn.

### Giao diện (UI/UX)
- "Thông số Bài toán" để **trống khi mở** (không điền sẵn giá trị); thêm **validation** yêu cầu nhập đủ Lx, Ly, d, [Po] (>0) trước khi chạy.
- Nạp file điền lại thông số dạng gọn (`6` thay vì `6.0`); điền cả `[M]`.

### Báo cáo / Xuất
- **Ẩn R7 (lực ngang) & R8 (P–M)** khỏi báo cáo khi đang tắt: bỏ cột `H_max`, dòng `[H]`, dòng R7/R8, và ghi chú lực ngang ở phụ lục.
- Sửa **đơn vị**: nhãn báo cáo/Excel `kN` → **`T`/`T.m`** (đồng bộ quy ước Tấn theo MCOC).
- Báo cáo ghi rõ "Nội lực tính bằng MCOC (chính xác)" thay vì "bệ cứng + K".

### Sửa lỗi / Độ chính xác
- **R3 layout B trong NSGA-II:** bộ lọc khả thi trước đây chỉ ràng `min_spacing` (khoảng cách tim-tim nhỏ nhất) nên **bỏ sót đường chéo** `√((sx/2)²+sy²)` có thể vượt 6d (tới ~6.7d) — khiến một số phương án layout B (kể cả phương án _khuyến nghị_) được gắn nhãn ĐẠT dù vi phạm R3. Nay kiểm khoảng cách **theo cấu trúc lưới, đồng nhất với `check_layout`** (`core/nsga2_optimizer.py`). Phát hiện qua `tests/sweep_robustness.py` (286 bất nhất → 0); test neo không hồi quy.
- **Công thức bệ cứng** in trong báo cáo/`run_validate`/test stub nay hiển thị **dạng đầy đủ** (dời mômen về trọng tâm `Mx − N·cy`) — khớp đúng code (`rigid_cap.pile_forces`).
- **Demo Kiểu B** không còn bị loại oan: giảm `sy` để kéo đường chéo về `[3d, 6d]`.
- **Cảnh báo R6 ở chế độ mock** (mômen đầu cọc là ước lượng `~1/n`) trong `run_nsga2` và `run_optimization`/`run_demo`.

### Kiểm chứng
- **Chuyển TOÀN BỘ §5 sang dữ liệu MCOC thật** trên 5 hồ sơ input (`T1, T7, T8, T11, T14` trong `mcoc_input_sample/`, bệ 6×9,6 → 34×28): thêm `tests/validate_mcoc.py` sinh các hình **convergence / pareto / pmax_ratio / layouts** từ MCOC thật (bỏ hẳn 4 hồ sơ tổng hợp C1–C4 + mô hình mock).
  - §5.1 Tối ưu: vét cạn+MCOC đạt n* trên cả 5; NSGA-II+MCOC đạt 4/5, T11 dừng +1 cọc (nghiệm tối ưu là cấu hình góc 5×3 bước cực đại — giới hạn metaheuristic, đã nêu trung thực).
  - §5.2 Khả thi: 64 phương án ĐẠT, max Pmax(MCOC)/[Po] = 0,985. §5.3 Pareto không bị trội. §5.4 Ổn định 5 seed. §5.7 Cân bằng tĩnh trên bố trí thật (sai số tương đối ~1e−15).
  - §5.8 (trước là §5.9): đổi ngưỡng R5/R5b/R6 trên cùng 5 hồ sơ, n* dao động 3↔30, đơn điệu đúng; dải ngưỡng suy từ nội lực thật (file input mặc định [Po]=500/[Ct]=[M]=0). Pool MCOC + memo nội lực được cache để chạy lại nhanh.
- **Bỏ** chiều "Bền vững 220 kịch bản tổng hợp" (`sweep_robustness.py`, `robustness.png`) — tính bền vững nay thể hiện trực tiếp qua 5 hồ sơ thật khác nhau xuyên suốt §5. Bỏ `make_validation_figures.py`; **parity (§5.6) nay đa hồ sơ MCOC thật** (5 hồ sơ, K≈0,944–0,998) trong `validate_mcoc.py`.
- Bổ sung chú thích ngữ nghĩa cho hình hội tụ (mỗi đường = 1 seed); pmax_ratio tô theo hồ sơ; ghi rõ R5b chỉ phát sinh ở T7/T8 (tải lệch tâm; T9–T14 toàn nén).
- Ghi nhận **lỗi đã sửa** (bộ lọc R3 Kiểu B bỏ sót đường chéo) tại §5.2; `tests/_scenarios.py` là nguồn dữ liệu kịch bản dùng chung.
- Hợp nhất kiểm chứng vào luồng thuật toán: `docs/BAO_CAO_THUAT_TOAN.md` §5 (tám phép kiểm, mỗi bước thuật toán kèm khối kiểm chứng tách bạch).

### Tài liệu
- Chuẩn hóa thuật ngữ báo cáo theo **TCVN 10304:2014** và văn phong bài báo tham khảo (`words_dict/`): thuật ngữ Pareto "thống trị" → "**trội/bị trội**"; neo hàm mục tiêu (§8.7), ràng buộc R3 (§8.13), R5/R5b (§7.1.11), công thức đài cứng (§7.1.13 công thức (4)) vào tiêu chuẩn; thêm ánh xạ ký hiệu `[Po]↔Rc,d`, `[Ct]↔Rt,d`, `Pmax/Pmin↔Nc,d/Nt,d`.
- Cập nhật `methodology.md`, `short_methodology.md`, `README.md`, `docs/BAO_CAO_THUAT_TOAN.md` theo định hướng MCOC-only + chiến lược "chính xác nhưng nhanh".
- Thêm **vault Obsidian** quản lý dự án: `docs/vault/` (ADR, concept, engine, module, issue) + hướng dẫn nối AI.

## [1.0.0]
- Bản phát hành đầu (installer `OptApp_Setup_1.0.0`).
