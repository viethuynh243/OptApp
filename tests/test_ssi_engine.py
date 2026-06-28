"""
test_ssi_engine.py - Kiểm chứng engine SSI (core/ssi_engine) bằng 2 mỏ neo độc lập:

  1) DỌC TRỤC: với độ cứng cọc ĐỀU, axial_distribution phải TRÙNG KHỚP công thức
     bệ cứng rigid_cap.pile_forces (qua nhiều layout & tổ hợp tải ngẫu nhiên).
  2) NGANG: dầm trên nền Winkler phải khớp nghiệm giải tích Hetenyi cho dầm VÔ HẠN
     chịu tải điểm giữa: y_max = Pβ/(2k), M_max = P/(4β).
"""
import numpy as np
import pytest

from core import rigid_cap
from core import ssi_engine as ssi


# --------------------------------------------------------------------------
# 1) Dọc trục: SSI (ka đều) == rigid_cap
# --------------------------------------------------------------------------
@pytest.mark.parametrize("seed", [0, 1, 2, 3, 7])
def test_axial_matches_rigid_cap(seed):
    """Lưới ĐỐI XỨNG (Ixy=0): SSI (ka đều) phải TRÙNG rigid_cap đến sai số máy."""
    rng = np.random.default_rng(seed)
    # Lưới chữ nhật ĐẦY ĐỦ, không nhiễu -> tích quán tính Ixy = 0 (trục chính)
    nx, ny = int(rng.integers(2, 5)), int(rng.integers(2, 5))
    xs = np.arange(nx) * 3.0
    ys = np.arange(ny) * 3.0
    coords = np.array([(x, y) for y in ys for x in xs], dtype=float)

    load = {'N': float(rng.uniform(500, 3000)),
            'Mx': float(rng.uniform(-800, 800)),
            'My': float(rng.uniform(-800, 800))}

    expected = rigid_cap.pile_forces(coords, load)
    # ka đều bất kỳ -> phân phối phải độc lập trị số ka và khớp rigid_cap
    got = ssi.axial_distribution(coords, load, ka=12345.6)['forces']
    assert np.allclose(got, expected, rtol=1e-9, atol=1e-6)

    # ka=None (đều = 1) cũng phải khớp
    got2 = ssi.axial_distribution(coords, load, ka=None)['forces']
    assert np.allclose(got2, expected, rtol=1e-9, atol=1e-6)


def test_axial_exact_equilibrium_when_rigidcap_approximates():
    """Lưới LỆCH TRỤC (Ixy≠0): SSI thỏa CHẶT cân bằng mômen, còn công thức
    rigid_cap (bỏ qua Ixy) thì KHÔNG — chứng tỏ engine là nghiệm bệ cứng đúng."""
    rng = np.random.default_rng(42)
    coords = np.array([(x, y) for y in (0, 3, 6) for x in (0, 3, 6)], dtype=float)
    coords += rng.normal(0, 0.4, coords.shape)        # phá đối xứng -> Ixy ≠ 0
    cx, cy = coords[:, 0].mean(), coords[:, 1].mean()
    Ixy = float(((coords[:, 0] - cx) * (coords[:, 1] - cy)).sum())
    assert abs(Ixy) > 1e-3                             # đúng là lệch trục

    load = {'N': 2000.0, 'Mx': 500.0, 'My': -350.0}
    Mx_t = load['Mx'] - load['N'] * cy
    My_t = load['My'] - load['N'] * cx

    f_ssi = ssi.axial_distribution(coords, load, ka=1.0)['forces']
    f_rc = rigid_cap.pile_forces(coords, load)

    # SSI: cân bằng mômen quanh tâm thỏa CHẶT
    assert abs((f_ssi * (coords[:, 0] - cx)).sum() - My_t) < 1e-6
    assert abs((f_ssi * (coords[:, 1] - cy)).sum() - Mx_t) < 1e-6
    # rigid_cap: lệch khỏi cân bằng do bỏ Ixy (sai số hữu hạn)
    err_rc = abs((f_rc * (coords[:, 0] - cx)).sum() - My_t)
    assert err_rc > 1e-3


