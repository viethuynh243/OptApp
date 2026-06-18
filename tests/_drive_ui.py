"""_drive_ui.py - Trình lái GUI để KIỂM TRA chức năng + layout (chụp màn hình).

Khởi chạy MainWindow THẬT, nạp file mẫu T7_EXT, dựng kết quả tối ưu mở rộng bằng
evaluator GIẢ (không cần MCOC), rồi chụp từng trạng thái để soi layout + xác minh
sửa lỗi "bệ của phương án nào đi theo phương án đó".

Chạy:  python tests/_drive_ui.py
Ảnh lưu ở: tests/_ui_shots/
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from tkinterdnd2 import TkinterDnD
from PIL import ImageGrab

from ui.main_window import MainWindow
from core.ext.orchestrator import run_extended_optimization
from core.ext.pile_section import DiameterTable
from core.ext.config_ext import ExtConfig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(__file__), '_ui_shots')
os.makedirs(OUT, exist_ok=True)
SAMPLE = os.path.join(ROOT, 'mcoc_input_sample', 'T7_EXT.txt')


def snap(root, name):
    root.update_idletasks()
    root.update()
    x, y = root.winfo_rootx(), root.winfo_rooty()
    w, h = root.winfo_width(), root.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    path = os.path.join(OUT, name)
    img.save(path)
    print('  saved', name, '(%dx%d)' % (w, h))


def mock_factory(params_d, dia, loads):
    """Evaluator giả: Pmax = maxN/n; momen = 0 (không cần MCOC)."""
    maxN = max((abs(l['N']) for l in loads), default=1000.0)

    def ev(coords):
        n = max(len(coords), 1)
        pmax = maxN / n
        return {'pmax': pmax, 'pmin': -0.05 * pmax, 'mxmax': 0.0, 'mymax': 0.0}
    return ev


def main():
    root = TkinterDnD.Tk()
    app = MainWindow(root)
    root.geometry('1600x1020')
    root.update()
    snap(root, '01_empty.png')

    # 1) Nạp file mẫu (bỏ qua hộp thoại)
    app.process_multiple_files([SAMPLE])
    root.update()
    snap(root, '02_loaded.png')
    print('  L_X=%s L_Y=%s d=%s Po=%s  | %d to hop tai'
          % (app.params['L_X'].get(), app.params['L_Y'].get(),
             app.params['D_PILE'].get(), app.params['P_LIMIT'].get(), len(app.loads)))

    # 2) Dựng kết quả TỐI ƯU MỞ RỘNG bằng evaluator giả
    params = app.get_params_dict()
    params['input_filepath'] = app.input_filepath
    params['mock_mode'] = True
    table = DiameterTable([(1.0, 300.0), (1.2, 500.0), (1.5, 900.0)])
    cfg = ExtConfig(enable_R7=True, enable_R8=True, cap_round_to=0.1, cap_resize=True)
    out = run_extended_optimization(
        params, list(app.loads), table, cfg=cfg, evaluator_factory=mock_factory,
        d_orig=float(app.params['D_PILE'].get()), Po_orig=float(app.params['P_LIMIT'].get()),
        pop_size=12, n_gen=6, seed=0, secondary='compact')

    app._show_ext_results(out, cfg)
    root.update()
    snap(root, '03_ext_recommended.png')

    cap = out['cap_report']
    rec = out['recommended']
    orig = out['original_config']
    print('  BE: goc %.2fx%.2f -> de xuat %.2fx%.2f'
          % (cap['old_LX'], cap['old_LY'], cap['new_LX'], cap['new_LY']))
    print('  rec.cap = %s x %s   | orig.cap = %s x %s'
          % (rec.get('cap_lx'), rec.get('cap_ly'), orig.get('cap_lx'), orig.get('cap_ly')))

    # 3) Xem PHƯƠNG ÁN GỐC (phải vẽ trong bệ GỐC, không phải bệ đã thu)
    app.cb_config.set('Phương án gốc')
    app.update_simulation()
    root.update()
    snap(root, '04_phuong_an_goc.png')

    # 4) Xem PHƯƠNG ÁN ĐỀ XUẤT
    app.cb_config.set('Phương án đề xuất')
    app.update_simulation()
    root.update()
    snap(root, '05_phuong_an_de_xuat.png')

    # 5) Bảng kiểm tra điều kiện R1–R8 (audit)
    app.view_mode.set('audit')
    app.update_simulation()
    root.update()
    snap(root, '06_audit_R1_R8.png')

    # 6) Quay lại mặt bằng + đổi tổ hợp tải (nếu có nhiều)
    app.view_mode.set('layout')
    if app.cb_load_case['values'] and len(app.cb_load_case['values']) > 1:
        app.cb_load_case.current(len(app.cb_load_case['values']) - 1)
    app.update_simulation()
    root.update()
    snap(root, '07_layout_last_load.png')

    # 7) Tab 2 - Hàng loạt (Batch)
    try:
        app.notebook.select(1)
        root.update()
        snap(root, '08_tab_batch.png')
    except Exception as e:
        print('  (khong chuyen duoc tab batch:', e, ')')

    print('XONG. Anh o:', OUT)
    root.destroy()


if __name__ == '__main__':
    main()
