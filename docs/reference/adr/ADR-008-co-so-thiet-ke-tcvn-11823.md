# ADR-008 — Chuyển cơ sở thiết kế sang TCVN 11823:2017

> **Mã:** OA-ADR-008 · **Trạng thái:** Đã duyệt định hướng — **CHƯA thực hiện** (proposed/accepted-direction) · **Ngày:** 2026-06-29

**Bối cảnh:** code hiện tại lấy **TCVN 10304:2014** (Móng cọc — thiết kế) làm cơ
sở: sức chịu tải cho phép `Rc,d`, ràng buộc allowable `Pmax ≤ [Po]`, lún theo
Đ.7.4.4 + TCVN 9362:2012, thiết kế đài theo TCVN 5574:2018. Chủ dự án yêu cầu
(2026-06-29) toàn bộ chương trình phải dựa trên **TCVN 11823:2017 — Thiết kế cầu
đường bộ** (bộ tiêu chuẩn theo triết lý **LRFD**, tương đương AASHTO LRFD; phần
móng cọc ở **TCVN 11823-10**).

**Quyết định:** lấy **TCVN 11823:2017** làm cơ sở thiết kế chính thức của chương
trình; TCVN 10304:2014 không còn là chuẩn áp dụng. Đây là **chỉnh sửa lớn toàn
bộ**, thực hiện ở pha tiếp theo (sau đợt dọn dẹp repo này).

**Hệ quả (phải làm ở pha migration):**
- Chuyển từ "sức chịu tải cho phép / hệ số riêng phần γ" sang **trạng thái giới
  hạn LRFD**: hệ số tải `γᵢ`, hệ số sức kháng `φ`, tổ hợp Strength I–V / Service I
  / Extreme Event.
- Viết lại `core/tcvn.py` (hoặc module mới) cho sức kháng `φ·Rn` theo TCVN 11823-10;
  cập nhật ràng buộc kiểm trong `core/mechanics.py` / `core/nsga2_optimizer.py`.
- Bổ sung hệ tổ hợp + hệ số tải LRFD ở lớp nhập liệu/UI.
- Rà thiết kế đài (`core/cap_design.py`) cho tương thích bê tông cốt thép cầu.
- Viết lại báo cáo/audit theo điều khoản TCVN 11823:2017/-10.

**Điều kiện tiên quyết:** có bản TCVN 11823:2017 (đặc biệt phần 10 — Móng và
phần 3 — Tải trọng & hệ số tải) ở dạng tra cứu được; kỹ sư kết cấu/địa kỹ thuật
xác nhận ánh xạ hệ số. **Không** sửa hồi tố tài liệu hiện hành thành "đã theo
11823" trước khi code chuyển đổi (tránh tài liệu sai lệch).

Liên quan: [Kế hoạch migration — Pha 1](../../project/MIGRATION_TCVN11823.md) · [Backlog M1](../../project/BACKLOG.md) · [Audit công thức TCVN](../AUDIT_CONG_THUC_TCVN.md) · [ADR-001](ADR-001-mcoc-oracle-duy-nhat.md)
