import numpy as np

def generate_coords(nx, ny, sx, sy, layout_type):
    """
    Sinh tọa độ cọc đối xứng qua gốc tọa độ.

    Kiểu A — Lưới trực giao:
        x_i = (i - (nx-1)/2) * sx,  y_j = (j - (ny-1)/2) * sy
        Tổng số cọc = nx × ny

    Kiểu B — Hoa mai (staggered):
        Hàng chẵn (j=0,2,...): nx cọc, x như Kiểu A
        Hàng lẻ  (j=1,3,...): (nx-1) cọc, lệch sx/2 so với hàng chẵn
        → Khoảng cách nhỏ nhất giữa các hàng liền kề = sqrt((sx/2)² + sy²)
    """
    coords = []
    if nx <= 0 or ny <= 0: return np.array(coords)

    if layout_type == "A":
        for j in range(ny):
            y = (j - (ny - 1) / 2.0) * sy
            for i in range(nx):
                x = (i - (nx - 1) / 2.0) * sx
                coords.append([x, y])
    elif layout_type == "B":
        for j in range(ny):
            y = (j - (ny - 1) / 2.0) * sy
            is_even_row = (j % 2 == 0)
            # Hàng chẵn: nx cọc; hàng lẻ: nx-1 cọc (lệch sx/2 tạo hoa mai)
            cols = nx if is_even_row else (nx - 1)
            if cols <= 0: continue
            offset = -(cols - 1) / 2.0 * sx  # căn giữa từng hàng riêng lẻ
            for i in range(cols):
                x = offset + i * sx
                coords.append([x, y])

    return np.array(coords)
