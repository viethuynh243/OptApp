# Plan 020 — Dựng mô hình ngang THẬT từ file MCOC (pp "m") + thiết kế lại layout

## A — Thiết kế lại layout Tab 1 (v1.6.0 → 1.7.0)
Phản hồi: kiểm soát số liệu cùng lúc, ô kết quả quá nhỏ, nút Chạy quá to, cửa sổ nhỏ.
- Cửa sổ mở **maximize** (`state('zoomed')`) + geometry 1560×960 + minsize.
- Panel trái nhập liệu chia **2 CỘT** (col1: Thông số/TCVN/Nền-đài; col2: Tải/Điều
  khiển/MCOC) → thấy mọi mục cùng lúc, giảm cuộn dọc.
- Nút "CHẠY TỐI ƯU HÓA" gọn lại (font 11→10, bỏ ipady).
- Ô "Kết quả Đánh giá" to hơn (height 12→18, weight 2→3, thêm cuộn ngang).
- Sash panel trái/phải đặt động ≈ 42% bề rộng (`_init_sash`, kẹp 560–820px) cho cân
  đối với cửa sổ mô phỏng.

## B — Parser đọc thêm Lc, Eb, m từ file MCOC
`io_handlers/file_io.py::parse_input_file` (nhánh TXT):
- Đọc **dòng vật liệu chung (dòng 3)**: Eb (T/m²) + **m** (hệ số nền, T/m⁴, cột 6).
- Đọc **chiều dài cọc Lc** = dòng `i+1` của khối cọc (H trong "Lo H Bpx...").
- `setdefault` để khối cọc không ghi đè Eb/m của dòng 3.
- Kiểm chứng T1_EXT.txt: D=1.2, Lc=20, Eb=3001028, m=400, Jo=0.102, 10 tổ hợp tải
  (đủ Hx/Hy/Mz), 6 cọc.

## C — Engine SSI dùng dữ liệu file + phương pháp "m" (TCVN 10304 Phụ lục A)
`core/ssi_engine.py`:
- Chuyển sang **hệ Tấn–m thuần** (E mặc định 2.96e6 T/m²); bỏ quy đổi kN.
- `analyze()` **ưu tiên EI=Eb·Jo, EA=Eb·Fo** của file (chính xác hơn tính từ d).
- Nền ngang: nếu file có **m** → `k(z)=m·z·d` (Cz=m·z, TCVN 10304 PL A); không có m →
  lò xo hằng `ks·d` (ks T/m³, dự phòng). Vẫn nhân p-multiplier nhóm cọc.
- `plot_canvas.draw_ssi_view` bỏ quy đổi kN; hiện nhãn mô hình nền (pp "m" / ks).
- Wiring: `process_multiple_files` lưu `self._file_params` (Eb, m, Jo, Fo, Lc, H đài)
  + tự điền ô Lc/H đài; `get_params_dict` hợp nhất vào dict engine.

## Kiểm chứng
- pytest: **54 passed** (thêm 2 test pp "m": dùng EI=Eb·Jo, model='m', và k(z) mềm ở
  đỉnh → chuyển vị đầu lớn hơn lò xo hằng tương đương).
- End-to-end từ T1_EXT.txt: model='m', m=400, EI=305467 T·m², Lc=20; **Pmax=518.3 T
  KHỚP giá trị MCOC thực ~519.6 T** (mỏ neo kiểm chứng dọc trục). y_đầu=7.4mm,
  M_max=112.3 T·m, lún bệ≈2.0mm. Render SSI view xác nhận biểu đồ + nhãn pp "m".

## Còn lại (2 bảng bổ sung — file MCOC KHÔNG có)
- Lún chính xác: cần **trụ địa chất** (E,γ,φ,c từng lớp) dưới mũi cọc.
- Thiết kế đài đầy đủ: cần **cột bx×by, mác BT/thép, lớp bảo vệ** (hồ sơ kết cấu trụ).
