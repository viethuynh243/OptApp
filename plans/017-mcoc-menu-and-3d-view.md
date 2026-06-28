# Plan 017 — Menu kiểu MCOC + khung nhìn 3D mô hình + Tab 2 ba tab

## Mục tiêu
- Giao diện giống MCOC Python hơn (thanh menu, bố cục panel phải Tab 2).
- Trả lời yêu cầu "mô phỏng chi tiết hơn để thấy toàn bộ tổng thể của mô hình":
  thêm khung nhìn **3D** (đài + cọc + lớp đất + móng khối quy ước).
- Ràng buộc: **chỉ dùng tool FREE/open-source**, không thêm phụ thuộc nặng
  (matplotlib 3D đã có sẵn — không cần PyVista/Qt ở bước này).

## Thay đổi
1. **Phiên bản** — `core/version.py`: 1.4.0 → **1.5.0** (RELEASE_DATE 2026-06-28).
2. **Thanh menu** (`ui/main_window.py::_build_menu`) kiểu MCOC:
   - File: Thêm file (Ctrl+O) · Thêm thư mục (Ctrl+Shift+O) · Xoá danh sách · Thoát
   - Tính toán: Tính toán (Ctrl+Enter) · Dừng (Esc) · Mở thư mục kết quả
   - Trợ giúp: Hướng dẫn (F1) · Giới thiệu
   - Lệnh **nhận biết tab** (`_active_tab`): Tab 1 chạy tối ưu / Tab 2 chạy hàng loạt.
   - Cố ý **bỏ "Cài đặt pass…"** (OptApp không có), không thêm menu rỗng gây hiểu nhầm.
3. **Nhãn phiên bản** kiểu MCOC ở góc phải thanh trạng thái: `OptApp vX | Windows desktop`.
4. **Khung nhìn 3D** (`ui/plot_canvas.py::draw_model_3d`):
   - Radio thứ 3 ở Tab 1: Mặt bằng / Kiểm tra điều kiện / **3D (mô hình)**.
   - Vẽ đài (khối xám), cọc (cột tròn tô màu theo lực P — cùng thang màu mặt bằng),
     lớp đất từ `soil_below`, **móng khối quy ước** từ `core.tcvn.equivalent_block`.
   - Thiếu chiều dài cọc → dùng Lc minh hoạ + ghi rõ trong tiêu đề (degrade an toàn).
   - matplotlib 3D nhúng tkinter, kéo chuột để xoay; KHÔNG thêm thư viện.
5. **Tab 2 — panel phải 3 tab** theo MCOC: **Xuất kết quả / Báo cáo / spColumn**.
   - spColumn: chỉ **giống giao diện** (checkbox disabled + ghi chú "đang phát triển"),
     chưa làm chức năng xuất .cti.

## Kiểm chứng
- `python -m py_compile ui/main_window.py ui/plot_canvas.py core/version.py` — sạch.
- Smoke (cửa sổ ẩn): menubar = [File, Tính toán, Trợ giúp]; mọi handler tồn tại.
- Render 3D (savefig) cho cả 2 trường hợp đủ/thiếu dữ liệu — không lỗi, ảnh hợp lệ.
- Chụp app thật: radio 3D + nhãn phiên bản (Tab 1); 3 tab MCOC (Tab 2).

## Lộ trình tiếp theo (đã chốt hướng, free-only)
1. (đang ở đây) 3D bằng matplotlib — bản đẹp hơn: PyVista pop-out (tùy chọn).
2. **OpenSeesPy** — engine tương tác đất–cọc p–y/t–z/q–z (BNWF): cọc chịu ngang,
   moment thân cọc, lún thực; cắm vào seam `evaluator(coords)` của nsga2.
3. **pymoo** thay NSGA-II tự viết.
