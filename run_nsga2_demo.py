"""
run_nsga2_demo.py - Demo NSGA-II tối ưu đa mục tiêu bố trí cọc (dùng mock, không cần MCOC).

Script chạy thuật toán tiến hóa đa mục tiêu NSGA-II để tìm mặt Pareto các phương
án bố trí cọc, sau đó in mặt Pareto và phương án kiến nghị ra màn hình. Mặc định
dùng chế độ mock (công thức bệ cứng) nên không cần phần mềm MCOC.

Cách chạy:
    cd d:/Project/TEDI/OptApp
    python run_nsga2_demo.py

Để đánh giá bằng MCOC EXACT, xem phần ghi chú ở cuối file (dưới if __name__).
"""

import sys
import os
import io
import time

# Ép mã hóa console về UTF-8 và bảo đảm import được từ thư mục gốc dự án
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.nsga2_optimizer import run_nsga2
from io_handlers.report_writer import export_technical_report

# =============================================================================
# === NHAP DU LIEU (giong run_demo.py de doi chieu) ===
# =============================================================================

# --- Thong so be & coc (giong run_demo.py de doi chieu) ---
params = {
    'L_X': 6.0, 'L_Y': 9.6, 'D_PILE': 1.2, 'SAFE_D': 1.2,
    'P_LIMIT': 500.0, 'P_TENSION': 0.0, 'M_LIMIT': 0.0,
    'mock_mode': True,
    'original_coords': [
        [-1.5, -3.0], [1.5, -3.0],
        [-1.5,  0.0], [1.5,  0.0],
        [-1.5,  3.0], [1.5,  3.0],
    ],
    'orig_pmax': 519.63, 'orig_pmin': 0.0,
    'orig_mxmax': 7.49, 'orig_mymax': 27.82,
}
loads = [
    {'Hx': 0.0, 'Hy': 0.0, 'N': 2577.0, 'Mx': 1500.0, 'My': 1500.0, 'Mz': 0.0},
    {'Hx': 0.0, 'Hy': 0.0, 'N': 2400.0, 'Mx':  800.0, 'My': 2000.0, 'Mz': 0.0},
    {'Hx': 0.0, 'Hy': 0.0, 'N': 2800.0, 'Mx': 1800.0, 'My': 1200.0, 'Mz': 0.0},
]

# =============================================================================
# === CHAY NSGA-II & IN KET QUA ===
# =============================================================================

LINE = "=" * 70


def main():
    """Chạy NSGA-II, in mặt Pareto và phương án kiến nghị kèm thời gian tính toán."""
    # In tiêu đề và thông số bệ - cọc
    print(LINE)
    print("  NSGA-II - Toi Uu Da Muc Tieu Bo Tri Coc Mong Cau")
    print(LINE)
    print(f"  Be: {params['L_X']} x {params['L_Y']} m | Coc d={params['D_PILE']} m"
          f" | Po={params['P_LIMIT']} T")
    print(LINE)

    # Chạy thuật toán NSGA-II và đo thời gian tính toán
    t0 = time.perf_counter()
    res = run_nsga2(params, loads, pop_size=40, n_gen=30, seed=1,
                    log=lambda m: print("  " + m))
    dt = time.perf_counter() - t0

    # In mặt Pareto: các phương án không bị thống trị
    print(f"\n  MAT PARETO ({len(res['pareto_front'])} phuong an khong bi thong tri)")
    print(f"  {'Kieu':<5} {'nx':>3} {'ny':>3} {'n':>4} {'sx':>7} {'sy':>7} {'Pmax(T)':>9}")
    print("  " + "-" * 48)
    for c in res['pareto_front']:
        print(f"  {c['type']:<5} {c['nx']:>3} {c['ny']:>3} {c['n']:>4} "
              f"{c['sx']:>7.2f} {c['sy']:>7.2f} {c['pmax']:>9.1f}")

    # In phương án kiến nghị chọn ra từ mặt Pareto
    rec = res['recommended']
    print(f"\n  PHUONG AN KIEN NGHI")
    if rec:
        print(f"  Kieu {rec['type']} {rec['nx']}x{rec['ny']} | {rec['n']} coc "
              f"| sx={rec['sx']:.2f} sy={rec['sy']:.2f} "
              f"| Pmax={rec['pmax']:.2f} T | Pmin={rec['pmin']:.2f} T")
    else:
        print("  Khong tim thay phuong an kha thi.")
    print(f"  Ly do: {res['reason']}")
    print(f"\n  So lan danh gia (n_evals): {res['n_evals']} | che do: {res['eval_mode']}")
    print(f"  [Time] {dt*1000:.0f} ms")
    print(LINE)

    # Xuất bản tính kỹ thuật ra tệp .txt (tái dùng report_writer, tương thích res NSGA-II)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "nsga2_result.txt")
    export_technical_report(out_path, res, params, loads,
                            project_name="NSGA-II demo (mock)")
    print(f"  [Xuat] Da ghi ban tinh ky thuat: {out_path}")
    print(LINE)


if __name__ == "__main__":
    # Chạy demo NSGA-II ở chế độ mock (mặc định)
    main()

    # ----- DANH GIA MCOC EXACT (bo comment khi co MCOC_Batch.exe) -----------
    # from core.blackbox import MCOCBlackbox
    # params['exe_path'] = r"D:\path\to\MCOC_Batch.exe"
    # params['input_filepath'] = r"D:\...\T1_EXT.txt"   # file input MCOC goc
    # evaluator = MCOCBlackbox.make_real_evaluator(params)
    # res = run_nsga2(params, loads, evaluator=evaluator,
    #                 pop_size=20, n_gen=10, max_evals=60,
    #                 log=lambda m: print("  " + m))
