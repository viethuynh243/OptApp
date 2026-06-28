# Plan 019 — Đầy đủ & dùng thực tế: nhập liệu SSI, hiệu ứng nhóm cọc, thiết kế đài, logo TEDI

Mở rộng để app dùng được thực tế: bỏ dần các giới hạn "CHƯA xét Hx/Hy/Mz, nhóm
cọc, lún, kết cấu bệ". Toàn bộ FREE/open-source, không license trả tiền.

## A — Nhập liệu nền & đài + logo TEDI (v1.5.0 → 1.6.0)
- Khung "Nền & đài cọc" ở Tab 1: Lc, ks (mô đun nền), H đài, lớp bảo vệ a, cột
  bx×by, mác bê tông, nhóm thép, checkbox "xét hiệu ứng nhóm cọc". Wire vào
  `get_params_dict` (keys: pile_length, ks_soil, cap_thickness, cover, col_b,
  col_h, conc_grade, steel_grade, group_effect).
- **Logo TEDI**: `packaging/make_tedi_logo.py` tái dựng (G xanh + tam giác đỏ + T
  trắng) → `tedi_logo.png` + `tedi.ico` (+ ghi đè `optapp.ico`). Đặt icon cửa sổ
  (`iconbitmap`/`iconphoto` trong setup_ui) + icon EXE (OptApp.spec dùng tedi.ico,
  bundle file logo vào datas).
- View-mode radios chuyển sang HÀNG RIÊNG (5 chế độ: Mặt bằng / Điều kiện R1–R8 /
  3D / SSI đất–cọc / Thiết kế đài) — tránh tràn ngang.

## B — Hiệu ứng nhóm cọc (core/ssi_engine.py)
- `p_multiplier(row, s/D)` theo AASHTO LRFD Bảng 10.7.2.4-1 (3D: 0.70/0.50/0.35;
  5D: 1.00/0.85/0.70; nội suy 3D↔5D; ≥5D dùng giá trị 5D).
- `lateral_group_pmult(coords, d, load)` — phân hàng theo phương tải, hàng dẫn
  đầu = trước theo chiều đẩy; trả p-mult từng cọc.
- `group_settlement_ratio(n)` = n^0.5 (Poulos). `analyze()` nhân p-mult vào mô đun
  nền của cọc bất lợi + khuếch đại lún bệ → lún nhóm. Tab SSI hiện p-mult, số hàng,
  s/D, lún nhóm.

## C — Thiết kế kết cấu đài (core/cap_design.py) theo TCVN 5574:2018
- Cường độ Rb/Rbt/Rs đối chiếu `words_dict/TCVN5574-2018.md` (B25=14.5/1.05,
  B30=17.0/1.15; CB400-V Rs=350).
- `flexure_As` (Điều 8.1.2: α_m, ξ, ζ, As, kiểm ξ≤ξ_R, μ_min=0.1%); `punching_column`
  & `punching_pile` (Điều 8.1.6: F_b,ult=Rbt·u_m·h0, u_m tại h0/2); `oneway_shear`
  (Điều 8.1.3: Q_b,min=0.5·Rbt·b·h0); `stm_tie` (giàn ảo cho đài sâu a/h0<1).
- `design_cap(coords, params, loads)` lấy tổ hợp chi phối → uốn 2 phương, chọc
  thủng cột (trừ cọc trong tháp) + cọc, cắt 2 phương, cờ đài sâu. Tab "Thiết kế
  đài" hiện bảng kết quả có badge ĐẠT/KHÔNG ĐẠT.

## Kiểm chứng
- pytest: **52 passed** (thêm 4 test nhóm cọc + 8 test thiết kế đài; uốn khớp tính
  tay As≈15100 mm², chọc thủng η≈0.847).
- Render từng view (savefig) + chụp app: radio đủ 5 chế độ không tràn, icon TEDI
  ở thanh tiêu đề, nhãn phiên bản v1.6.0.

## Giới hạn còn lại (thiết kế SƠ BỘ)
- SSI tách dọc trục ⊥ ngang, nền Winkler tuyến tính; chọc thủng bỏ số hạng mô men
  (tải đúng tâm, thiên an toàn). Hồ sơ chi tiết vẫn cần MCOC/FEM đầy đủ.
