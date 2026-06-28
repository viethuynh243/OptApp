# Plan 022 — DEMO đầy đủ cho mọi sample + 3D sát thực tế + sửa lẹm chữ (v1.8→1.9)

## A — Nút "⚡ Nạp DEMO đầy đủ" (điền MỌI ô trống, cỡ theo tải file)
`_load_demo_geotech`: ngoài địa chất, nay điền cả **[Po]/[Ct]** (cỡ theo Pmax/Pmin
bệ cứng → R1/R2 đạt), **tiết diện cột**, và **TỰ TĂNG chiều cao đài H** để chọc
thủng đạt (giải h0 từ F_ult=Rbt·2(cb+ch+2h0)·h0 ≥ 1.15·Nmax). Chỉ điền ô TRỐNG.

→ Verify: **15/15 trụ T1–T22 đều ĐẠT** (R1, R2, chọc thủng η=0.32–0.70, uốn, lún).
Bảng số liệu đầy đủ đã ghi `docs/SO_LIEU_DEMO.md` (Mục 3) + ví dụ điền từng ô (Mục 0)
+ 5 case test KHÔNG ĐẠT (Mục 0bis).

## B — 3D sát thực tế hơn (draw_model_3d)
- Thêm **cột/trụ** trên đỉnh đài (khối bê tông) + nhãn.
- **Mặt đất** (mặt phẳng ngang đỉnh đài) + **dải đất quanh cọc** (kháng ngang pp m).
- **Lớp đất dưới mũi** (soil_below) vẽ ĐÚNG từ z_tip (trước đây sai từ đáy đài),
  alpha đậm hơn, **nhãn E từng lớp**.
- **Dấu "+" GỐC TỌA ĐỘ** trên mặt đất + trục tâm thẳng đứng (mảnh).
- Colorbar tách xa (pad 0.10) khỏi nhãn trục z; bỏ tight_layout → subplots_adjust;
  box_aspect zoom 0.84 + zlim gồm cột → hết "lẹm hình".

## C — Mặt bằng 2D: gốc tọa độ
- `_draw_base`: trục đối xứng qua gốc (nét đứt mảnh) + **dấu "+" O(0,0)**.

## D — Sửa LẸM CHỮ
- SSI: suptitle 9.5→8.0, top 0.84→0.82 (hết cắt 2 biên).
- Sash panel trái 0.42→**0.47** (kẹp 600–900) → khung "Điều Khiển Tối Ưu"/MCOC ở
  cột phải không bị cắt chữ.

## Kiểm chứng
- pytest **54 passed**; render mặt bằng (có O(0,0)), 3D (cột+đất+lớp+gốc), app
  (cột phải đủ chữ). version → **1.9.0**.
