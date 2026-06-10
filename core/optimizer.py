import numpy as np
from core.generator import generate_coords
from core.mechanics import check_layout

def run_optimization(params, loads):
    """
    Thuật toán tìm cấu hình cọc tối ưu và so sánh Kiểu A, Kiểu B.
    """
    L_X = params['L_X']
    L_Y = params['L_Y']
    d = params['D_PILE']
    SAFE_D = params.get('SAFE_D', 1.0)
    
    best_configs = {'A': None, 'B': None}
    best_n = {'A': float('inf'), 'B': float('inf')}
    all_valid_configs = []
    all_candidates = []  # Tất cả ứng viên kể cả không đạt
    
    for layout_type in ["A", "B"]:
        for nx in range(2, 11):
            for ny in range(2, 11):
                if layout_type == "A":
                    n_piles = nx * ny
                elif layout_type == "B":
                    n_piles = sum(nx if j%2==0 else nx-1 for j in range(ny))
                
                sx_max = min(6.0*d, (L_X - 2*SAFE_D)/(nx-1) if nx > 1 else 0)
                sy_max = min(6.0*d, (L_Y - 2*SAFE_D)/(ny-1) if ny > 1 else 0)
                
                if sx_max < 3.0*d or sy_max < 3.0*d:
                    continue
                    
                coords = generate_coords(nx, ny, sx_max, sy_max, layout_type)
                n = len(coords)
                
                ok, pmax, pmin, mxmax, mymax, forces, msg = check_layout(coords, nx, ny, sx_max, sy_max, layout_type, params, loads)
                
                candidate = {
                    'type': layout_type,
                    'nx': nx, 'ny': ny,
                    'sx': sx_max, 'sy': sy_max,
                    'n': n,
                    'coords': coords,
                    'pmax': pmax,
                    'pmin': pmin,
                    'mxmax': mxmax,
                    'mymax': mymax,
                    'forces': forces,
                    'ok': ok,
                    'msg': msg
                }
                all_candidates.append(candidate)
                
                if ok:
                    all_valid_configs.append(candidate)
                    if n < best_n[layout_type]:
                        best_n[layout_type] = n
                        best_configs[layout_type] = candidate
                        
    # Sort valid configs by n, then by pmax
    all_valid_configs.sort(key=lambda x: (x['n'], x['pmax']))
    all_candidates.sort(key=lambda x: (x['n'], x['pmax']))

    recommended = None
    reason = "Khong co"
    
    if best_configs['A'] and best_configs['B']:
        if best_configs['B']['n'] < best_configs['A']['n']:
            recommended = best_configs['B']
            reason = f"Kieu So le tiet kiem coc nhat (chi {best_configs['B']['n']} coc)."
        elif best_configs['A']['n'] < best_configs['B']['n']:
            recommended = best_configs['A']
            reason = f"Kieu Truc giao tiet kiem coc nhat (chi {best_configs['A']['n']} coc)."
        else:
            if best_configs['B']['pmax'] < best_configs['A']['pmax']:
                recommended = best_configs['B']
                reason = f"Cung {best_configs['A']['n']} coc, nhung kieu So le co P_max = {best_configs['B']['pmax']:.1f} T an toan hon."
            else:
                recommended = best_configs['A']
                reason = f"Cung {best_configs['A']['n']} coc, nhung kieu Truc giao co P_max = {best_configs['A']['pmax']:.1f} T an toan hon."
    elif best_configs['A']:
        recommended = best_configs['A']
        reason = "Chi kieu Truc giao thoa man dieu kien."
    elif best_configs['B']:
        recommended = best_configs['B']
        reason = "Chi kieu So le thoa man dieu kien."
        
    original_config = None
    if 'original_coords' in params:
        orig_coords = np.array(params['original_coords'])
        orig_nx = 0
        orig_ny = 0
        
        # Đánh giá phương án gốc dựa trên RÀNG BUỘC MỚI của người dùng (P_LIMIT, D_PILE hiện tại)
        ok, pmax, pmin, mxmax, mymax, forces, msg = check_layout(orig_coords, orig_nx, orig_ny, 0, 0, "Goc", params, loads)
        original_config = {
            'type': 'Goc',
            'coords': orig_coords,
            'n': len(orig_coords),
            'ok': ok,
            'pmax': pmax,
            'pmin': pmin,
            'mxmax': mxmax,
            'mymax': mymax,
            'forces': forces,
            'msg': msg
        }
        
        # Ưu tiên phương án gốc nếu nó đạt và các phương án lưới không tiết kiệm cọc hơn
        if ok and (recommended is None or recommended['n'] >= len(orig_coords)):
            recommended = {
                'type': 'Goc',
                'nx': 0, 'ny': 0,
                'sx': 0, 'sy': 0,
                'n': len(orig_coords),
                'coords': orig_coords,
                'pmax': pmax,
                'pmin': pmin,
                'mxmax': mxmax,
                'mymax': mymax,
                'forces': forces,
                'ok': True,
                'msg': 'Su dung phuong an goc'
            }
            reason = f"Phuong an goc trong file DAT (Pmax={pmax:.1f}T). Cac phuong an luoi deu khong tiet kiem coc hon."
        elif recommended is None and not ok:
            clean_msg = msg.replace("Khong dat: ", "")
            reason = f"Phuong an goc KHONG DAT ({clean_msg}). Can thay doi cau hinh dai coc, mong coc hoac gioi han uon."
        
    return {
        'best_A': best_configs['A'],
        'best_B': best_configs['B'],
        'recommended': recommended,
        'reason': reason,
        'all_valid_configs': all_valid_configs,
        'all_candidates': all_candidates,
        'original_config': original_config
    }
