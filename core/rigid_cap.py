"""
rigid_cap.py - Mô hình BỆ CỨNG (Rigid Pile Cap): NGUỒN DUY NHẤT công thức nội lực cọc.

Giả thiết bệ cứng tuyệt đối: tải trọng quy về tâm nhóm cọc, mỗi cọc nhận lực dọc
trục theo công thức tuyến tính (nén/uốn 2 phương):
    P_i = N/n + (Mx - N*cy)*(y_i-cy)/Ix + (My - N*cx)*(x_i-cx)/Iy
trong đó (cx, cy) là tâm nhóm cọc, (Ix, Iy) là mômen quán tính nhóm cọc quanh tâm,
và mômen tải trọng được quy về tâm nhóm cọc (khử lệch tâm N*cy, N*cx).

Đơn vị: tọa độ theo m, tải trọng N theo lực (thường kN), mômen theo lực*m;
lực cọc trả về cùng đơn vị với N. Hiệu chỉnh về Tấn do tầng gọi đảm nhận.

Module này CHỈ dùng nội bộ để DẪN HƯỚNG / vẽ heatmap (dự báo nhanh); kết quả
nội lực chính thức luôn do MCOC quyết định. Đây là nơi DUY NHẤT đặt công thức bệ
cứng để tránh viết lặp ở nhiều nơi.
"""

import numpy as np
from core.constants import EPS


# ============================================================================
# Đặc trưng hình học nhóm cọc (tâm, mômen quán tính)
# ============================================================================
def group_props(coords):
    """Tính (cx, cy, Ix, Iy) của nhóm cọc.

    Đầu vào:
        coords : mảng (n, 2) tọa độ tim cọc (m).
    Trả về:
        cx, cy : tọa độ trọng tâm nhóm cọc (m).
        Ix     : mômen quán tính nhóm cọc quanh trục x, sum((y-cy)^2) (m^2).
        Iy     : mômen quán tính nhóm cọc quanh trục y, sum((x-cx)^2) (m^2).
    Chống chia 0: thay Ix/Iy bằng EPS khi nhóm cọc thẳng hàng (= 0).
    """
    coords = np.asarray(coords, dtype=float)
    cx = float(coords[:, 0].mean())
    cy = float(coords[:, 1].mean())
    # Ix, Iy: bình phương khoảng lệch so với tâm; "or EPS" tránh chia 0 khi cọc thẳng hàng
    Ix = float(np.sum((coords[:, 1] - cy) ** 2)) or EPS
    Iy = float(np.sum((coords[:, 0] - cx) ** 2)) or EPS
    return cx, cy, Ix, Iy


# ============================================================================
# Nội lực DỌC TRỤC cọc (nén / kéo) theo công thức bệ cứng
# ============================================================================
def pile_forces(coords, load, props=None):
    """Lực dọc trục từng cọc cho 1 tổ hợp tải -> mảng (n,).

    Đầu vào:
        coords : mảng (n, 2) tọa độ tim cọc (m).
        load   : dict tải trọng {'N','Mx','My'} quy về gốc tọa độ.
        props  : (cx,cy,Ix,Iy) tính sẵn; nếu None thì tự tính từ coords.
    Trả về:
        Mảng (n,) lực dọc trục mỗi cọc; dương = nén, âm = kéo (cùng đơn vị N).
    """
    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    if n == 0:
        return np.zeros(0)
    cx, cy, Ix, Iy = props if props is not None else group_props(coords)
    N = load.get('N', 0.0); Mx = load.get('Mx', 0.0); My = load.get('My', 0.0)
    # Quy mômen tải trọng về TÂM nhóm cọc (khử lệch tâm do hợp lực N đặt tại gốc)
    Mx_t = Mx - N * cy
    My_t = My - N * cx
    # Khoảng lệch của từng cọc so với tâm nhóm cọc
    dx = coords[:, 0] - cx
    dy = coords[:, 1] - cy
    # P_i = lực dọc do N chia đều + thành phần uốn quanh 2 trục
    return N / n + Mx_t * dy / Ix + My_t * dx / Iy


def forces_all_loads(coords, loads):
    """Ma trận lực dọc trục cho mọi tổ hợp tải -> (len(loads), n).

    props của nhóm cọc tính 1 lần rồi dùng lại cho tất cả tổ hợp tải.
    """
    coords = np.asarray(coords, dtype=float)
    if len(coords) == 0 or not loads:
        return np.zeros((0, 0))
    props = group_props(coords)
    return np.array([pile_forces(coords, ld, props) for ld in loads])


