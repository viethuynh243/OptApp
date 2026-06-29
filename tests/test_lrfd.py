"""test_lrfd.py - Kiểm thử core/lrfd.py (TCVN 11823:2017 — LRFD).

Hand-calc các hệ số γ/φ, giảm 20% móng 1 cọc, áp hệ số tải/sức kháng, và điều phối
cơ sở thiết kế. (Trị γ/φ là TRỊ THAM KHẢO — test neo công thức/đường đi, không thay
cho việc kỹ sư đối chiếu bản TCVN 11823-3/-10.)
"""
import math
import pytest
from core import lrfd


# --------------------------------------------------------------------------- φ
def test_resistance_factor_lookup():
    assert lrfd.resistance_factor('driven', 'compression', 'static_load_test') == 0.75
    assert lrfd.resistance_factor('driven', 'compression', 'static_analysis') == 0.50
    assert lrfd.resistance_factor('drilled', 'compression', 'static_load_test') == 0.70
    # uplift thấp hơn nén
    assert lrfd.resistance_factor('driven', 'uplift', 'static_analysis') < \
           lrfd.resistance_factor('driven', 'compression', 'static_analysis')
    # phương pháp lạ -> default
    assert lrfd.resistance_factor('driven', 'compression', 'khong_co') == 0.45


def test_single_pile_reduces_20pct():
    base = lrfd.resistance_factor('driven', 'compression', 'static_load_test')
    red = lrfd.resistance_factor('driven', 'compression', 'static_load_test', single_pile=True)
    assert red == pytest.approx(base * 0.80)


def test_extreme_phi_is_one():
    assert lrfd.resistance_factor(extreme=True) == 1.00
    assert lrfd.resistance_factor(extreme=True, single_pile=True) == pytest.approx(0.80)


def test_factored_resistance():
    # φ·Rn: driven, static_load_test, Rn=1000 -> 0.75*1000
    assert lrfd.factored_resistance(1000, 'driven', 'compression', 'static_load_test') == pytest.approx(750.0)
    assert lrfd.factored_resistance(0) == 0.0
    assert lrfd.factored_resistance(-5) == 0.0


# --------------------------------------------------------------------------- γ
def test_factor_loads_strength_i_LL():
    loads = [{'N': 100.0, 'Mx': 10.0, 'load_type': 'LL'}]
    out = lrfd.factor_loads(loads, 'STRENGTH_I')
    assert out[0]['N'] == pytest.approx(175.0)   # 1.75 * 100
    assert out[0]['Mx'] == pytest.approx(17.5)


def test_factor_loads_DC_max_min():
    loads = [{'N': 200.0, 'load_type': 'DC'}]
    assert lrfd.factor_loads(loads, 'STRENGTH_I')[0]['N'] == pytest.approx(250.0)   # 1.25
    assert lrfd.factor_loads(loads, 'STRENGTH_I', use_min=True)[0]['N'] == pytest.approx(180.0)  # 0.90


def test_factor_loads_service_is_unity():
    loads = [{'N': 100.0, 'load_type': 'LL'}]
    assert lrfd.factor_loads(loads, 'SERVICE_I')[0]['N'] == pytest.approx(100.0)


def test_factor_loads_skips_zero_gamma():
    # Hoạt tải ở Cường độ IV có γ=0 -> dòng bị bỏ; rỗng thì trả về tải gốc (an toàn)
    loads = [{'N': 100.0, 'load_type': 'LL'}]
    out = lrfd.factor_loads(loads, 'STRENGTH_IV')
    assert out == loads   # fallback giữ tải gốc khi mọi dòng γ=0


def test_default_load_type_is_LL():
    loads = [{'N': 100.0}]   # không gắn loại -> LL
    assert lrfd.factor_loads(loads, 'STRENGTH_I')[0]['N'] == pytest.approx(175.0)


# ----------------------------------------------------------- apply_lrfd_capacities
def test_apply_lrfd_capacities_with_Rn():
    p = {'R_N': 1000.0, 'PILE_TYPE': 'driven', 'RESISTANCE_METHOD': 'static_load_test'}
    lrfd.apply_lrfd_capacities(p)
    assert p['P_LIMIT'] == pytest.approx(750.0)        # 0.75 * 1000
    assert p['_capacity_source'] == 'tcvn_11823_10'


def test_apply_lrfd_capacities_single_pile():
    p = {'R_N': 1000.0, 'RESISTANCE_METHOD': 'static_load_test', 'SINGLE_PILE': True}
    lrfd.apply_lrfd_capacities(p)
    assert p['P_LIMIT'] == pytest.approx(600.0)        # 0.75 * 0.8 * 1000


