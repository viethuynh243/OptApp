"""
_scenarios.py - NGUỒN DỮ LIỆU KỊCH BẢN DÙNG CHUNG cho mọi script kiểm chứng.

Gom về một chỗ để ĐỒNG NHẤT dữ liệu giữa các "chiều" kiểm chứng
(validate_mcoc, validate_method, sweep_constraints):
không còn định nghĩa hồ sơ rải rác, lệch nhau giữa các script.

  - MOCK_CASES      : 4 hồ sơ bệ/tải dùng cho các chiều mock (tối ưu, khả thi,
                      Pareto, ổn định, cân bằng tĩnh).
  - FIDELITY_SAMPLE : mẫu MCOC để kiểm round-trip / predictor (§5.5–§5.6).
  - CONSTRAINT_SAMPLE: mẫu MCOC để quét ngưỡng R5/R5b/R6 (§5.9) — bệ lớn,
                      tải cỡ nghìn để n* dao động mạnh khi đổi tham số.
  - PO_VALS/CT_VALS/M_VALS: dải ngưỡng quét cho ba ràng buộc sức chịu.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCOC_LNK = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\MCOC Python\MCOC Batch (Command Line).lnk"


# ----------------------------------------------------------------------------
# 4 hồ sơ mock dùng chung (chiều 1–4, 7)
# ----------------------------------------------------------------------------
MOCK_CASES = [
    dict(name="C1 bệ nhỏ",   L_X=6.0,  L_Y=9.6,  D_PILE=1.2, P_LIMIT=500.0,
         loads=[{'N': 2000, 'Mx': 800,  'My': 600}]),
    dict(name="C2 bệ vừa",   L_X=12.0, L_Y=15.0, D_PILE=1.0, P_LIMIT=420.0,
         loads=[{'N': 4200, 'Mx': 1500, 'My': 1000}]),
    dict(name="C3 bệ lớn",   L_X=14.0, L_Y=16.0, D_PILE=1.0, P_LIMIT=500.0,
         loads=[{'N': 4000, 'Mx': 1500, 'My': 1000}]),
    dict(name="C4 lệch tâm", L_X=12.0, L_Y=18.0, D_PILE=1.0, P_LIMIT=450.0,
         loads=[{'N': 3000, 'Mx': 2500, 'My': 400}]),
]


def mock_params(c):
    """Tham số tối ưu (chế độ mock) cho một hồ sơ trong MOCK_CASES."""
    return dict(L_X=c['L_X'], L_Y=c['L_Y'], D_PILE=c['D_PILE'],
                SAFE_D=c['D_PILE'], P_LIMIT=c['P_LIMIT'], P_TENSION=0.0,
                M_LIMIT=0.0, mock_mode=True)


# ----------------------------------------------------------------------------
# Mẫu MCOC
# ----------------------------------------------------------------------------
def _sample(name):
    """Đường dẫn tới một file input MCOC trong mcoc_input_sample/."""
    return os.path.join(ROOT, "mcoc_input_sample", name + ".txt")


FIDELITY_SAMPLE = _sample("T1_EXT")          # round-trip/predictor (§5.5–§5.6)

# Bộ hồ sơ MCOC THẬT để quét ngưỡng R5/R5b/R6 (§5.9) — trải từ bệ nhỏ tới bệ lớn,
# để chứng minh "đổi ngưỡng vẫn tìm được tối ưu" XUYÊN SUỐT trên nhiều hồ sơ thật.
#   T1: bệ 6×9,6 (n* 3–6) · T7: 9,6×16,8 (3–15, có nhổ) · T8: 34×22 (3–25, có nhổ)
#   T11: 34×28 (3–30) · T14: 34×22 (3–25)
# Lưu ý: các file input để mặc định [Po]=500, [Ct]=[M]=0; dải ngưỡng kiểm nghiệm
# KHÔNG lấy mặc định mà SUY TỪ nội lực thật của từng pool (xem sweep_constraints.py).
CONSTRAINT_SAMPLES = [_sample(n) for n in ("T1_EXT", "T7_EXT", "T8_EXT", "T11_EXT", "T14_EXT")]
