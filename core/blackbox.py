import os
import tempfile
import numpy as np
from io_handlers.file_io import parse_mcoc_result_file

class MCOCBlackbox:
    @staticmethod
    def evaluate_layout(coords, loads, params, executable_path="", mock_mode=True):
        """
        Đánh giá phương án bằng mô hình Hộp đen.
        """
        if mock_mode or not executable_path:
            return MCOCBlackbox._mock_execution(coords, loads, params)

        # Gọi MCOC thực: sinh file input từ template + chạy subprocess
        try:
            evaluator = MCOCBlackbox.make_real_evaluator(params)
            res = evaluator(coords)
            return res, "Kết quả MCOC thực (" + os.path.basename(res.get('result_path', '')) + ")"
        except Exception as e:
            return None, "Lỗi gọi MCOC: %s" % e

    @staticmethod
    def make_real_evaluator(params, log=None):
        """
        Tạo evaluator(coords) -> dict gọi MCOC THỰC:
            input template + tọa độ mới -> file input -> MCOCRunner -> kết quả.
        params cần: exe_path, input_filepath (file input MCOC gốc), original_coords.
        """
        from core.mcoc_runner import MCOCRunner
        from io_handlers.mcoc_writer import MCOCTemplate

        input_file = params.get('input_filepath', '')
        if not input_file or not os.path.exists(input_file):
            raise ValueError("Chưa có file input MCOC gốc (params['input_filepath']).")
        if not params.get('original_coords'):
            raise ValueError("Chưa có original_coords để nhận diện khối cọc trong template.")

        template = MCOCTemplate(input_file, params['original_coords'])
        runner = MCOCRunner(params['exe_path'], log=log)

        # Thư mục làm việc riêng cạnh file input (MCOC ghi _result.txt tại đây)
        workdir = os.path.join(os.path.dirname(os.path.abspath(input_file)), "_opt_runs")
        os.makedirs(workdir, exist_ok=True)
        base = os.path.splitext(os.path.basename(input_file))[0]
        counter = [0]

        def evaluator(coords):
            counter[0] += 1
            in_path = os.path.join(workdir, "%s_opt%03d.txt" % (base, counter[0]))
            template.write(coords, in_path, name_suffix="OPT%03d" % counter[0])
            return runner.run(in_path)

        evaluator.runner = runner
        evaluator.workdir = workdir
        return evaluator

    @staticmethod
    def make_mock_evaluator(params, loads):
        """
        Evaluator giả lập (không cần MCOC): bệ cứng + hiệu chỉnh K từ phương án gốc.
        Dùng để chạy thử thuật toán tinh chỉnh.
        """
        def evaluator(coords):
            res, _ = MCOCBlackbox._mock_execution(np.asarray(coords, dtype=float), loads, params)
            return res
        return evaluator

    @staticmethod
    def _mock_execution(coords, loads, params):
        """
        Mô phỏng đánh giá bằng cách scale kết quả thực từ file _result.txt.
        
        Nguyên lý:
        - Phương án gốc (6 cọc): đọc trực tiếp Nmax=519.63 từ file.
        - Các phương án khác: ước lượng dựa trên công thức bệ cứng,
          sau đó hiệu chỉnh bằng hệ số lấy từ file kết quả thực.
        """
        n = len(coords)
        if n == 0:
            return None, "Không có cọc"

        orig_coords = params.get('original_coords', [])
        orig_n = len(orig_coords)

        # Kiểm tra có phải phương án gốc không (so sánh không phụ thuộc thứ tự)
        is_original = False
        if orig_n == n and orig_n > 0:
            coords_arr = np.array(coords, dtype=float)
            orig_arr = np.array(orig_coords, dtype=float)
            ka = coords_arr[np.lexsort((coords_arr[:, 1], coords_arr[:, 0]))]
            kb = orig_arr[np.lexsort((orig_arr[:, 1], orig_arr[:, 0]))]
            is_original = np.allclose(ka, kb, atol=1e-3)

        if is_original:
            # Ưu tiên đọc từ result_filepath đã lưu trong params
            result_filepath = params.get('result_filepath', '')
            if result_filepath and os.path.exists(result_filepath):
                res = parse_mcoc_result_file(result_filepath)
                if res:
                    return res, "Kết quả thực từ " + result_filepath

            # Fallback: tìm file _result.txt bất kỳ
            for fname in ['T1_EXT_result.txt', 'T3_EXT_result.txt']:
                if os.path.exists(fname):
                    res = parse_mcoc_result_file(fname)
                    if res:
                        return res, "Kết quả thực từ " + fname

            orig_pmax = params.get('orig_pmax')
            if orig_pmax is None:
                # Không có file MCOC và không có orig_pmax → dùng bệ cứng trực tiếp (K=1.0)
                orig_arr_tmp = np.array(orig_coords, dtype=float)
                pmax_t = MCOCBlackbox._rigid_cap_pmax(orig_arr_tmp, loads)
                pmin_t = MCOCBlackbox._rigid_cap_pmin(orig_arr_tmp, loads)
                forces_t = MCOCBlackbox._rigid_cap_forces_worst(orig_arr_tmp, loads)
                return {
                    'pmax': round(pmax_t, 2), 'pmin': round(pmin_t, 2),
                    'mxmax': 0.0, 'mymax': 0.0,
                    'forces': [round(f, 2) for f in forces_t]
                }, "Ước lượng bệ cứng (K=1.0, không có file MCOC)"
            orig_pmin = params.get('orig_pmin', 0.0)
            orig_mxmax = params.get('orig_mxmax', 0.0)
            orig_mymax = params.get('orig_mymax', 0.0)
            orig_arr_tmp = np.array(orig_coords, dtype=float)
            forces_t = MCOCBlackbox._rigid_cap_forces_worst(orig_arr_tmp, loads)
            # Lực per-pile hiệu chỉnh tỉ lệ với K_global (nếu có)
            pmax_theory = MCOCBlackbox._rigid_cap_pmax(orig_arr_tmp, loads)
            k_tmp = (orig_pmax / pmax_theory) if pmax_theory > 0 else 1.0
            return {
                'pmax': orig_pmax, 'pmin': orig_pmin,
                'mxmax': orig_mxmax, 'mymax': orig_mymax,
                'forces': [round(f * k_tmp, 2) for f in forces_t]
            }, "Kết quả từ params gốc"

        # ─────────────────────────────────────────────────────────────────────
        # Phương án mới: tính Pmax theo công thức bệ cứng,
        # hiệu chỉnh bằng hệ số calibration từ phương án gốc.
        # ─────────────────────────────────────────────────────────────────────
        coords_arr = np.array(coords, dtype=float)

        # Tính Pmax lý thuyết cho phương án mới
        pmax_new = MCOCBlackbox._rigid_cap_pmax(coords_arr, loads)

        # Tính hệ số hiệu chỉnh K = Pmax_MCOC_thực / Pmax_lý_thuyết_bệ_cứng
        # K bù đắp sai số mô hình và đổi đơn vị (kN → T khi dùng với MCOC).
        # Nếu không có phương án gốc hoặc không có orig_pmax → K=1.0 (bệ cứng thuần túy).
        if orig_n > 0:
            orig_arr = np.array(orig_coords, dtype=float)
            pmax_orig_theory = MCOCBlackbox._rigid_cap_pmax(orig_arr, loads)
            pmax_orig_actual = params.get('orig_pmax')  # None nếu không có MCOC data
            if pmax_orig_actual is not None and pmax_orig_theory > 0:
                calibration = pmax_orig_actual / pmax_orig_theory
            else:
                calibration = 1.0
        else:
            calibration = 1.0

        pmax_calibrated = pmax_new * calibration

        # Pmin (cọc chịu kéo)
        pmin_new = MCOCBlackbox._rigid_cap_pmin(coords_arr, loads)
        pmin_calibrated = pmin_new * calibration

        # Ước lượng Mxmax, Mymax: tỉ lệ nghịch với số cọc (ít cọc → mỗi cọc chịu uốn nhiều hơn)
        orig_mxmax = params.get('orig_mxmax', 0.0)
        orig_mymax = params.get('orig_mymax', 0.0)
        m_calibration = float(orig_n) / n if (n > 0 and orig_n > 0) else 1.0
        mxmax_calibrated = orig_mxmax * m_calibration
        mymax_calibrated = orig_mymax * m_calibration

        # Tính lực từng cọc cho tổ hợp tải bất lợi nhất (dùng cho bảng nội lực và heatmap)
        worst_forces = MCOCBlackbox._rigid_cap_forces_worst(coords_arr, loads)

        return {
            'pmax': round(pmax_calibrated, 2),
            'pmin': round(pmin_calibrated, 2),
            'mxmax': round(mxmax_calibrated, 2),
            'mymax': round(mymax_calibrated, 2),
            'forces': [round(f * calibration, 2) for f in worst_forces]
        }, "Ước lượng hiệu chỉnh (%d cọc)" % n

    @staticmethod
    def _rigid_cap_pmax(coords_arr, loads):
        """
        Tính Pmax theo công thức bệ cứng (Rigid Pile Cap):
            P_i = N/n + Mx*(yi-cy)/Ix + My*(xi-cx)/Iy
        trong đó Ix = Σ(yi-cy)², Iy = Σ(xi-cx)² là moment quán tính nhóm cọc.
        Duyệt qua toàn bộ tổ hợp tải và toàn bộ cọc, trả về giá trị lớn nhất.
        """
        n = len(coords_arr)
        if n == 0:
            return 0.0
        cx = np.mean(coords_arr[:, 0])
        cy = np.mean(coords_arr[:, 1])
        Ix = np.sum((coords_arr[:, 1] - cy) ** 2) or 1e-9
        Iy = np.sum((coords_arr[:, 0] - cx) ** 2) or 1e-9

        global_pmax = -1e18
        for load in loads:
            N = load.get('N', 0)
            Mx = load.get('Mx', 0)
            My = load.get('My', 0)
            for xi, yi in coords_arr:
                dx = xi - cx
                dy = yi - cy
                p = N / n + Mx * dy / Ix + My * dx / Iy
                if p > global_pmax:
                    global_pmax = p
        return global_pmax

    @staticmethod
    def _rigid_cap_pmin(coords_arr, loads):
        """Tính Pmin theo công thức bệ cứng."""
        n = len(coords_arr)
        if n == 0:
            return 0.0
        cx = np.mean(coords_arr[:, 0])
        cy = np.mean(coords_arr[:, 1])
        Ix = np.sum((coords_arr[:, 1] - cy) ** 2) or 1e-9
        Iy = np.sum((coords_arr[:, 0] - cx) ** 2) or 1e-9

        global_pmin = 1e18
        for load in loads:
            N = load.get('N', 0)
            Mx = load.get('Mx', 0)
            My = load.get('My', 0)
            for xi, yi in coords_arr:
                dx = xi - cx
                dy = yi - cy
                p = N / n + Mx * dy / Ix + My * dx / Iy
                if p < global_pmin:
                    global_pmin = p
        return global_pmin

    @staticmethod
    def _rigid_cap_forces_worst(coords_arr, loads):
        """
        Trả về list lực từng cọc [P1, P2, ..., Pn] cho tổ hợp tải bất lợi nhất
        (tổ hợp có Pmax lớn nhất). Dùng cho bảng nội lực và heatmap trực quan.
        """
        n = len(coords_arr)
        if n == 0:
            return []
        cx = np.mean(coords_arr[:, 0])
        cy = np.mean(coords_arr[:, 1])
        Ix = float(np.sum((coords_arr[:, 1] - cy) ** 2)) or 1e-9
        Iy = float(np.sum((coords_arr[:, 0] - cx) ** 2)) or 1e-9

        best_forces = [0.0] * n
        best_pmax = -1e18
        for load in loads:
            N = load.get('N', 0)
            Mx = load.get('Mx', 0)
            My = load.get('My', 0)
            forces = []
            for xi, yi in coords_arr:
                p = N / n + Mx * (yi - cy) / Ix + My * (xi - cx) / Iy
                forces.append(p)
            load_pmax = max(forces)
            if load_pmax > best_pmax:
                best_pmax = load_pmax
                best_forces = forces
        return best_forces
