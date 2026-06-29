"""
test_cap_design.py - Kiểm chứng module thiết kế đài cọc (core/cap_design) bằng
một ví dụ TÍNH TAY được + các tính chất đơn điệu/biên.

Cấu hình chuẩn: 4 cọc tại (±1.5, ±1.5) m, D=1 m, cột 1×1 m ở tâm, đài H=2 m,
lớp bảo vệ 0.1 m → h0=1.9 m. B25 (Rb=14.5, Rbt=1.05), CB400-V (Rs=350).
Tải 1 tổ hợp N=2000 T đúng tâm → mỗi cọc 500 T.
"""
import math
import numpy as np
import pytest

from core import cap_design as cap

COORDS = np.array([(1.5, 1.5), (-1.5, 1.5), (1.5, -1.5), (-1.5, -1.5)], dtype=float)
LOADS = [{'N': 2000.0, 'Mx': 0.0, 'My': 0.0}]
# DESIGN_BASIS='TCVN10304' để kiểm ĐÚNG đường TCVN 5574:2018 (đài cọc cũ). Mặc định
# dự án nay là TCVN11823 → design_cap uỷ quyền sang cap_design_lrfd (test riêng:
# tests/test_cap_design_lrfd.py). 5574 KHÔNG dùng cho cầu — chỉ giữ đối chiếu/hồi quy.
PARAMS = {'D_PILE': 1.0, 'cap_thickness': 2.0, 'cover': 0.10, 'DESIGN_BASIS': 'TCVN10304',
          'col_b': 1.0, 'col_h': 1.0, 'conc_grade': 'B25', 'steel_grade': 'CB400-V'}
TF = cap.TF_TO_KN * cap.KN_TO_N    # N cho 1 Tấn


def test_materials_tcvn():
    rb, rbt, rs, xi_R = cap.materials('B25', 'CB400-V')
    assert (rb, rbt, rs) == (14.5, 1.05, 350.0)
    assert xi_R == pytest.approx(0.531, abs=0.01)   # ξ_R CB400 ~0.53


def test_flexure_hand_calc():
    """As phương X khớp tính tay ~15100 mm²; ζ, α_m hợp lý; ĐẠT."""
    r = cap.design_cap(COORDS, PARAMS, LOADS)
    assert r['ok'] is True
    fx = r['flexure']['x']
    # M tay = 2 cọc × 500T × (1.5−0.5)m
    M_hand = 2 * (500 * TF) * 1000.0    # N·mm (cánh tay 1000 mm)
    assert fx['M'] == pytest.approx(M_hand, rel=1e-6)
    assert fx['As'] == pytest.approx(15100, rel=0.03)
    assert fx['ok'] is True and fx['xi'] < fx['xi_R']


def test_punching_column_ratio():
    r = cap.design_cap(COORDS, PARAMS, LOADS)
    pc = r['punching']['column']
    assert pc['n_inside'] == 0                      # cọc nằm ngoài tháp
    assert pc['u_m'] == pytest.approx(11600.0)      # 2(1000+1000+2·1900)
    assert pc['ratio'] == pytest.approx(0.847, abs=0.02)
    assert pc['ok'] is True


def test_oneway_shear_section_at_column_face():
    """Cắt 1 phương (TCVN 5574 Đ.8.1.3): tiết diện tại MÉP CỘT, Q = 2 cọc ngoài mép;
    C = 1,0 m < h0 → kẹp về h0 → Qb = 1,5·Rbt·b·h0 (≤ 2,5·Rbt·b·h0) đủ lớn → ĐẠT."""
    r = cap.design_cap(COORDS, PARAMS, LOADS)
    sx = r['shear']['x']
    Q_hand = 2 * (500 * TF)                          # 2 cọc × 500 T (N)
    assert sx['Q'] == pytest.approx(Q_hand, rel=1e-6)
    rbt, b, h0 = 1.05, (3.0 + 1.0) * 1000.0, 1.9 * 1000.0
    Qb_hand = min(1.5 * rbt * b * h0, 2.5 * rbt * b * h0)
    assert sx['Q_concrete'] == pytest.approx(Qb_hand, rel=1e-6)
    assert sx['need_stirrups'] is False and sx['ok'] is True


def test_oneway_shear_far_pile_reduces_qb():
    """Cọc XA mép cột (C tăng tới 2h0) → Qb giảm (φb2·Rbt·b·h0²/C). Kiểm Qb(xa) < Qb(gần)."""
    near = cap.oneway_shear(1.0, 1.05, 4000.0, 1900.0, C=1900.0, rb=14.5)   # C=h0
    far = cap.oneway_shear(1.0, 1.05, 4000.0, 1900.0, C=3800.0, rb=14.5)    # C=2h0
    assert far['Q_concrete'] < near['Q_concrete']
    # C=2h0: Qb = 1.5·Rbt·b·h0²/(2h0) = 0.75·Rbt·b·h0 (trong [0.5,2.5])
    assert far['Q_concrete'] == pytest.approx(0.75 * 1.05 * 4000.0 * 1900.0, rel=1e-6)
    # giới hạn nén dải bê tông = 0.3·Rb·b·h0
    assert far['Q_max'] == pytest.approx(0.3 * 14.5 * 4000.0 * 1900.0, rel=1e-6)


def test_deep_cap_flag_and_stm():
    r = cap.design_cap(COORDS, PARAMS, LOADS)
    stm = r['stm']
    assert stm['deep'] is True                      # a/h0 = 1000/1900 < 1
    assert stm['As_tie'] > 0 and 20 < stm['theta_deg'] < 80


def test_missing_geometry_reported():
    bad = {k: v for k, v in PARAMS.items() if k != 'cap_thickness'}
    r = cap.design_cap(COORDS, bad, LOADS)
    assert r['ok'] is False
    assert any('chiều cao đài' in m for m in r['missing'])


def test_more_load_more_steel():
    r1 = cap.design_cap(COORDS, PARAMS, LOADS)
    r2 = cap.design_cap(COORDS, PARAMS, [{'N': 4000.0, 'Mx': 0.0, 'My': 0.0}])
    assert r2['flexure']['x']['As'] > r1['flexure']['x']['As']


def test_thin_cap_overstressed():
    """Đài quá mỏng → α_m>0.5 hoặc ξ>ξ_R → cờ KHÔNG ĐẠT ở uốn."""
    thin = {**PARAMS, 'cap_thickness': 0.5}        # h0 chỉ 0.4 m
    r = cap.design_cap(COORDS, thin, [{'N': 8000.0, 'Mx': 0.0, 'My': 0.0}])
    assert r['flexure']['x']['ok'] is False


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
