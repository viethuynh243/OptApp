import numpy as np
from core.blackbox import MCOCBlackbox

def check_layout(coords, nx, ny, sx, sy, layout_type, params, loads):
    """
    Kiểm tra một phương án (coords) với tất cả các tổ hợp tải trọng.
    Trả về: (is_ok, pmax, pmin, mxmax, mymax, p_forces, message)

    Ràng buộc kiểm tra:
        R1: Pmax ≤ P_LIMIT     — không cọc nào bị nén vượt giới hạn
        R2: Pmin ≥ -P_TENSION  — không cọc nào bị nhổ vượt giới hạn
        R3: 3d ≤ spacing ≤ 6d  — khoảng cách tim-tim đảm bảo thi công
        R4: cọc ngoài cách mép bệ ≥ SAFE_D  — cọc không phá vỡ bệ
        R5: Mx_max ≤ M_LIMIT   — momen uốn X trong giới hạn
        R6: My_max ≤ M_LIMIT   — momen uốn Y trong giới hạn
    """
    L_X = params['L_X']
    L_Y = params['L_Y']
    d = params['D_PILE']
    SAFE_D = params.get('SAFE_D', d)
    
    n_piles = len(coords)
    if n_piles == 0:      return False, 0, 0, 0, 0, [], "Khong co coc"
    if len(loads) == 0:   return False, 0, 0, 0, 0, [], "Chua nhap to hop tai trong"
    
    # Ràng buộc hình học: Bệ móng (R4) và R3
    max_x = np.max(np.abs(coords[:, 0]))
    max_y = np.max(np.abs(coords[:, 1]))
    
    geo_errors = []
    if max_x + SAFE_D > L_X / 2 + 1e-4:
        geo_errors.append(f"Vi pham mep be (X={max_x:.2f})")
    if max_y + SAFE_D > L_Y / 2 + 1e-4:
        geo_errors.append(f"Vi pham mep be (Y={max_y:.2f})")
        
    if layout_type == "A":
        # R3: khoảng cách ngang sx và dọc sy đều phải trong [3d, 6d]
        if nx > 1 and not (3*d - 1e-4 <= sx <= 6*d + 1e-4):
            geo_errors.append("sx vi pham 3d-6d")
        if ny > 1 and not (3*d - 1e-4 <= sy <= 6*d + 1e-4):
            geo_errors.append("sy vi pham 3d-6d")
    elif layout_type == "B":
        # R3: khoảng cách ngang sx (cùng hàng) và đường chéo diag (hàng liền kề) trong [3d, 6d]
        if nx > 1 and not (3*d - 1e-4 <= sx <= 6*d + 1e-4):
            geo_errors.append("sx vi pham 3d-6d")
        diag = np.sqrt((sx/2)**2 + sy**2)
        if ny > 1 and not (3*d - 1e-4 <= diag <= 6*d + 1e-4):
            geo_errors.append("khoang cach cheo vi pham 3d-6d")
    else:
        # Phương án gốc / bố trí tùy ý: kiểm tra khoảng cách nhỏ nhất giữa mọi cặp cọc
        if n_piles > 1:
            dists = []
            for i in range(n_piles):
                for j in range(i + 1, n_piles):
                    dx = coords[i, 0] - coords[j, 0]
                    dy = coords[i, 1] - coords[j, 1]
                    dists.append(np.sqrt(dx*dx + dy*dy))
            s_min = min(dists)
            if s_min < 3*d - 1e-4:
                geo_errors.append(f"khoang cach nho nhat {s_min:.2f}m < 3d={3*d:.2f}m")
        
    # Đánh giá nội lực (Black-box)
    mock_mode = params.get('mock_mode', True)
    exe_path = params.get('exe_path', '')
    
    res, msg = MCOCBlackbox.evaluate_layout(coords, loads, params, exe_path, mock_mode)
    
    if not res:
        return False, 0, 0, 0, 0, [], "Loi goi Hop Den: " + msg
        
    pmax = res['pmax']
    pmin = res['pmin']
    mxmax = res.get('mxmax', 0)
    mymax = res.get('mymax', 0)
    
    P_LIMIT   = params.get('P_LIMIT', 500.0)
    P_TENSION = params.get('P_TENSION', 0.0)
    M_LIMIT_raw = params.get('M_LIMIT', 0.0)
    M_LIMIT = float('inf') if (M_LIMIT_raw is None or M_LIMIT_raw <= 0) else M_LIMIT_raw
    
    ok = True
    fail_msg = []
    
    if pmax > P_LIMIT:
        ok = False
        fail_msg.append(f"Pmax={pmax:.1f} > {P_LIMIT}")
        
    if P_TENSION > 0 and pmin < -P_TENSION:
        ok = False
        fail_msg.append(f"Pmin={pmin:.1f} < -{P_TENSION}")
        
    if mxmax > M_LIMIT:
        ok = False
        fail_msg.append(f"Mx={mxmax:.1f} > {M_LIMIT}")
        
    if mymax > M_LIMIT:
        ok = False
        fail_msg.append(f"My={mymax:.1f} > {M_LIMIT}")
        
    if len(geo_errors) > 0:
        ok = False
        fail_msg.extend(geo_errors)
        
    final_msg = msg if ok else "Khong dat: " + ", ".join(fail_msg)
    
    # Lấy forces từ kết quả Hộp đen (nếu có), nếu không có thì gán mặc định
    forces = res.get('forces', [])
    if not forces or len(forces) != n_piles:
        forces = [0.0] * n_piles
    
    return ok, pmax, pmin, mxmax, mymax, forces, final_msg
