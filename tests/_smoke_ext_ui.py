"""Smoke test tich hop UI toi uu mo rong (khong goi MCOC, dung evaluator gia).

Dung root TkinterDnD an (withdraw), nap du lieu mau T3_EXT, chay orchestrator
voi factory gia roi day vao _show_ext_results + bang audit. Kiem tra UI cap nhat
dung (D_PILE, L_X/L_Y theo duong kinh thang) va bang audit them dong R7/R8.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tkinterdnd2 import TkinterDnD
from ui.main_window import MainWindow
from io_handlers.file_io import parse_input_file
from core.ext.pile_section import DiameterTable
from core.ext.config_ext import ExtConfig
from core.ext.orchestrator import run_extended_optimization

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "mcoc_input_sample", "T3_EXT.txt")


def mock_factory(params_d, dia, loads):
    maxN = max((abs(l['N']) for l in loads), default=1000.0)
    def ev(coords):
        n = max(len(coords), 1)
        pmax = maxN / n
        return {'pmax': pmax, 'pmin': -0.05 * pmax, 'mxmax': 0.0, 'mymax': 0.0}
    return ev


def main():
    root = TkinterDnD.Tk(); root.withdraw()
    w = MainWindow(root)

    params, loads, _ = parse_input_file(SAMPLE)
    w.loads = loads
    w.original_coords = params['original_coords']
    w.original_d = params['D_PILE']; w.original_p = params['P_LIMIT']
    w.input_filepath = SAMPLE
    for k in ('L_X', 'L_Y', 'D_PILE', 'P_LIMIT'):
        w.params[k].set(f"{params.get(k, 0):g}")

    params['input_filepath'] = SAMPLE
    table = DiameterTable([(1.0, 300.0), (1.2, 500.0), (1.5, 900.0, 0.0, 0.0, 600.0)])
    cfg = ExtConfig(enable_R7=True, enable_R8=True, cap_round_to=0.1)
    out = run_extended_optimization(params, loads, table, cfg=cfg,
                                    evaluator_factory=mock_factory,
                                    pop_size=12, n_gen=6, seed=0)
    assert out['recommended'] is not None, "Khong co phuong an"

    old_lx = w.params['L_X'].get()
    w._show_ext_results(out, cfg)

    # Kiem tra UI cap nhat theo duong kinh thang
    dwin = out['winner_diameter']
    assert abs(float(w.params['D_PILE'].get()) - dwin) < 1e-9, w.params['D_PILE'].get()
    assert w._ext_active is True
    txt = w.txt_result.get('1.0', 'end')
    assert 'TOI UU MO RONG' in txt and 'THANG' in txt, txt[:120]
    print("[OK] _show_ext_results: d_thang=%g, L_X %s -> %s, txt_len=%d"
          % (dwin, old_lx, w.params['L_X'].get(), len(txt)))

    # Kiem tra bang audit them R7/R8
    w.view_mode.set('audit')
    import numpy as np
    cfg_rec = w.current_config['recommended']
    coords = np.asarray(cfg_rec['coords'], float)
    cdata = w._build_constraint_data(cfg_rec, coords, w.get_params_dict(), 1.0)
    joined = " | ".join(cdata['geom_summary'])
    assert 'R7' in joined and 'R8' in joined, joined
    assert cdata['cons_label'] == 'R1–R8', cdata['cons_label']
    print("[OK] audit R7/R8: %s" % joined)
    print("[OK] cons_label = %s" % cdata['cons_label'])

    root.destroy()
    print("SMOKE EXT UI: PASS")


if __name__ == "__main__":
    main()
