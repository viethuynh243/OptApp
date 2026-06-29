"""_smoke_full.py - SMOKE đa luồng UI: lái MainWindow thật qua nhiều kịch bản,
bắt mọi exception. KHÔNG cần MCOC (dùng evaluator giả + config dựng tay).

Chạy:  python tests/_smoke_full.py   (in PASS/FAIL từng bước)
"""
import os
import sys
import io
import traceback

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import tkinter.messagebox as mb
mb.askyesno = lambda *a, **k: True
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: None
mb.showinfo = lambda *a, **k: None

from tkinterdnd2 import TkinterDnD
from ui.main_window import MainWindow
from core.ext.orchestrator import run_extended_optimization
from core.ext.pile_section import DiameterTable
from core.ext.config_ext import ExtConfig

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'mcoc_input_sample', 'T7_EXT.txt')
results = []


def step(name, fn):
    try:
        fn()
        results.append((name, True, ''))
        print('[PASS]', name)
    except Exception as e:
        results.append((name, False, traceback.format_exc()))
        print('[FAIL]', name, '->', e)


def mock_factory(params_d, dia, loads):
    mN = max((abs(l['N']) for l in loads), default=1000.0)

    def ev(c):
        n = max(len(c), 1); pm = mN / n
        return {'pmax': pm, 'pmin': -0.05 * pm, 'mxmax': 8.0, 'mymax': 8.0}
    return ev


def main():
    root = TkinterDnD.Tk(); app = MainWindow(root); root.geometry('1400x900'); root.update()

    step('1. Khoi tao + man trong', lambda: root.update())
    step('2. Nap file mau', lambda: (app.process_multiple_files([SAMPLE]), root.update()))
    step('3. Nhap [Po]', lambda: app.params['P_LIMIT'].set('900'))

    def build_regular():
        # Dung ket qua luong THUONG (mock) bang cach goi _show_nsga2_results
        from core.blackbox import MCOCBlackbox
        from core.nsga2_optimizer import run_nsga2
        p = app.get_params_dict(); p['mock_mode'] = True
        ev = MCOCBlackbox.make_mock_evaluator(p, app.loads)
        res = run_nsga2(p, app.loads, evaluator=ev, pop_size=12, n_gen=4, max_evals=60, seed=0)
        res['_orig_eval'] = (len(app.original_coords), ev(np.asarray(app.original_coords, float)))
        app._show_nsga2_results(res)
        root.update()
    step('4. Luong THUONG (mock) + render', build_regular)

    def switch_all():
        for v in app.cb_config['values']:
            app.cb_config.set(v); app.update_simulation(); root.update()
    step('5. Chuyen tat ca phuong an (mat bang)', switch_all)

    def switch_loads():
        for i in range(len(app.cb_load_case['values'] or [])):
            app.cb_load_case.current(i); app.update_simulation(); root.update()
    step('6. Chuyen tat ca to hop tai', switch_loads)

    def audit_cycle():
        for _ in range(2):
            app.view_mode.set('audit'); app.update_simulation(); app.plot_canvas._run_redraw()
            app.view_mode.set('layout'); app.update_simulation()
        root.update()
    step('7. Audit R1-R8 + resize lap', audit_cycle)

    def build_ext():
        params = app.get_params_dict(); params['input_filepath'] = app.input_filepath; params['mock_mode'] = True
        table = DiameterTable([(1.0, 350.0), (1.2, 900.0), (1.5, 1500.0)])
        cfg = ExtConfig(enable_R7=True, enable_R8=True, cap_round_to=0.1, cap_resize=True)
        out = run_extended_optimization(params, list(app.loads), table, cfg=cfg,
                                        evaluator_factory=mock_factory, d_orig=1.2, Po_orig=900,
                                        pop_size=12, n_gen=4, seed=0)
        app._show_ext_results(out, cfg); root.update()
    step('8. Luong MO RONG (mock) + render', build_ext)
    step('9. Chuyen phuong an sau ext', switch_all)
    step('10. Audit sau ext', audit_cycle)

    def all_view_modes():
        # Phu MOI che do xem (3D/SSI/thiet ke dai von khong duoc cac smoke khac cham)
        app._load_demo_geotech()   # bom dia chat de SSI/capdesign co du lieu
        for v in ('layout', 'audit', 'model3d', 'ssi', 'capdesign'):
            app.view_mode.set(v); app.update_simulation(); app.plot_canvas._run_redraw()
            root.update()
        app.view_mode.set('layout')
    step('10b. MOI che do xem (layout/audit/3D/SSI/capdesign)', all_view_modes)

    def tight_cap():
        # Be chat -> vo nghiem -> goi y noi be
        app.params['L_X'].set('6'); app.params['L_Y'].set('6')
        params = app.get_params_dict(); params['input_filepath'] = app.input_filepath; params['mock_mode'] = True
        table = DiameterTable([(1.2, 500.0)])
        cfg = ExtConfig(enable_R7=False, enable_R8=False, cap_round_to=0.1, cap_resize=True)
        out = run_extended_optimization(params, list(app.loads), table, cfg=cfg,
                                        evaluator_factory=mock_factory, d_orig=1.2, Po_orig=500,
                                        pop_size=10, n_gen=3, seed=0)
        app._show_ext_results(out, cfg); root.update()
    step('11. Be chat + goi y noi be', tight_cap)

    def min_spacing_opt():
        app.var_min_spacing.set('2.5'); app.update_simulation()
        app.var_min_spacing.set('3.0')
    step('12. Doi K/c toi thieu', min_spacing_opt)

    step('13. Tab Hang loat', lambda: (app.notebook.select(1), root.update()))

    def batch_dnd():
        # Kéo-thả file vào danh sách (nhánh _re), rồi xóa/clear (qua batch_tab)
        class _E:
            data = "{%s}" % SAMPLE
        app.batch_tab._batch_drop(_E())
        assert len(app.batch_files) >= 1, "drag-drop khong them duoc file"
        app.batch_tab.clear_all_batch()
        root.update()
    step('13b. Batch keo-tha + clear', batch_dnd)

    step('14. Quay lai Tab 1', lambda: (app.notebook.select(0), root.update()))
    step('15. Lam moi (clear)', lambda: (app.clear_loads(), root.update()))

    def reload_after_clear():
        app.process_multiple_files([SAMPLE]); app.params['P_LIMIT'].set('900'); root.update()
    step('16. Nap lai sau lam moi', reload_after_clear)

    root.destroy()
    n_fail = sum(1 for _, ok, _ in results if not ok)
    print('\n==== %d/%d PASS, %d FAIL ====' % (len(results) - n_fail, len(results), n_fail))
    for name, ok, tb in results:
        if not ok:
            print('\n--- FAIL:', name, '---\n', tb[-600:])
    sys.exit(1 if n_fail else 0)


if __name__ == '__main__':
    main()
