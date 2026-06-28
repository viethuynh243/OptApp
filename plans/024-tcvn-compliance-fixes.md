# Plan 024 — Khắc phục 6 mục 🔶 trong audit công thức TCVN

> Nguồn: `docs/AUDIT_CONG_THUC_TCVN.md` (2026-06-28). Mỗi mục dưới đây là điểm mà
> code dùng phương pháp đơn giản/thực hành, CHƯA tuân thủ-đầy-đủ TCVN 10304:2014 /
> 5574:2018, hoặc cần xác nhận trị số.

## ⚠️ NGUYÊN TẮC CHUNG (khác Plan 023)
- Plan 023 **giữ nguyên hành vi**. Plan này **CỐ Ý ĐỔI KẾT QUẢ TÍNH** ở một số mục →
  **golden `_ui_regression` + một số unit test SẼ đổi**; chỉ `--update` golden khi đã
  xác nhận thay đổi là đúng chủ đích, kèm ghi rõ trong commit.
- **Cần KỸ SƯ kết cấu/địa kỹ thuật duyệt** công thức/trị số trước khi coi là "đúng chuẩn".
- Ưu tiên thiết kế **giữ mặc định = hành vi cũ**, bật cái mới qua **cờ/đầu vào** để
  không phá phương án người dùng đang chạy. Mỗi mục **1 commit**, chạy lại 3 cổng an toàn.
- Mỗi mục bổ sung/điều chỉnh **unit test** chứng minh công thức mới khớp tính tay.

---

## P1 — Minh bạch hoá (rủi ro THẤP, KHÔNG đổi số, làm trước)

### 024-1. Ghi rõ "Lún = ước lượng theo TCVN 9362", không phải Đ.7.4
- **Vấn đề:** `tcvn.settlement` dùng cộng lún 2:1 + β=0.8 (TCVN 9362), không phải hệ số
  ảnh hưởng của TCVN 10304 Đ.7.4. Báo cáo hiện chưa nói rõ điều này.
- **Sửa:** trong `io_handlers/report_writer.py` (mục lún, ~dòng 297-315) và nhãn tab SSI/lún
  ở GUI: thêm câu "Phương pháp: cộng lún từng lớp 2:1, β=0,8 (TCVN 9362) — ƯỚC LƯỢNG,
  không phải hệ số ảnh hưởng Đ.7.4 TCVN 10304." Sửa docstring `tcvn.settlement` cho nhất quán.
- **Đổi số?** Không. **Verify:** 3 cổng PASS (golden không đổi). **Effort:** S.

