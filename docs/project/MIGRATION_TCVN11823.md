# Kế hoạch chuyển cơ sở thiết kế sang TCVN 11823:2017 (LRFD)

> **Mã:** OA-DOC-14 · **Phiên bản:** 0.4 (Pha 1–4 + form GUI + 43 test LRFD; chờ nghiệm thu hệ số với bản TCVN gốc) · **Cập nhật:** 2026-06-29 · **Trạng thái:** Draft
> **Căn cứ:** khảo sát `core/`, `io_handlers/`, `ui/` (trạng thái cơ sở TCVN 10304:2014) + tra cứu web TCVN 11823 / AASHTO LRFD. Quyết định gốc: [ADR-008](../reference/adr/ADR-008-co-so-thiet-ke-tcvn-11823.md) · [Backlog M1](BACKLOG.md).

> ⚠️ **Mọi giá trị hệ số `γ`/`φ` trong tài liệu này là TRỊ THAM KHẢO theo AASHTO LRFD**
> (cơ sở của TCVN 11823) và **PHẢI được kỹ sư đối chiếu, xác nhận với bản TCVN
> 11823-3:2017 (Tải trọng) và TCVN 11823-10:2017 (Nền móng)** trước khi cài vào code
> hoặc dùng cho hồ sơ. Tài liệu này là **kế hoạch**, chưa đổi logic code.

---

## 1. Mục tiêu & phạm vi

Chuyển toàn bộ cơ sở kiểm toán của OptApp từ **TCVN 10304:2014** (sức chịu tải cho
phép + hệ số riêng phần γ) sang **TCVN 11823:2017 — Thiết kế cầu đường bộ** (triết
lý **LRFD**: trạng thái giới hạn, hệ số tải `γᵢ`, hệ số sức kháng `φ`). Phần móng cọc
theo **TCVN 11823-10**; tải trọng & tổ hợp theo **TCVN 11823-3**; kết cấu bê tông đài
theo **TCVN 11823-5**.

**Giữ nguyên (không đổi):** MCOC vẫn là oracle nội lực duy nhất ([ADR-001](../reference/adr/ADR-001-mcoc-oracle-duy-nhat.md));
NSGA-II vẫn là engine tối ưu; kiến trúc UI composition. Migration đổi **tiêu chí kiểm
toán** (demand/resistance), KHÔNG đổi cách tính nội lực.

## 2. Khác biệt triết lý (vì sao là "chỉnh sửa lớn toàn bộ")

| | TCVN 10304:2014 (hiện tại) | TCVN 11823:2017 (LRFD, đích) |
|---|---|---|
| Tiêu chí | `N ≤ Rc,d` (allowable) | `ΣγᵢQᵢ ≤ φ·Rn` (trạng thái giới hạn) |
| Phía tải (demand) | tải danh nghĩa, **không hệ số** | **tổ hợp có hệ số** Strength/Service/Extreme |
| Phía sức kháng | `Rc,d = (γ0/γn)·(Rc,k/γk)` | `φ·Rn` — `φ` theo **phương pháp** xác định Rn |
| Phân loại tải | không phân loại | DC/DW/LL+IM/WS/WL/EQ… (mỗi loại 1 `γ`) |
| Số tổ hợp kiểm | 1 (mỗi dòng tải) | nhiều tổ hợp giới hạn × hệ số |

⇒ Phải bổ sung **cả một lớp tổ hợp tải LRFD** mà OptApp hiện chưa có (đây là phần mới
lớn nhất), đồng thời đổi công thức sức kháng và mọi chỗ so sánh `Pmax ≤ [Po]`.

## 3. Bản đồ điểm chạm code (file-by-file)

