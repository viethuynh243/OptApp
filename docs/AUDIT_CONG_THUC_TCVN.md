# Rà soát công thức lõi đối chiếu TCVN (audit độc lập)

> **CẬP NHẬT 2026-06-28 (Plan 024 — ĐÃ KHẮC PHỤC, v1.10.0):** các mục 🔶/❓ bên dưới đã
> xử lý theo nguyên tắc "có trong TCVN → theo đúng TCVN; không có → giữ công thức audit,
> ghi rõ nguồn" (đối chiếu nguồn chính thức + web). Tóm tắt:
> - **Lún (Đ.7.4.4)** = Se (đàn hồi thân cọc, CT 21) + lún khối; ứng suất tâm theo
>   **Boussinesq** (thay 2:1), β=0,8, vùng nén tới 0,2σ'vz.
> - **Móng khối**: chặn **a≤2d** khi đất dính yếu IL>0,6 (checkbox GUI).
> - **γk**: `resolve_gamma_k` theo bảng số cọc (1,40/1,55/1,65/1,75; thử tĩnh 1,25/1,40/1,50/1,60).
> - **Cắt 1 phương**: Qb=1,5·Rbt·b·h0²/C (kẹp [0,5;2,5]·Rbt·b·h0) + nén dải 0,3·Rb·b·h0.
> - **ξ_R/εb2**: xác nhận khớp CT(31)+εb2=0,0035 (thêm trích dẫn, không đổi số).
> - **STM**: giữ công thức + ghi rõ nguồn ACI/AASHTO (không phải trị TCVN).
> Có unit test hand-calc từng mục. Chi tiết: `plans/024-tcvn-compliance-fixes.md`.

> Phạm vi: `core/rigid_cap.py`, `core/tcvn.py`, `core/cap_design.py`, `core/mechanics.py`
> đối chiếu **TCVN 10304:2014** (móng cọc) và **TCVN 5574:2018** (BTCT), dùng bản trích
> trong `words_dict/TCVN10304-2014.md` & `words_dict/TCVN5574-2018.md`.
> Ngày: 2026-06-28. Chỉ ĐỌC, không sửa code. Đây là rà soát kỹ thuật — các mục
> 🔶 cần **kỹ sư kết cấu/địa kỹ thuật xác nhận** trước khi dùng cho hồ sơ thật.

Ký hiệu: ✅ chứng minh khớp tiêu chuẩn · ⚠️ đơn giản hoá THIÊN AN TOÀN · 🔶 sai lệch/giả định
cần kỹ sư xác nhận · ❓ theo thực hành (không trích được từ tiêu chuẩn).

---

## 1. `tcvn.py` — TCVN 10304:2014

| Mục                           | Code                                                         | Tiêu chuẩn (trích)                                                                                                                                    | Kết luận                                                                                                                                                                                                                                                       |
| ------------------------------ | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Rc,d (Đ.7.1.11)               | `(γ0/γn)·(Rck/γk)` (dòng 66)                          | CT(2):`Rc,d=(γ0/(γn·γk))·Rc,k` (TCVN10304 dòng 573-580)                                                                                          | ✅**ĐỒNG NHẤT đại số** (cùng giá trị). test_design_axial_capacity xác nhận                                                                                                                                                                      |
| γn (I/II/III)                 | 1.20/1.15/1.10 (dòng 41)                                    | "1,2; 1,15; 1,1 cho cấp I, II, III" (dòng 608)                                                                                                         | ✅ khớp chính xác                                                                                                                                                                                                                                             |
| γ0                            | 1.15 nhiều cọc / 1.0 đơn (dòng 44)                      | "1 cọc đơn; 1,15 móng nhiều cọc" (dòng 599-607)                                                                                                   | ✅ khớp                                                                                                                                                                                                                                                         |
| γk mặc định                | 1.40 (dòng 46)                                              | k=1,4 (cọc ma sát, xác định bằng tính toán, ngoài cọc đơn) (dòng 611-628)                                                                   | ✅ mặc định hợp lý — ⚠️ γk phụ thuộc**số cọc/cách xác định** (1,2–1,75); **người dùng phải nhập đúng γk cho bài toán**                                                                                                   |
| Móng khối quy ước (Đ.7.4) | `spread=2·Lc·tan(φ/4)` (dòng 152)                      | CT(40):`a=h·tg(φII,mt/4)` (dòng 2182-2188)                                                                                                          | ✅ đúng dạng — 🔶 (a) dùng**Lc** thay vì h (= sâu từ mũi tới mặt đất); (b) **thiếu chặn `a ≤ 2d` cho đất dính yếu IL>0,6** → có thể nới khối quá lớn (thiên KHÔNG an toàn cho lún ở ca đất yếu)                 |
| Lún                           | `S=Σ β·σz·h/E, β=0.8`, phân bố 2:1 (dòng 168-231) | TCVN10304 Đ.7.4 dùng**hệ số ảnh hưởng α**, KHÔNG có dạng Σβσh/E; β=0,3–0,7 ở đó là cho **lún đàn hồi thân cọc Se** | 🔶**Sai lệch phương pháp**: code dùng **cộng lún từng lớp TCVN 9362** (2:1 + β=0,8) — phổ biến & hợp lý, nhưng KHÔNG phải thủ tục Đ.7.4 của 10304. Coi là **ước lượng**; docstring đã nói rõ là theo TCVN 9362 |

