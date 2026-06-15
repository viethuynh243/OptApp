"""
run_demo.py - Script demo chạy OptApp trực tiếp (không cần giao diện đồ họa).

Chạy toàn bộ quy trình tối ưu bố trí cọc từ dòng lệnh: nhập thông số bệ - cọc,
nhập các tổ hợp tải trọng, gọi bộ tối ưu rồi in báo cáo ra màn hình (phương án
gốc, các phương án quét được, phương án kiến nghị và bảng nội lực từng cọc).

Cách chạy:
    cd d:/Project/TEDI/OptApp
    python run_demo.py

Thay đổi dữ liệu trong block '=== NHAP DU LIEU ===' để thử nghiệm các kịch bản.
"""

import sys
import os
import time
import io

# Ép mã hóa console Windows về UTF-8 để in được tiếng Việt có dấu
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Bảo đảm import được từ thư mục gốc dự án
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.optimizer import run_optimization
from core.generator import generate_coords
from core.mechanics import check_layout

# =============================================================================
# === NHAP DU LIEU TUY Y TAI DAY ===
# Thay đổi các giá trị bên dưới để kiểm thử các kịch bản khác nhau.
# =============================================================================

SCENARIO = "T1_EXT"   # Ten kich ban (chi de hien thi)

# --- Thong so be & coc ---
params = {
    'L_X'       : 6.0,     # Chieu rong be Lx (m)
    'L_Y'       : 9.6,     # Chieu dai be Ly (m)
    'D_PILE'    : 1.2,     # Duong kinh coc d (m)
    'SAFE_D'    : 1.2,     # Khoang cach toi thieu tim coc den mep be (m)
    'P_LIMIT'   : 500.0,   # Suc chiu nen cho phep Po (T)
    'P_TENSION' : 0.0,     # Suc chiu nho cho phep Ct (T), 0 = bo qua
    'M_LIMIT'   : 0.0,     # Suc chiu uon cho phep Mmax (T.m), 0 = bo qua
    'mock_mode' : True,    # True = dung Be Cung + Calibration (khong can MCOC)

    # Phuong an goc (neu co) — dung de so sanh & calibration
    'original_coords': [
        [-1.5, -3.0],  # Coc 1
        [ 1.5, -3.0],  # Coc 2
        [-1.5,  0.0],  # Coc 3
        [ 1.5,  0.0],  # Coc 4
        [-1.5,  3.0],  # Coc 5
        [ 1.5,  3.0],  # Coc 6
    ],
    # Ket qua thuc tu MCOC de hieu chinh (Calibration)
    'orig_pmax' : 519.63,
    'orig_pmin' :   0.0,
    'orig_mxmax':   7.49,
    'orig_mymax':  27.82,
}

# --- To hop tai trong ---
# Moi to hop: Hx, Hy (kN) - luc ngang; N (kN) - luc dung;
#              Mx, My (kNm) - momen; Mz (kNm) - momen xoan
loads = [
    {'Hx':  0.0, 'Hy':  0.0, 'N': 2577.0, 'Mx': 1500.0, 'My': 1500.0, 'Mz': 0.0},
    {'Hx':  0.0, 'Hy':  0.0, 'N': 2400.0, 'Mx':  800.0, 'My': 2000.0, 'Mz': 0.0},
    {'Hx':  0.0, 'Hy':  0.0, 'N': 2800.0, 'Mx': 1800.0, 'My': 1200.0, 'Mz': 0.0},
]

# =============================================================================
# === CHAY TOI UU & IN KET QUA ===
# Các hàm in báo cáo bên dưới chỉ định dạng và xuất kết quả ra màn hình.
# =============================================================================

LINE = "=" * 70

def print_header():
    """In tiêu đề: tên kịch bản, kích thước bệ - cọc và các sức chịu cho phép."""
    print(LINE)
    print(f"  OPT APP - Toi Uu Hoa Bo Tri Coc Mong Cau")
    print(f"  Kich ban: {SCENARIO}")
    print(LINE)
    print(f"  Be: {params['L_X']} x {params['L_Y']} m   |   Coc d={params['D_PILE']} m")
    print(f"  Po = {params['P_LIMIT']} T  |  Ct = {params['P_TENSION']} T  |  Mmax = {params['M_LIMIT'] or 'Bo qua'} T.m")
    print(f"  So to hop tai trong: {len(loads)}")
    print(LINE)