def test_apply_lrfd_capacities_no_Rn_keeps_input():
    p = {'P_LIMIT': 500.0}
    lrfd.apply_lrfd_capacities(p)
    assert p['P_LIMIT'] == 500.0
    assert p['_capacity_source'] == 'input'


def test_apply_lrfd_capacities_idempotent():
    p = {'R_N': 1000.0, 'RESISTANCE_METHOD': 'static_load_test'}
    lrfd.apply_lrfd_capacities(p)
    first = p['P_LIMIT']
    p['R_N'] = 9999.0           # đổi sau khi áp -> không tính lại
    lrfd.apply_lrfd_capacities(p)
    assert p['P_LIMIT'] == first


# ------------------------------------------------------------- điều phối cơ sở
def test_design_basis_resolution():
    assert lrfd.design_basis({'DESIGN_BASIS': 'TCVN 11823'}) == 'TCVN11823'
    assert lrfd.design_basis({'DESIGN_BASIS': 'tcvn10304'}) == 'TCVN10304'


def test_factoring_disabled_when_unconfigured():
    # 11823 nhưng chưa khai báo load_type/LRFD_ENABLE -> KHÔNG nhân hệ số
    p = {'DESIGN_BASIS': 'TCVN11823', '_loads_for_lrfd_check': [{'N': 100.0}]}
    assert not lrfd.lrfd_load_factoring_enabled(p)
    out = lrfd.demand_loads([{'N': 100.0}], p)
    assert out[0]['N'] == pytest.approx(100.0)


def test_factoring_enabled_by_flag():
    p = {'DESIGN_BASIS': 'TCVN11823', 'LRFD_ENABLE': True}
    assert lrfd.lrfd_load_factoring_enabled(p)
    out = lrfd.demand_loads([{'N': 100.0}], p)       # mặc định LL, Cường độ I
    assert out[0]['N'] == pytest.approx(175.0)


def test_factoring_enabled_by_load_type():
    p = {'DESIGN_BASIS': 'TCVN11823', '_loads_for_lrfd_check': [{'N': 100.0, 'load_type': 'LL'}]}
    assert lrfd.lrfd_load_factoring_enabled(p)


def test_apply_design_basis_11823_path():
    p = {'DESIGN_BASIS': 'TCVN11823', 'LRFD_ENABLE': True,
         'R_N': 1000.0, 'RESISTANCE_METHOD': 'static_load_test'}
    loads = [{'N': 100.0, 'load_type': 'LL'}]
    p2, dem = lrfd.apply_design_basis(p, loads)
    assert p2['P_LIMIT'] == pytest.approx(750.0)
    assert dem[0]['N'] == pytest.approx(175.0)


def test_apply_design_basis_10304_path_delegates_tcvn():
    p = {'DESIGN_BASIS': 'TCVN10304', 'P_LIMIT': 500.0}
    loads = [{'N': 100.0}]
    p2, dem = lrfd.apply_design_basis(p, loads)
    # đường 10304: tải KHÔNG nhân hệ số, dùng core.tcvn (giữ [Po] nhập)
    assert dem[0]['N'] == pytest.approx(100.0)
    assert p2['P_LIMIT'] == 500.0


# ----------------------------------------- tích hợp end-to-end qua run_nsga2
def test_run_nsga2_lrfd_sets_factored_resistance():
    """Đường LRFD đi qua điểm vào chính run_nsga2: P_LIMIT thành φ·R_N (φ=0,75 →
    R_N=900 ⇒ 675) và vẫn ra phương án kiến nghị. Chứng minh dispatch sức kháng
    hoạt động end-to-end (không chỉ unit)."""
    from core.nsga2_optimizer import run_nsga2
    p = {
        'L_X': 6.0, 'L_Y': 9.6, 'D_PILE': 1.2, 'SAFE_D': 1.2,
        'P_TENSION': 0.0, 'M_LIMIT': 0.0, 'mock_mode': True,
        'DESIGN_BASIS': 'TCVN11823', 'LRFD_ENABLE': True,
        'R_N': 900.0, 'PILE_TYPE': 'driven', 'RESISTANCE_METHOD': 'static_load_test',
        'original_coords': [[-1.5, -3.0], [1.5, -3.0], [-1.5, 0.0],
                            [1.5, 0.0], [-1.5, 3.0], [1.5, 3.0]],
        'orig_pmax': 519.63, 'orig_pmin': 0.0, 'orig_mxmax': 7.49, 'orig_mymax': 27.82,
    }
    loads = [{'N': 300.0, 'Mx': 100.0, 'My': 100.0, 'load_type': 'LL'}]
    res = run_nsga2(p, loads, pop_size=20, n_gen=10, seed=1)
    assert p['P_LIMIT'] == pytest.approx(675.0)        # 0.75 * 900
    assert p['_capacity_source'] == 'tcvn_11823_10'
    assert res['recommended'] is not None
