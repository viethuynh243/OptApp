"""
test_refine.py - Kiem thu END-TO-END vong lap toi uu Hop Den:
    input template -> mcoc_writer -> mcoc_runner (goi stub qua subprocess/stdin)
    -> parse ket qua -> refine_optimizer lap den khi khong tot hon.

Chay:  python tests/test_refine.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np
from core.blackbox import MCOCBlackbox
from core.refine_optimizer import run_refinement
from io_handlers.file_io import parse_input_file
from io_handlers.mcoc_writer import self_check

WORK = os.path.join(ROOT, "tests", "_work")
os.makedirs(WORK, exist_ok=True)
INPUT_FILE = os.path.join(WORK, "DEMO.txt")
STUB = os.path.join(ROOT, "tests", "mcoc_stub.py")


def build_demo_input():
    """Tao file input MCOC tong hop: be 7.2x13.2, 8 coc D1.2 (luoi 2x4, s=3.6m), Po=500T."""
    coords = [(-1.8, -5.4), (1.8, -5.4),
              (-1.8, -1.8), (1.8, -1.8),
              (-1.8,  1.8), (1.8,  1.8),
              (-1.8,  5.4), (1.8,  5.4)]
    lines = []
    lines.append("DEMO TOI UU COC")
    lines.append("8 2 0 0 0 0 0 0 7.2 13.2 1.8")
    lines.append("")
    # 2 to hop tai trong: Hx Hy P Mx My Mz  (don vi T, T.m)
    lines.append("83.0 105.0 2025.0 -1499.0 951.0 0.0")
    lines.append("20.0 0.0 2577.0 -94.0 170.0 0.0")
    # Khoi du lieu tung coc (16 dong/khoi, toa do o dong thu 13)
    for i, (x, y) in enumerate(coords, 1):
        lines.append("0.0")                                          # i    Lo
        lines.append(str(i))                                         # i+1
        lines.append("3001028 3001028 3001028 3001028 100 0 400")    # i+2  E,m
        lines.append("20.0")                                         # i+3  H
        lines.append("1.2")                                          # i+4  a
        lines.append("1.2")                                          # i+5  b
        lines.append("0.0")                                          # i+6  cday
        lines.append("1.131")                                        # i+7  Fo
        lines.append("0.1018")                                       # i+8  Jo
        lines.append("500")                                          # i+9  Po
        lines.append("33333.3")                                      # i+10 Co
        lines.append("16666.7")                                      # i+11 Ct
        lines.append("%.3f   %.3f" % (x, y))                         # i+12 X Y
        lines.append("0")
        lines.append("0")
        lines.append("0")
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
    return coords


def main():
    print("=" * 70)
    print(" TEST END-TO-END: Hop den MCOC (stub) + tinh chinh tung buoc")
    print("=" * 70)

    coords = build_demo_input()

    # 1) Parser doc dung file input?
    params, loads, name = parse_input_file(INPUT_FILE)
    got = np.asarray(params.get('original_coords', []))
    assert got.shape == (8, 2), "Parser doc sai toa do: %s" % got
    assert len(loads) == 2, "Parser doc sai to hop tai: %d" % len(loads)
    assert abs(params['D_PILE'] - 1.2) < 1e-6
    assert abs(params['P_LIMIT'] - 500.0) < 1e-6
    print("[OK] parse_input_file: 8 coc, 2 to hop tai, d=1.2, Po=500")

    # 2) Template tu sinh lai file -> doc nguoc phai khop
    ok, msg = self_check(INPUT_FILE, params['original_coords'])
    assert ok, "Self-check template FAIL: " + msg
    print("[OK] mcoc_writer self-check:", msg)

    # 3) Vong lap toi uu goi stub MCOC qua subprocess
    params['exe_path'] = STUB
    params['input_filepath'] = INPUT_FILE
    params['SAFE_D'] = params['D_PILE']
    params['P_TENSION'] = 250.0
    params['M_LIMIT'] = 0.0

    evaluator = MCOCBlackbox.make_real_evaluator(params)
    results = run_refinement(params, loads, evaluator)

    best = results['best']
    assert best is not None, "Khong tim duoc phuong an: " + results['reason']
    assert best['ok']
    assert best['pmax'] <= params['P_LIMIT'] + 1e-6
    n_files = len([f for f in os.listdir(evaluator.workdir) if f.endswith('_result.txt')])
    assert results['n_calls'] >= 2, "Vong lap chi goi MCOC %d lan?" % results['n_calls']
    assert n_files >= 1, "MCOC stub khong sinh file ket qua"

    print()
    print("KET QUA:", results['reason'])
    print("  Goc : %d coc, Pmax=%.2f T" % (results['original']['n'], results['original']['pmax']))
    print("  Toi uu: %d coc, Pmax=%.2f T, kich thuoc bao=%.2f" %
          (best['n'], best['pmax'], best['footprint']))
    print("  So lan goi MCOC: %d  |  File da sinh trong: %s" %
          (results['n_calls'], evaluator.workdir))
    print()
    print("TAT CA PASS.")


if __name__ == "__main__":
    main()