def print_loads():
    """In bảng các tổ hợp tải trọng (N, Mx, My) đưa vào tính toán."""
    print(f"\n  TO HOP TAI TRONG")
    print(f"  {'TH':<4} {'N (kN)':>10} {'Mx (kNm)':>10} {'My (kNm)':>10}")
    print("  " + "-" * 38)
    for i, ld in enumerate(loads):
        print(f"  {i+1:<4} {ld['N']:>10.1f} {ld['Mx']:>10.1f} {ld['My']:>10.1f}")


def print_original(orig):
    """In thông tin phương án gốc (số cọc, Pmax, Pmin, Mmax) và trạng thái đạt/không đạt."""
    if not orig:
        return
    status = "[DAT]" if orig['ok'] else "[KHONG DAT]"
    print(f"\n  PHUONG AN GOC: {status}")
    print(f"  +-- So coc  : {orig['n']}")
    print(f"  +-- Pmax    : {orig['pmax']:.2f} T  (gioi han: {params['P_LIMIT']} T)")
    print(f"  +-- Pmin    : {orig['pmin']:.2f} T")
    if params['M_LIMIT'] > 0:
        mmax = max(orig.get('mxmax', 0), orig.get('mymax', 0))
        print(f"  +-- Mmax    : {mmax:.2f} T.m  (gioi han: {params['M_LIMIT']} T.m)")
    if not orig['ok']:
        print(f"  +-- Ly do   : {orig['msg']}")
    else:
        print(f"  +-- Trang thai: OK")


def print_candidates(all_cands):
    """In thống kê các phương án đã quét: số phương án đạt/không đạt và bảng phương án đạt."""
    valid   = [c for c in all_cands if c['ok']]
    invalid = [c for c in all_cands if not c['ok']]

    print(f"\n  KET QUA QUET KHONG GIAN ({len(all_cands)} cau hinh kiem tra)")
    print(f"  +-- Phuong an DAT      : {len(valid)}")
    print(f"  +-- Phuong an KHONG DAT: {len(invalid)}")

    if valid:
        print(f"\n  PHUONG AN DAT (sap xep theo n tang dan):")
        print(f"  {'Kieu':<5} {'nx':>3} {'ny':>3} {'n':>4} {'sx (m)':>8} {'sy (m)':>8} {'Pmax (T)':>10} {'Pmin (T)':>10}")
        print("  " + "-" * 60)
        for c in valid:
            marker = " << TOT NHAT" if c == valid[0] else ""
            print(f"  {c['type']:<5} {c['nx']:>3} {c['ny']:>3} {c['n']:>4} "
                  f"{c['sx']:>8.3f} {c['sy']:>8.3f} {c['pmax']:>10.1f} {c['pmin']:>10.1f}{marker}")


def print_recommendation(rec, reason):
    """In phương án kiến nghị chi tiết: kiểu bố trí, lưới, khoảng cách, nội lực và tọa độ cọc."""
    print(f"\n  {'='*64}")
    print(f"  PHUONG AN KIEN NGHI")
    print(f"  {'='*64}")
    if not rec:
        print(f"  [X] Khong tim thay phuong an thoa man.")
        print(f"  Ly do: {reason}")
        return

    type_map = {"A": "Truc giao (Rectangular)", "B": "So le (Staggered)", "Goc": "Phuong an Goc (Giu nguyen)"}
    # Handle Vietnamese original type key
    t = rec['type']
    if t not in type_map:
        type_map[t] = t
    type_str = type_map.get(t, t)
    print(f"  Kieu bo tri : {type_str}")
    print(f"  So coc      : {rec['n']} coc")
    if rec['type'] not in ('Goc', 'G\u1ed1c'):
        print(f"  Luoi        : {rec['nx']} x {rec['ny']}")
        print(f"  Khoang cach : sx = {rec['sx']:.3f} m  |  sy = {rec['sy']:.3f} m")
    status_p = 'OK' if rec['pmax'] <= params['P_LIMIT'] else 'VUOT GIOI HAN!'
    print(f"  Pmax        : {rec['pmax']:.2f} T  ({status_p})")
    print(f"  Pmin        : {rec['pmin']:.2f} T")
    mmax = max(rec.get('mxmax', 0), rec.get('mymax', 0))
    if params['M_LIMIT'] > 0:
        print(f"  Mmax        : {mmax:.2f} T.m  (gioi han: {params['M_LIMIT']} T.m)")
    print(f"  Ly do chon  : {reason}")

    # In bảng tọa độ đầu cọc của phương án kiến nghị
    print(f"\n  TOA DO DAU COC:")
    print(f"  {'Coc':>5} {'X (m)':>10} {'Y (m)':>10}")
    print("  " + "-" * 30)
    for i, (x, y) in enumerate(rec['coords']):
        print(f"  {i+1:>5} {x:>10.3f} {y:>10.3f}")
    print(f"  {'-'*64}")


