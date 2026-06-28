# Plan 021 — Panel "Trụ địa chất & lún" + bộ số liệu demo cho mọi sample (v1.7→1.8)

## Mục tiêu
File MCOC không có số liệu cho LÚN (trụ địa chất) và THIẾT KẾ ĐÀI (tiết diện trụ).
Cho dev (không phải kỹ sư cầu) nhập được trong app + bộ số liệu mẫu để ra demo chuẩn.

## A — Panel nhập "Trụ địa chất & lún" (Tab 1, cột trái)
- `core/version.py` 1.7.0 → **1.8.0**.
- Khung mới (LabelFrame trong col1): **φ tb dọc cọc, độ sâu đáy đài, γ' tb trên đáy
  khối, lún giới hạn Sgh** + ô Text nhập **lớp đất dưới mũi cọc** (mỗi dòng `h, E, γ`).
- Nút **"Nạp số liệu địa chất demo"** (`_load_demo_geotech`) — tự chọn mẫu theo Lc
  (cọc dài d~1.2 vs cọc ngắn d~2.0).
- `get_params_dict` parse: `phi_tb, cap_depth, gamma_avg, S_LIMIT, soil_below[]`.
- **Lún móng khối quy ước (TCVN 10304 Đ.7.4)** hiện ngay trên tab **"SSI (đất–cọc)"**:
  khối B_qu×L_qu, S, Sgh, ĐẠT/KHÔNG (dùng N lớn nhất qua mọi tổ hợp — `draw_ssi_view`
  nhận thêm `loads`).

## B — Tài liệu số liệu demo: docs/SO_LIEU_DEMO.md
- 3 KIỂU trụ địa chất (A yếu / B trung bình / C tốt) — bảng h/γ/φ/c/E/SPT (TCVN 9362).
- Số liệu thiết kế đài (mác BT/thép, lớp bảo vệ) theo TCVN 5574.
- **Bảng áp dụng cho TẤT CẢ sample T1–T22**: 2 họ cọc (d1.2/Lc20/m400 — T1–T6,T22;
  d2.0/Lc12/m600 — T7–T14) + kiểu địa chất + cột bx×by gợi ý.
- Hướng dẫn nhập từng bước + kết quả demo đã verify.

## Kiểm chứng
- pytest **54 passed**; render SSI có dòng "Lún khối quy ước ... S=24mm/Sgh=80 → ĐẠT".
- Demo verify: **T1** đài ĐẠT (As=220 cm², chọc thủng η=0.72, khối 7.9×11.5m, S≈24mm);
  **T10** đài KHÔNG ĐẠT (η=1.89 — cột 3×8 quá nhỏ cho 34.900T → tool bắt đúng).

## Ghi chú
- `gamma_avg` để trống → cộng lún hết lớp (demo rõ); có γ' → lún nhỏ (đúng cọc sâu).
- Vẫn THIẾT KẾ SƠ BỘ: lún cộng lớp 2:1, chọc thủng bỏ số hạng mômen (tải đúng tâm).
