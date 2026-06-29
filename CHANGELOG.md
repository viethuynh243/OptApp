# Changelog — OptApp

Tất cả thay đổi đáng kể của ứng dụng. Phiên bản theo [SemVer](https://semver.org/lang/vi/).
Nguồn version duy nhất: `core/version.py`.

## [Chưa phát hành]

### Khung cơ sở thiết kế TCVN 11823:2017 (LRFD) — chuyển khỏi TCVN 10304:2014
> Định hướng bắt buộc của chủ dự án ([ADR-008](docs/reference/adr/ADR-008-co-so-thiet-ke-tcvn-11823.md)).
> Đây là **chỉnh sửa lớn**, làm theo pha. Trị số γ/φ hiện là **tham khảo AASHTO — cần
> kỹ sư nghiệm thu** với TCVN 11823-3/-10. Chi tiết: [docs/project/MIGRATION_TCVN11823.md](docs/project/MIGRATION_TCVN11823.md).
- **`core/lrfd.py`** (mới): nguồn duy nhất LRFD — hệ số tải γ (Cường độ I–V / Sử dụng /
  Đặc biệt), hệ số sức kháng φ cọc (đóng/khoan, nén/kéo, theo phương pháp; móng 1 cọc
  giảm 20%), `φ·Rn`, tải có hệ số `Σγ·Q`, `apply_design_basis`.
- **Cờ `DESIGN_BASIS`** (`core/constants.py`, mặc định `'TCVN11823'`): điều phối tại
  `run_nsga2`/`run_optimization`/`run_pareto_refinement`/`report_writer`/UI. Tiêu chí
  kiểm đổi từ `N ≤ Rc,d` (allowable) sang `Σγ·Q ≤ φ·Rn` (LRFD). MCOC vẫn là oracle.
- **Không phá vỡ:** chưa khai báo tham số LRFD → hành xử y hệt đường cũ (γ=1, [Po] nhập);
  toàn bộ pytest cũ vẫn xanh. Cấu hình qua cột file input (chưa cần GUI).
- **Báo cáo** thêm "Mục 0 — Cơ sở thiết kế" (basis, φ/γ, trạng thái, banner nghiệm thu).
- **Tài liệu** `docs/` tái cấu trúc theo SDLC (guides/reference/project + adr); gỡ
  plans/mcoc_input_sample/words_dict/vault khỏi git. Test: `tests/test_lrfd.py`.

## [1.10.0] — 2026-06-28

### Bám sát TCVN cho địa kỹ thuật & thiết kế đài (Plan 024 — CỐ Ý đổi kết quả tính)
> Sau rà soát `docs/AUDIT_CONG_THUC_TCVN.md`, khắc phục 6 mục theo nguyên tắc "có
> trong TCVN → theo đúng TCVN; không có → giữ công thức audit, ghi rõ nguồn". Đối
> chiếu nguồn chính thức + web để đảm bảo trị số (lưu ý file TCVN convert có lỗi OCR).
- **Lún móng cọc** theo **TCVN 10304:2014 Đ.7.4.4**: `S = Se + S_khối`, trong đó Se là
  biến dạng đàn hồi thân cọc (CT 21, β=0,5) và S_khối tính như móng nông trên nền thiên
  nhiên theo **TCVN 9362:2012** — cộng lún từng lớp (β=0,8), **ứng suất tại tâm theo
  Boussinesq** (thay xấp xỉ 2:1), vùng nén tới σz≤0,2σ'vz. (`core/tcvn.py`)
- **Móng khối quy ước**: thêm chặn **a≤2d** khi nền dưới mũi là **đất dính yếu IL>0,6**
  (Đ.7.4.4) — bật bằng checkbox mới ở panel Trụ địa chất & lún. Mặc định TẮT.
- **γk theo số cọc** (`resolve_gamma_k`, Đ.7.1.11): 1,40/1,55/1,65/1,75 (≥21 / 11–20 /
  6–10 / 1–5 cọc; cột thử tải tĩnh 1,25/1,40/1,50/1,60); ô nhập tay γk vẫn ưu tiên.
- **Cắt một phương** (`cap_design`, TCVN 5574 Đ.8.1.3): dùng đầy đủ
  **Qb=1,5·Rbt·b·h0²/C** (kẹp [0,5;2,5]·Rbt·b·h0) + giới hạn nén dải **0,3·Rb·b·h0**;
  tiết diện nguy hiểm tại mép cột.
- **ξ_R**: xác nhận khớp **CT(31) TCVN 5574** (0,8/(1+εs,el/εb2), εb2=0,0035) — thêm trích
  dẫn, KHÔNG đổi số. **STM** giữ công thức nhưng ghi rõ nguồn **ACI/AASHTO** (TCVN không định lượng).
- Thêm unit test hand-calc: γk, chặn 2d, lún Se+Boussinesq, cắt 1 phương (gần/xa) →
  **pytest 58 passed**. Báo cáo kỹ thuật nay tách Se/S_khối + ghi rõ phương pháp.
- **Kiểm cọc chịu ngang theo phương pháp "m"** (TCVN 10304:2014 **Phụ lục A**, k=m·z·d):
  báo cáo thêm **Mục 6c** (chuyển vị đầu cọc, M_max thân cọc, β) qua `core/ssi_engine`
  cho tổ hợp ngang bất lợi — bổ trợ R7 (sàng lọc Hmax≤[H]).
- **Nguồn tham khảo** gom tại `docs/THAM_KHAO_TCVN.md` (bản trích trong kho + nguồn web
  đối chiếu) để trích dẫn & kiểm chứng.
- *Chưa làm (cần bản chuẩn searchable):* lún nhóm cọc theo **hệ số tương hỗ Đ.7.4.3**
  (công thức trong file convert bị lỗi OCR; phương pháp móng khối Đ.7.4.4 đã cài là lựa
  chọn hợp lệ theo Đ.7.4.1). Chi tiết: `plans/024-tcvn-compliance-fixes.md`.

## [1.9.1] — 2026-06-28

### Tái cấu trúc giao diện theo composition (KHÔNG đổi hành vi)
- **Tách `ui/main_window.py`** từ **3247 → 515 dòng** (vỏ điều phối). Logic chuyển vào các component nhận tham chiếu `app` (shared context):
  - `ui/controllers/`: `params` (tham số+TCVN+demo), `loads` (CRUD tải), `file_ops` (nạp/xuất/làm mới), `results` (render kết quả+KPI+combobox), `simulation` (vẽ mô phỏng+audit R1–R8), `optimization` (chạy NSGA-II/mở rộng/tinh chỉnh, thread).
  - `ui/tabs/`: `interactive_tab` (dựng Tab 1), `batch_tab` (dựng Tab 2 + chạy hàng loạt).
  - `ui/widgets/`: `tooltip`, `widget_utils` (set_state_recursive, safe_float, to_safe_filename); `ui/constants.py` (geometry + preset NSGA-II); `ui/strings.py` (nhãn phương án + khóa chế độ xem — nguồn duy nhất, khớp chính xác giữa nơi đặt ↔ nơi kiểm).
- MainWindow giữ **delegator mỏng** cho các method test/harness/UI gọi → **API ngoài bất biến**.
- **Hạ tầng**: thêm `__init__.py` cho `core/` `ui/` `io_handlers/` (package tường minh); `.gitignore` thêm `*.log`, golden regression, `tests/_work/`.
- **Lưới an toàn mới**: `tests/_ui_regression.py` — dựng MainWindow thật, chạy luồng thường + mở rộng + làm mới (có seed, tự chứa), chụp snapshot hành vi so golden.
- **Kiểm sâu + sửa 3 lỗi import** (phát hiện khi rà nhánh chưa chạy, ĐÃ sửa): `ui/tabs/batch_tab.py` thiếu `re`/`subprocess`/`numpy` → trước đó **kéo-thả file vào Tab Hàng loạt**, **mở thư mục kết quả**, và **chạy hàng loạt** sẽ lỗi. Quét tĩnh AST xác nhận: 0 rò rỉ `self`→`self.app`, mọi `self.app.X` đều phân giải, không tên chưa định nghĩa, không method trùng.
- `tests/_smoke_full.py` mở rộng **16→18 bước**: phủ thêm mọi chế độ xem (3D/SSI/thiết kế đài) và kéo-thả Tab Hàng loạt → chống tái phát loại lỗi trên. Giữ nguyên: pytest **54 passed**.
- Chi tiết & các pha: `plans/023-refactor-ui-composition.md`.

## [1.9.0] — 2026-06-28

### Mô phỏng "xịn hơn MCOC" + demo trơn tru (toàn bộ FREE / open-source)
- **Khung nhìn 3D** mô hình tổng thể: đài + cọc (cột màu theo lực) + cột/trụ trên đỉnh + lớp đất (nhãn E) + dải đất quanh cọc + **móng khối quy ước** + mặt đất + dấu **"+" gốc tọa độ** (cả 2D & 3D). matplotlib-3D nhúng tkinter, không thêm thư viện.
- **Engine SSI thuần NumPy** (`core/ssi_engine.py`): tương tác đất–cọc — phân phối lực dọc trục (3 bậc tự do, khớp `rigid_cap`) + **cọc chịu ngang** (dầm trên nền Winkler) + **độ lún** + **hiệu ứng nhóm cọc** (p-multiplier AASHTO). Tự dùng **EI=Eb·Jo & hệ số nền m** đọc từ file MCOC, theo **phương pháp "m" TCVN 10304 Phụ lục A** (k=m·z·d). Pmax SSI ≈ MCOC thực (T1: 518 vs 519,6).
- **Thiết kế kết cấu đài cọc** (`core/cap_design.py`) theo **TCVN 5574:2018**: cốt thép uốn (8.1.2), chọc thủng cột + cọc (8.1.6), cắt một phương (8.1.3), giàn ảo STM cho đài sâu. Cường độ Rb/Rbt/Rs đối chiếu `words_dict/TCVN5574-2018.md`.
- **Panel "Trụ địa chất & lún"** (φ_tb, độ sâu đáy đài, γ', Sgh + bảng lớp đất) → tính **lún móng khối quy ước (Điều 7.4)** hiển thị ở tab SSI.
- **Nút "⚡ Nạp DEMO đầy đủ"**: điền mọi ô trống ([Po]/[Ct] cỡ theo tải, cột, **tự tăng chiều cao đài H** để chọc thủng đạt) → **cả 15 trụ T1–T22 đều ĐẠT**.
- **Thiết kế lại Tab 1**: cửa sổ maximize, panel trái **2 cột nhập liệu**, nút Chạy gọn, ô "Kết quả Đánh giá" to hơn, sash cân đối, thu gọn khung TCVN khi tắt.
- **Giao diện kiểu MCOC**: thanh **menu** (File / Tính toán / Trợ giúp), hộp **Giới thiệu**, **logo TEDI** (icon cửa sổ + EXE), nhãn phiên bản; Tab 2 panel phải 3 tab (Xuất kết quả / Báo cáo / spColumn).
- **Tài liệu**: `docs/SO_LIEU_DEMO.md` (số liệu địa chất + thiết kế đài đầy đủ cho T1–T22, hướng dẫn nhập từng ô, bộ case test ĐẠT/KHÔNG ĐẠT).
- **Kiểm thử**: thêm `tests/test_ssi_engine.py` + `tests/test_cap_design.py` (axial ≡ rigid_cap; Winkler ≡ Hetenyi; p-multiplier ≡ AASHTO; thiết kế đài khớp tính tay) — tổng **54 passed**.

> Lộ trình nội bộ: 1.5.0 menu/logo · 1.6.0 3D+SSI+thiết kế đài · 1.7.0 pp "m" từ file · 1.8.0 trụ địa chất+lún · 1.9.0 demo đầy đủ + 3D sát thực tế. Ràng buộc: chỉ tool free (đã loại OpenSeesPy vì chưa hỗ trợ Python 3.13).

## [1.4.0] — 2026-06-20

### Hợp nhất ext + TCVN 10304:2014
- Hợp nhất hai nhánh phát triển: **Tối ưu MỞ RỘNG** (`core/ext/`, R1–R8, quét đường kính + thu bệ) và **Bám sát TCVN 10304:2014** (sức chịu tải thiết kế `core/tcvn.py`). Nay nhánh chính là hợp của cả hai. Chi tiết từng mảng xem dưới (mục 1.3.0).

## [1.3.0] — 2026-06-18

### Tính năng lớn — Tối ưu MỞ RỘNG (gói `core/ext/`)
- **Quét nhiều đường kính cọc**: khai báo "Bảng đường kính" (mỗi `d` có `[Po]/[Ct]/[M]/[H]` riêng); chương trình patch tiết diện thật (Fo, Jo, Po) vào file MCOC rồi chấm chính xác từng đường kính.
- **Chọn toàn cục** đường kính thắng theo **hàm chi phí vật liệu** (số cọc × diện tích tiết diện), đồng hạng thì ít cọc hơn.
- **Tự thu bệ** (cap_resize) theo TCVN 10304:2014: bệ vừa khít cọc (mép ≥ d), làm tròn bội số thi công; báo "tiết kiệm diện tích bệ %".
- ⇒ Tối ưu đồng thời **bố trí + đường kính + kích thước bệ**, không chỉ bố trí.

### Ràng buộc: R1–R6 → **R1–R8**
- **R7 lực ngang** `Hmax ≤ [H]` và **R8 tương tác P–M** `N/[Po] + M/[M] ≤ 1.0` (bật ở luồng mở rộng; không sửa lõi — dùng cờ context manager). Bảng audit + báo cáo PDF/MD thành **R1–R8** (thêm cột H_max).

### So sánh "tiến hóa" giữa các phương án
- **Mỗi phương án mang bệ / đường kính / sức chịu RIÊNG**: phương án gốc vẽ & audit theo bệ + d gốc; phương án đề xuất theo bệ đã thu + d thắng.
- **Khung nhìn CHUNG**: mọi phương án **cùng tỉ lệ** khi chuyển (cọc giữ nguyên cỡ) — dễ quan sát thay đổi.
- **Bệ gốc luôn đủ chứa cọc gốc** (`max(ô L_X/L_Y, bệ vừa khít)`), không để cọc tràn ra ngoài khi ô đã bị thu.

### Xử lý BỆ CHẬT (tùy chọn người dùng — không đổi mặc định thuật toán)
- **Lượng hóa** khi vô nghiệm: bệ hiện chứa tối đa N cọc (lưới nx×ny @ k/c).
- **Đề xuất nới bệ** tối thiểu (`core/cap_suggest.py`): lưới ≥2×2 ít cọc nhất đạt lực + bệ nhỏ nhất chứa nó (checkbox, mặc định bật).
- **Tùy chỉnh k/c tối thiểu** `3.0 / 2.75 / 2.5 ×d` (qua `SPACING_MIN_FACTOR`; thiếu/≤0 → giữ 3d).

### Giao diện (UI/UX)
- Gộp khung **"Tối ưu mở rộng" vào "Điều Khiển Tối Ưu"**.
- "Thông số Bài toán" bố cục **2 cột cân đối** (kích thước | sức chịu) — ô `[Po]/[Ct]/[M]` luôn hiện đủ, không bị cắt.
- **"Làm mới" sạch hoàn toàn**: xóa cả dải KPI + ô Tổ hợp + về chế độ Mặt bằng.

### Sửa lỗi
- **Bảng R1–R8 vẽ vỡ thành dải mảnh** khi đổi tổ hợp/kéo cửa sổ — do `tight_layout` co dồn lề tích lũy; nay đặt **lề cố định** (`plot_canvas.draw_constraint_view`).
- **Phương án gốc vẽ trong bệ đã thu** (cọc tràn ngoài) + mâu thuẫn "ĐẠT/KHÔNG ĐẠT" — nay bệ gốc đủ chứa cọc, audit R4 dùng bệ riêng → trạng thái nhất quán.

### Tài liệu & kiểm thử
- **`docs/SO_TAY_VAN_HANH.md`** (sổ tay toàn bộ chức năng) + **`docs/HUONG_DAN_NHANH.md`** (làm theo từng bước với số liệu thật).
- **Vault Obsidian** quản lý dự án (ADR, concept, engine, module).
- Test/harness mới: `tests/test_ext.py`, `test_cap_suggest.py`, `validate_mcoc.py`, `validate_method.py`, và các harness lái GUI / duyệt bộ mẫu.

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