| File | Hiện tại (10304) | Phải làm (11823) | Mức |
|---|---|---|---|
| `core/tcvn.py` | `design_axial_capacity` → `Rc,d`; `resolve_gamma_k(n_piles)`; `apply_design_capacities` ghi đè `[Po]/[Ct]` | Module mới (hoặc thay) tính `φ·Rn`: nhập **Rn danh nghĩa** + chọn **phương pháp** → tra `φ` (Bảng 10.5.5.2.3/-2.4); bỏ γ0/γn/γk kiểu 10304 | rất cao |
| `core/mechanics.py` (≈ dòng 49–68) | R5 `pmax > P_LIMIT`, R5b `pmin < −P_TENSION`, R8 P–M | So **demand có hệ số** với `φ·Rn`; R8 tương tác theo 11823 | cao |
| `core/nsga2_optimizer.py` (`evaluate`/CV) | gọi `apply_design_capacities`; CV theo `Pmax/[Po]` | sinh **tổ hợp LRFD** → demand có hệ số → CV theo `ΣγQ/(φRn)` | cao |
| `core/constants.py` | `DEFAULTS[P_LIMIT]`… ngữ nghĩa allowable; cờ R7/R8 | thêm hằng **tổ hợp & hệ số tải**, hệ số `φ` mặc định; đổi ngữ nghĩa | cao |
| Lớp tải `ui/controllers/loads.py` + `params.py` + `io_handlers/file_io.py` | tải thô `Hx,Hy,P,Mx,My,Mz` (không loại) | thêm **phân loại tải** (DC/DW/LL…) + chọn trạng thái giới hạn để áp `γ` | cao (UX) |
| `core/blackbox.py` / `core/mcoc_runner.py` | MCOC chấm tải danh nghĩa | quyết định: factor tải **trước** MCOC (nhiều lần gọi) hay scale nội lực **sau** MCOC (giả thiết tuyến tính) — xem §5 QĐ-2 | cao |
| `io_handlers/report_writer.py` | mục R1–R8 + lún Đ.7.4.4, dẫn TCVN 10304/5574 | viết lại theo điều khoản 11823-3/-10/-5; báo cáo demand có hệ số vs `φRn` theo từng tổ hợp | trung |
| `core/cap_design.py` | thiết kế đài TCVN 5574:2018 | rà/khớp **TCVN 11823-5** (BTCT cầu); quyết định giữ hay đổi — §5 QĐ-4 | trung |
| `core/ssi_engine.py` / lún | lún Đ.7.4.4 (10304) + 9362 | trạng thái **Sử dụng** theo 11823-10 (§10.7.2.3 lún cọc) | trung |
| `core/ext/*` (orchestrator, blackbox_ext, nsga2_ext) | kế thừa lõi | kế thừa thay đổi lõi; bảng đường kính giữ Rn danh nghĩa | trung |

## 4. Danh mục hệ số cần cài (⚠️ trị tham khảo AASHTO — CẦN KỸ SƯ XÁC NHẬN với TCVN 11823)

### 4.1 Hệ số tải trọng `γ` — tổ hợp (AASHTO Table 3.4.1-1 ⇄ TCVN 11823-3, Bảng 3.4.1-1)
| Tổ hợp | DC (max/min) | DW (max/min) | LL+IM | WS | WL | EQ | Ghi chú |
|---|---|---|---|---|---|---|---|
| **Cường độ I** (Strength I) | 1,25 / 0,90 | 1,50 / 0,65 | **1,75** | — | — | — | tải xe thông thường |
| **Cường độ II** | 1,25 / 0,90 | 1,50 / 0,65 | 1,35 | — | — | — | xe đặc biệt |
| **Cường độ III** | 1,25 / 0,90 | 1,50 / 0,65 | — | 1,40 | — | — | gió ≥ ngưỡng, không xe |
| **Cường độ IV** | **1,50** / 0,90 | 1,50 / 0,65 | — | — | — | — | tĩnh tải chi phối |
| **Cường độ V** | 1,25 / 0,90 | 1,50 / 0,65 | 1,35 | 0,40 | 1,0 | — | xe + gió |
| **Sử dụng I** (Service I) | 1,0 | 1,0 | 1,0 | 0,30 | 1,0 | — | kiểm lún/biến dạng |
| **Đặc biệt I** (Extreme I) | 1,25 / 0,90 | 1,50 / 0,65 | γEQ (0–1,0) | — | — | 1,0 | động đất |
| **Đặc biệt II** (Extreme II) | 1,25 / 0,90 | 1,50 / 0,65 | 0,50 | — | — | — | va xô/băng |

> γEQ do chủ đầu tư quy định (thường 0; 0,5; hoặc 1,0). Bảng rút gọn — bản đầy đủ còn
> EH/EV/ES, TU/TG/SE, BR/CE/CT/CV, FR… (TCVN 11823-3 §3.4).

