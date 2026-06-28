"""test_tcvn.py - Kiểm thử module core/tcvn.py (TCVN 10304:2014).

Chạy: python tests/test_tcvn.py
Bao gồm: công thức Rc,d (7.1.11), apply_design_capacities, móng khối quy ước,
lún (Phụ lục C) và cờ hạ cấp ràng buộc 6d (ENFORCE_SPACING_MAX).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest
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


def test_resolve_gamma_k_table():
    """γk theo số cọc (Đ.7.1.11): 1-5→1.75, 6-10→1.65, 11-20→1.55, ≥21→1.40."""
    assert tcvn.resolve_gamma_k(3) == 1.75
    assert tcvn.resolve_gamma_k(6) == 1.65
    assert tcvn.resolve_gamma_k(10) == 1.65
    assert tcvn.resolve_gamma_k(11) == 1.55
    assert tcvn.resolve_gamma_k(25) == 1.40
    # Cột thử tải tĩnh (trong ngoặc)
    assert tcvn.resolve_gamma_k(3, by_static_test=True) == 1.60
    assert tcvn.resolve_gamma_k(25, by_static_test=True) == 1.25
    # apply_design_capacities tự suy γk từ n_piles khi KHÔNG nhập tay GAMMA_K
    p = {'D_PILE': 1.2, 'R_C_K': 1000.0, 'n_piles': 8}   # 8 cọc -> γk=1.65
    tcvn.apply_design_capacities(p)
    assert abs(p['P_LIMIT'] - (1.15 / 1.15) * (1000.0 / 1.65)) < 1e-6, p['P_LIMIT']
    print("OK  resolve_gamma_k khop bang TCVN 10304 + auto theo n_piles")


def test_equivalent_block_2d_cap():
    """Chặn a≤2d cho đất dính yếu IL>0,6 (Đ.7.4.4): bật cờ -> spread nhỏ lại."""
    coords = np.array([[-1.8, -3.0], [1.8, 3.0]])
    base = {'D_PILE': 1.2, 'pile_length': 30.0, 'phi_tb': 30.0}   # a = 30·tan(7.5°) ≈ 3.95 m > 2d=2.4
    b_off = tcvn.equivalent_block(coords, base)
    b_on = tcvn.equivalent_block(coords, {**base, 'soft_clay_below': True})
    assert b_off['a_capped_2d'] is False
    assert b_on['a_capped_2d'] is True
    assert b_on['a_side'] == 2.0 * 1.2                  # bị kẹp về 2d
    assert b_on['B_qu'] < b_off['B_qu']                 # khối nhỏ lại -> lún lớn hơn (an toàn)
    print("OK  chan a<=2d khi dat dinh yeu (soft_clay_below)")


def test_settlement_includes_Se_and_boussinesq():
    """Lún = Se + lún khối (Boussinesq). Se>0 khi có E_b; σz dùng Boussinesq (≤ p_gl)."""
    coords = np.array([[-1.8, -3.0], [1.8, -3.0], [-1.8, 3.0], [1.8, 3.0]])
    p = {'D_PILE': 1.2, 'pile_length': 20.0, 'phi_tb': 24.0, 'cap_depth': 2.0,
         'E_b': 2.7e6, 'F_o': 1.131,     # mô đun thân cọc (T/m²) + diện tích cọc (m²)
         'soil_below': [{'h': 3.0, 'E': 3000.0}, {'h': 5.0, 'E': 5000.0}],
         'S_LIMIT': 0.10}
    loads = [{'N': 2000.0}]
    st = tcvn.settlement(coords, loads, p)
    assert st['evaluated']
    assert st['se_evaluated'] is True and st['S_e'] > 0
    assert st['S'] == pytest.approx(st['S_e'] + st['S_block'], rel=1e-9)
    # σz lớp đầu phải nhỏ hơn p_gl (suy giảm theo độ sâu) và > 0
    assert 0 < st['layers'][0]['sigma_z'] < st['p_gl']
    print(f"OK  lun = Se({st['S_e']*1000:.2f}mm) + khoi({st['S_block']*1000:.1f}mm) Boussinesq")


if __name__ == '__main__':
    test_design_axial_capacity()
    test_apply_design_capacities_from_rck()
    test_apply_design_capacities_input_mode()
    test_equivalent_block_and_settlement()
    test_settlement_missing_data()
    test_soft_6d_default_off()
    test_resolve_gamma_k_table()
    test_equivalent_block_2d_cap()
    test_settlement_includes_Se_and_boussinesq()
    print("\n== TAT CA TEST TCVN DAT ==")
