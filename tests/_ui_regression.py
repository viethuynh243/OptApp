"""_ui_regression.py - LƯỚI AN TOÀN cho việc tái cấu trúc UI.

Mục đích: phát hiện THAY ĐỔI HÀNH VI âm thầm của giao diện khi refactor
ui/main_window.py (khác với _smoke_full.py vốn chỉ bắt crash).

Cách hoạt động:
    1. Dựng MainWindow THẬT (mock mọi hộp thoại) — KHÔNG phụ thuộc file mẫu
       (mcoc_input_sample/*.txt không track trong repo); thay vào đó nạp
       params + loads + toạ độ gốc TRỰC TIẾP để chạy ổn định ở mọi máy.
    2. Chạy luồng THƯỜNG (NSGA-II mock, có seed) và luồng MỞ RỘNG (orchestrator
       mock, có seed) — đều TẤT ĐỊNH.
    3. Chụp "snapshot" có cấu trúc các tín hiệu HÀNH VI quan sát được:
       - nội dung ô kết quả (txt_result),
       - danh sách phương án / tổ hợp tải trong combobox,
       - nhãn KPI khi audit từng phương án,
       - các trường số chính của current_config.
    4. So với golden (tests/_ui_regression_golden.json). Lệch -> in diff + FAIL.

Chạy:
    python tests/_ui_regression.py            # so với golden, exit 1 nếu lệch
    python tests/_ui_regression.py --update    # ghi/đè golden (mốc mới)

QUY ƯỚC: chỉ cập nhật golden khi thay đổi hành vi là CỐ Ý. Trong lúc refactor
"giữ nguyên hành vi", golden KHÔNG được đổi — mọi lệch là hồi quy cần sửa.
"""
import os
import sys
import io
import json
import argparse
import traceback

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import tkinter.messagebox as mb
# Vô hiệu hoá mọi hộp thoại để chạy không tương tác
mb.askyesno = lambda *a, **k: True
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: None
mb.showinfo = lambda *a, **k: None

from tkinterdnd2 import TkinterDnD
from ui.main_window import MainWindow
from core.blackbox import MCOCBlackbox
from core.nsga2_optimizer import run_nsga2
from core.ext.orchestrator import run_extended_optimization
from core.ext.pile_section import DiameterTable
from core.ext.config_ext import ExtConfig

GOLDEN = os.path.join(os.path.dirname(__file__), '_ui_regression_golden.json')

# Dữ liệu bài toán CỐ ĐỊNH (không phụ thuộc file ngoài) ---------------------------
PARAMS = {
    'L_X': '12', 'L_Y': '12', 'D_PILE': '1.2',
    'P_LIMIT': '900', 'P_TENSION': '300', 'M_LIMIT': '0',
}
LOADS = [
    {'Hx': 30.0, 'Hy': 20.0, 'N': 3200.0, 'Mx': 180.0, 'My': 240.0, 'Mz': 0.0},
    {'Hx': 45.0, 'Hy': 10.0, 'N': 2600.0, 'Mx': 120.0, 'My': 300.0, 'Mz': 0.0},
]
# Toạ độ "phương án gốc" — lưới 3x3 @ 4.0 m quanh tâm
ORIG_COORDS = [(x * 4.0, y * 4.0) for y in (-1, 0, 1) for x in (-1, 0, 1)]


def mock_factory(params_d, dia, loads):
    """Evaluator giả cho luồng mở rộng: Pmax = maxN/n; momen cố định nhỏ."""
    mN = max((abs(l['N']) for l in loads), default=1000.0)

    def ev(c):
        n = max(len(c), 1)
        pm = mN / n
        return {'pmax': pm, 'pmin': -0.05 * pm, 'mxmax': 8.0, 'mymax': 8.0}
    return ev


def _round(x, nd=4):
    try:
        return round(float(x), nd)
    except (TypeError, ValueError):
        return x


def _cfg_digest(cfg):
    """Trích các trường SỐ ổn định của 1 phương án để so sánh (bỏ coords thô)."""
    if not isinstance(cfg, dict):
        return None
    keys = ('type', 'nx', 'ny', 'sx', 'sy', 'n', 'pmax', 'pmin', 'mxmax',
            'mymax', 'ok', 'cap_lx', 'cap_ly', 'd', 'Po')
    out = {}
    for k in keys:
        if k in cfg:
            out[k] = _round(cfg[k]) if isinstance(cfg[k], (int, float)) else cfg[k]
    if isinstance(cfg.get('coords'), (list, np.ndarray)):
        out['n_coords'] = len(cfg['coords'])
    return out


def _capture_flow(app, label):
    """Chụp snapshot tín hiệu hành vi sau khi 1 luồng đã render kết quả."""
    snap = {'label': label}
    # 1) Nội dung ô kết quả (chuẩn hoá cuối dòng)
    txt = app.txt_result.get('1.0', 'end').rstrip('\n')
    snap['result_lines'] = [ln.rstrip() for ln in txt.splitlines()]
    # 2) Combobox phương án + tổ hợp tải
    snap['config_values'] = list(app.cb_config['values'])
    snap['load_values'] = list(app.cb_load_case['values'])
    # 3) current_config: digest phương án đề xuất + gốc
    cc = app.current_config or {}
    snap['recommended'] = _cfg_digest(cc.get('recommended'))
    snap['original_config'] = _cfg_digest(cc.get('original_config'))
    snap['n_valid'] = len(cc.get('all_valid_configs', []) or [])
    # 4) KPI khi audit từng phương án
    kpi = {}
    for name in snap['config_values']:
        try:
            app.cb_config.set(name)
            app.view_mode.set('audit')
            app.update_simulation()
            kpi[name] = app.lbl_kpi['text']
        except Exception as e:
            kpi[name] = '<ERR:%s>' % e
    snap['kpi_by_config'] = kpi
    app.view_mode.set('layout')
    return snap


