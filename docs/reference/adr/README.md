# Quyết định kiến trúc (ADR) — chỉ mục

> **Mã:** OA-DOC-08 · **Phiên bản:** 1.0 · **Cập nhật:** 2026-06-29 · **Trạng thái:** Approved
> **Căn cứ:** nhật ký quyết định thiết kế OptApp (di cư từ vault Obsidian cũ).

Mỗi ADR ghi lại **một quyết định lớn** + bối cảnh, lựa chọn và hệ quả. Khi đảo
ngược hoặc thay đổi một quyết định, **thêm ADR mới** trỏ ngược lại thay vì sửa
ADR cũ (giữ dấu vết). Tất cả hiện ở trạng thái *Đã chấp nhận (accepted)*.

| ADR | Quyết định | Trạng thái |
|---|---|---|
| [ADR-001](ADR-001-mcoc-oracle-duy-nhat.md) | MCOC là oracle duy nhất, cấm xấp xỉ | accepted |
| [ADR-002](ADR-002-chon-nsga2.md) | Chọn NSGA-II làm engine chính | accepted |
| [ADR-003](ADR-003-tat-r7-r8-o-loi.md) | Tắt R7/R8 ở luồng lõi | accepted (bổ sung bởi ADR-005) |
| [ADR-004](ADR-004-batch-theo-mcoc.md) | Tab Hàng loạt theo đúng luồng MCOC | accepted |
| [ADR-005](ADR-005-bat-r7-r8-trong-ext.md) | Bật R7/R8 ở luồng mở rộng, không sửa lõi | accepted |
| [ADR-006](ADR-006-duong-kinh-coc-bien-toi-uu.md) | Đường kính cọc là biến tối ưu (MCOC chính xác) | accepted |
| [ADR-007](ADR-007-doi-kich-thuoc-be-theo-tcvn.md) | Thu kích thước bệ sau tối ưu theo TCVN | accepted |
| [ADR-008](ADR-008-co-so-thiet-ke-tcvn-11823.md) | **Chuyển cơ sở thiết kế sang TCVN 11823:2017** (thay TCVN 10304:2014) | định hướng — chưa thực hiện |

Liên quan: [Kiến trúc](../ARCHITECTURE.md) · [Gói mở rộng (ext)](../EXT_TOIUU_MO_RONG.md) · [Tham chiếu TCVN](../THAM_KHAO_TCVN.md)
