# Tóm tắt Phương pháp Tối ưu hóa Móng Cọc

Dưới đây là tóm tắt ngắn gọn 4 bước cốt lõi trong thuật toán của chương trình:

## 1. Mục tiêu
Tìm cấu hình cọc có **số lượng ít nhất** nhưng vẫn đảm bảo tuyệt đối các tiêu chuẩn chịu lực và thi công trên một kích thước bệ cho trước.

## 2. Sinh lưới (Grid Generation)
Sử dụng phương pháp quét cạn (Grid Search) có chọn lọc:
- **Kiểu lưới:** Quét 2 mô hình lưới là Trực giao (Kiểu A) và So le (Kiểu B).
- **Giới hạn không gian:** Khống chế khoảng cách tối đa giữa các cọc (sx, sy) để đảm bảo tim cọc ngoài cùng luôn cách mép bệ một khoảng an toàn (>= d).

## 3. Lõi Giả lập Cơ học (Mock Black-box)
Thay vì dùng mô hình phần tử hữu hạn chậm chạp, chương trình sử dụng phương pháp **Bệ Cứng + Hiệu chỉnh (Rigid Cap + Calibration)** để dự báo nội lực tốc độ cao:
1. **Tính bệ cứng:** Tính nội lực cọc (P, M) bằng công thức cơ học của móng tuyệt đối cứng (tốc độ < 1 mili-giây):
   ```text
   P_i = (N / n)  +  (Mx * y_i / Ix)  +  (My * x_i / Iy)
   ```
2. **Trích xuất sai số:** Tính Hệ số hiệu chỉnh (K) dựa trên kết quả của Phương án Gốc (nhằm khớp với bệ đàn hồi thực tế): 
   ```text
   K = P_thực_tế_midas / P_bệ_cứng
   ```
3. **Nội suy (Calibration):** Lấy nội lực bệ cứng của các lưới cọc mới sinh ra nhân với K. Phương pháp này giúp triệt tiêu sai số hệ thống, đưa kết quả dự báo bám sát độ uốn thực tế của móng đàn hồi (sai số xấp xỉ 0%).
   ```text
   P_dự_báo = P_mới_bệ_cứng * K
   ```

## 4. Xử lý Ràng buộc & Đề xuất
Từng cấu hình sau khi qua bộ giả lập sẽ bị loại ngay lập tức (`KHÔNG ĐẠT`) nếu vi phạm 1 trong các điều kiện sau:
- **R1, R2:** Lực nén / Nhổ vượt quá Giới hạn cho phép.
- **R3, R4:** Khoảng cách cọc vi phạm tiêu chuẩn thi công (3d đến 6d).
- **R5, R6:** Momen đầu cọc vượt Sức uốn cho phép.

**Đề xuất tối ưu:** Trong số các cấu hình `ĐẠT`, chọn phương án có số cọc ít nhất. Nếu không có phương án nào tiết kiệm hơn phương án thiết kế ban đầu, chương trình sẽ kiến nghị giữ nguyên **Phương án Gốc**.