### 4.2 Hệ số sức kháng `φ` cọc (TCVN 11823-10, Bảng 10.5.5.2.3-1 cọc đóng / 10.5.5.2.4-1 cọc khoan)
| Đối tượng | Cách xác định Rn | φ (tham khảo) |
|---|---|---|
| Cọc đóng — nén dọc trục | thử tải tĩnh (có thử động) | ~0,75 |
| Cọc đóng — nén dọc trục | phân tích tĩnh (α/β, SPT…) | ~0,35–0,50 (theo pp) |
| Cọc khoan nhồi — nén dọc trục | thử tải tĩnh | ~0,70 |
| Cọc khoan nhồi — nén dọc trục | phân tích tĩnh | ~0,45–0,55 (theo pp) |
| Cọc (đóng/khoan) — **kéo/nhổ** | phân tích/thử | ~0,35–0,45 (thấp hơn nén) |
| Trạng thái **Đặc biệt** (động đất/va xô) | — | thường φ = 1,0 |

> **Quy tắc giảm 20%:** khi móng chỉ có **1 cọc** đỡ một trụ → φ trong bảng **× 0,8**
> (xác nhận từ TCVN 11823-10). Với cọc khoan trong sét/đất dễ xáo trộn phải xét kinh
> nghiệm địa phương.

## 5. Quyết định kiến trúc cần chốt (cho kỹ sư / chủ dự án)

- **QĐ-1 — Phân loại tải:** OptApp nhập tải/cách phân loại DC/DW/LL… thế nào? (a) thêm
  cột "loại tải" cho mỗi tổ hợp + app tự dựng các tổ hợp giới hạn; hay (b) người dùng
  tự nhập sẵn **tải đã có hệ số** theo từng trạng thái (đơn giản hoá, ít đúng tinh thần
  LRFD). → ảnh hưởng lớn tới UI.
- **QĐ-2 — Vị trí áp `γ` so với MCOC:** (a) nhân hệ số vào tải **rồi** chạy MCOC cho
  từng tổ hợp (đúng nhất, nhưng **×N lần gọi MCOC** → cần song song hoá [O1](BACKLOG.md));
  hay (b) chạy MCOC tải danh nghĩa **rồi** scale nội lực theo `γ` (chỉ đúng nếu phản hồi
  tuyến tính — cần kỹ sư xác nhận MCOC tuyến tính theo tải).
- **QĐ-3 — Nguồn `Rn` danh nghĩa:** hiện `[Po]` được coi là sức chịu **thiết kế**. LRFD
  cần **Rn danh nghĩa** + chọn **phương pháp** để app áp `φ`. Người dùng nhập Rn + method,
  hay vẫn nhập trực tiếp `φRn`?
- **QĐ-4 — Thiết kế đài: ĐÃ CHỐT → TCVN 11823-5:2017** (chủ dự án 2026-06-29: TCVN
  5574 KHÔNG được áp dụng cho cầu). Đã cài [`core/cap_design_lrfd.py`](../../core/cap_design_lrfd.py)
  (uốn φMn, cắt φVn, chọc thủng 2 phương, STM) + dispatch trong `cap_design.design_cap`.
- **QĐ-5 — Lún/Sử dụng:** dùng lún theo **11823-10 §10.7.2.3** thay cho Đ.7.4.4 (10304)
  + 9362 hiện có?

## 6. Lộ trình theo pha

- **Pha 1 — Khảo sát & kế hoạch (tài liệu này).** ✅ Bản đồ điểm chạm + danh mục hệ số
  (tham khảo) + quyết định cần chốt. **Chưa đổi code.**
- **Pha 2 — Hạ tầng tải LRFD.** Phân loại tải + dựng tổ hợp giới hạn (11823-3) ở lớp
  nhập liệu/UI + cấu trúc dữ liệu tải mới (QĐ-1).
- **Pha 3 — Sức kháng `φ·Rn` & tiêu chí kiểm.** Viết module sức kháng 11823-10 (QĐ-3);
  đổi `mechanics`/`nsga2` sang `ΣγQ ≤ φRn` (QĐ-2).
- **Pha 4 — Lún/đài/báo cáo.** Trạng thái Sử dụng (QĐ-5), đài (QĐ-4), viết lại report
  + audit theo 11823.
- **Pha 5 — Kiểm chứng & tài liệu.** Bộ test hand-calc theo 11823; cập nhật toàn bộ
  `docs/` (gỡ "trạng thái 10304", chuyển sang 11823); cập nhật [ADR-008](../reference/adr/ADR-008-co-so-thiet-ke-tcvn-11823.md).

