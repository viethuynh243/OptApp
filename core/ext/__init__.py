"""
core.ext - Gói MỞ RỘNG (tách biệt) cho OptApp.

Gói này chứa các tính năng mở rộng được phát triển trên nhánh riêng, CỐ Ý
KHÔNG sửa các module lõi cũ (core/nsga2_optimizer.py, core/constants.py,
io_handlers/mcoc_writer.py, core/blackbox.py...) để tránh nhập nhằng và giữ
nguyên hành vi chương trình cũ. Ba tính năng chính:

    1. BẬT ràng buộc R7 (lực ngang Hmax ≤ [H]) và R8 (tương tác P-M ≤ 1).
    2. Thay đổi ĐƯỜNG KÍNH cọc như một biến tối ưu (quét theo bảng đường kính,
       mỗi đường kính có sức chịu tải [Po]/[Ct]/[M] riêng), chấm bằng MCOC THỰC.
    3. Sau khi có phương án tối ưu, ĐỔI KÍCH THƯỚC bệ (L_X, L_Y) cho vừa khít
       theo TCVN 10304:2014 (cọc cách mép ≥ SAFE_D) rồi làm tròn thi công.

Quy ước đơn vị: giữ nguyên như lõi cũ — kích thước (m), lực (T), mômen (T.m).
"""
