import csv
import os
import numpy as np

def parse_input_file(filepath):
    """
    Tự động nhận diện và đọc file (CSV cũ hoặc TXT chuẩn MCOC).
    """
    params = {}
    loads = []
    project_name = "Du An Toi Uu Coc"
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        
    if not lines:
        raise ValueError("File rỗng")
        
    if "CHUONG TRINH TINH KHONG GIAN MONG COC" in "".join(lines[:10]):
        return parse_mcoc_result_as_input(filepath)
        
    # Nhận diện: nếu dòng đầu có dấu phẩy thì là CSV, nếu không thì khả năng là MCOC
    if ',' in lines[0] or (len(lines)>1 and ',' in lines[1]):
        # Đọc theo kiểu CSV
        param_keys = [k.strip() for k in lines[0].split(',')]
        param_vals = [float(v.strip()) for v in lines[1].split(',')]
        for k, v in zip(param_keys, param_vals):
            params[k] = v
            
        # Dòng 1: L_X, L_Y, D_PILE, SAFE_D, P_LIMIT, P_TENSION
        # Dòng 2: values...
        # Dòng 3: Hx, Hy, P, Mx, My, Mz
        for i in range(3, len(lines)):
            if not lines[i].strip(): continue
            parts = lines[i].split(',')
            if len(parts) >= 6:
                loads.append({'Hx': float(parts[0].strip()), 'Hy': float(parts[1].strip()), 
                              'N': float(parts[2].strip()), 'Mx': float(parts[3].strip()), 
                              'My': float(parts[4].strip()), 'Mz': float(parts[5].strip())})
            elif len(parts) >= 3:
                # Fallback to old format
                loads.append({'Hx': 0.0, 'Hy': 0.0, 'N': float(parts[0].strip()), 
                              'Mx': float(parts[1].strip()), 'My': float(parts[2].strip()), 'Mz': 0.0})
    else:
        # Đọc theo chuẩn MCOC TXT
        # Dòng 1: Tên
        project_name = lines[0].strip()
        
        # Dòng 2: Nc Np ... Ax By H
        parts_l2 = lines[1].split()
        if len(parts_l2) >= 11:
            Ax = float(parts_l2[8])
            By = float(parts_l2[9])
            params['L_X'] = Ax
            params['L_Y'] = By
            params['H_cap'] = float(parts_l2[10])
            
        # Tổ hợp tải trọng bắt đầu từ dòng 4 (index 3)
        i = 3
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            parts = line.split()
            if len(parts) == 6:
                try:
                    hx = float(parts[0])
                    hy = float(parts[1])
                    p = float(parts[2])
                    mx = float(parts[3])
                    my = float(parts[4])
                    mz = float(parts[5])
                    loads.append({'Hx': hx, 'Hy': hy, 'N': p, 'Mx': mx, 'My': my, 'Mz': mz})
                except ValueError:
                    pass
            elif len(parts) == 1 and '.' in parts[0]:
                break
            i += 1
            
        original_coords = []
        d_pile = None
        p_limit = None
        
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            try:
                # Dòng i+2: Ev.uon Er.uon Ev.nen Er.nen m.day m.be m
                props = lines[i+2].split()
                if len(props) >= 7:
                    Eb = float(props[0])
                    m_soil = float(props[6])
                else:
                    Eb = 3e6; m_soil = 400.0
                    
                a = float(lines[i+4].strip())
                # Dòng i+5: a b cday Fo Jo (Cũ, không đúng)
                # Thực tế mỗi thông số 1 dòng:
                # i+7: Fo
                # i+8: Jo
                # i+9: Po
                # i+10: Co
                # i+11: Ct
                try:
                    Fo = float(lines[i+7].strip())
                    Jo = float(lines[i+8].strip())
                    Co = float(lines[i+10].strip())
                    Ct = float(lines[i+11].strip())
                except:
                    Fo = 1.0; Jo = 0.1; Co = 33333.3; Ct = 16666.7
                    
                Po = float(lines[i+9].strip())
                
                # Check for X, Y coords (usually after 12 lines)
                # find the first line with two floats
                idx_coord = i + 12
                for j in range(i+12, min(i+20, len(lines))):
                    parts = lines[j].split()
                    if len(parts) == 2 or len(parts) == 5:
                        try:
                            X = float(parts[0])
                            Y = float(parts[1])
                            idx_coord = j
                            break
                        except ValueError:
                            pass
                else:
                    X = float(lines[i+12].strip())
                    Y = float(lines[i+13].strip())
                    
                if d_pile is None:
                    d_pile = a
                    p_limit = Po
                    params['E_b'] = Eb
                    params['m_soil'] = m_soil
                    params['F_o'] = Fo
                    params['J_o'] = Jo
                    params['C_o'] = Co
                    params['C_t'] = Ct
                    
                original_coords.append([X, Y])
                # Skip to next pile block
                i = idx_coord + 4
            except (IndexError, ValueError) as e:
                print("Parse error at line", i, e)
                break
                
        if d_pile is not None:
            params['D_PILE'] = d_pile
        if p_limit is not None:
            params['P_LIMIT'] = p_limit
        if original_coords:
            params['original_coords'] = original_coords
            
    return params, loads, project_name

