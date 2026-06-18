"""_review_all.py - DUYỆT TOÀN BỘ file đầu vào trong mcoc_input_sample/.

Với mỗi file: nạp (parse) -> kiểm tra hình học phương án GỐC (R3 k/c, R4 mép bệ)
+ nội lực bệ-cứng (Pmax/Pmin theo từng tổ hợp) -> báo cờ bất thường. KHÔNG gọi
MCOC (dùng mô hình bệ cứng rigid_cap), nên chạy nhanh và duyệt được cả 38 file.

Chạy:  python tests/_review_all.py
"""
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from io_handlers.file_io import parse_input_file
from core import rigid_cap
from core.constants import effective_min_spacing, SPACING_MAX_FACTOR

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'mcoc_input_sample')


def min_pair_spacing(coords):
    """Khoảng cách tim-tim nhỏ nhất giữa mọi cặp cọc (m)."""
    c = np.asarray(coords, float)
    if len(c) < 2:
        return float('inf')
    best = float('inf')
    for i in range(len(c)):
        d = np.hypot(c[i + 1:, 0] - c[i, 0], c[i + 1:, 1] - c[i, 1])
        if len(d):
            best = min(best, float(d.min()))
    return best


def review(path):
    name = os.path.basename(path)
    flags = []
    try:
        params, loads, proj = parse_input_file(path)
    except Exception as e:
        return {'name': name, 'error': 'PARSE: %s' % e, 'flags': ['PARSE_FAIL']}

    coords = params.get('original_coords') or []
    n = len(coords)
    d = params.get('D_PILE') or 0.0
    Lx = params.get('L_X') or 0.0
    Ly = params.get('L_Y') or 0.0
    Po = params.get('P_LIMIT') or 0.0
    nloads = len(loads)

    if n == 0:
        flags.append('NO_COORDS')
    if nloads == 0:
        flags.append('NO_LOADS')

    pmax = pmin = 0.0
    smin = float('inf')
    edge_ok = True
    if n > 0 and nloads > 0:
        c = np.asarray(coords, float)
        P = rigid_cap.forces_all_loads(c, loads)
        pmax = float(P.max()); pmin = float(P.min())
        smin = min_pair_spacing(c)
        # R3 cận dưới (3d) — cận trên 6d không áp cho bố trí GỐC tự do
        s_min_req = effective_min_spacing(params)
        if smin < s_min_req - 1e-3:
            flags.append('R3_min(%.2f<%.2f)' % (smin, s_min_req))
        # R4 mép bệ: tim cọc cách mép >= d
        if Lx > 0 and Ly > 0:
            mx = float(np.max(np.abs(c[:, 0]))); my = float(np.max(np.abs(c[:, 1])))
            if mx + d > Lx / 2 + 1e-3 or my + d > Ly / 2 + 1e-3:
                edge_ok = False
                flags.append('R4_edge')
        # R5 nén so với [Po] file (chỉ tham khảo — [Po] file là mặc định)
        if Po > 0 and pmax > Po + 1e-3:
            flags.append('Pmax>Po_file(%.0f>%.0f)' % (pmax, Po))

    return {'name': name, 'proj': proj, 'n': n, 'd': d, 'Lx': Lx, 'Ly': Ly,
            'Po': Po, 'nloads': nloads, 'pmax': pmax, 'pmin': pmin,
            'smin': smin, 'flags': flags}


def main():
    files = sorted(f for f in os.listdir(DIR) if f.lower().endswith('.txt'))
    print('Duyet %d file trong %s\n' % (len(files), DIR))
    hdr = ('%-14s %-5s %4s %5s %7s %7s %6s %9s %9s %7s  %s'
           % ('FILE', 'NTH', 'n', 'd', 'Lx', 'Ly', '[Po]',
              'Pmax', 'Pmin', 'smin', 'CO BAT THUONG'))
    print(hdr)
    print('-' * len(hdr))
    n_flagged = 0
    by_flag = {}
    for f in files:
        r = review(os.path.join(DIR, f))
        if r.get('error'):
            print('%-14s  !! %s' % (r['name'], r['error']))
            n_flagged += 1
            continue
        fl = r['flags']
        if fl:
            n_flagged += 1
            for k in fl:
                key = k.split('(')[0]
                by_flag[key] = by_flag.get(key, 0) + 1
        print('%-14s %-5d %4d %5.2f %7.2f %7.2f %6.0f %9.1f %9.1f %7.2f  %s'
              % (r['name'], r['nloads'], r['n'], r['d'], r['Lx'], r['Ly'],
                 r['Po'], r['pmax'], r['pmin'], r['smin'],
                 ', '.join(fl) if fl else 'OK'))
    print('-' * len(hdr))
    print('\nTong: %d file | %d file co co canh bao' % (len(files), n_flagged))
    if by_flag:
        print('Thong ke co:', ', '.join('%s=%d' % (k, v) for k, v in sorted(by_flag.items())))


if __name__ == '__main__':
    main()
