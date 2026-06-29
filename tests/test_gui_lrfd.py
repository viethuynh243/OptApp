"""test_gui_lrfd.py - Kiểm thử LOGIC form GUI cơ sở thiết kế TCVN 11823 (LRFD).

Dựng MainWindow THẬT (như harness), set các biến panel LRFD → get_params_dict() →
kiểm params chảy đúng vào core (DESIGN_BASIS, R_N → φ·Rn = P_LIMIT, FC, loại cọc...).
Bỏ qua nếu môi trường không có Tk/tkinterdnd2 (CI headless)."""
import pytest


@pytest.fixture
def app():
    pytest.importorskip("tkinter")
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except Exception:
        pytest.skip("tkinterdnd2/display không khả dụng")
    try:
        root.withdraw()
        from ui.main_window import MainWindow
        a = MainWindow(root)
    except Exception as e:                       # build cần display/canvas — skip nếu lỗi
        try:
            root.destroy()
        except Exception:
            pass
        pytest.skip("Không dựng được MainWindow headless: %r" % e)
    yield a
    try:
        root.destroy()
    except Exception:
        pass


def test_lrfd_panel_flows_to_params(app):
    app.var_design_basis.set('TCVN11823')
    app.var_lrfd_enable.set(True)
    app.var_rn.set('1000')
    app.var_pile_type.set('driven')
    app.var_resist_method.set('static_load_test')
    app.var_fc.set('35')
    app.var_strength_state.set('STRENGTH_I')
    d = app.get_params_dict()
    assert d['DESIGN_BASIS'] == 'TCVN11823'
    assert d.get('LRFD_ENABLE') is True
    assert d['R_N'] == pytest.approx(1000.0)
    assert d['P_LIMIT'] == pytest.approx(750.0)        # φ=0,75 (driven, thử tải tĩnh)
    assert d['_capacity_source'] == 'tcvn_11823_10'
    assert d['RESISTANCE_METHOD'] == 'static_load_test'
    assert d['PILE_TYPE'] == 'driven'
    assert d['FC'] == pytest.approx(35.0)


def test_single_pile_reduction_in_params(app):
    app.var_design_basis.set('TCVN11823')
    app.var_rn.set('1000')
    app.var_resist_method.set('static_load_test')
    app.var_single_pile.set(True)
    d = app.get_params_dict()
    assert d['P_LIMIT'] == pytest.approx(600.0)        # 0,75 × 0,8 × 1000


def test_basis_switch_to_10304(app):
    app.var_design_basis.set('TCVN10304')
    app.var_rn.set('1000')                              # R_N bị bỏ qua ở cơ sở 10304
    d = app.get_params_dict()
    assert d['DESIGN_BASIS'] == 'TCVN10304'
    # đường 10304 KHÔNG dùng R_N → không có nguồn 11823
    assert d.get('_capacity_source') != 'tcvn_11823_10'


def test_design_cap_uses_lrfd_when_basis_11823(app):
    """Thiết kế đài đi theo TCVN 11823-5 khi cơ sở là 11823 (xuyên get_params_dict)."""
    from core import cap_design
    app.var_design_basis.set('TCVN11823')
    app.var_cap_h.set('1.5')
    app.var_col_b.set('1.0')
    app.var_col_h.set('1.0')
    app.var_fc.set('30')
    d = app.get_params_dict()
    d['D_PILE'] = 1.2
    coords = [[-1.5, -1.5], [1.5, -1.5], [-1.5, 1.5], [1.5, 1.5]]
    res = cap_design.design_cap(coords, d, [{'N': 800.0, 'Mx': 0.0, 'My': 0.0}])
    assert res.get('standard') == 'TCVN 11823-5:2017'
    assert 'fc' in res['mat']