def export_output_file(filepath, results, params, loads, project_name, output_option="BEST"):
    """
    Xuất kết quả giống chuẩn MCOC có thêm Bảng So sánh Kiểu bố trí.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("     TONG CONG TY TVTK GTVT\n\n")
        f.write("              CHUONG TRINH TINH KHONG GIAN MONG COC - OPTIMIZER\n\n\n")
        f.write(f"            Ten cong trinh : {project_name}\n\n\n")
        
        if not results or not results.get('recommended'):
            f.write("      ❌ KHONG TIM THAY PHUONG AN BO TRI NAO THOA MAN CAC RANG BUOC!\n")
            return
            
        config = results['recommended']
        
        f.write("                        SO LIEU BAN DAU HE MONG COC\n\n")
        f.write(f"       Nc =  {config['n']:<4}    Np =  {len(loads)}\n\n")
        f.write("            Kich thuoc be (m)\n\n")
        f.write(f"       Ax = {params.get('L_X', 0):<10.1f} By = {params.get('L_Y', 0):<10.1f}\n\n\n")
        
        if results.get('original_config'):
            orig = results['original_config']
            status_str = "DAT" if orig['ok'] else "KHONG DAT"
            f.write(f"                        PHUONG AN GOC TRONG FILE ({status_str})\n\n")
            f.write(f"       So luong coc: {orig['n']} coc\n")
            f.write(f"       P_max = {orig['pmax']:.1f} kN (Gioi han: {params.get('P_LIMIT', 1000.0):.1f} kN)\n")
            if not orig['ok']:
                f.write(f"       Ly do khong dat: {orig['msg']}\n")
            f.write("\n\n")
            
        if output_option == "ALL":
            f.write(f"                        TAT CA PHUONG AN DAT YEU CAU ({len(results['all_valid_configs'])})\n\n")
            for i, cfg in enumerate(results['all_valid_configs']):
                type_str = "Truc giao" if cfg['type'] == "A" else "So le"
                f.write(f"       {i+1:<3}. Phuong an {i+1} ({type_str}): {cfg['nx']}x{cfg['ny']}, n={cfg['n']}, Pmax={cfg['pmax']:.1f} kN\n")
            f.write("\n\n")
        
        f.write("                        BANG SO SANH CAC KIEU BO TRI\n\n")
        
        if results.get('best_A'):
            A = results['best_A']
            f.write(f"       Kieu A (Truc giao): {A['n']} coc, P_max = {A['pmax']:.1f} kN\n")
        else:
            f.write("       Kieu A (Truc giao): Khong thoa man\n")
            
        if results.get('best_B'):
            B = results['best_B']
            f.write(f"       Kieu B (So le)  : {B['n']} coc, P_max = {B['pmax']:.1f} kN\n")
        else:
            f.write("       Kieu B (So le)  : Khong thoa man\n")
            
        f.write("\n")
        f.write(f"       PHUONG AN KIEN NGHI: Kieu {config['type']}\n")
        f.write(f"       Ly do: {results['reason']}\n\n\n")

        f.write("                        CAC TO HOP TAI TRONG\n\n")
        f.write("     T.T      Hx        Hy        P         Mx        My        Mz\n\n")
        for i, load in enumerate(loads):
            f.write(f"       {i+1:<6} {load.get('Hx',0):<9.1f} {load.get('Hy',0):<9.1f} {load['N']:<9.1f} {load['Mx']:<9.1f} {load['My']:<9.1f} {load.get('Mz',0):<9.1f}\n")
            
        f.write("\n\n")
        f.write(f"                        TOA DO DAU COC (PHUONG AN TOI UU: Kieu {config['type']})\n\n")
        f.write(f"       Luoi: {config['nx']} x {config['ny']}, sx = {config['sx']:.3f} m, sy = {config['sy']:.3f} m\n\n")
        f.write("          T.T     X         Y\n\n")
        for i, coord in enumerate(config['coords']):
            f.write(f"            {i+1:<5} {coord[0]:<9.3f} {coord[1]:<9.3f}\n")
            
        f.write("\n\n")
        f.write("                             NOI LUC COC KIEM TRA\n\n")
        f.write("     Coc t.h       N\n\n")
        
        cg_x, cg_y = np.mean([x for x,y in config['coords']]), np.mean([y for x,y in config['coords']])
        I_x = sum((y - cg_y)**2 for x,y in config['coords'])
        I_y = sum((x - cg_x)**2 for x,y in config['coords'])
        I_x = I_x if I_x > 0 else 1e-9
        I_y = I_y if I_y > 0 else 1e-9
        n_piles = config['n']
        
        all_forces = {}
        global_pmax = -float('inf')
        global_pmin = float('inf')
        max_p_pile = -1
        max_p_load = -1
        min_p_pile = -1
        min_p_load = -1
        
        for p_idx, (x, y) in enumerate(config['coords']):
            all_forces[p_idx] = []
            dx = x - cg_x
            dy = y - cg_y
            
            for l_idx, load in enumerate(loads):
                N = load['N']
                Mx_cg = load['Mx'] - N * cg_y
                My_cg = load['My'] - N * cg_x
                p = N/n_piles + Mx_cg*dy/I_x + My_cg*dx/I_y
                all_forces[p_idx].append(p)
                
                if p > global_pmax:
                    global_pmax = p
                    max_p_pile = p_idx + 1
                    max_p_load = l_idx + 1
                if p < global_pmin:
                    global_pmin = p
                    min_p_pile = p_idx + 1
                    min_p_load = l_idx + 1
                    
        for p_idx in range(n_piles):
            first_th = True
            for l_idx in range(len(loads)):
                if first_th:
                    f.write(f"       {p_idx+1:<3} {l_idx+1:<6} {all_forces[p_idx][l_idx]:.2f}\n")
                    first_th = False
                else:
                    f.write(f"           {l_idx+1:<6} {all_forces[p_idx][l_idx]:.2f}\n")
            f.write("\n")
            
        f.write("\n")
        f.write("                                     BANG TONG KET NOI LUC\n\n")
        f.write("                 Coc   t.h     N\n\n")
        f.write(f"         Nmin      {min_p_pile:<5} {min_p_load:<7} {global_pmin:.2f}\n")
        f.write(f"         Nmax      {max_p_pile:<5} {max_p_load:<7} {global_pmax:.2f}\n\n")


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
            # T.T Lo H Bpx Bpy a b cday Fo Jo Po Co [Ct]
            if len(parts) >= 12:
                try:
                    int(parts[0])
                    h_pile  = float(parts[2])   # H  — Chieu dai coc (m)
                    a_pile  = float(parts[5])   # a  — Duong kinh coc (m)
                    fo_pile = float(parts[8])   # Fo — Dien tich tiet dien (m2)
                    jo_pile = float(parts[9])   # Jo — Moment quan tinh (m4)
                    po_pile = float(parts[10])  # Po — Suc nen cho phep (T)
                    # Ct (suc nho) la cot thu 13 (index 12). Neu khong co, de 0
                    ct_pile = float(parts[12]) if len(parts) >= 13 else 0.0
                    if 'D_PILE' not in params:
                        params['D_PILE'] = a_pile
                    if 'P_LIMIT' not in params:
                        params['P_LIMIT'] = po_pile  # T
                    if 'P_TENSION' not in params:
                        params['P_TENSION'] = ct_pile  # T (0 neu file khong co)
                    # Store pile properties for R5/R6 6-DOF solver
                    if 'pile_H' not in params:
                        params['pile_H'] = h_pile
                        params['pile_Fo'] = fo_pile
                        params['pile_Jo'] = jo_pile
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

    # Lưu Nmax/Nmin/Mxmax/Mymax thực tế từ bảng tổng kết
    result = parse_mcoc_result_file(filepath)
    if result:
        params['orig_pmax'] = result['pmax']
        params['orig_pmin'] = result['pmin']
        params['orig_mxmax'] = result['mxmax']
        params['orig_mymax'] = result['mymax']


    return params, loads, 'Imported from Result'
