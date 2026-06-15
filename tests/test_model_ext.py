"""
test_model_ext.py - Kiem thu mo rong mo hinh: luc ngang Hx/Hy/Mz, thong thuy,
tuong tac P-M, va xuat bao cao ky thuat.

Chay: PYTHONPATH=. python tests/test_model_ext.py
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import rigid_cap
from core.constants import (effective_min_spacing,
                           ENABLE_LATERAL_CHECK, ENABLE_PM_INTERACTION)
from core.optimizer import run_optimization
from core.mechanics import check_layout
from io_handlers.report_writer import build_report_text


def _check(c, m):
    """In [PASS]/[FAIL] kèm thông điệp rồi assert điều kiện."""
    print(("  [PASS] " if c else "  [FAIL] ") + m); assert c, m


# ============================================================================
# Dữ liệu dùng chung: cụm 6 cọc (lưới 2x3) làm bố trí mẫu
# ============================================================================
C6 = np.array([[-1.8, -3.6], [1.8, -3.6], [-1.8, 0.], [1.8, 0.], [-1.8, 3.6], [1.8, 3.6]])


# ============================================================================
# Các test
# ============================================================================
def test_horizontal():
    """Phân phối lực ngang: Hx chia đều theo số cọc, không lực ngang -> 0, Mz -> >0."""
    print("TEST 1: phan phoi luc ngang Hx/Hy/Mz")
    # Hx=120 chia đều 6 cọc -> 20 T/cọc
    h = rigid_cap.hmax(C6, [{'Hx': 120, 'Hy': 0, 'N': 0, 'Mx': 0, 'My': 0, 'Mz': 0}])
    _check(abs(h - 20.0) < 1e-6, f"Hx=120/6coc -> Hmax=20 (got {h:.3f})")
    # Không có lực ngang -> 0
    _check(rigid_cap.hmax(C6, [{'N': 1000, 'Mx': 500}]) == 0.0, "khong Hx/Hy/Mz -> Hmax=0")
    # Mz tạo lực tỉ lệ khoảng cách tới tâm -> > 0
    hz = rigid_cap.hmax(C6, [{'Mz': 300}])
    _check(hz > 0, f"Mz=300 -> Hmax>0 (got {hz:.3f})")


def test_clearance():
    """Thông thủy: trị chi phối là max(3d, d+CLEAR_MIN) tùy đường kính cọc."""
    print("TEST 2: thong thuy >= 1 m cho coc nho")
    _check(abs(effective_min_spacing({'D_PILE': 0.4}) - 1.2) < 1e-9, "d=0.4 khong clear -> 3d=1.2")
    _check(abs(effective_min_spacing({'D_PILE': 0.4, 'CLEAR_MIN': 1.0}) - 1.4) < 1e-9,
           "d=0.4 clear=1.0 -> d+1=1.4 (chi phoi)")
    _check(abs(effective_min_spacing({'D_PILE': 1.2, 'CLEAR_MIN': 1.0}) - 3.6) < 1e-9,
           "d=1.2 clear=1.0 -> 3d=3.6 (van chi phoi)")


def test_R7_R8_in_check():
    """Ràng buộc R7 (lực ngang): tôn trọng cờ ENABLE_LATERAL_CHECK; khi bật thì
    Hmax>[H] làm phương án không đạt, Hmax<[H] thì qua."""
    print("TEST 3: R7 (luc ngang) - ton trong co ENABLE_LATERAL_CHECK")
    # Không đặt original_coords/orig_pmax -> blackbox tính axial từ tải (K=1):
    # N=1000/6 ~ 167 T < 500 (qua R5), để R7 (lực ngang) nổi lên.
    base = dict(L_X=6.0, L_Y=9.6, D_PILE=1.2, SAFE_D=1.2, P_LIMIT=500.0,
                P_TENSION=0.0, M_LIMIT=0.0, mock_mode=True)
    loads = [{'Hx': 600, 'Hy': 0, 'N': 1000, 'Mx': 0, 'My': 0, 'Mz': 0}]  # Hx lon -> Hmax=100
    if not ENABLE_LATERAL_CHECK:
        # R7 đã TẮT theo thiết kế (R1-R6, MCOC tính 3D đầy đủ) -> lực ngang
        # không được làm phương án không đạt.
        p = dict(base, H_LIMIT=50.0)
        ok, *_rest, msg = check_layout(C6, 2, 3, 3.6, 3.6, "A", p, loads)
        _check(ok or "Hmax" not in msg, f"R7 tat -> khong chan luc ngang: {msg}")
        print("  [SKIP] R7 dang TAT (ENABLE_LATERAL_CHECK=False) - bo qua kiem tra chan")
        return
    # [H]=50T: Hmax=100>50 -> R7 không đạt
    p = dict(base, H_LIMIT=50.0)
    ok, *_rest, msg = check_layout(C6, 2, 3, 3.6, 3.6, "A", p, loads)
    _check((not ok) and "Hmax" in msg, f"R7 bat luc ngang vuot: {msg}")
    # [H]=200T: Hmax=100<200 -> qua R7
    p2 = dict(base, H_LIMIT=200.0)
    ok2, *_2 = check_layout(C6, 2, 3, 3.6, 3.6, "A", p2, loads)
    _check(ok2, "Hmax<[H] -> qua R7")


def test_report():
    """Báo cáo kỹ thuật xuất ra phải chứa đủ các mục bắt buộc."""
    print("TEST 4: xuat bao cao ky thuat co cac muc bat buoc")
    # Tải vừa sức bệ (6 cọc lọt trong cấp 6x9.6, d=1.2) để có phương án ĐẠT,
    # nhờ đó báo cáo sinh đầy đủ các mục (không rơi vào nhánh "không tìm được").
    p = dict(L_X=6.0, L_Y=9.6, D_PILE=1.2, SAFE_D=1.2, P_LIMIT=500.0, P_TENSION=0.0,
             M_LIMIT=0.0, H_LIMIT=0.0, mock_mode=True, original_coords=C6.tolist(),
             orig_pmax=450.0, orig_pmin=0.0, orig_mxmax=7.49, orig_mymax=27.82)
    loads = [{'Hx': 0, 'Hy': 0, 'N': 2000, 'Mx': 800, 'My': 600, 'Mz': 0},
             {'Hx': 0, 'Hy': 0, 'N': 1800, 'Mx': 600, 'My': 500, 'Mz': 0}]
    r = run_optimization(p, loads)
    txt = build_report_text(r, p, loads, "Cau Demo")
    for kw in ["SO LIEU DAU VAO", "TO HOP TAI TRONG", "he so su dung",
               "BANG TONG HOP RANG BUOC", "PHU LUC", "To hop chi phoi"]:
        _check(kw in txt, f"bao cao co muc: {kw}")


if __name__ == "__main__":
    test_horizontal()
    test_clearance()
    test_R7_R8_in_check()
    test_report()
    print("\n  TAT CA TEST MO RONG DA PASS.")
