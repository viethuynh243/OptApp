import os
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

        # Khi có executable_path thực
        # subprocess.run([executable_path, 'input.txt', 'output.txt'])
        # return parse_mcoc_result_file('output.txt'), "Kết quả từ phần mềm"
        return None, "Chưa cài đặt lệnh gọi subprocess."

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

        # Kiểm tra có phải phương án gốc không
        is_original = False
        if orig_n == n and orig_n > 0:
            coords_arr = np.array(coords, dtype=float)
            orig_arr = np.array(orig_coords, dtype=float)
            is_original = np.allclose(coords_arr, orig_arr, atol=1e-3)

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

            orig_pmax = params.get('orig_pmax', 519.63)
            orig_pmin = params.get('orig_pmin', 0.0)
            orig_mxmax = params.get('orig_mxmax', 7.49)
            orig_mymax = params.get('orig_mymax', 27.82)
            return {
                'pmax': orig_pmax, 'pmin': orig_pmin,
                'mxmax': orig_mxmax, 'mymax': orig_mymax
            }, "Kết quả từ params gốc"

        # ─────────────────────────────────────────────────────────────────────
        # Phương án mới: tính Pmax theo công thức bệ cứng,
        # hiệu chỉnh bằng hệ số calibration từ phương án gốc.
        # ─────────────────────────────────────────────────────────────────────
        coords_arr = np.array(coords, dtype=float)

        # Tính Pmax lý thuyết cho phương án mới
        pmax_new = MCOCBlackbox._rigid_cap_pmax(coords_arr, loads)

        # Tính Pmax lý thuyết cho phương án gốc (để lấy hệ số hiệu chỉnh)
        if orig_n > 0:
            orig_arr = np.array(orig_coords, dtype=float)
            pmax_orig_theory = MCOCBlackbox._rigid_cap_pmax(orig_arr, loads)
            pmax_orig_actual = params.get('orig_pmax', 519.63)

            # Hệ số hiệu chỉnh (MCOC / Lý thuyết bệ cứng)
            if pmax_orig_theory > 0:
                calibration = pmax_orig_actual / pmax_orig_theory
            else:
                calibration = 1.0
        else:
            calibration = 1.0

        pmax_calibrated = pmax_new * calibration

        # Pmin (cọc chịu kéo)
        pmin_new = MCOCBlackbox._rigid_cap_pmin(coords_arr, loads)
        pmin_calibrated = pmin_new * calibration

        # Uoc luong Mxmax, Mymax (ty le nghich voi so coc: it coc thi tung coc phai chiu uon nhieu hon)
        orig_mxmax = params.get('orig_mxmax', 7.49)
        orig_mymax = params.get('orig_mymax', 27.82)
        m_calibration = float(orig_n) / n if (n > 0 and orig_n > 0) else 1.0
        
        mxmax_calibrated = orig_mxmax * m_calibration
        mymax_calibrated = orig_mymax * m_calibration

        return {
            'pmax': round(pmax_calibrated, 2),
            'pmin': round(pmin_calibrated, 2),
            'mxmax': round(mxmax_calibrated, 2),
            'mymax': round(mymax_calibrated, 2)
        }, "Ước lượng hiệu chỉnh (%d cọc)" % n

    @staticmethod
    def _rigid_cap_pmax(coords_arr, loads):
        """Tính Pmax theo công thức bệ cứng (Rigid Pile Cap)."""
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
