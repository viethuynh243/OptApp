import numpy as np

def generate_coords(nx, ny, sx, sy, layout_type):
    """
    Sinh tọa độ cọc cho cấu hình A và B.
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
            cols = nx if is_even_row else (nx - 1)
            if cols <= 0: continue
            
            offset = -(cols - 1) / 2.0 * sx
            for i in range(cols):
                x = offset + i * sx
                coords.append([x, y])
                
    return np.array(coords)
