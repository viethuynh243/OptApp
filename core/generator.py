"""
generator.py - Sinh tọa độ lưới cọc đối xứng cho hai kiểu bố trí.

    Kiểu A (trục giao)      :  o o o     Kiểu B (so le / hoa mai):  o o o
                               o o o                                 o o
                               o o o                                o o o

Mọi tọa độ được đặt đối xứng quanh TÂM bệ móng để tâm nhóm cọc trùng tâm
bệ. Module được optimizer/refine_optimizer gọi để dựng phương án ứng viên
trước khi chuyển sang mechanics kiểm tra ràng buộc.
"""

import numpy as np


# ============================================================================
# Sinh tọa độ lưới cọc
# ============================================================================
def generate_coords(nx, ny, sx, sy, layout_type):
    """
    Sinh tọa độ cọc cho cấu hình A (trục giao) và B (so le / hoa mai).

    Hệ tọa độ đặt gốc tại TÂM bệ móng, nên lưới cọc được sinh đối xứng
    quanh gốc: hàng/cột thứ k có tọa độ (k - (số_hàng - 1)/2) * khoảng_cách.
    Nhờ đó tâm nhóm cọc trùng tâm bệ, đảm bảo lực phân bố đều nhất.
    """
    coords = []
    if nx <= 0 or ny <= 0: return np.array(coords)

    if layout_type == "A":
        # Kiểu A: lưới chữ nhật đều nx x ny.
        # Công thức tâm đối xứng: x_i = (i - (nx-1)/2)*sx, y_j = (j - (ny-1)/2)*sy
        # => khi i chạy 0..nx-1, x đối xứng quanh 0 (vd nx=3: -sx, 0, +sx).
        for j in range(ny):
            y = (j - (ny - 1) / 2.0) * sy
            for i in range(nx):
                x = (i - (nx - 1) / 2.0) * sx
                coords.append([x, y])
    elif layout_type == "B":
        # Kiểu B (so le): hàng chẵn có nx cọc, hàng lẻ có nx-1 cọc.
        # Mỗi hàng tự đối xứng quanh x=0 qua offset = -(cols-1)/2 * sx,
        # nên hàng lẻ (ít hơn 1 cọc) tự động lệch sx/2 so với hàng chẵn
        # — tạo bố trí hoa mai mà không cần cộng offset riêng.
        for j in range(ny):
            y = (j - (ny - 1) / 2.0) * sy
            is_even_row = (j % 2 == 0)
            cols = nx if is_even_row else (nx - 1)
            if cols <= 0: continue

            offset = -(cols - 1) / 2.0 * sx
            for i in range(cols):
                x = offset + i * sx
                coords.append([x, y])

    return np.array(coords)
