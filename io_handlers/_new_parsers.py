
import re

def parse_mcoc_result_file(filepath):
    """
    Đọc Nmax, Nmin, Mxmax, Mymax từ bảng BANG TONG KET NOI LUC trong file _result.txt.
    """
    pmax = None
    pmin = None
    mxmax = 0.0
    mymax = 0.0

    with open(filepath, 'r', encoding='utf-8', errors='replace') as r:
        lines = r.readlines()

    in_summary = False
    for line in lines:
        if 'BANG TONG KET NOI LUC' in line:
            in_summary = True
            continue

        if in_summary:
            if line.strip().startswith('---') or 'DO CUNG' in line or 'CHUYEN VI' in line:
                break
            parts = line.split()
            # Các dòng có dạng:
            #   Nmin      1     5       0.0       0.0  ...
            #   Nmax      3     1       519.63    ...
            # => parts: ['Nmax', '3', '1', '519.63', '-13.83', '-17.5', '0.0', '-7.49', '-23.65']
            if 'Nmax' in line and len(parts) >= 4:
                try:
                    pmax = float(parts[3])
                    if len(parts) >= 9:
                        mxmax = max(mxmax, abs(float(parts[7])))
                        mymax = max(mymax, abs(float(parts[8])))
                except:
                    pass
            elif 'Nmin' in line and len(parts) >= 4:
                try:
                    pmin = float(parts[3])
                except:
                    pass
            elif 'M2max' in line and len(parts) >= 8:
                try:
                    mxmax = max(mxmax, abs(float(parts[7])))
                except:
                    pass
            elif 'M3max' in line and len(parts) >= 9:
                try:
                    mymax = max(mymax, abs(float(parts[8])))
                except:
                    pass

    if pmax is None:
        return None

    return {
        'pmax': pmax,
        'pmin': pmin if pmin is not None else 0.0,
        'mxmax': mxmax,
        'mymax': mymax
    }


def parse_mcoc_result_as_input(filepath):
    """
    Đọc toàn bộ dữ liệu từ file _result.txt để làm Input cho bài toán tối ưu.
    """
    params = {}
    loads = []
    original_coords = []

    with open(filepath, 'r', encoding='utf-8', errors='replace') as r:
        lines = r.readlines()

    in_loads = False
    in_pile_props = False
    in_pile_coords = False
    loads_header_skipped = False
    pile_props_header_skipped = False
    pile_coords_header_skipped = False

    for line in lines:
        stripped = line.strip()

        # Kích thước bệ
        if 'Ax =' in line and 'By =' in line:
            parts = line.split()
            try:
                ax_idx = next(i for i, p in enumerate(parts) if p == 'Ax')
                by_idx = next(i for i, p in enumerate(parts) if p == 'By')
                params['L_X'] = float(parts[ax_idx + 2])
                params['L_Y'] = float(parts[by_idx + 2])
            except:
                pass
            continue

        # Tải trọng
        if 'CAC TO HOP TAI TRONG' in line:
            in_loads = True
            loads_header_skipped = False
            continue

        if in_loads:
            if not loads_header_skipped:
                if 'T.T' in line and 'Hx' in line:
                    loads_header_skipped = True
                continue
            if 'DAC TRUNG COC' in line:
                in_loads = False
                in_pile_props = True
                pile_props_header_skipped = False
                continue
            parts = stripped.split()
            if len(parts) == 7:
                try:
                    int(parts[0])
                    loads.append({
                        'Hx': float(parts[1]), 'Hy': float(parts[2]),
                        'N':  float(parts[3]), 'Mx': float(parts[4]),
                        'My': float(parts[5]), 'Mz': float(parts[6])
                    })
                except:
                    pass

        # Đặc trưng cọc
        if in_pile_props:
            if not pile_props_header_skipped:
                if 'T.T' in line and 'Lo' in line:
                    pile_props_header_skipped = True
                continue
            if 'TOA DO DAU COC' in line:
                in_pile_props = False
                in_pile_coords = True
                pile_coords_header_skipped = False
                continue
            parts = stripped.split()
            # T.T Lo H Bpx Bpy a b cday Fo Jo Po Co Ct
            if len(parts) >= 11:
                try:
                    int(parts[0])
                    if 'D_PILE' not in params:
                        params['D_PILE'] = float(parts[5])   # 'a'
                    if 'P_LIMIT' not in params:
                        params['P_LIMIT'] = float(parts[10]) # 'Po'
                except:
                    pass

        # Tọa độ đầu cọc
        if in_pile_coords:
            if not pile_coords_header_skipped:
                if 'T.T' in line and 'X' in line:
                    pile_coords_header_skipped = True
                continue
            if stripped and any(k in line for k in ['CHUYEN VI', 'NOI LUC', 'BANG TONG', 'DO CUNG']):
                in_pile_coords = False
                continue
            parts = stripped.split()
            if len(parts) >= 3:
                try:
                    int(parts[0])
                    original_coords.append([float(parts[1]), float(parts[2])])
                except:
                    pass

    if original_coords:
        params['original_coords'] = original_coords

    # Lưu Nmax/Nmin thực tế từ bảng tổng kết
    result = parse_mcoc_result_file(filepath)
    if result:
        params['orig_pmax'] = result['pmax']
        params['orig_pmin'] = result['pmin']

    return params, loads, 'Imported from Result'