def test_axial_equilibrium():
    """Tổng lực dọc = N; tổng mômen quanh tâm = mômen tải quy về tâm."""
    coords = np.array([(0, 0), (3, 0), (0, 4), (3, 4), (1.5, 2)], dtype=float)
    load = {'N': 1000.0, 'Mx': 400.0, 'My': -250.0}
    r = ssi.axial_distribution(coords, load, ka=1000.0)
    f = r['forces']
    assert abs(f.sum() - load['N']) < 1e-6
    cx, cy = coords[:, 0].mean(), coords[:, 1].mean()
    Mx_t = load['Mx'] - load['N'] * cy
    My_t = load['My'] - load['N'] * cx
    assert abs((f * (coords[:, 1] - cy)).sum() - Mx_t) < 1e-6
    assert abs((f * (coords[:, 0] - cx)).sum() - My_t) < 1e-6


# --------------------------------------------------------------------------
# 2) Ngang: dầm Winkler vô hạn == Hetenyi
# --------------------------------------------------------------------------
def test_winkler_infinite_beam_vs_hetenyi():
    EI = 5.0e5          # kN·m²
    k_line = 8000.0     # kN/m/m
    P = 100.0           # kN
    beta = ssi.characteristic_beta(EI, k_line)
    # "Vô hạn" ~ 25/β; lưới mịn
    Lb = 25.0 / beta
    n_elem = 400
    res = ssi.beam_on_winkler(EI, k_line, Lb, n_elem=n_elem,
                              point_loads=[(Lb / 2.0, P)])
    i_mid = n_elem // 2
    y_mid = res['w'][i_mid]
    M_mid = res['M'][i_mid]

    y_exact = P * beta / (2.0 * k_line)
    M_exact = P / (4.0 * beta)

    assert y_mid == pytest.approx(y_exact, rel=2e-2), (y_mid, y_exact)
    assert abs(M_mid) == pytest.approx(M_exact, rel=3e-2), (M_mid, M_exact)


# --------------------------------------------------------------------------
# 3) Hiệu ứng nhóm cọc: p-multiplier (AASHTO) + tỷ số lún nhóm
# --------------------------------------------------------------------------
def test_p_multiplier_aashto_table():
    # Đúng giá trị bảng tại 3D / 5D
    assert ssi.p_multiplier(1, 3.0) == pytest.approx(0.70)
    assert ssi.p_multiplier(2, 3.0) == pytest.approx(0.50)
    assert ssi.p_multiplier(3, 3.0) == pytest.approx(0.35)
    assert ssi.p_multiplier(1, 5.0) == pytest.approx(1.00)
    assert ssi.p_multiplier(2, 5.0) == pytest.approx(0.85)
    # Hàng ≥3 dùng giá trị hàng 3
    assert ssi.p_multiplier(5, 3.0) == pytest.approx(0.35)
    # Nội suy 4D = trung điểm 3D↔5D
    assert ssi.p_multiplier(1, 4.0) == pytest.approx(0.85)
    # ≥5D và None → hết hiệu ứng nhóm
    assert ssi.p_multiplier(1, 6.0) == pytest.approx(1.0)
    assert ssi.p_multiplier(2, None) == pytest.approx(1.0)


def test_lateral_group_rows_and_pmult():
    # Lưới 3×3, k/c 3m, d=1 (=3D). Tải theo +x → 3 hàng theo x.
    coords = np.array([(x, y) for y in (0, 3, 6) for x in (0, 3, 6)], dtype=float)
    pmult, info = ssi.lateral_group_pmult(coords, d=1.0, load={'Hx': 100.0, 'Hy': 0.0})
    assert info['rows'] == 3
    assert info['s_over_D'] == pytest.approx(3.0, rel=1e-6)
    # Hàng dẫn đầu = x lớn nhất (x=6) → 0.70; x=3 → 0.50; x=0 → 0.35
    for (x, _y), pm in zip(coords, pmult):
        if x == 6: assert pm == pytest.approx(0.70)
        elif x == 3: assert pm == pytest.approx(0.50)
        else: assert pm == pytest.approx(0.35)


def test_group_settlement_ratio():
    assert ssi.group_settlement_ratio(9) == pytest.approx(3.0)
    assert ssi.group_settlement_ratio(16) == pytest.approx(4.0)
    assert ssi.group_settlement_ratio(1) == pytest.approx(1.0)


