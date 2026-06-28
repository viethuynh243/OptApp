"""blackbox.py - Hộp đen đánh giá nội lực 1 phương án cọc (mock bệ cứng / MCOC thực).

Cung cấp lớp MCOCBlackbox với hai chế độ đánh giá một bố trí cọc:
    - Mock (bệ cứng có hiệu chỉnh): tính nhanh bằng công thức bệ cứng,
      hiệu chỉnh theo hệ số K rút ra từ kết quả MCOC của phương án gốc.
    - MCOC thực: ghi file input, gọi chương trình MCOC ngoài và đọc kết quả.

Kết quả trả về là dict {'pmax','pmin','mxmax','mymax','forces'} cùng một
thông điệp mô tả nguồn gốc kết quả.
"""

import os
import numpy as np
from io_handlers.file_io import parse_mcoc_result_file
from core import rigid_cap


class MCOCBlackbox:
    """Hộp đen đánh giá nội lực một phương án bố trí cọc."""

    # ========================================================================
    # ĐÁNH GIÁ CHUNG (chọn mock hoặc MCOC thực)
    # ========================================================================
    @staticmethod
    def evaluate_layout(coords, loads, params, executable_path="", mock_mode=True):
        """Đánh giá 1 bố trí cọc: dùng mock hoặc gọi MCOC thực.

        Trả về (res_dict, thông_điệp); res_dict = None nếu lỗi.
        """
        # Không có file chạy hoặc bật mock -> tính nhanh bằng mock bệ cứng
        if mock_mode or not executable_path:
            return MCOCBlackbox._mock_execution(coords, loads, params)
        # Ngược lại gọi MCOC thực qua evaluator
        try:
            evaluator = MCOCBlackbox.make_real_evaluator(params, loads=loads)
            res = evaluator(coords)
            return res, "Ket qua MCOC thuc (" + os.path.basename(res.get('result_path', '')) + ")"
        except Exception as e:
            return None, "Loi goi MCOC (%s): %s" % (type(e).__name__, e)

    # ========================================================================
    # ĐÁNH GIÁ MCOC THỰC (ghi input - chạy chương trình - đọc kết quả)
    # ========================================================================
    @staticmethod
    def make_real_evaluator(params, loads=None, log=None):
        """evaluator(coords)->dict goi MCOC thuc. loads != None -> ghi de tai tu UI.

        Tạo hàm đánh giá đóng (closure) dùng lại template input và runner.
        Mỗi lần gọi sẽ ghi 1 file input mới rồi chạy MCOC trên file đó.
        """
        from core.mcoc_runner import MCOCRunner
        from io_handlers.mcoc_writer import MCOCTemplate
        # Bắt buộc phải có file input MCOC gốc và toạ độ cọc gốc
        input_file = params.get('input_filepath', '')
        if not input_file or not os.path.exists(input_file):
            raise ValueError("Chua co file input MCOC goc (params['input_filepath']).")
        if not params.get('original_coords'):
            raise ValueError("Chua co original_coords de nhan dien khoi coc.")
        # Chuẩn bị template input + runner + thư mục làm việc tạm
        template = MCOCTemplate(input_file, params['original_coords'])
        runner = MCOCRunner(params['exe_path'], log=log)
        workdir = os.path.join(os.path.dirname(os.path.abspath(input_file)), "_opt_runs")
        os.makedirs(workdir, exist_ok=True)
        base = os.path.splitext(os.path.basename(input_file))[0]
        counter = [0]

        def evaluator(coords):
            """Ghi file input cho 1 bố trí rồi chạy MCOC, trả về dict kết quả."""
            counter[0] += 1
            in_path = os.path.join(workdir, "%s_opt%03d.txt" % (base, counter[0]))
            template.write(coords, in_path, name_suffix="OPT%03d" % counter[0], loads=loads)
            return runner.run(in_path)

        # Gắn kèm runner và workdir để bên ngoài truy cập khi cần
        evaluator.runner = runner
        evaluator.workdir = workdir
        return evaluator

    # ========================================================================
    # ĐÁNH GIÁ MOCK BỆ CỨNG (tính nhanh có hiệu chỉnh)
    # ========================================================================
    @staticmethod
    def make_mock_evaluator(params, loads):
        """Tạo evaluator(coords)->dict tính bằng mock bệ cứng (không gọi MCOC)."""
        def evaluator(coords):
            res, _ = MCOCBlackbox._mock_execution(np.asarray(coords, dtype=float), loads, params)
            return res
        return evaluator

    @staticmethod
    def _mock_execution(coords, loads, params):
        """Ước lượng nội lực bằng công thức bệ cứng có hiệu chỉnh hệ số K.

        Nếu bố trí trùng phương án gốc thì trả thẳng kết quả thực của phương
        án gốc. Ngược lại tính bệ cứng cho bố trí mới rồi nhân hệ số hiệu
        chỉnh K (rút từ phương án gốc) cho lực; mô men được ước lượng theo
        tỉ lệ số cọc.
        Trả về (res_dict, thông_điệp).
        """
        coords = np.asarray(coords, dtype=float)
        n = len(coords)
        if n == 0:
            return None, "Khong co coc"
        orig_coords = params.get('original_coords', [])
        orig_n = len(orig_coords)
        # Trùng phương án gốc -> dùng kết quả thực đã có
        if MCOCBlackbox._is_original(coords, orig_coords):
            return MCOCBlackbox._eval_original(coords, loads, params)
        # Tính bệ cứng cho bố trí mới
        pmax_new, pmin_new = rigid_cap.pmax_pmin(coords, loads)
        # Hệ số hiệu chỉnh K = Pmax_thuc_goc / Pmax_be_cung_goc
        K = 1.0
        orig_pmax_actual = params.get('orig_pmax')
        if orig_n > 0 and orig_pmax_actual is not None:
            pmax_orig_theory = rigid_cap.pmax_pmin(orig_coords, loads)[0]
            K = rigid_cap.calibration_factor(pmax_orig_theory, orig_pmax_actual)
        # Mô men ước lượng theo tỉ lệ số cọc gốc/mới
        orig_mxmax = params.get('orig_mxmax', 0.0)
        orig_mymax = params.get('orig_mymax', 0.0)
        m_cal = float(orig_n) / n if (n > 0 and orig_n > 0) else 1.0
        wf = rigid_cap.worst_case_forces(coords, loads)
        return {'pmax': round(pmax_new * K, 2), 'pmin': round(pmin_new * K, 2),
                'mxmax': round(orig_mxmax * m_cal, 2), 'mymax': round(orig_mymax * m_cal, 2),
                'forces': [round(f * K, 2) for f in wf]}, "Uoc luong hieu chinh (%d coc)" % n

    @staticmethod
    def _is_original(coords, orig_coords):
        """Kiểm tra bố trí có trùng phương án gốc không (không phụ thuộc thứ tự)."""
        orig_n = len(orig_coords)
        if orig_n == 0 or orig_n != len(coords):
            return False
        # Sắp xếp 2 tập điểm theo (x, y) rồi so khớp trong dung sai
        a = np.asarray(coords, dtype=float)
        b = np.asarray(orig_coords, dtype=float)
        ka = a[np.lexsort((a[:, 1], a[:, 0]))]
        kb = b[np.lexsort((b[:, 1], b[:, 0]))]
        return ka.shape == kb.shape and np.allclose(ka, kb, atol=1e-3)

    @staticmethod
    def _eval_original(coords, loads, params):
        """Lấy kết quả nội lực của phương án gốc theo thứ tự ưu tiên.

        Lần lượt thử: file kết quả chỉ định trong params -> file kết quả mặc
        định trên đĩa -> giá trị đã lưu sẵn trong params -> cuối cùng mới tính
        bệ cứng (K=1.0). Trả về (res_dict, thông_điệp).
        """
        # 1) File kết quả chỉ định trong params
        rf = params.get('result_filepath', '')
        if rf and os.path.exists(rf):
            res = parse_mcoc_result_file(rf)
            if res:
                return res, "Ket qua thuc tu " + rf
        # 2) File kết quả mặc định nằm sẵn trên đĩa
        for fname in ('T1_EXT_result.txt', 'T3_EXT_result.txt'):
            if os.path.exists(fname):
                res = parse_mcoc_result_file(fname)
                if res:
                    return res, "Ket qua thuc tu " + fname
        # 3) Giá trị nội lực gốc đã lưu trong params
        op = params.get('orig_pmax')
        if op is not None:
            return {'pmax': op, 'pmin': params.get('orig_pmin', 0.0),
                    'mxmax': params.get('orig_mxmax', 0.0),
                    'mymax': params.get('orig_mymax', 0.0)}, "Ket qua tu params goc"
        # 4) Phương án cuối: tính bệ cứng (K=1.0)
        pmax, pmin = rigid_cap.pmax_pmin(coords, loads)
        wf = rigid_cap.worst_case_forces(coords, loads)
        return {'pmax': round(pmax, 2), 'pmin': round(pmin, 2), 'mxmax': 0.0, 'mymax': 0.0,
                'forces': [round(f, 2) for f in wf]}, "Uoc luong be cung (K=1.0)"

    # ========================================================================
    # TIỆN ÍCH BỆ CỨNG (gói gọn lời gọi rigid_cap)
    # ========================================================================
    @staticmethod
    def _rigid_cap_pmax(coords_arr, loads):
        """Pmax theo bệ cứng - xem rigid_cap.pmax_pmin."""
        return rigid_cap.pmax_pmin(coords_arr, loads)[0]

    @staticmethod
    def _rigid_cap_pmin(coords_arr, loads):
        """Pmin theo bệ cứng - xem rigid_cap.pmax_pmin."""
        return rigid_cap.pmax_pmin(coords_arr, loads)[1]

    @staticmethod
    def _rigid_cap_forces_worst(coords_arr, loads):
        """Tổ hợp lực bất lợi nhất theo bệ cứng - xem rigid_cap.worst_case_forces."""
        return rigid_cap.worst_case_forces(coords_arr, loads)