## 7. Rủi ro & nguyên tắc
- **Không bịa số:** mọi `γ`/`φ` phải dẫn nguồn TCVN 11823; trị trong §4 mới là tham
  khảo AASHTO, **kỹ sư xác nhận** trước khi cài.
- **Chi phí MCOC** tăng theo số tổ hợp (QĐ-2a) → song song hoá là điều kiện thực tế.
- **Tương thích ngược:** cân nhắc cờ chọn chế độ (10304 cũ / 11823 mới) trong giai đoạn
  chuyển tiếp, hay cắt hẳn sang 11823.
- **Tài liệu trung thực:** chỉ ghi "đã theo 11823" cho phần code đã thực sự chuyển.

## 8. Nguồn tra cứu (Pha 1B — cần đối chiếu bản chuẩn gốc)
- TCVN 11823-10:2017 (Nền móng) — danh mục/giới thiệu: caselaw.vn, tieuchuanquocgia.com,
  studocu.vn (toàn văn cần truy cập có phép). Xác nhận: φ chọn theo bảng tùy **phương
  pháp**; móng 1 cọc **giảm 20%**; dùng trạng thái Cường độ/Sử dụng/Đặc biệt.
- TCVN 11823-3:2017 (Tải trọng & hệ số tải trọng) — tổ hợp & `γ` (Bảng 3.4.1-1).
- AASHTO LRFD Bridge Design Specifications, Table 3.4.1-1 (tổ hợp/`γ`) và §10.5.5.2
  (φ cọc) — cơ sở của TCVN 11823 (đối chiếu national annex).

## 9. Trạng thái triển khai (cập nhật 2026-06-29)

**ĐÃ CÀI (Pha 2–4 lõi):**
- [`core/lrfd.py`](../../core/lrfd.py) — **nguồn duy nhất** LRFD: `LOAD_FACTORS` (γ),
  `RESISTANCE_FACTORS` (φ), `factored_resistance` (φ·Rn, giảm 20% móng 1 cọc),
  `factor_loads`/`demand_loads` (Σγ·Q), `apply_lrfd_capacities`, `apply_design_basis`.
- Cờ `DESIGN_BASIS='TCVN11823'` (mặc định) trong [`core/constants.py`](../../core/constants.py);
  điều phối tại `run_nsga2` / `run_optimization` / `run_pareto_refinement` /
  `report_writer.build_report_text` / UI `get_params_dict`.
- Cơ chế lắp KHÉO: `P_LIMIT = φ·Rn` (sức kháng) + tải nhân γ (demand) ⇒ phép so
  `pmax ≤ P_LIMIT` sẵn có thành `Σγ·Q ≤ φ·Rn`. MCOC vẫn là oracle, **không** tăng số
  lần gọi (QĐ-2: factor tải trước, MCOC chạy 1 lần/phương án trên cả bộ tải).
- Báo cáo có **Mục 0 — Cơ sở thiết kế**: nêu basis, φ/γ đã dùng, trạng thái cấu hình,
  và **banner "TRỊ THAM KHẢO — cần kỹ sư nghiệm thu"**.
- Test: [`tests/test_lrfd.py`](../../tests/test_lrfd.py) (20 ca hand-calc + 1 tích hợp
  qua `run_nsga2`). Toàn bộ pytest xanh.
- **Bê tông đài theo TCVN 11823-5:2017** (QĐ-4): [`core/cap_design_lrfd.py`](../../core/cap_design_lrfd.py)
  — vật liệu f'c/fy/β1, uốn `Mu≤φMn` (5.6.3), cắt 1 phương `Vu≤φVn` β=2 (5.7.3.3),
  chọc thủng 2 phương (5.12.8.6), STM. `cap_design.design_cap` uỷ quyền khi basis=11823;
  đường TCVN 5574 chỉ còn cho basis 10304 (đối chiếu). UI `plot_canvas` hiển thị
  basis-aware (φ·Rn). Test [`tests/test_cap_design_lrfd.py`](../../tests/test_cap_design_lrfd.py)
  (10 ca). **TCVN 5574 KHÔNG dùng cho cầu.**

