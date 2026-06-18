"""_test_cases.py - KIỂM TRA các trường hợp: chạy bộ tối ưu (NSGA-II) trên từng
file *_EXT trong mcoc_input_sample/ bằng mô hình bệ cứng (mock, KHÔNG cần MCOC).

[Po] trong file chỉ là MẶC ĐỊNH (500). Để mỗi ca KHẢ THI, đặt [Po] = làm tròn lên
của Pmax phương án gốc (util gốc ≈ 1.0) rồi xem bộ tối ưu có tìm được phương án
ÍT CỌC HƠN / Pmax thấp hơn mà vẫn ĐẠT không. Mục tiêu: phát hiện crash, phương án
rỗng, hoặc vi phạm hình học — không phải để lấy số liệu thiết kế.

Chạy:  python tests/_test_cases.py
"""
import os
import sys
import io
import math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from io_handlers.file_io import parse_input_file
from core import rigid_cap
from core.blackbox import MCOCBlackbox
from core.nsga2_optimizer import run_nsga2

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'mcoc_input_sample')


def run_one(path):
    name = os.path.basename(path)
    params, loads, proj = parse_input_file(path)
    coords = params.get('original_coords') or []
    if not coords or not loads:
        return {'name': name, 'note': 'thieu coords/loads'}

    c = np.asarray(coords, float)
    P = rigid_cap.forces_all_loads(c, loads)
    orig_pmax = float(P.max()); orig_pmin = float(P.min())
    n_orig = len(coords)

    # [Po] khả thi: làm tròn lên 50T trên Pmax gốc; [Ct] = |Pmin| nếu có nhổ.
    Po = math.ceil(orig_pmax / 50.0) * 50.0
    params['P_LIMIT'] = Po
    params['P_TENSION'] = math.ceil(abs(min(orig_pmin, 0.0)) / 50.0) * 50.0
    params['M_LIMIT'] = 0.0          # bỏ R6 (mock momen chỉ ước lượng)
    params['mock_mode'] = True
    params['SAFE_D'] = params.get('D_PILE', 1.2)

    evaluator = MCOCBlackbox.make_mock_evaluator(params, loads)
    res = run_nsga2(params, loads, evaluator=evaluator,
                    pop_size=16, n_gen=8, max_evals=90, seed=0, secondary='compact')
    rec = res.get('recommended')
    nvalid = len(res.get('all_valid_configs', []))
    out = {'name': name, 'n_orig': n_orig, 'orig_pmax': orig_pmax, 'Po': Po,
           'nvalid': nvalid, 'evals': res.get('n_evals', 0)}
    if rec:
        out.update({'n_opt': rec['n'], 'opt_pmax': rec['pmax'],
                    'sx': rec.get('sx', 0), 'sy': rec.get('sy', 0),
                    'type': rec.get('type', '?')})
    else:
        out['note'] = 'KHONG tim duoc phuong an: ' + res.get('reason', '')[:40]
    return out


def main():
    files = sorted(f for f in os.listdir(DIR)
                   if f.lower().endswith('_ext.txt'))
    print('Chay toi uu (mock be cung) tren %d file EXT\n' % len(files))
    hdr = ('%-12s %5s %9s %7s %5s %8s %6s %6s %4s  %s'
           % ('FILE', 'n_org', 'Pmax_org', '[Po]*', 'n_opt', 'Pmax_opt',
              'sx', 'sy', 'kieu', 'GHI CHU'))
    print(hdr); print('-' * len(hdr))
    n_found = 0
    for f in files:
        try:
            r = run_one(os.path.join(DIR, f))
        except Exception as e:
            print('%-12s  !! LOI: %s' % (f, e))
            continue
        if 'n_opt' in r:
            n_found += 1
            saved = r['n_orig'] - r['n_opt']
            note = ('giam %d coc' % saved) if saved > 0 else (
                'bang so coc' if saved == 0 else 'TANG %d coc' % (-saved))
            print('%-12s %5d %9.1f %7.0f %5d %8.1f %6.2f %6.2f %4s  %s'
                  % (r['name'], r['n_orig'], r['orig_pmax'], r['Po'],
                     r['n_opt'], r['opt_pmax'], r['sx'], r['sy'],
                     r['type'], note))
        else:
            print('%-12s %5d %9.1f %7s  %s'
                  % (r['name'], r.get('n_orig', 0), r.get('orig_pmax', 0),
                     '-', r.get('note', '')))
    print('-' * len(hdr))
    print('\n%d/%d ca tim duoc phuong an ĐẠT.' % (n_found, len(files)))


if __name__ == '__main__':
    main()