### 024-2. Ghi rõ STM theo ACI/AASHTO (không phải TCVN 5574)
- **Vấn đề:** `cap_design.stm_tie` (z=0,9h0, deep a/h0<1) là thực hành ACI/AASHTO.
- **Sửa:** comment trong `core/cap_design.py:104-113` + nhãn kết quả STM ("tham khảo ACI 318
  / AASHTO LRFD — TCVN 5574 chỉ nêu STM cho cấu kiện ngắn, không định lượng a/h0, z").
  Cân nhắc đưa `z_factor` và ngưỡng `a/h0` thành hằng số module có chú thích để dễ override.
- **Đổi số?** Không. **Effort:** S.

### 024-3. Xác nhận εb2 trong ξ_R
- **Vấn đề:** `materials()` dùng εb2=0.0035 (EPS_B2). Bản trích 5574 nêu ε0b=0,002 (đỉnh) +
  dài hạn 0,0042–0,0056; chưa thấy 0,0035 tường minh cho ξ_R.
- **Sửa:** ĐỌC điều khoản ξ_R của TCVN 5574:2018 (mục cấu kiện chịu uốn 8.1.2.x) trong
  `words_dict/TCVN5574-2018.md`. Nếu chuẩn cho **bảng ξ_R theo nhóm thép** → dùng bảng đó;
  nếu cho công thức với εb2 cụ thể → cập nhật EPS_B2 + ghi rõ số dòng tiêu chuẩn vào comment.
  Nếu 0,0035 đúng → chỉ thêm trích dẫn.
- **Đổi số?** Có thể (nếu εb2 khác) → cập nhật test_cap_design + golden có chủ đích.
  **Quyết định cần:** giá trị/cách lấy ξ_R theo đúng 5574. **Effort:** S–M.

---

## P2 — Đổi hành vi CÓ KIỂM SOÁT (sau cờ/đầu vào, mặc định giữ cũ)

### 024-4. Chặn `a ≤ 2d` cho móng khối quy ước khi đất dính yếu (IL>0,6)
- **Vấn đề:** `tcvn.equivalent_block` (dòng 152) `spread=2·Lc·tan(φ/4)` KHÔNG áp chặn
  "a ≤ 2d khi dưới mũi là đất dính IL>0,6" (TCVN 10304 dòng 2182-2188). Bỏ chặn → nới
  khối quá lớn → p_gl nhỏ → lún nhỏ giả (thiên KHÔNG an toàn ở ca đất yếu).
- **Sửa:** thêm đầu vào tuỳ chọn `soft_clay_below` (checkbox GUI "đất dính yếu IL>0,6 dưới
  mũi", mặc định TẮT). Khi bật: `a_side = min(Lc·tan(φ/4), 2*d)` (chặn theo từng bên),
  `spread = 2*a_side`. Khi tắt: giữ công thức cũ.
- **Đổi số?** Chỉ khi người dùng bật cờ (mặc định không đổi). **Verify:** unit test
  `test_equivalent_block` thêm ca soft-clay (a bị chặn 2d); golng không đổi (mặc định off).
  **Quyết định cần:** UI đặt cờ ở panel "Trụ địa chất & lún". **Effort:** M.

### 024-5. Hướng dẫn chọn γk theo số cọc / cách xác định
- **Vấn đề:** chỉ 1 mặc định γk=1.40. TCVN 10304 (dòng 611-628) cho γk = 1,4 / 1,55 /
  1,65 / 1,75 theo số cọc (≥21 / 11–20 / 6–10 / 1–5) và khác cho thử tải tĩnh / cọc đơn.
- **Sửa:** thêm `tcvn.resolve_gamma_k(n_piles, by_static_test=False, single_pile=False)`
  trả γk đúng bảng; UI panel TCVN thêm chế độ "γk tự theo số cọc" (mặc định) bên cạnh ô
  nhập tay hiện có (`var_gk`). `params.py` truyền `n_piles` (từ phương án) để suy γk khi
  người dùng không nhập tay. Ô nhập tay **luôn được ưu tiên** nếu có.
- **Đổi số?** Có (γk đổi theo số cọc thay vì luôn 1,4) → **golden đổi có chủ đích**;
  thêm `test_resolve_gamma_k` khớp bảng tiêu chuẩn.
- **Quyết định cần:** giá trị trong/ngoài ngoặc (thử tải tĩnh vs tính toán) — xác nhận
  dùng cột nào mặc định (đề xuất: cột "tính toán" = ngoài ngoặc). **Effort:** M.

---

## P3 — Lớn, cần tiêu chuẩn đầy đủ + kỹ sư (tách giai đoạn sau)

### 024-6. (TUỲ CHỌN) Triển khai lún theo hệ số ảnh hưởng TCVN 10304 Đ.7.4
- **Vấn đề:** muốn tuân thủ-đầy-đủ Đ.7.4 thay vì ước lượng 9362.
- **Sửa:** đọc CT(31)-(39) + bảng hệ số ảnh hưởng α_i,j trong `words_dict/TCVN10304-2014.md`
  (dòng ~quanh 2174-2245 và Phụ lục), cài hàm `settlement_10304(...)` song song; cho người
  dùng chọn "phương pháp lún: 9362 (nhanh) / 10304 Đ.7.4 (đầy đủ)". GIỮ 9362 làm mặc định
  cho tới khi kỹ sư duyệt phương pháp mới.
- **Rủi ro:** cao (nhiều tham số đất, dễ sai bảng α). **Cần kỹ sư địa kỹ thuật.**
- **Đổi số?** Chỉ khi chọn phương pháp mới. **Effort:** L. **Khuyến nghị:** làm sau cùng,
  hoặc chỉ khi có yêu cầu hồ sơ thật.

### 024-7. (TUỲ CHỌN) Nâng mô hình cọc chịu ngang/SSI cho hồ sơ
- `rigid_cap.horizontal_forces` (Hx/n…) là dẫn hướng; `ssi_engine` đã có Winkler/“m”.
  Nếu cần kết quả ngang dùng cho hồ sơ → thống nhất nguồn lực ngang về `ssi_engine` (pp “m”
  TCVN 10304 Phụ lục A) thay vì chia đều. **Effort:** L, cần kỹ sư.

---

## Thứ tự đề xuất
1. **P1 (024-1,2,3)** trước — minh bạch, gần như không rủi ro; 024-3 có thể chốt luôn εb2.
2. **P2 (024-4,5)** — đổi số có kiểm soát; cần chốt 2 quyết định nhỏ (UI cờ đất yếu; cột γk).
3. **P3 (024-6,7)** — chỉ khi cần tuân thủ-đầy-đủ cho hồ sơ; cần kỹ sư chuyên ngành.

## Cổng an toàn (sau MỖI mục)
```
python -m pytest -q
python tests/_ui_regression.py 2>/dev/null     # golden: P1 không đổi; P2/P3 đổi CÓ CHỦ ĐÍCH
python tests/_smoke_full.py 2>/dev/null
```

## Trạng thái — DONE (2026-06-28, v1.10.0)
- **024-1,2 (minh bạch)**: DONE — báo cáo ghi rõ phương pháp lún; STM ghi nguồn ACI/AASHTO.
- **024-3 (ξ_R/εb2)**: DONE — xác nhận khớp CT(31)+εb2=0,0035 (đối chiếu dòng 3469-3487 & 2250 + web); thêm trích dẫn, không đổi số.
- **024-4 (chặn 2d)**: DONE — `equivalent_block` chặn a≤2d khi `soft_clay_below`; checkbox GUI (mặc định tắt). Test `test_equivalent_block_2d_cap`.
- **024-5 (γk)**: DONE — `resolve_gamma_k` theo bảng số cọc; auto khi có `n_piles`, ô nhập tay ưu tiên. Test `test_resolve_gamma_k_table`.
- **024-6 (lún)**: DONE — `S=Se+S_khối`, Boussinesq tại tâm, β=0,8, 0,2σ'vz; theo Đ.7.4.4 + TCVN 9362. Test `test_settlement_includes_Se_and_boussinesq`.
- **Cắt 1 phương**: DONE — Qb=1,5·Rbt·b·h0²/C + nén dải 0,3·Rb·b·h0. Test `test_oneway_shear_*`.
### P3 — cập nhật 2026-06-28
- **024-7 (lực ngang pp "m")**: **DONE** — báo cáo thêm **Mục 6c** gọi `ssi_engine.analyze`
  (pp "m", k=m·z·d, TCVN 10304 Phụ lục A) hiển thị H_cọc/chuyển vị đầu cọc/M_max/β cho
  tổ hợp ngang bất lợi; R7 vẫn là kiểm sàng lọc. `ssi_engine` đã kiểm vs Hétényi/AASHTO.
- **024-6 (lún đầy đủ Đ.7.4.3 — hệ số tương hỗ δij)**: **KHÔNG cài (chặn có chủ đích)**.
  Lý do: công thức 7.4.2/7.4.3 (CT 31–39) trong `words_dict` BỊ LỖI OCR; đã thử mọi nguồn
  (web search secondary không có hệ số; oxyz.vn chết DNS; PDF chính thức phanvu.vn khóa
  mật khẩu/FlateDecode không đọc được). Đoán hệ số sẽ tạo số lún SAI → vi phạm yêu cầu
  "đảm bảo chính xác". **Phương pháp móng khối quy ước Đ.7.4.4 (đã cài, v1.10.0) là LỰA
  CHỌN HỢP LỆ theo Đ.7.4.1 cho nhóm cọc** — đủ dùng. Khi có bản TCVN searchable/ảnh rõ
  của 7.4.2-7.4.3, sẽ cài `settlement_interaction()` song song (G≈0,4·E0, kν=2,0 theo
  chú thích chuẩn để giảm input). Nguồn lưu tại `docs/THAM_KHAO_TCVN.md`.

Đối chiếu nguồn: TCVN 5574 cắt φb2=1,5 + chặn [0,5;2,5]; TCVN 9362 β=0,8 + 0,2σ'vz;
Boussinesq tâm=4×góc — đã xác nhận qua web (papanh/betongminhngoc/ebookxaydung,
vulcanhammer, TCVN 9362 studocu/opacontrol). pytest 58 passed; golden UI không đổi.
