"""
make_icon.py - Sinh icon đơn giản (.ico) cho bộ cài OptApp.

Vẽ một biểu tượng "mặt bằng cọc": nền bo góc xanh đậm (màu kỹ thuật), lưới
2x3 chấm tròn tượng trưng bố trí cọc, kèm chữ "OP". Xuất ra packaging/optapp.ico
với nhiều kích thước để Windows/Inno Setup dùng mượt ở mọi nơi (taskbar, shortcut).

Chạy: python packaging/make_icon.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "optapp.ico")

# Vẽ ở độ phân giải cao (256px) rồi để Pillow hạ kích thước cho các size còn lại.
SIZE = 256
BG = (15, 76, 129)        # xanh kỹ thuật đậm
GRID = (235, 240, 245)    # màu chấm cọc (gần trắng)
ACCENT = (255, 193, 7)    # vàng nhấn cho 1 cọc "chi phối"


def _rounded(draw, box, radius, fill):
    """Vẽ hình chữ nhật bo góc (tương thích Pillow cũ/mới)."""
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def build():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Nền bo góc
    _rounded(d, [8, 8, SIZE - 8, SIZE - 8], radius=44, fill=BG)

    # Lưới cọc 2 cột x 3 hàng (giống mặt bằng bố trí cọc)
    cols, rows = 2, 3
    x0, y0, x1, y1 = 70, 60, SIZE - 70, SIZE - 60
    r = 16
    for j in range(rows):
        for i in range(cols):
            cx = x0 + (x1 - x0) * (i / (cols - 1))
            cy = y0 + (y1 - y0) * (j / (rows - 1))
            color = ACCENT if (i, j) == (1, 0) else GRID
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    # Chữ "OP" nhỏ ở góc dưới
    try:
        font = ImageFont.truetype("arialbd.ttf", 52)
    except Exception:
        font = ImageFont.load_default()
    d.text((SIZE // 2, SIZE - 30), "OptApp", anchor="mm", fill=GRID, font=font)

    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(OUT, format="ICO", sizes=sizes)
    print("Da tao icon:", OUT)


if __name__ == "__main__":
    build()
