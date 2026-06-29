# Plan 025 — Chuyển mô hình sang TCVN 11823:2017 (LRFD) thống nhất

## Mục tiêu
Phát biểu **một mô hình tối ưu duy nhất, thống nhất** cho thiết kế móng cọc trụ cầu,
tuân theo **TCVN 11823:2017** (tiêu chuẩn thiết kế cầu đường bộ — bản Việt hóa AASHTO
LRFD). Bỏ cách dùng nhiều tiêu chuẩn rời (TCVN 10304:2014, 9362:2012, 5574:2018, trích
AASHTO trực tiếp) và bỏ các ràng buộc "bật/tắt". Phạm vi lần này: **chỉ tài liệu mô hình**
(không sửa code tính toán).

## Quyết định nền tảng
Đổi triết lý: **Hệ số an toàn (10304)** → **LRFD**: `Σ η·γ·Q ≤ φ·R_n`, kiểm theo các
trạng thái giới hạn Strength I / Service I / Extreme Event I. Việc này cũng **hợp nhất
phạm vi**: p-multiplier và giàn ảo (STM) — trước là "AASHTO ngoài phạm vi" — nay là nội
dung gốc của TCVN 11823.

## Ánh xạ tiêu chuẩn (cũ → TCVN 11823)
| Hạng mục | Cũ (bỏ) | Mới | Loại |
|---|---|---|---|
| Tải & tổ hợp | ad-hoc / TCVN 2737 | **11823-3** Bảng 3.4.1-1 | định nghĩa lại |
| Sức chịu cọc | 10304 Đ.7.1.11 `(γ0/γn)(Rck/γk)` | **11823-10** Đ.10.5.5.2.3 `φ·R_n` | đổi công thức |
| Hiệu ứng nhóm | AASHTO 10.7.2.4 | **11823-10** Đ.10.7.2.4 | đổi trích dẫn |
| Cọc chịu ngang | "pp m" 10304 PL A | **11823-10** Đ.10.7.3.12 (p-y) | đổi phương pháp |
| Lún | 10304 Đ.7.4 + 9362 (Boussinesq) | **11823-10** Đ.10.7.2.2 (móng tương đương) | đổi khung |
| Thiết kế đài | 5574:2018 (ξ_R, εb2) | **11823-5** Đ.5.5.4.2 (khối ứng suất CN, φ) | đổi công thức |
| STM | AASHTO/ACI tham khảo | **11823-5** (giàn ảo) | về nội bộ chuẩn |
| Khoảng cách min | 3D | **2.5D** (≥750mm), mép 225mm — 11823-10 Đ.10.7.1.2 | đổi trị số |

## Trị số chuẩn (AASHTO LRFD mà TCVN 11823 áp dụng — đối chiếu bản TCVN khi xuất hồ sơ)
- **Hệ số tải** (Bảng 3.4.1-1): Strength I `γDC=1.25/0.90, γDW=1.50/0.65, γLL=1.75`;
  Service I `1.0/1.0/1.0`; Extreme I `γEQ(LL)=0.50, EQ=1.0`. η=ηD·ηR·ηI ≥ 0.95.
- **Hệ số sức kháng**: cọc nén φc=0.45–0.80 (theo cách kiểm chứng thi công: tĩnh ~0.50,
  PDA/CAPWAP ~0.65, nén tĩnh ~0.75); nhổ φup=0.35–0.45; ngang φℓ=1.0; uốn φf=0.90;
  cắt φv=0.90; STM thanh chống/nút 0.70, thanh kéo 0.90; Extreme (địa kỹ thuật) φ=1.0.
- **Bê tông** (11823-5): uốn `Mn=As·fy(ds−a/2), a=As·fy/(0.85f'c·b)`; cắt 1 phương
  `Vc=0.083·β√f'c·bv·dv (MPa)`; cắt 2 phương `Vn=(0.17+0.33/βc)√f'c·b0·dv ≤ 0.33√f'c·b0·dv`.

## Mô hình thống nhất (tóm tắt — chi tiết ở MO_HINH_TOI_UU.tex)
- Biến: lưới đối xứng (t,nx,ny,sx,sy), D, Lc, đài (Bx,By,h), As.
- Mục tiêu: **chi phí công trình** C (cọc + đài); n là proxy chi phối.
- Ràng buộc: C1–C13 — mọi trạng thái giới hạn LRFD **luôn áp dụng**, gộp thành Θ
  (Σ tỉ số `ΣηγQ/(φRn)−1` vượt 1). Khả thi ⟺ Θ=0.
- Giải: NSGA-II + oracle MCOC + gieo hạt + cache + trần ngân sách.

## Phạm vi đã làm (Plan này)
- [x] `docs/MO_HINH_TOI_UU.tex` — viết lại theo LRFD thống nhất.
- [x] `docs/THUAT_TOAN_PSEUDOCODE.md` — đồng bộ (Θ gộp tỉ số LRFD, tổ hợp tải theo 11823-3).
- [x] Plan này.

## Chưa làm (cần khi triển khai vào CODE — plan sau)
- [ ] `core/tcvn.py → tcvn11823.py`: φ·R_n thay (γ0/γn)/γk; lún móng tương đương.
- [ ] `core/cap_design.py`: khối ứng suất CN + φ (11823-5) thay ξ_R/εb2 (5574).
- [ ] `core/ssi_engine.py`: trích dẫn p-multiplier → 11823-10; ngang theo p-y.
- [ ] `core/ext/*`, `core/mechanics.py`: khoảng cách min 2.5D, mép 225mm; chú thích.
- [ ] UI: ô nhập φ/γ + chọn trạng thái giới hạn (thay ô γ0/γn/γk của 10304).
- [ ] `io_handlers/report_writer.py`, `ui/plot_canvas.py`: nhãn/nguồn 11823.
- [ ] Tests: viết lại trị số kỳ vọng theo LRFD.
- [ ] Đối chiếu bản chuẩn TCVN 11823 phần 3/5/10 để xác nhận φ, γ, số điều khoản.

## Nguồn tham khảo (web — AASHTO LRFD)
- AASHTO LRFD Bridge Design Specifications, Bảng 3.4.1-1 (tải); Đ.10.5.5.2.3 (φ cọc);
  Đ.10.7.1.2 (khoảng cách/mép); Đ.10.7.2.4 (p-multiplier); Đ.5.5.4.2 (φ bê tông).
- MnDOT LRFD Bridge Design Manual §3; NCHRP Report 507 (LRFD deep foundations).
