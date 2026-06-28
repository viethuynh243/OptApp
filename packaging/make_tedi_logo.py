"""
make_tedi_logo.py - Tạo logo TEDI (tái dựng) cho OptApp: blue "G" + red inverted
triangle + white "T". Xuất packaging/tedi_logo.png (512) và packaging/tedi.ico
(đa kích thước), đồng thời ghi đè packaging/optapp.ico để bộ cài dùng cùng logo.

Chạy: python packaging/make_tedi_logo.py

Lưu ý: đây là bản TÁI DỰNG từ hình tham chiếu (không trích được file gốc bạn dán).
Nếu có file logo TEDI chính thức, đặt vào packaging/tedi_logo.png là app sẽ dùng.
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1024                      # vẽ ở độ phân giải cao rồi thu nhỏ (mịn)
BLUE = (31, 120, 190, 255)
RED = (228, 32, 38, 255)
WHITE = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)


def build(size=S):
    img = Image.new("RGBA", (size, size), CLEAR)
    d = ImageDraw.Draw(img)
    cx, cy = size * 0.50, size * 0.52
    R = size * 0.40           # bán kính TRỤC của vòng G
    T = size * 0.115          # bề dày vòng
    inner = R - T / 2
    outer = R + T / 2
    ring_box = [cx - R, cy - R, cx + R, cy + R]
    full_box = [cx - outer - 2, cy - outer - 2, cx + outer + 2, cy + outer + 2]

    # Lớp 1: vòng G xanh
    d.ellipse(ring_box, outline=BLUE, width=int(T))
    # Lớp 2: cắt khe hở chữ G ở phía TRÊN-PHẢI (0°=Đông, dương=kim đồng hồ)
    d.pieslice(full_box, start=-56, end=-8, fill=CLEAR)
    # Lớp 3: lưỡi ngang (spur) của G — thanh xanh ngay dưới khe, chĩa vào tâm
    bar_h = T * 0.86
    d.rectangle([cx + inner * 0.08, cy - bar_h / 2, cx + outer, cy + bar_h / 2], fill=BLUE)
    # Lớp 4: đĩa trắng bên trong (phủ phần trong, kể cả nơi khe vừa cắt -> nền trắng)
    d.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], fill=WHITE)

    # Lớp 5: khối đỏ — thanh ngang trên (đỉnh T) + tam giác ngược, ngăn bởi khe trắng
    lx, rx = cx - inner * 0.60, cx + inner * 0.60
    top_y0, top_y1 = cy - inner * 0.60, cy - inner * 0.38
    d.rectangle([lx, top_y0, rx, top_y1], fill=RED)
    tri_top = cy - inner * 0.28
    tri_bot = cy + inner * 0.78
    d.polygon([(lx, tri_top), (rx, tri_top), (cx, tri_bot)], fill=RED)

    # Lớp 6: chữ "T" trắng — thân đứng cắt qua thanh ngang + phần trên tam giác
    stem_w = inner * 0.15
    d.rectangle([cx - stem_w / 2, top_y0 - 2, cx + stem_w / 2, cy + inner * 0.14], fill=WHITE)

    return img


def main():
    big = build(S)
    png = big.resize((512, 512), Image.LANCZOS)
    out_png = os.path.join(HERE, "tedi_logo.png")
    png.save(out_png)
    # .ico đa kích thước
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    out_ico = os.path.join(HERE, "tedi.ico")
    png.save(out_ico, sizes=ico_sizes)
    # Ghi đè optapp.ico (bộ cài đang trỏ tới) để icon EXE cũng là TEDI
    png.save(os.path.join(HERE, "optapp.ico"), sizes=ico_sizes)
    print("Da tao:", out_png, "+", out_ico, "+ optapp.ico")


if __name__ == "__main__":
    main()
