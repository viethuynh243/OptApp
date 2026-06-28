# Plan 018 — Engine tương tác đất–cọc (SSI) thuần NumPy + tab xem

## Bối cảnh
Mô hình bệ cứng (rigid_cap) chỉ phân phối lực DỌC TRỤC, chưa xét Hx/Hy/Mz, độ
lún, kết cấu bệ. Mục tiêu: bổ sung tương tác đất–cọc cho thiết kế sơ bộ.

**OpenSeesPy không khả dụng:** bản 3.8.0.0 build cho Python 3.12 (link
python312.dll), không nạp được trên Python 3.13 (lỗi DLL). Đã pivot sang engine
**thuần NumPy** — chạy mọi Python, đóng gói PyInstaller không rủi ro, miễn phí.

## Thành phần
1. **`core/ssi_engine.py`**
   - `axial_distribution(coords, load, ka)` — hệ bệ cứng 3 bậc tự do (lún w, xoay
     θx, θy). Khi ka ĐỀU ⇒ trùng `rigid_cap.pile_forces`; lại thỏa CHẶT cân bằng
     mômen ngay cả khi tích quán tính Ixy≠0 (rigid_cap bỏ Ixy → xấp xỉ). Trả thêm
     độ lún bệ + xoay.
   - `beam_on_winkler(EI, k_line, length, ...)` — dầm Euler–Bernoulli trên nền
     Winkler (FE 1D, lò xo nhất quán) → chuyển vị + mômen dọc thân cọc, M_max.
   - `pile_section`, `characteristic_beta`, và `analyze(coords, params, load)` tổng
     hợp: lực dọc + lún (axial) và cọc chịu ngang lớn nhất (lateral).
2. **`tests/test_ssi_engine.py`** — kiểm chứng độc lập:
   - Axial (ka đều, lưới đối xứng) == rigid_cap đến sai số máy.
   - Lưới lệch trục (Ixy≠0): SSI thỏa chặt cân bằng, rigid_cap thì không.
   - Winkler dầm vô hạn tải điểm == Hetenyi: y=Pβ/2k, M=P/4β.
   - `analyze()` smoke (đủ/thiếu chiều dài cọc).
3. **UI** — Tab 1 thêm radio **“SSI (đất–cọc)”**; `plot_canvas.draw_ssi_view`
   vẽ 2 biểu đồ (chuyển vị & mômen theo độ sâu, kiểu LPILE) + tiêu đề tóm tắt
   Pmax/Pmin, lún bệ, H/y_đầu/M_max của cọc chịu ngang lớn nhất. Quy đổi tải
   Tấn→kN (×9.80665) cho khớp đơn vị E; hiện lại theo Tấn/mm/T·m.
4. Cập nhật ghi chú phạm vi mô hình (SSI bổ sung sơ bộ Hx/Hy/Mz + lún).

## Kiểm chứng
- `pytest` toàn bộ: **40 passed** (gồm 9 test SSI mới), không hồi quy.
- Render `draw_ssi_view` (savefig): biểu đồ đúng dạng cọc đầu ngàm (mômen ngàm
  đầu, đổi dấu, bướu dương, tắt dần) — hợp lý vật lý.
- py_compile + smoke dựng cửa sổ đầy đủ (menubar + radio) OK.

## Giới hạn & bước sau
- Cọc đứng giả thiết TÁCH dọc trục ⊥ ngang (sơ bộ); chưa ghép 3D đầy đủ.
- Lò xo nền TUYẾN TÍNH (subgrade reaction) — chưa p–y phi tuyến.
- **Chưa làm:** (a) hiệu ứng nhóm cọc (p-multiplier / hệ số tương tác Poulos),
  (b) kết cấu bệ (uốn/chọc thủng/strut–tie). Đây là 2 hạng mục mở rộng kế tiếp.