def test_analyze_group_effect_amplifies():
    coords = np.array([(x, y) for y in (0, 3, 6) for x in (0, 3, 6)], dtype=float)
    load = {'N': 2000.0, 'Mx': 200.0, 'My': 150.0, 'Hx': 300.0, 'Hy': 0.0, 'Mz': 0.0}
    base = {'D_PILE': 1.0, 'pile_length': 18.0, 'ks_soil': 12000.0}
    off = ssi.analyze(coords, {**base, 'group_effect': False}, load)
    on = ssi.analyze(coords, {**base, 'group_effect': True}, load)
    # Bật nhóm: lún nhóm lớn hơn (R_s>1) và chuyển vị/mômen ngang ≥ (nền mềm hơn)
    assert on['axial']['settle_group'] > off['axial']['settle_group']
    assert on['lateral']['pmult'] <= 1.0
    assert abs(on['lateral']['y_head']) >= abs(off['lateral']['y_head']) - 1e-9
    assert on['meta']['group_effect'] is True


# --------------------------------------------------------------------------
# 4) Phương pháp hệ số nền "m" (TCVN 10304 Phụ lục A) + EI=Eb·Jo của file
# --------------------------------------------------------------------------
def test_analyze_m_method_uses_file_EI_and_m():
    coords = np.array([(x, y) for y in (0, 3, 6) for x in (0, 3)], dtype=float)
    load = {'N': 1500.0, 'Mx': 0.0, 'My': 0.0, 'Hx': 200.0, 'Hy': 0.0, 'Mz': 0.0}
    # giống file MCOC: Eb (T/m²), Jo (m⁴), Fo (m²), m (T/m⁴), Lc (m)
    params = {'D_PILE': 1.2, 'pile_length': 20.0, 'E_b': 3.0e6, 'J_o': 0.1018,
              'F_o': 1.131, 'm_soil': 400.0}
    res = ssi.analyze(coords, params, load)
    assert res['meta']['lateral_model'] == 'm'
    assert res['meta']['m_soil'] == pytest.approx(400.0)
    assert res['meta']['EI'] == pytest.approx(3.0e6 * 0.1018, rel=1e-9)   # EI = Eb·Jo
    lat = res['lateral']
    assert lat['model'] == 'm' and lat['M_max'] > 0 and abs(lat['y_head']) > 0
    # Đầu cọc ngàm (mặc định) → mômen đầu cọc khác 0
    assert abs(lat['profile']['M'][0]) > 0

    # KHÔNG có m → quay về lò xo hằng ks
    res2 = ssi.analyze(coords, {'D_PILE': 1.2, 'pile_length': 20.0, 'ks_soil': 2000.0}, load)
    assert res2['meta']['lateral_model'] == 'ks'


def test_m_method_softer_than_equivalent_constant():
    """k(z)=m·z·d (mềm ở đỉnh) cho chuyển vị đầu LỚN HƠN lò xo hằng k=m·Lc·d."""
    coords = np.array([(0.0, 0.0), (3.0, 0.0)], dtype=float)
    load = {'N': 0.0, 'Hx': 100.0, 'Hy': 0.0, 'Mz': 0.0, 'Mx': 0.0, 'My': 0.0}
    base = {'D_PILE': 1.0, 'pile_length': 20.0, 'E_b': 3.0e6, 'J_o': 0.05}
    y_m = abs(ssi.analyze(coords, {**base, 'm_soil': 400.0}, load)['lateral']['y_head'])
    y_k = abs(ssi.analyze(coords, {**base, 'ks_soil': 400.0 * 20.0}, load)['lateral']['y_head'])
    assert y_m > y_k


def test_analyze_smoke():
    """analyze() chạy trơn, trả cấu trúc đầy đủ kể cả khi thiếu chiều dài cọc."""
    coords = np.array([(x, y) for y in (0, 3, 6) for x in (0, 3)], dtype=float)
    load = {'N': 1500.0, 'Mx': 300.0, 'My': 200.0, 'Hx': 120.0, 'Hy': 60.0, 'Mz': 0.0}
    out = ssi.analyze(coords, {'D_PILE': 1.0, 'ks_soil': 12000.0}, load)
    assert out['axial']['forces'].shape == (6,)
    assert out['lateral']['M_max'] >= 0.0
    assert out['meta']['Lc_illustrative'] is True
    # Có chiều dài cọc thật -> hết minh hoạ
    out2 = ssi.analyze(coords, {'D_PILE': 1.0, 'pile_length': 20.0}, load)
    assert out2['meta']['Lc_illustrative'] is False


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