**R7.1.11:** chứng minh đúng. **Móng khối + lún:** dùng phương pháp đơn giản (9362) thay vì
hệ số ảnh hưởng của 10304 — hợp lý nhưng cần kỹ sư địa kỹ thuật chấp nhận, và bổ sung chặn 2d.

---

## 2. `cap_design.py` — TCVN 5574:2018  *(module bạn đang mở)*

| Mục                                                                                         | Code                                                           | Tiêu chuẩn (trích)                                                             | Kết luận                                                                                                                                                                                                                 |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Rb (B15–B40)                                                                                | 8.5/11.5/14.5/17.0/19.5/22.0 (dòng 26)                        | Bảng 7 (TCVN5574 dòng 1666-1702)                                                | ✅**khớp từng giá trị**                                                                                                                                                                                          |
| Rbt                                                                                          | 0.75/0.90/1.05/1.15/1.30/1.40 (dòng 27)                       | Bảng 7                                                                           | ✅ khớp từng giá trị                                                                                                                                                                                                   |
| Rs (CB240→CB500)                                                                            | 210/260/350/435 (dòng 28)                                     | Bảng 13 (dòng 2650-2714)                                                        | ✅ khớp                                                                                                                                                                                                                   |
| Es                                                                                           | 200000 MPa (dòng 29)                                          | 2,0×10⁵ MPa (dòng 2792-2805)                                                   | ✅ khớp                                                                                                                                                                                                                   |
| ξ_R                                                                                         | `0.8/(1+(Rs/Es)/εb2)`, εb2=0.0035 (dòng 39)               | dạng ξ_R = 0,8/(1+εs,el/εb2)                                                  | ✅ đúng dạng — ⚠️ εb2=0,0035 là giá trị quy ước (ngắn hạn); tài liệu nêu ε0b=0,002 (đỉnh) + dài hạn 0,0042–0,0056 →**nên xác nhận εb2 đúng ca tải**                                   |
| Uốn As (Đ.8.1.2)                                                                           | α_m, ξ=1−√(1−2α_m), ζ, As=M/(Rs·ζ·h0) (dòng 46-71)  | CT(34-35) M_u tổng quát                                                         | ✅**dạng rút gọn tương đương** (cốt đơn). ⚠️ bỏ cốt nén As′ (giả định hợp lý cho đài). test_flexure_hand_calc khớp tính tay                                                                |
| μ_min                                                                                       | 0.1% (dòng 31)                                                | μmin = 0,1% (dòng 11887)                                                        | ✅ khớp                                                                                                                                                                                                                   |
| Chọc thủng cột (Đ.8.1.6)                                                                 | `u_m=2(bc+hc+2h0)`, `F_ult=Rbt·u_m·h0` (dòng 80-81)     | tiết diện ở**h0/2**, `F_b,u=Rbt·A_b`, `A_b=u·h0` (dòng 6739-6797) | ✅**khớp chính xác** (chu vi tại h0/2 của cột chữ nhật)                                                                                                                                                      |
| Chọc thủng cọc                                                                            | `u_m=π(D+h0)` (dòng 88)                                    | chu vi tại h0/2 quanh tiết diện tròn                                          | ✅ khớp                                                                                                                                                                                                                   |
| Cắt 1 phương (Đ.8.1.3)                                                                   | `Qc=0.5·Rbt·b·h0`, `Qmax=2.5·Rbt·b·h0` (dòng 97-98) | Qb ∈ [0,5 ; 2,5]·Rbt·b·h0 (dòng 5252-5282)                                   | ⚠️**THIÊN AN TOÀN**: lấy **cận dưới 0,5** làm khả năng bê tông (thực tế Qb có thể cao hơn qua `βb2·Rbt·b·h0²/C`). An toàn nhưng có thể đòi đài dày/đai khi chưa thật cần |
| STM (đài sâu)                                                                             | z=0.9·h0, deep khi a/h0<1.0 (dòng 104-113)                   | TCVN5574 chỉ nêu STM cho cấu kiện ngắn,**không** cho a/h0 hay z=0,9h0 | ❓**theo thực hành (ACI/AASHTO)**, không trích được từ 5574 — dùng tham khảo, không phải trị tiêu chuẩn                                                                                              |
| Tiết diện uốn tại**mép cột**; lực chọc thủng = N_cột − Σ(cọc trong tháp) | dòng 176-194                                                  | phương pháp đài cọc kinh điển                                             | ✅ đúng cách đặt tiết diện nguy hiểm                                                                                                                                                                               |

**Vật liệu + chọc thủng + uốn + μ_min: chứng minh khớp tiêu chuẩn.** Cắt 1 phương thiên an toàn.
STM theo thực hành. ξ_R đúng dạng (xác nhận εb2).