# ============================================================================
# Trích xuất giá trị bất lợi từ ma trận lực dọc trục
# ============================================================================
def pmax_pmin(coords, loads):
    """Trả về (Pmax, Pmin) trên mọi cọc x mọi tổ hợp tải (cùng đơn vị N)."""
    P = forces_all_loads(coords, loads)
    if P.size == 0:
        return 0.0, 0.0
    return float(P.max()), float(P.min())


def worst_case_forces(coords, loads):
    """Lực từng cọc của tổ hợp BẤT LỢI NHẤT (tổ hợp có Pmax lớn nhất).

    Trả về list lực dọc trục theo từng cọc cho tổ hợp đó.
    """
    P = forces_all_loads(coords, loads)
    if P.size == 0:
        return []
    # argmax theo trục cọc -> chọn tổ hợp có lực cọc lớn nhất
    return P[int(np.argmax(P.max(axis=1)))].tolist()


# ============================================================================
# Nội lực NGANG cọc (xoắn Mz + cắt Hx, Hy)
# ============================================================================
def polar_inertia(coords, props=None):
    """Mômen quán tính cực Ip = Ix + Iy (dùng cho lực xoắn Mz), m^2."""
    cx, cy, Ix, Iy = props if props is not None else group_props(coords)
    return (Ix + Iy) or EPS


def horizontal_forces(coords, load, props=None):
    """Lực ngang từng cọc từ Hx, Hy, Mz (cọc đứng độ cứng đều).

    Công thức (chia đều lực cắt + phân phối mômen xoắn theo Ip):
        Hxi = Hx/n - Mz*(y_i-cy)/Ip
        Hyi = Hy/n + Mz*(x_i-cx)/Ip

    Đầu vào:
        coords : mảng (n, 2) tọa độ tim cọc (m).
        load   : dict tải trọng {'Hx','Hy','Mz'}.
        props  : (cx,cy,Ix,Iy) tính sẵn; None thì tự tính.
    Trả về:
        (Hxi, Hyi) - hai mảng (n,) lực ngang theo phương x và y mỗi cọc.
    """
    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    if n == 0:
        return np.zeros(0), np.zeros(0)
    cx, cy, Ix, Iy = props if props is not None else group_props(coords)
    Ip = (Ix + Iy) or EPS
    Hx = load.get('Hx', 0.0); Hy = load.get('Hy', 0.0); Mz = load.get('Mz', 0.0)
    # Khoảng lệch của cọc so với tâm nhóm (để phân phối mômen xoắn Mz)
    dx = coords[:, 0] - cx
    dy = coords[:, 1] - cy
    return Hx / n - Mz * dy / Ip, Hy / n + Mz * dx / Ip


def hmax(coords, loads):
    """Lực ngang tổng hợp lớn nhất trên bất kỳ cọc nào, qua mọi tổ hợp tải.

    Với mỗi tổ hợp tính độ lớn vector sqrt(Hxi^2 + Hyi^2) cho từng cọc rồi
    lấy giá trị lớn nhất; trả về max qua tất cả tổ hợp.
    """
    coords = np.asarray(coords, dtype=float)
    if len(coords) == 0 or not loads:
        return 0.0
    props = group_props(coords)
    best = 0.0
    for ld in loads:
        Hxi, Hyi = horizontal_forces(coords, ld, props)
        best = max(best, float(np.sqrt(Hxi ** 2 + Hyi ** 2).max()))
    return best


# ============================================================================
# Tiện ích hình học và hiệu chỉnh
# ============================================================================
def min_spacing(coords):
    """Khoảng cách tim-tim nhỏ nhất giữa các cọc (m).

    Trả về inf nếu có ít hơn 2 cọc. Tính qua ma trận khoảng cách bình phương,
    bỏ qua đường chéo (khoảng cách cọc với chính nó = inf).
    """
    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    if n < 2:
        return float('inf')
    # Ma trận khoảng cách bình phương giữa mọi cặp cọc
    d2 = np.sum((coords[:, None, :] - coords[None, :, :]) ** 2, axis=2)
    d2[np.diag_indices(n)] = np.inf  # loại cặp cọc trùng chính nó
    return float(np.sqrt(d2.min()))


def calibration_factor(rigid_pmax, actual_pmax):
    """Hệ số hiệu chỉnh K = Pmax_thực / Pmax_bệ_cứng.

    Dùng để hiệu chỉnh dự báo bệ cứng theo kết quả MCOC thực tế.
    Trả về 1.0 nếu thiếu dữ liệu (chưa có Pmax thực hoặc bệ cứng ~ 0).
    """
    if rigid_pmax and rigid_pmax > EPS and actual_pmax:
        return actual_pmax / rigid_pmax
    return 1.0
