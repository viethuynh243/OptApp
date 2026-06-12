"""
mcoc_stub.py - MCOC Batch GIA LAP de kiem thu vong lap toi uu khong can MCOC that.

Hanh vi giong MCOC Batch (Command Line):
    1. Hoi ten file input qua stdin.
    2. Doc file, tinh noi luc coc (be cung * he so 1.07 gia lap FEM).
    3. Ghi file <ten>_result.txt cung thu muc, co bang BANG TONG KET NOI LUC.

Chay thu:  python tests/mcoc_stub.py  (roi go duong dan file input)
"""

import os
import re
import sys

_NUM = re.compile(r'^-?\d+\.?\d*(?:[eE][+-]?\d+)?$')
FEM_FACTOR = 1.07   # gia lap chenh lech FEM so voi be cung


def parse_input(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.read().splitlines()
    loads, coords = [], []
    singles = []        # cac dong 1 so (khoi du lieu coc dang moi-thong-so-1-dong)
    for ln in lines[3:]:
        parts = ln.split()
        if not parts or not all(_NUM.match(p) for p in parts):
            continue
        if len(parts) == 6:
            loads.append([float(p) for p in parts])
        elif len(parts) in (2, 5):
            # Dong toa do coc: 'X Y' hoac 'X Y a b c'
            coords.append((float(parts[0]), float(parts[1])))
        elif len(parts) == 1:
            singles.append(float(parts[0]))

    if not coords and singles:
        # Dang split: moi thong so 1 dong, khoi 16 gia tri/coc,
        # X = gia tri thu 13, Y = gia tri thu 14 cua khoi (offset 12, 13)
        try:
            nc = int(float(lines[1].split()[0]))
        except (ValueError, IndexError):
            nc = 0
        if nc > 0 and len(singles) % nc == 0:
            blk = len(singles) // nc
            if blk >= 14:
                for k in range(nc):
                    coords.append((singles[k * blk + 12], singles[k * blk + 13]))
    return loads, coords


def main():
    sys.stdout.write("CHUONG TRINH TINH KHONG GIAN MONG COC (STUB)\n")
    # Giong MCOC_Batch.exe: nhan duong dan file qua THAM SO dong lenh
    # (bo qua cac flag --out-dir, --quiet...); fallback: hoi qua stdin.
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    flags = sys.argv[1:]
    out_dir = None
    if '--out-dir' in flags:
        i = flags.index('--out-dir')
        if i + 1 < len(flags):
            out_dir = flags[i + 1]
            if out_dir in args:
                args.remove(out_dir)
    if args:
        fname = args[0].strip('"')
    else:
        sys.stdout.write("Nhap ten file so lieu: ")
        sys.stdout.flush()
        fname = sys.stdin.readline().strip().strip('"')
    if not os.path.isabs(fname):
        fname = os.path.abspath(fname)
    if not os.path.exists(fname) and os.path.exists(fname + ".txt"):
        fname += ".txt"

    loads, coords = parse_input(fname)
    n = len(coords)
    if n == 0 or not loads:
        sys.stdout.write("Loi: khong doc duoc so lieu.\n")
        sys.exit(1)

    cx = sum(x for x, _ in coords) / n
    cy = sum(y for _, y in coords) / n
    Ix = sum((y - cy) ** 2 for _, y in coords) or 1e-9
    Iy = sum((x - cx) ** 2 for x, _ in coords) or 1e-9

    pmax, pmin = -1e18, 1e18
    pos_max = (1, 1)
    pos_min = (1, 1)
    for li, (hx, hy, N, mx, my, mz) in enumerate(loads, 1):
        for pi, (x, y) in enumerate(coords, 1):
            p = (N / n + mx * (y - cy) / Ix + my * (x - cx) / Iy) * FEM_FACTOR
            if p > pmax:
                pmax, pos_max = p, (pi, li)
            if p < pmin:
                pmin, pos_min = p, (pi, li)

    # Momen dau coc gia lap (giam khi nhieu coc)
    mxm = 45.0 / n
    mym = 167.0 / n

    base = os.path.splitext(fname)[0]
    if out_dir:
        base = os.path.join(out_dir, os.path.basename(base))
    out = base + "_result.txt"
    with open(out, 'w', encoding='utf-8') as f:
        f.write("     TONG CONG TY TVTK GTVT\n\n")
        f.write("              CHUONG TRINH TINH KHONG GIAN MONG COC\n\n\n")
        f.write("            Ten cong trinh : STUB RUN\n\n\n")
        f.write("       Nc =  %d    Np =  %d\n\n\n" % (n, len(loads)))
        f.write("                                     BANG TONG KET NOI LUC\n\n")
        f.write("                 Coc   t.h     N         Qx        Qy        Mz        Mx        My\n\n")
        f.write("         Nmin      %-5d %-7d %-9.2f 0.0       0.0       0.0       %-9.2f %-9.2f\n"
                % (pos_min[0], pos_min[1], pmin, -mxm, -mym))
        f.write("         Nmax      %-5d %-7d %-9.2f 0.0       0.0       0.0       %-9.2f %-9.2f\n"
                % (pos_max[0], pos_max[1], pmax, mxm, mym))
        f.write("\n")
    sys.stdout.write("Da ghi ket qua: %s\n" % out)


if __name__ == "__main__":
    main()