---

## 3. `rigid_cap.py` — lý thuyết bệ cứng (predictor)

| Mục                   | Code                                                                | Lý thuyết                                            | Kết luận                                                                                                               |
| ---------------------- | ------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| Lực dọc cọc         | `P=N/n+(Mx−N·cy)(y−cy)/Ix+(My−N·cx)(x−cx)/Iy` (dòng 48-71) | bệ cứng đàn hồi, quy mômen về trọng tâm nhóm | ✅**thoả cân bằng tĩnh ΣP=N, ΣP·d=M tới ~1e-13** (validate_method [7])                                     |
| Lực ngang             | `Hx/n − Mz·dy/Ip`, `Hy/n + Mz·dx/Ip` (dòng 118-142)         | chia đều lực cắt + xoắn theo Ip                   | ✅ đúng (giả định độ cứng ngang đều) — ⚠️ mô hình đơn giản (không xét tương tác đất-cọc ngang) |
| Hệ số hiệu chỉnh K | `actual/rigid` (dòng 208-216)                                    | hiệu chỉnh predictor theo MCOC                       | ✅ đúng định nghĩa                                                                                                  |

**Quan trọng (ADR-001):** `rigid_cap` là **bộ DẪN HƯỚNG/dự báo nhanh**; nội lực CHÍNH THỨC do
**MCOC (oracle)** quyết định. validate_method: predictor (bệ cứng × K) vs MCOC = **0,0% lệch** trên
cùng bố trí. Vai trò này là đúng thiết kế, không phải thiếu sót.

---

## 4. `mechanics.py` — ràng buộc R1–R8

| RB                | Code                                                  | Tiêu chuẩn                                                          | Kết luận                                                                                                                               |
| ----------------- | ----------------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| R3 cận dưới 3d | `effective_min_spacing` = 3d (bắt buộc)           | "không bé hơn 3d" cọc ma sát (TCVN10304 Đ.8.13 dòng 2574-2583) | ✅ khớp                                                                                                                                 |
| R3 cận trên 6d  | `ENFORCE_SPACING_MAX=False` → chỉ cảnh báo mềm | TCVN10304**KHÔNG có** cận trên 6d                           | ✅**xử lý đúng & trung thực**: 6d là cận tìm kiếm/heuristic, không loại phương án (constants.py dòng 10-14 ghi rõ) |
| R4 mép bệ       | tim cọc → mép ≥ SAFE_D (≈ d)                     | quy tắc cấu tạo (lớp phủ ≥ d)                                   | ✅ hợp lý                                                                                                                              |
| R5/R5b/R6         | Pmax≤[Po], Pmin≥−[Ct], M≤[M]                      | so giới hạn thiết kế                                              | ✅ đúng (nội lực từ MCOC)                                                                                                           |
| R7/R8             | tắt ở lõi (bật ở`core/ext/`)                   | ngoài đề cơ bản                                                  | ✅ tài liệu hoá                                                                                                                       |

---

## Kết luận tổng

**Chứng minh KHỚP tiêu chuẩn (✅):** Rc,d (Đ.7.1.11) & hệ số γ; toàn bộ **cường độ vật
liệu** Rb/Rbt/Rs/Es (Bảng 7/13); **chọc thủng** cột & cọc (Đ.8.1.6); **uốn** As (Đ.8.1.2,
cốt đơn) + μ_min; **R3 cận dưới 3d**; **lực cọc bệ cứng thoả cân bằng tĩnh** (~1e-13);
khớp **MCOC 0,0%**. Có test tự động cho phần lớn các mục.

**Thiên AN TOÀN (⚠️ chấp nhận được):** cắt 1 phương lấy cận dưới 0,5·Rbt·b·h0; uốn cốt đơn.

**Cần KỸ SƯ xác nhận trước khi dùng cho hồ sơ thật (🔶/❓):**

1. **Lún** dùng cộng lún từng lớp 2:1 + β=0,8 (TCVN 9362), KHÔNG phải hệ số ảnh hưởng
   của TCVN 10304 Đ.7.4 → là **ước lượng**.
2. **Móng khối quy ước** thiếu chặn `a ≤ 2d` cho đất dính yếu (IL>0,6).
3. **γk** chỉ có 1 mặc định 1,4 — phải nhập đúng theo số cọc/cách xác định (1,2–1,75).
4. **STM** (z=0,9h0, a/h0<1) theo ACI/AASHTO, không trích được từ TCVN 5574.
5. **εb2=0,0035** trong ξ_R — xác nhận đúng giá trị/ca tải theo TCVN 5574.
6. Mô hình **lực ngang & SSI** là đơn giản hoá dẫn hướng (đã kiểm vs Hétényi/AASHTO ở
   `test_ssi_engine`), không thay phân tích cọc-đất đầy đủ.

> Lưu ý: refactor (Plan 023) KHÔNG đổi các công thức trên — đây là logic backend có sẵn,
> đã được rà đối chiếu tiêu chuẩn ở mức công thức.
