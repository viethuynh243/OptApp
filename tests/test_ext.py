"""
test_ext.py - Kiem thu cac module MO RONG (core/ext) chay KHONG can MCOC.

Chay:  python tests/test_ext.py

Bao phu:
    1) pile_section: Fo=pi d^2/4, Jo=pi d^4/64 khop gia tri file MCOC mau.
    2) DiameterTable: sap xep, tra cuu, as_params gan dung gioi han theo d.
    3) mcoc_writer_ext: round-trip patch duong kinh tren file mau that.
    4) cap_resize: be vua khit + lam tron, coc van nam trong be (R4).
    5) orchestrator: quet duong kinh + R7/R8 bat + chon toan cuc + resize be
       (dung evaluator gia, khong goi MCOC). Kiem tra co bat/khoi phuc R7/R8.

So neo: d=1.2 -> Fo=1.1309733552923256, Jo=0.10178760197630929.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from core.ext.pile_section import (area, inertia, section_props,
                                   DiameterOption, DiameterTable)
from core.ext.config_ext import ExtConfig
from core.ext.cap_resize import recommend_cap_size, resize_cap
from core.ext.orchestrator import run_extended_optimization, material_cost
from core.ext import nsga2_ext
from core import nsga2_optimizer as _core
from io_handlers.file_io import parse_input_file
from io_handlers.mcoc_writer_ext import self_check_diameter

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "mcoc_input_sample", "T3_EXT.txt")


def test_pile_section():
    """Fo/Jo khop gia tri MCOC nhung trong file mau (d=1.2)."""
    Fo, Jo = section_props(1.2)
    assert abs(Fo - 1.1309733552923256) < 1e-12, Fo
    assert abs(Jo - 0.10178760197630929) < 1e-12, Jo
    assert abs(area(2.0) - np.pi) < 1e-12
    assert abs(inertia(2.0) - np.pi / 4.0) < 1e-12
    print("[OK] pile_section: Fo=%.16f Jo=%.16f" % (Fo, Jo))


def test_diameter_table():
    """DiameterTable sap xep tang dan + as_params gan dung gioi han."""
    t = DiameterTable([(1.5, 950, 100, 200, 50), {'d': 1.0, 'Po': 400},
                       DiameterOption(1.2, 600)])
    assert t.diameters() == [1.0, 1.2, 1.5], t.diameters()
    o = t.get(1.5)
    p = o.as_params({'D_PILE': 1.2, 'L_X': 6.0, 'L_Y': 9.6})
    assert p['D_PILE'] == 1.5 and p['SAFE_D'] == 1.5
    assert p['P_LIMIT'] == 950 and p['P_TENSION'] == 100
    assert p['M_LIMIT'] == 200 and p['H_LIMIT'] == 50
    print("[OK] diameter_table: d=%s" % t.diameters())


def test_writer_diameter():
    """Round-trip patch duong kinh tren file MCOC mau that."""
    params, _, _ = parse_input_file(SAMPLE)
    ok, msg = self_check_diameter(SAMPLE, params['original_coords'],
                                  params['D_PILE'], params['P_LIMIT'], 1.5, 850.0)
    assert ok, msg
    print("[OK] writer_diameter:", msg)


def test_cap_resize():
    """Be vua khit + lam tron; coc van nam trong be voi mep >= safe_d."""
    coords = [[-2.8, -3.6], [2.8, 3.6], [0.0, 0.0]]
    lx, ly = recommend_cap_size(coords, safe_d=1.2, round_to=0.1)
    # span_x = 5.6, +2*1.2 = 8.0 -> 8.0 ; span_y = 7.2 +2.4 = 9.6 -> 9.6
    assert abs(lx - 8.0) < 1e-9 and abs(ly - 9.6) < 1e-9, (lx, ly)
    # Kiem tra R4: max|coord| + safe_d <= L/2
    assert max(abs(c[0]) for c in coords) + 1.2 <= lx / 2 + 1e-9
    assert max(abs(c[1]) for c in coords) + 1.2 <= ly / 2 + 1e-9
    # Lam tron len 0.5 m: 8.0 (boi so cua 0.5) giu nguyen; 9.6 -> 10.0
    lx2, ly2 = recommend_cap_size(coords, safe_d=1.2, round_to=0.5)
    assert abs(lx2 - 8.0) < 1e-9 and abs(ly2 - 10.0) < 1e-9, (lx2, ly2)
    print("[OK] cap_resize: 0.1m -> %.2f x %.2f" % (lx, ly))


def _mock_factory(params_d, dia, loads):
    """Evaluator gia: Pmax = maxN/n (don vi T), khong goi MCOC.

    Khong phu thuoc dia.Po (suc chiu so sanh trong constraint), chi mo phong
    noi luc giam khi tang so coc. Mx/My = 0 (R6/R8 khong rang buoc o mock).
    """
    maxN = max((abs(l['N']) for l in loads), default=1000.0)

    def ev(coords):
        n = max(len(coords), 1)
        pmax = maxN / n
        return {'pmax': pmax, 'pmin': -0.05 * pmax, 'mxmax': 0.0, 'mymax': 0.0}
    return ev


def test_orchestrator():
    """Quet duong kinh + R7/R8 + chon toan cuc + resize be (evaluator gia)."""
    params, loads, _ = parse_input_file(SAMPLE)
    # Bang duong kinh: Po tang theo d; M/H = 0 de R6/R7/R8 khong chan o mock.
    table = DiameterTable([(1.0, 300.0), (1.2, 500.0), (1.5, 900.0)])
    cfg = ExtConfig(enable_R7=True, enable_R8=True, cap_round_to=0.1)

    # Truoc khi chay: co R7/R8 cua loi dang TAT
    assert _core.ENABLE_LATERAL_CHECK is False
    assert _core.ENABLE_PM_INTERACTION is False

    out = run_extended_optimization(
        params, loads, table, cfg=cfg, evaluator_factory=_mock_factory,
        pop_size=12, n_gen=6, seed=0, secondary='compact')

    # Sau khi chay: co R7/R8 phai duoc KHOI PHUC ve TAT (khong ro trang thai)
    assert _core.ENABLE_LATERAL_CHECK is False, "R7 chua khoi phuc!"
    assert _core.ENABLE_PM_INTERACTION is False, "R8 chua khoi phuc!"

    assert out['recommended'] is not None, "Khong tim duoc phuong an."
    rec = out['recommended']
    dwin = out['winner_diameter']
    cap = out['cap_report']
    # Chi phi thang phai la nho nhat trong cac duong kinh kha thi
    feas = [r for r in out['per_diameter'] if r['best']]
    assert out['winner']['cost'] == min(r['cost'] for r in feas)
    # Be moi khong lon hon be cu va coc nam trong be (R4)
    assert cap['new_LX'] <= cap['old_LX'] + 1e-9
    assert cap['new_LY'] <= cap['old_LY'] + 1e-9
    coords = np.asarray(rec['coords'], dtype=float)
    safe_d = cap['safe_d']
    assert np.max(np.abs(coords[:, 0])) + safe_d <= cap['new_LX'] / 2 + 1e-6
    assert np.max(np.abs(coords[:, 1])) + safe_d <= cap['new_LY'] / 2 + 1e-6
    # Be cua moi phuong an PHAI di theo phuong an do (so sanh tien hoa):
    #  - de xuat mang be DA THU (vi cfg.cap_resize mac dinh = True)
    assert abs(rec['cap_lx'] - cap['new_LX']) < 1e-9
    assert abs(rec['cap_ly'] - cap['new_LY']) < 1e-9
    #  - phuong an goc GIU be GOC (khong lay be da thu cua phuong an thang)
    orig = out['original_config']
    assert orig is not None
    assert abs(orig['cap_lx'] - params['L_X']) < 1e-9
    assert abs(orig['cap_ly'] - params['L_Y']) < 1e-9
    print("[OK] orchestrator: d=%.3f, %d coc, Pmax=%.1f, be %.2fx%.2f -> %.2fx%.2f"
          % (dwin, rec['n'], rec['pmax'], cap['old_LX'], cap['old_LY'],
             cap['new_LX'], cap['new_LY']))


def main():
    """Chay lan luot tat ca kiem thu module mo rong."""
    print("=" * 60)
    print(" KIEM THU MODULE MO RONG (core/ext)")
    print("=" * 60)
    test_pile_section()
    test_diameter_table()
    test_writer_diameter()
    test_cap_resize()
    test_orchestrator()
    print("=" * 60)
    print(" TAT CA PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