def print_pile_forces(rec):
    """In bảng nội lực từng cọc cho tổ hợp tải bất lợi nhất (theo công thức bệ cứng)."""
    if not rec:
        return
    from io_handlers.export_utils import calculate_pile_forces

    # Tính nội lực từng cọc cho mọi tổ hợp tải trọng
    forces_by_load = calculate_pile_forces(rec['coords'], loads)
    if not forces_by_load:
        return

    # Quy về cùng đơn vị với Pmax đã hiệu chỉnh (T):
    # calib = Pmax hiệu chỉnh / Pmax thô lớn nhất (công thức bệ cứng)
    raw_pmax = max((max(v) for v in forces_by_load.values() if v), default=0.0)
    cfg_pmax = rec.get('pmax', 0) or 0
    calib = (cfg_pmax / raw_pmax) if (raw_pmax > 0 and cfg_pmax > 0) else 1.0

    # Tìm tổ hợp bất lợi nhất (Pmax lớn nhất)
    worst_i = max(forces_by_load, key=lambda i: max(forces_by_load[i]))

    P_LIMIT = params['P_LIMIT']
    P_TENSION = params['P_TENSION']

    print(f"\n  BANG NOI LUC TUNG COC (to hop bat loi nhat: TH{worst_i+1})")
    print(f"  {'Coc':>5} {'X (m)':>10} {'Y (m)':>10} {'P (T)':>10}  Trang thai")
    print("  " + "-" * 52)
    for i, ((x, y), p_raw) in enumerate(zip(rec['coords'], forces_by_load[worst_i])):
        p = p_raw * calib
        if p > P_LIMIT:
            status = "VUOT NEN!"
        elif P_TENSION > 0 and p < -P_TENSION:
            status = "VUOT NHO!"
        else:
            status = "OK"
        print(f"  {i+1:>5} {x:>10.3f} {y:>10.3f} {p:>10.2f}  {status}")
    print("  " + "-" * 52)
    print(f"  Pmax = {max(forces_by_load[worst_i])*calib:.2f} T  |  "
          f"Pmin = {min(forces_by_load[worst_i])*calib:.2f} T  |  [Po] = {P_LIMIT} T")


if __name__ == "__main__":
    # In phần đầu báo cáo: tiêu đề và tổ hợp tải trọng
    print_header()
    print_loads()

    # Chạy bộ tối ưu và đo thời gian tính toán
    t0 = time.perf_counter()
    results = run_optimization(params, loads)
    elapsed = time.perf_counter() - t0

    # In các phần kết quả: phương án gốc, phương án quét, kiến nghị, nội lực cọc
    print_original(results.get('original_config'))
    print_candidates(results.get('all_candidates', []))
    print_recommendation(results.get('recommended'), results.get('reason', ''))
    print_pile_forces(results.get('recommended'))

    if results.get('warning'):
        print(f"\n  [CANH BAO] {results['warning']}")

    print(f"\n  [Time] Thoi gian tinh toan: {elapsed*1000:.1f} ms")
    print(LINE + "\n")

