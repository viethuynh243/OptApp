"""test_tcvn.py - Kiểm thử module core/tcvn.py (TCVN 10304:2014).

Chạy: python tests/test_tcvn.py
Bao gồm: công thức Rc,d (7.1.11), apply_design_capacities, móng khối quy ước,
lún (Phụ lục C) và cờ hạ cấp ràng buộc 6d (ENFORCE_SPACING_MAX).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from core import tcvn
from core import constants


def test_design_axial_capacity():
    """Rc,d = (g0/gn)*(Rc,k/gk). Kiểm số học trực tiếp."""
    # Rc,k=1000, g0=1.15, gn=1.15, gk=1.4 -> 1000/1.4 = 714.29
    rcd = tcvn.design_axial_capacity(1000.0, 1.15, 1.15, 1.4)
    assert abs(rcd - 1000.0 / 1.4) < 1e-6, rcd
    # Đổi gn=1.2 (cấp I): Rc,d = (1.15/1.2)*(1000/1.4)
    rcd2 = tcvn.design_axial_capacity(1000.0, 1.15, 1.2, 1.4)
    assert abs(rcd2 - (1.15 / 1.2) * (1000.0 / 1.4)) < 1e-6, rcd2
    # Thiếu/không hợp lệ -> 0
    assert tcvn.design_axial_capacity(0, 1, 1, 1) == 0.0
    print("OK  design_axial_capacity: Rc,d = (g0/gn)*(Rc,k/gk)")


def test_apply_design_capacities_from_rck():
    """Khi có Rc,k + hệ số -> P_LIMIT bị ghi đè thành Rc,d; idempotent."""
    p = {'D_PILE': 1.2, 'R_C_K': 1000.0, 'R_T_K': 400.0,
         'GAMMA_0': 1.15, 'IMPORTANCE_LEVEL': 'II', 'GAMMA_K': 1.4,
         'P_LIMIT': 9999.0, 'P_TENSION': 9999.0}
    tcvn.apply_design_capacities(p)
    assert p['_capacity_source'] == 'tcvn_7.1.11'
    assert abs(p['P_LIMIT'] - (1.15 / 1.15) * (1000.0 / 1.4)) < 1e-6, p['P_LIMIT']
    assert abs(p['P_TENSION'] - (1.15 / 1.15) * (400.0 / 1.4)) < 1e-6, p['P_TENSION']
    # Gọi lại không đổi (idempotent)
    po = p['P_LIMIT']
    tcvn.apply_design_capacities(p)
    assert p['P_LIMIT'] == po
    print("OK  apply_design_capacities: Rc,k -> ghi de P_LIMIT, idempotent")


def test_apply_design_capacities_input_mode():
    """Không có Rc,k -> giữ nguyên P_LIMIT, nguồn = 'input'."""
    p = {'D_PILE': 1.2, 'P_LIMIT': 500.0, 'P_TENSION': 0.0}
    tcvn.apply_design_capacities(p)
    assert p['_capacity_source'] == 'input'
    assert p['P_LIMIT'] == 500.0
    print("OK  apply_design_capacities: che do 'input' giu nguyen [Po]")


def test_equivalent_block_and_settlement():
    """Móng khối quy ước mở rộng phi_tb/4 + lún cộng lớp dương khi có số liệu."""
    coords = np.array([[-1.8, -3.0], [1.8, -3.0], [-1.8, 0.0],
                       [1.8, 0.0], [-1.8, 3.0], [1.8, 3.0]])
    p = {'D_PILE': 1.2, 'pile_length': 20.0, 'phi_tb': 24.0, 'cap_depth': 2.0,
         'soil_below': [{'h': 2.0, 'E': 2000.0, 'gamma': 1.9},
                        {'h': 3.0, 'E': 3000.0, 'gamma': 2.0},
                        {'h': 5.0, 'E': 5000.0, 'gamma': 2.0}],
         'S_LIMIT': 0.10}
    blk = tcvn.equivalent_block(coords, p)
    assert blk['evaluated']
    # span_x=3.6, +d=1.2, +spread; spread=2*20*tan(6deg)
    spread = 2 * 20.0 * np.tan(np.radians(24.0) / 4.0)
    assert abs(blk['B_qu'] - (3.6 + 1.2 + spread)) < 1e-6, blk['B_qu']
    assert blk['base_depth'] == 22.0
    loads = [{'N': 2577.0, 'Mx': 1500.0, 'My': 1500.0}]
    st = tcvn.settlement(coords, loads, p)
    assert st['evaluated'] and st['S'] > 0
    assert st['ok'] in (True, False)
    print(f"OK  equivalent_block + settlement: Bqu={blk['B_qu']:.2f}m, S={st['S']*1000:.1f}mm")


def test_settlement_missing_data():
    """Thiếu số liệu địa chất -> evaluated=False, không âm thầm bỏ qua."""
    coords = np.array([[-1.8, -3.0], [1.8, 3.0]])
    blk = tcvn.equivalent_block(coords, {'D_PILE': 1.2})
    assert blk['evaluated'] is False and 'reason' in blk
    st = tcvn.settlement(coords, [{'N': 1000.0}], {'D_PILE': 1.2})
    assert st['evaluated'] is False and 'reason' in st
    print("OK  thieu so lieu dia chat -> evaluated=False (bao 'CHUA KIEM')")


def test_soft_6d_default_off():
    """Mặc định 6d KHÔNG phải ràng buộc cứng (chỉ cảnh báo)."""
    assert constants.ENFORCE_SPACING_MAX is False
    print("OK  ENFORCE_SPACING_MAX = False (6d la canh bao mem)")


if __name__ == '__main__':
    test_design_axial_capacity()
    test_apply_design_capacities_from_rck()
    test_apply_design_capacities_input_mode()
    test_equivalent_block_and_settlement()
    test_settlement_missing_data()
    test_soft_6d_default_off()
    print("\n== TAT CA TEST TCVN DAT ==")
