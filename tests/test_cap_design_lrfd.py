"""test_cap_design_lrfd.py - Kiểm thử core/cap_design_lrfd.py (TCVN 11823-5:2017, LRFD).

Hand-calc φ, β1, uốn φMn, cắt Vc/Vr, chọc thủng; dispatch theo DESIGN_BASIS; và
đủ khoá kết quả cho UI plot_canvas render. (Trị φ là tham khảo AASHTO — test neo
công thức/đường đi, không thay cho kỹ sư đối chiếu TCVN 11823-5.)
"""
import math
import pytest
from core import cap_design_lrfd as cl


def test_phi_factors():
    assert cl.PHI_FLEXURE == 0.90
    assert cl.PHI_SHEAR == 0.90


def test_materials_beta1():
    fc, fy, b1 = cl.materials('C28', 'CB400-V')
    assert (fc, fy) == (28.0, 400.0)
    assert b1 == pytest.approx(0.85)                 # f'c ≤ 28 → 0,85
    _, _, b2 = cl.materials(params={'FC': 42.0})
    assert b2 == pytest.approx(0.85 - 0.05 * (42 - 28) / 7.0)   # = 0,75
    # khai trực tiếp FC/FY ưu tiên
    fc3, fy3, _ = cl.materials(params={'FC': 35.0, 'FY': 500.0})
    assert (fc3, fy3) == (35.0, 500.0)


def test_oneway_shear_handcalc():
    fc, bv, de, H = 30.0, 1000.0, 900.0, 1000.0
    r = cl.oneway_shear(0.0, fc, bv, de, H)
    dv = max(0.9 * de, 0.72 * H)                     # = 810
    Vc = 0.083 * 2.0 * math.sqrt(fc) * bv * dv
    assert r['dv'] == pytest.approx(dv)
    assert r['Vc'] == pytest.approx(Vc)
    assert r['Vr'] == pytest.approx(0.90 * min(Vc, 0.25 * fc * bv * dv))
    assert r['ok'] is True                           # Vu=0 ≤ Vr


def test_oneway_shear_fail_and_stirrups():
    r = cl.oneway_shear(1e7, 30.0, 1000.0, 900.0, 1000.0)   # Vu rất lớn
    assert r['ok'] is False and r['need_stirrups'] is True


def test_punching_column_handcalc():
    fc, bc, hc, de, H = 30.0, 1000.0, 1000.0, 900.0, 1000.0
    r = cl.punching_column(0.0, bc, hc, de, H, fc)
    dv = max(0.9 * de, 0.72 * H)
    bo = 2.0 * (bc + hc) + 4.0 * dv
    beta_c = 1.0
    vn_unit = min((0.17 + 0.33 / beta_c) * math.sqrt(fc), 0.33 * math.sqrt(fc))
    assert r['bo'] == pytest.approx(bo)
    assert r['Vn'] == pytest.approx(vn_unit * bo * dv)
    assert r['phi'] == 0.90


def test_flexure_tension_controlled():
    # Mu vừa phải → đạt, c/de ≤ 0,42, φMn ≥ Mu, As ≥ As_min
    fc, fy, b1, b, de = 30.0, 400.0, 0.85, 1000.0, 900.0
    Mu = 300e6   # N·mm
    r = cl.flexure_As(Mu, fc, fy, b1, b, de)
    assert r['ok'] is True
    assert r['c_over_de'] <= 0.42
    assert r['Mr'] >= Mu - 1.0
    assert r['As'] >= r['As_min'] > 0
    assert r['phi'] == 0.90


def test_flexure_overstressed_section():
    # Mu khổng lồ trên tiết diện nhỏ → vượt khả năng (disc<0 hoặc c/de>0,42)
    r = cl.flexure_As(5e9, 30.0, 400.0, 0.85, 300.0, 300.0)
    assert r['ok'] is False


# ----------------------------------------------------- tích hợp + dispatch
PARAMS = {
    'D_PILE': 1.2, 'cap_thickness': 1.5, 'cover': 0.1,
    'col_b': 1.0, 'col_h': 1.0, 'conc_grade': 'C30', 'steel_grade': 'CB400-V',
}
COORDS = [[-1.5, -1.5], [1.5, -1.5], [-1.5, 1.5], [1.5, 1.5]]
LOADS = [{'N': 800.0, 'Mx': 0.0, 'My': 0.0}]


def test_design_cap_lrfd_shape_and_keys():
    res = cl.design_cap_lrfd(COORDS, PARAMS, LOADS)
    assert res['ok'] and res['standard'] == 'TCVN 11823-5:2017'
    # đủ khoá cho plot_canvas render (chống KeyError ở UI)
    assert {'fc', 'fy', 'beta1', 'phi_f', 'phi_v'} <= set(res['mat'])
    assert 'dv_mm' in res['geom']
    fx = res['flexure']['x']
    assert {'Mu', 'As', 'As_min', 'c_over_de', 'Mr', 'ok'} <= set(fx)
    pc = res['punching']['column']
    assert {'Vu', 'Vr', 'bo', 'ratio', 'n_inside', 'ok'} <= set(pc)
    pp = res['punching']['pile']
    assert {'Vu', 'Vr', 'ratio', 'pile_index', 'ok'} <= set(pp)
    sx = res['shear']['x']
    assert {'Vu', 'Vr', 'need_stirrups', 'ok'} <= set(sx)
    assert {'deep', 'T', 'As_tie', 'theta_deg'} <= set(res['stm'])


def test_design_cap_lrfd_missing():
    res = cl.design_cap_lrfd(COORDS, {'D_PILE': 1.2}, LOADS)   # thiếu H, cột
    assert res['ok'] is False and res['standard'] == 'TCVN 11823-5:2017'
    assert res['missing']


def test_design_cap_dispatches_by_basis():
    from core import cap_design
    # 11823 → uỷ quyền sang LRFD (có 'standard' 11823-5)
    p11 = dict(PARAMS, DESIGN_BASIS='TCVN11823')
    r11 = cap_design.design_cap(COORDS, p11, LOADS)
    assert r11.get('standard') == 'TCVN 11823-5:2017'
    assert 'fc' in r11['mat']
    # 10304 → đường 5574 cũ (mat có Rb/Rbt, KHÔNG có 'standard' 11823)
    p10 = dict(PARAMS, DESIGN_BASIS='TCVN10304', conc_grade='B25')
    r10 = cap_design.design_cap(COORDS, p10, LOADS)
    assert r10.get('standard', 'TCVN 5574:2018') == 'TCVN 5574:2018'
    assert 'Rb' in r10['mat']
