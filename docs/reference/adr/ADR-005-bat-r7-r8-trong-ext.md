# ADR-005 — Bật R7/R8 trong luồng mở rộng, không sửa lõi

> **Mã:** OA-ADR-005 · **Trạng thái:** Đã chấp nhận (accepted) · **Ngày:** 2026-06-18

**Bối cảnh:** người dùng (2026-06-18) yêu cầu **bật R7 và R8**. Lõi đã có sẵn 2
cờ `ENABLE_LATERAL_CHECK` / `ENABLE_PM_INTERACTION` nhưng để tắt
([ADR-003](ADR-003-tat-r7-r8-o-loi.md)). Cần tránh nhập nhằng với chương trình cũ.

**Quyết định:** luồng mở rộng bật R7/R8 qua context manager
`core/ext/nsga2_ext.py::constraints_enabled(cfg)` — tạm gán cờ ở cấp module
(`core.nsga2_optimizer`, `core.mechanics`) rồi **khôi phục trong `finally`**.
KHÔNG sửa mã nguồn lõi, không rò trạng thái sang chương trình cũ.

**Hệ quả:** dùng đúng cơ chế lõi đã thiết kế; chương trình cũ vẫn thấy R7/R8 tắt.
R7 cần `[H] > 0`, R8 cần `[M] > 0` mới chặn (lấy theo bảng đường kính).

Liên quan: [Kiến trúc — Ràng buộc R1–R8](../ARCHITECTURE.md#ràng-buộc-r1r8) · [Gói mở rộng (ext)](../EXT_TOIUU_MO_RONG.md) · [ADR-003](ADR-003-tat-r7-r8-o-loi.md)