def build_snapshot():
    root = TkinterDnD.Tk()
    app = MainWindow(root)
    root.geometry('1400x900')
    root.update()

    # Nạp bài toán trực tiếp (không qua file)
    for k, v in PARAMS.items():
        app.params[k].set(v)
    app.loads = [dict(l) for l in LOADS]
    app.refresh_loads_ui()
    app.original_coords = list(ORIG_COORDS)

    snapshot = {'params': dict(PARAMS), 'n_loads': len(LOADS),
                'n_orig_coords': len(ORIG_COORDS)}

    # --- Luồng THƯỜNG (NSGA-II mock) ---
    p = app.get_params_dict()
    p['mock_mode'] = True
    ev = MCOCBlackbox.make_mock_evaluator(p, app.loads)
    res = run_nsga2(p, app.loads, evaluator=ev,
                    pop_size=16, n_gen=6, max_evals=120, seed=0)
    res['_orig_eval'] = (len(app.original_coords),
                         ev(np.asarray(app.original_coords, float)))
    app._show_nsga2_results(res)
    root.update()
    snapshot['regular'] = _capture_flow(app, 'regular')

    # --- Luồng MỞ RỘNG (orchestrator mock) ---
    params = app.get_params_dict()
    params['input_filepath'] = app.input_filepath
    params['mock_mode'] = True
    table = DiameterTable([(1.0, 350.0), (1.2, 900.0), (1.5, 1500.0)])
    cfg = ExtConfig(enable_R7=True, enable_R8=True, cap_round_to=0.1, cap_resize=True)
    out = run_extended_optimization(params, list(app.loads), table, cfg=cfg,
                                    evaluator_factory=mock_factory,
                                    d_orig=1.2, Po_orig=900,
                                    pop_size=16, n_gen=6, seed=0)
    app._show_ext_results(out, cfg)
    root.update()
    snapshot['extended'] = _capture_flow(app, 'extended')

    # --- Làm mới (clear) — exercise nhánh delattr các thuộc tính 'gốc' ---
    # Đặt sẵn vài thuộc tính orig_* + original_d/p để clear_loads phải xoá chúng.
    app.original_d = 1.2
    app.original_p = 900.0
    app.orig_pmax = 519.6
    app.orig_pmin = -30.0
    app.result_filepath = 'x'
    app.clear_loads()
    root.update()
    snapshot['after_clear'] = {
        'n_loads': len(app.loads),
        'result_empty': app.txt_result.get('1.0', 'end').strip() == '',
        'config_values': list(app.cb_config['values']),
        'kpi': app.lbl_kpi['text'],
        'params_cleared': {k: app.params[k].get() for k in
                           ('L_X', 'L_Y', 'D_PILE', 'P_LIMIT')},
        'has_orig_d': hasattr(app, 'original_d'),
        'has_orig_pmax': hasattr(app, 'orig_pmax'),
    }

    # Lưu ý: khi destroy có thể in cảnh báo vô hại "invalid command name
    # ...idle_draw" (callback matplotlib chạy sau destroy) — không ảnh hưởng
    # kết quả so sánh ở dưới.
    root.destroy()
    return snapshot


def _diff(golden, current, path=''):
    """So sánh đệ quy, trả về danh sách dòng khác biệt (đường dẫn + giá trị)."""
    diffs = []
    if type(golden) != type(current) and not (
            isinstance(golden, (int, float)) and isinstance(current, (int, float))):
        diffs.append('%s: type %s != %s' % (path, type(golden).__name__,
                                            type(current).__name__))
        return diffs
    if isinstance(golden, dict):
        for k in golden:
            if k not in current:
                diffs.append('%s.%s: THIEU trong ban moi' % (path, k))
            else:
                diffs += _diff(golden[k], current[k], '%s.%s' % (path, k))
        for k in current:
            if k not in golden:
                diffs.append('%s.%s: THUA trong ban moi' % (path, k))
    elif isinstance(golden, list):
        if len(golden) != len(current):
            diffs.append('%s: len %d != %d' % (path, len(golden), len(current)))
        for i in range(min(len(golden), len(current))):
            diffs += _diff(golden[i], current[i], '%s[%d]' % (path, i))
    else:
        if golden != current:
            diffs.append('%s: %r != %r' % (path, golden, current))
    return diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--update', action='store_true',
                    help='Ghi/đè golden (chỉ khi thay đổi hành vi là CỐ Ý)')
    args = ap.parse_args()

    try:
        snap = build_snapshot()
    except Exception:
        print('[FAIL] Khong dung duoc snapshot:')
        print(traceback.format_exc())
        sys.exit(2)

    if args.update or not os.path.exists(GOLDEN):
        with open(GOLDEN, 'w', encoding='utf-8') as f:
            json.dump(snap, f, ensure_ascii=False, indent=2)
        action = 'GHI DE' if args.update else 'TAO MOI'
        print('[OK] Golden %s: %s' % (action, GOLDEN))
        sys.exit(0)

    with open(GOLDEN, 'r', encoding='utf-8') as f:
        golden = json.load(f)
    diffs = _diff(golden, snap, 'snapshot')
    if not diffs:
        print('[PASS] Snapshot KHOP golden (khong doi hanh vi).')
        sys.exit(0)
    print('[FAIL] Snapshot LECH golden (%d khac biet):' % len(diffs))
    for d in diffs[:60]:
        print('   ', d)
    if len(diffs) > 60:
        print('    ... va %d khac biet nua' % (len(diffs) - 60))
    sys.exit(1)


if __name__ == '__main__':
    main()
