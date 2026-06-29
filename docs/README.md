# Bộ tài liệu OptApp — Tối ưu bố trí cọc móng cầu

> **Mã:** OA-DOC-00 · **Phiên bản:** 1.0 · **Cập nhật:** 2026-06-29 · **Trạng thái:** Approved

Tài liệu tổ chức theo vòng đời phần mềm (SDLC). Mỗi tài liệu có **mã số (OA-DOC-xx)**,
**phiên bản**, **ngày** và **trạng thái** ở đầu file — sửa nội dung thì tăng phiên
bản. Bắt đầu nhanh: [README gốc của repo](../README.md) và [Hướng dẫn sử dụng](guides/HUONG_DAN_SU_DUNG.md).

> ⚠️ **Định hướng lớn (2026-06-29):** chương trình sẽ **chuyển cơ sở thiết kế sang
> TCVN 11823:2017** (thay TCVN 10304:2014) — chỉnh sửa lớn ở pha tiếp theo. Mọi tài
> liệu dưới đây mô tả **trạng thái code hiện tại** (cơ sở TCVN 10304:2014). Xem
> [ADR-008](reference/adr/ADR-008-co-so-thiet-ke-tcvn-11823.md) và [Backlog M1](project/BACKLOG.md).

## 0. Cấu trúc — 3 nhóm

| Nơi | Chứa gì |
|---|---|
| [`guides/`](guides/) | **Người dùng** — hướng dẫn sử dụng, sổ tay vận hành, thuật ngữ |
| [`reference/`](reference/) | **Cách hoạt động (ít sửa)** — kiến trúc, thuật toán, phương pháp, tuân thủ TCVN, định dạng đầu ra, `adr/` |
| [`project/`](project/) | **Tiến trình** — backlog, kế hoạch test, số liệu demo, spike |
| [`../CHANGELOG.md`](../CHANGELOG.md) · [`../README.md`](../README.md) | Phát hành & tổng quan (ở gốc repo, theo quy ước GitHub) |

## 1. Bản đồ tài liệu

| Mã | Tài liệu | Nhóm | Trả lời câu hỏi |
|---|---|---|---|
| OA-DOC-01 | [reference/ARCHITECTURE.md](reference/ARCHITECTURE.md) | Kiến trúc | Hệ thống ghép từ module nào? Luồng MCOC, NSGA-II, R1–R8 ra sao? |
| OA-DOC-02 | [reference/BAO_CAO_THUAT_TOAN.md](reference/BAO_CAO_THUAT_TOAN.md) | Thuật toán | Thuật toán + 8 phép kiểm chứng trên dữ liệu MCOC thật |
| OA-DOC-03 | [reference/METHODOLOGY.md](reference/METHODOLOGY.md) | Phương pháp | Cơ sở phương pháp luận tối ưu (đầy đủ) |
| OA-DOC-03b | [reference/METHODOLOGY_TOM_TAT.md](reference/METHODOLOGY_TOM_TAT.md) | Phương pháp | Bản tóm tắt phương pháp |
| OA-DOC-04 | [reference/AUDIT_CONG_THUC_TCVN.md](reference/AUDIT_CONG_THUC_TCVN.md) | Tuân thủ | Công thức nào đã khớp TCVN, mục nào cần kỹ sư xác nhận |
| OA-DOC-05 | [reference/THAM_KHAO_TCVN.md](reference/THAM_KHAO_TCVN.md) | Tham chiếu | Nguồn & điều khoản TCVN dùng để trích dẫn |
| OA-DOC-06 | [reference/BAN_OUTPUT_CHUAN.md](reference/BAN_OUTPUT_CHUAN.md) | Đầu ra | Chuẩn định dạng file kết quả/báo cáo |
| OA-DOC-06b | [reference/BAO_CAO_KY_THUAT_MAU.md](reference/BAO_CAO_KY_THUAT_MAU.md) | Đầu ra | Mẫu báo cáo kỹ thuật |
| OA-DOC-07 | [reference/EXT_TOIUU_MO_RONG.md](reference/EXT_TOIUU_MO_RONG.md) | Kiến trúc | Gói tối ưu mở rộng (R7/R8 + đường kính + thu bệ) |
| OA-DOC-08 | [reference/adr/](reference/adr/) | Quyết định | Vì sao thiết kế thế này (ADR-001…008) |
| OA-DOC-09 | [guides/HUONG_DAN_SU_DUNG.md](guides/HUONG_DAN_SU_DUNG.md) | Người dùng | Dùng app thế nào (đầy đủ) |
| OA-DOC-09b | [guides/HUONG_DAN_NHANH.md](guides/HUONG_DAN_NHANH.md) | Người dùng | Bắt đầu nhanh với số liệu thật |
| OA-DOC-09c | [guides/SO_TAY_VAN_HANH.md](guides/SO_TAY_VAN_HANH.md) | Người dùng | Sổ tay toàn bộ chức năng |
| OA-DOC-09d | [guides/GLOSSARY.md](guides/GLOSSARY.md) | Người dùng | Thuật ngữ & ký hiệu |
| OA-DOC-10 | [project/KE_HOACH_TEST_MCOC.md](project/KE_HOACH_TEST_MCOC.md) | Kiểm thử | Kế hoạch test MCOC (test gì, cách nào) |
| OA-DOC-11 | [project/SO_LIEU_DEMO.md](project/SO_LIEU_DEMO.md) | Kiểm thử | Số liệu demo T1–T22 (ĐẠT/KHÔNG ĐẠT) |
| OA-DOC-12 | [project/BACKLOG.md](project/BACKLOG.md) | Quản trị | Vấn đề/cải tiến đang mở, định hướng lớn |
| OA-DOC-13 | [project/spike_parallel_mcoc.md](project/spike_parallel_mcoc.md) | Spike | Khảo sát song song hóa lời gọi MCOC |
| OA-DOC-14 | [project/MIGRATION_TCVN11823.md](project/MIGRATION_TCVN11823.md) | Kế hoạch | Migration cơ sở thiết kế sang **TCVN 11823:2017** (LRFD) — Pha 1: khảo sát & kế hoạch |

## 2. Quy ước cập nhật tài liệu

1. **Header chuẩn** — mỗi tài liệu mở đầu bằng một dòng trích dẫn:
   `> **Mã:** OA-DOC-xx · **Phiên bản:** x.y · **Cập nhật:** YYYY-MM-DD · **Trạng thái:** <Draft|Review|Approved|Living> · **Căn cứ:** <file nguồn>`.
2. **Đánh số phiên bản** — sửa lớn (thêm/bỏ mục): +1.0; sửa nhỏ (cập nhật số liệu/câu chữ): +0.1.
3. **Đối chiếu được** — mọi khẳng định phải chỉ về căn cứ kiểm tra được (file path,
   tên hàm, điều khoản TCVN) để rà lại bằng grep.
4. **Trung thực với code** — tài liệu mô tả đúng trạng thái phần mềm hiện tại; KHÔNG
   ghi "đã theo TCVN 11823" trước khi code thực sự chuyển đổi (xem [ADR-008](reference/adr/ADR-008-co-so-thiet-ke-tcvn-11823.md)).

> **Không nằm trong repo (chỉ lưu nội bộ):** thư mục `plans/` (thiết kế cá nhân),
> `mcoc_input_sample/` (dữ liệu nội bộ), `words_dict/` (bản trích tiêu chuẩn), và
> vault Obsidian cũ — đều đã đưa vào `.gitignore`. Nội dung ADR/thuật ngữ giá trị
> đã được di cư vào bộ tài liệu này.
