"""
blackbox_ext.py - Hộp đen MCOC THỰC có ĐỔI ĐƯỜNG KÍNH (mở rộng).

Tương tự MCOCBlackbox.make_real_evaluator nhưng dùng DiameterMCOCTemplate để
mỗi lần chấm còn patch tiết diện cọc (d, Fo, Jo, Po) theo đường kính đang xét.
Nhờ vậy NSGA-II có thể đánh giá CHÍNH XÁC từng đường kính ứng viên bằng MCOC.

Mỗi đường kính ứng viên -> một evaluator(coords) riêng (đóng kín d và [Po]).
Các file input tạm được tách theo đường kính để không ghi đè lẫn nhau.
"""

import os

from core.ext.pile_section import DiameterOption


# ===========================================================================
# Tạo evaluator MCOC thực gắn với một đường kính cụ thể
# ===========================================================================
def make_diameter_evaluator(params, dia, loads=None, d_orig=None,
                            Po_orig=None, log=None):
    """Tạo evaluator(coords)->dict chấm MCOC thực với đường kính của `dia`.

    Đầu vào:
        params  : tham số bài toán (phải có input_filepath, original_coords,
                  exe_path). D_PILE/P_LIMIT trong params là của FILE GỐC.
        dia     : DiameterOption — đường kính + [Po] dùng để patch file MCOC.
        loads   : danh sách tổ hợp tải (ghi đè tải từ UI); None giữ tải template.
        d_orig  : đường kính cọc GỐC trong file (m); None -> lấy params['D_PILE'].
        Po_orig : [Po] GỐC trong file (T); None -> lấy params['P_LIMIT'].
        log     : callable(str) ghi log cho runner.

    Trả về evaluator(coords) -> {'pmax','pmin','mxmax','mymax',...}.
    """
    from core.mcoc_runner import MCOCRunner
    from io_handlers.mcoc_writer_ext import DiameterMCOCTemplate

    input_file = params.get('input_filepath', '')
    if not input_file or not os.path.exists(input_file):
        raise ValueError("Chua co file input MCOC goc (params['input_filepath']).")
    if not params.get('original_coords'):
        raise ValueError("Chua co original_coords de nhan dien khoi coc.")
    if not isinstance(dia, DiameterOption):
        raise TypeError("dia phai la DiameterOption.")

    d_orig = float(params['D_PILE']) if d_orig is None else float(d_orig)
    Po_orig = float(params['P_LIMIT']) if Po_orig is None else float(Po_orig)

    template = DiameterMCOCTemplate(input_file, params['original_coords'],
                                    d_orig, Po_orig)
    runner = MCOCRunner(params['exe_path'], log=log)
    # Thư mục tạm tách theo đường kính (đặt theo mm để tránh ký tự '.')
    workdir = os.path.join(os.path.dirname(os.path.abspath(input_file)),
                           "_opt_runs", "d%04d" % int(round(dia.d * 1000)))
    os.makedirs(workdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_file))[0]
    counter = [0]

    def evaluator(coords):
        """Ghi input (patch đường kính) cho 1 bố trí rồi chạy MCOC."""
        counter[0] += 1
        in_path = os.path.join(workdir, "%s_d%04d_opt%03d.txt"
                               % (base, int(round(dia.d * 1000)), counter[0]))
        template.write_diameter(coords, in_path, dia.d, dia.Po,
                                name_suffix="D%04dOPT%03d"
                                % (int(round(dia.d * 1000)), counter[0]),
                                loads=loads)
        return runner.run(in_path)

    evaluator.runner = runner
    evaluator.workdir = workdir
    evaluator.dia = dia
    return evaluator