**An toàn không phá vỡ:** khi CHƯA khai báo tham số LRFD (`R_N`, `load_type`/`LRFD_ENABLE`),
mặc định 11823 hành xử **y hệt** đường cũ (γ=1, `P_LIMIT`=[Po] nhập) → mọi test 10304 vẫn
xanh; báo cáo ghi rõ "CHƯA cấu hình tải LRFD".

**Cách dùng ngay (qua FILE input — chưa cần GUI):** thêm các cột params:
`DESIGN_BASIS=TCVN11823`, `LRFD_ENABLE=1`, `R_N=<sức kháng nén danh nghĩa>`,
`R_N_T=<kéo>`, `PILE_TYPE=driven|drilled`, `RESISTANCE_METHOD=static_load_test|static_analysis|...`,
`STRENGTH_STATE=STRENGTH_I`, `SINGLE_PILE=1` (nếu móng 1 cọc). (Parser nạp mọi cột
header vào `params`.)

**CÒN LẠI (chưa làm):**
- **Nghiệm thu trị số γ/φ** với bản TCVN 11823-3/-10 (đang là trị tham khảo AASHTO).
- **Form GUI** nhập `R_N`/phương pháp/`load_type` (tôn trọng 3 cổng an toàn GUI +
  golden regression — increment riêng).
- **Tổ hợp đa-loại-tải đồng thời** (hiện mỗi dòng tải áp 1 γ theo loại; cộng DC+DW+LL
  đồng thời cần nhóm `combo` — QĐ-1).
- **Lún trạng thái Sử dụng theo 11823-10 §10.7.2.3** (QĐ-5) — `core/tcvn.py` lún hiện
  còn theo Đ.7.4.4 (10304) khi tính ở tab SSI.
- **f'c quy đổi từ cấp B** trong `cap_design_lrfd` là GẦN ĐÚNG — nên nhập `FC` trực
  tiếp + bổ sung cấp C vào combobox GUI (increment).
- Cập nhật `docs/reference/AUDIT_CONG_THUC_TCVN.md` sang khung 11823 sau nghiệm thu.

## 10. Nghiệm thu hệ số γ/φ — trạng thái (2026-06-29)

- **Đã làm:** đối chiếu cấu trúc với nhiều nguồn AASHTO/DOT (Caltrans BDP, Minnesota
  DOT, ADOT, NCHRP 507, PCI Journal, TxDOT) + xác nhận **TCVN 11823-3/-5/-10 dựa trên
  AASHTO LRFD**. Trị γ/φ trong code là **trị chuẩn AASHTO LRFD** (Bảng 3.4.1-1; §5.5.4.2
  bê tông φ=0,90 uốn & cắt, 0,75 nén; §10.5.5.2 sức kháng cọc theo phương pháp xác định).
- **Chưa làm được tự động:** trích NGUYÊN VĂN trị số từ bản TCVN 11823 GỐC — toàn văn nằm
  sau cổng đăng nhập/paywall (caselaw, studocu, vsqi) hoặc PDF khoá mật khẩu. Vì vậy
  **đối chiếu số chính xác + sai khác phụ lục quốc gia là việc của KỸ SƯ** với bản chuẩn.
- **Bảo chứng nội bộ — 43 ca test LRFD** (`test_lrfd.py` 25, `test_cap_design_lrfd.py` 14,
  `test_gui_lrfd.py` 4) neo công thức & đường đi: φ tra bảng (đầy đủ ma trận), giảm 20%
  móng 1 cọc, Đặc biệt φ=1,0, factor tải γ (min/uplift/đa loại/bỏ γ=0), **nhân tải tuyến
  tính → lực cọc đúng γ**, **tiêu chí Σγ·Q ≤ φ·Rn thoả end-to-end qua `run_nsga2`**, uốn
  round-trip `φMn`, βc chọc thủng, dv, dispatch theo cơ sở, form GUI → params. Toàn bộ
  pytest xanh (101 ca).
- **Khi có bản TCVN 11823 (text):** chỉ cần sửa trị trong `LOAD_FACTORS`/`RESISTANCE_FACTORS`
  ([core/lrfd.py](../../core/lrfd.py)) và `PHI_*`/`FC_BY_GRADE` ([core/cap_design_lrfd.py](../../core/cap_design_lrfd.py))
  — đã gom MỘT chỗ; test hand-calc sẽ bắt ngay sai lệch.
