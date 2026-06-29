# Nguồn tham khảo TCVN (để trích dẫn trong báo cáo & kiểm chứng công thức)

> **Mã:** OA-DOC-05 · **Phiên bản:** 1.0 · **Cập nhật:** 2026-06-29 · **Trạng thái:** Approved · **Căn cứ:** TCVN 10304:2014, TCVN 5574:2018, TCVN 9362:2012


> Tập hợp nguồn đã dùng khi rà & cài công thức (Plan 023/024, v1.10.0). Gồm bản trích
> trong kho (`words_dict/`) và nguồn trực tuyến đối chiếu. Khi convert PDF→MD có lỗi OCR
> ở một số công thức → đã kiểm chéo bằng keyword + nguồn web bên dưới.

## 1. Bản trích trong kho (words_dict/)
| Tài liệu | File | Điều/khoản dùng (số dòng) |
|---|---|---|
| TCVN 10304:2014 — Móng cọc | `words_dict/TCVN10304-2014.md` | 7.1.11 sức chịu tải thiết kế Rc,d (573-628); γ0/γn/γk (599-628); 7.4.2 lún cọc đơn (1995-2103); 7.4.3 lún nhóm cọc theo tương hỗ (2105-2172); 7.4.4 móng khối quy ước + a≤2d (2174-2245); 8.13 k/c cọc ≥3d (2574-2583); Se=β·N·l/EA, β=0,3–0,7 (1572-1581) |
| TCVN 5574:2018 — Kết cấu BTCT | `words_dict/TCVN5574-2018.md` | Bảng 7 Rb/Rbt (1666-1702); Bảng 13 Rs/Es (2650-2805); 8.1.2 uốn + ξ_R CT(31) (3403-3515); εb2=0,0035 (2250); 8.1.3 cắt Qb/φb2=1,5 (5166-5311); 8.1.6 chọc thủng h0/2 (6419-6945); μmin 0,1% (11887) |

## 2. Nguồn trực tuyến đối chiếu (đã nghiên cứu)
### TCVN 5574:2018 — BTCT
- Cắt cốt đai (Qb = φb2·Rbt·b·h0²/C, φb2=1,5; kẹp [0,5;2,5]·Rbt·b·h0):
  https://papanh.com/tinh-toan-cot-dai-chiu-cat-cau-kien-chiu-nen-tcvn-5574-2018/
  · https://betongminhngoc.com/tinh-toan-cot-dai-cho-dam/
  · https://vietcons.edu.vn/tinh-toan-cot-dai-chiu-cat-cua-dam-be-tong-cot-thep-tiet-dien-chu-nhat-theo-tcvn-5574-2018
- Toàn văn / vật liệu: https://www.rds.com.vn/TCXD1/TCVN5574-2018.pdf
  · https://caselaw.vn/van-ban-phap-luat/345138-tieu-chuan-quoc-gia-tcvn-5574-2018-...
  · https://ketcausoft.com/tracuu/thong-so-vat-lieu

### TCVN 10304:2014 — Móng cọc
- Sức chịu tải + hệ số γk theo số cọc:
  https://ebookxaydung.com/cac-phuong-phap-xac-dinh-suc-chiu-tai-cua-coc-trong-nen-dat/
  · https://www.kynangxaydung.com/2020/08/thiet-ke-xay-dung-sct-coc-10304.html
- Bản PDF tiêu chuẩn: https://www.phanvu.vn/Data/Sites/1/media/tieu-chuan/tcvn-10304.2014-tieu-chuan-thiet-ke-mong-coc.pdf
- Lún cọc đơn / nhóm cọc: https://thuvienketcau.com/tinh-lun-mong-coc/
  · https://www.studocu.vn/vn/document/.../chuong-73-tieu-chuan/76353708

### TCVN 9362:2012 — Lún nền (móng khối quy ước)
- Cộng lún từng lớp, β=0,8, vùng nén σz≤0,2σ'vz:
  https://opacontrol.com.vn/tcvn/tcvn-9362-2012/
  · https://caselaw.vn/van-ban-phap-luat/251558-tieu-chuan-quoc-gia-tcvn-9362-2012-...
  · https://thuvienketcau.com/tinh-lun-mong-coc/

### Cơ học đất — phân bố ứng suất Boussinesq/Newmark
- Hệ số ảnh hưởng ứng suất dưới góc/tâm móng chữ nhật (tâm = 4× góc):
  https://vulcanhammer.net/2020/01/29/analytical-boussinesq-solutions-for-strip-square-and-rectangular-loads/
  · https://www.engineeringenotes.com/soil-engineering/vertical-stress-in-soil-mass/theories-for-determining-vertical-stress-in-soil-mass/38741

## 3. Tham chiếu khác
- AASHTO LRFD / ACI 318 — mô hình giàn ảo (STM) đài sâu, p-multiplier nhóm cọc (các trị
  z=0,9h0, a/h0<1, p-mult): theo thực hành, KHÔNG phải trị số TCVN (xem `core/cap_design.py`).

> Lưu ý dùng: các trang bên thứ ba (papanh, betongminhngoc, vietcons, ebookxaydung,
> thuvienketcau, studocu...) chỉ để ĐỐI CHIẾU nhanh; trích dẫn chính thức trong hồ sơ phải
> dẫn theo BẢN TIÊU CHUẨN GỐC (TCVN 5574:2018, TCVN 10304:2014, TCVN 9362:2012).
