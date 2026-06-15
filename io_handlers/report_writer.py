"""
report_writer.py - Xuất BẢN TÍNH KỸ THUẬT CHUẨN (Markdown) cho phương án cọc.

Khác với file_io.export_output_file (định dạng MCOC), báo cáo này hướng tới
THẨM TRA KỸ SƯ: có hệ số sử dụng, tổ hợp chi phối, bảng ràng buộc R1-R8 kèm
tỷ lệ, lực ngang Hmax, và phụ lục phạm vi/giới hạn mô hình.

Đơn vị: tải trọng nhập kN/kN.m; sức chịu tải & lực cọc quy về Tấn (T) để so
với [Po]/[Ct]. Hàm tự đọc từ results['recommended'] + params + loads.
"""

import os
import numpy as np

from core import rigid_cap
from core.constants import (SPACING_MIN_FACTOR, SPACING_MAX_FACTOR,
                            get_safe_d, effective_min_spacing,
                            ENABLE_LATERAL_CHECK, ENABLE_PM_INTERACTION)


# ============================================================================
# Tiện ích định dạng số liệu
# ============================================================================
def _fmt(v, nd=2):
    """Định dạng số thực thành chuỗi với nd chữ số sau dấu thập phân."""
    return f"{v:.{nd}f}"


def _ratio(actual, limit):
    """Tỷ lệ sử dụng actual/limit (%). Trả về '-' nếu không kiểm (limit<=0)."""
    if limit is None or limit <= 0:
        return "-"
    return f"{actual / limit * 100:.1f}%"


# ============================================================================
# Dựng nội dung báo cáo
# ============================================================================
def build_report_text(results, params, loads, project_name="Cong trinh"):
    """Dựng nội dung báo cáo (str, Markdown). Tách riêng để dễ test."""
    cfg = results.get('recommended')
    if not cfg:
        return f"# BAN TINH MONG COC — {project_name}\n\nKhong tim duoc phuong an thoa man.\n"

    coords = np.asarray(cfg['coords'], dtype=float)
    n = len(coords)
    d = params['D_PILE']
    Po = params.get('P_LIMIT', 0.0)
    Ct = params.get('P_TENSION', 0.0)
    Mlim = params.get('M_LIMIT', 0.0)
    Hlim = params.get('H_LIMIT', 0.0)
    SAFE_D = get_safe_d(params)
    s_min_req = effective_min_spacing(params)
    s_max_req = SPACING_MAX_FACTOR * d

    # Lực dọc trục thô theo bệ cứng (kN) -> calib về T cho khớp config['pmax']
    P = rigid_cap.forces_all_loads(coords, loads)           # (n_load, n_pile)
    raw_pmax = float(P.max()) if P.size else 0.0
    calib = (cfg['pmax'] / raw_pmax) if (raw_pmax > 0 and cfg.get('pmax')) else 1.0

    # Hình học
    s_act = rigid_cap.min_spacing(coords)
    max_x = float(np.max(np.abs(coords[:, 0])))
    max_y = float(np.max(np.abs(coords[:, 1])))

    L = []
    L.append(f"# BAN TINH KIEM TRA & TOI UU BO TRI MONG COC")
    L.append(f"## Cong trinh: {project_name}\n")
    L.append("Tieu chuan: TCVN 10304:2014 (mong coc); TCVN 11823 (cau, LRFD). "
             "Noi luc tinh bang MCOC (chinh xac). Don vi: Tan (T), T.m.\n")

    # 1. Số liệu đầu vào
    L.append("## 1. SO LIEU DAU VAO\n")
    L.append("| Thong so | Ky hieu | Gia tri | Don vi |")
    L.append("|---|---|---:|---|")
    L.append(f"| Rong be | Lx | {_fmt(params.get('L_X',0))} | m |")
    L.append(f"| Dai be | Ly | {_fmt(params.get('L_Y',0))} | m |")
    L.append(f"| Duong kinh coc | d | {_fmt(d)} | m |")
    L.append(f"| Tim coc -> mep be toi thieu | c_min | {_fmt(SAFE_D)} | m |")
    L.append(f"| Suc chiu nen | [Po] | {_fmt(Po,1)} | T |")
    L.append(f"| Suc chiu nho | [Ct] | {_fmt(Ct,1)} | T |")
    L.append(f"| Suc chiu uon | [M] | {_fmt(Mlim,1)} | T.m |")
    if ENABLE_LATERAL_CHECK:
        L.append(f"| Suc chiu luc ngang | [H] | {_fmt(Hlim,1)} | T |")
    L.append("")

    # 2. Tổ hợp tải trọng
    L.append("## 2. TO HOP TAI TRONG  (luc T, momen T.m)\n")
    L.append("| TH | Hx | Hy | N | Mx | My | Mz |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for i, ld in enumerate(loads):
        L.append(f"| {i+1} | {_fmt(ld.get('Hx',0),1)} | {_fmt(ld.get('Hy',0),1)} | "
                 f"{_fmt(ld.get('N',0),1)} | {_fmt(ld.get('Mx',0),1)} | "
                 f"{_fmt(ld.get('My',0),1)} | {_fmt(ld.get('Mz',0),1)} |")
    L.append("")

    # 3. Phương án khuyến nghị
    type_str = {'A': 'A - Truc giao', 'B': 'B - Hoa mai/So le',
                'Goc': 'Giu nguyen phuong an goc'}.get(cfg['type'], cfg['type'])
    L.append("## 3. PHUONG AN KHUYEN NGHI\n")
    L.append(f"- Kieu bo tri: **{type_str}**")
    L.append(f"- So coc: **{n}**" + (f" (luoi {cfg.get('nx')} x {cfg.get('ny')})"
                                     if cfg.get('nx') else ""))
    if cfg.get('sx'):
        L.append(f"- Buoc coc: sx = {_fmt(cfg['sx'])} m; sy = {_fmt(cfg['sy'])} m")
    L.append(f"- Ly do chon: {results.get('reason','')}")
    L.append("")

    # 4. Kiểm tra hình học
    L.append("## 4. KIEM TRA HINH HOC\n")
    L.append("| Ma | Dieu kien | Gia tri | Gioi han | Ty le | KL |")
    L.append("|---|---|---:|---:|---:|:--:|")
    L.append(f"| R3a | Khoang cach tim-tim >= {_fmt(s_min_req)} m | {_fmt(s_act)} | "
             f"{_fmt(s_min_req)} | {_ratio(s_min_req, s_act)} | "
             f"{'DAT' if s_act >= s_min_req - 1e-3 else 'KHONG'} |")
    L.append(f"| R3b | Khoang cach <= 6d | {_fmt(s_act)} | {_fmt(s_max_req)} | "
             f"{_ratio(s_act, s_max_req)} | {'DAT' if s_act <= s_max_req + 1e-3 else 'KHONG'} |")
    L.append(f"| R4x | max|x| + c_min <= Lx/2 | {_fmt(max_x + SAFE_D)} | "
             f"{_fmt(params.get('L_X',0)/2)} | {_ratio(max_x + SAFE_D, params.get('L_X',0)/2)} | "
             f"{'DAT' if max_x + SAFE_D <= params.get('L_X',0)/2 + 1e-3 else 'KHONG'} |")
    L.append(f"| R4y | max|y| + c_min <= Ly/2 | {_fmt(max_y + SAFE_D)} | "
             f"{_fmt(params.get('L_Y',0)/2)} | {_ratio(max_y + SAFE_D, params.get('L_Y',0)/2)} | "
             f"{'DAT' if max_y + SAFE_D <= params.get('L_Y',0)/2 + 1e-3 else 'KHONG'} |")
    L.append("")

    # 5. Nội lực theo từng tổ hợp
    L.append("## 5. NOI LUC COC THEO TUNG TO HOP  (quy ve Tan)\n")
    # Cột H_max (lực ngang) chỉ hiện khi R7 được BẬT.
    if ENABLE_LATERAL_CHECK:
        L.append("| TH | N_max (T) | N_min (T) | H_max (T) | N_max/[Po] | KL |")
        L.append("|---|---:|---:|---:|---:|:--:|")
    else:
        L.append("| TH | N_max (T) | N_min (T) | N_max/[Po] | KL |")
        L.append("|---|---:|---:|---:|:--:|")
    gov_i, gov_nmax = 0, -1e18
    props = rigid_cap.group_props(coords)
    for i, ld in enumerate(loads):
        nmax = float(P[i].max()) * calib
        nmin = float(P[i].min()) * calib
        ok_i = (nmax <= Po if Po > 0 else True) and (nmin >= -Ct if Ct > 0 else True)
        if ENABLE_LATERAL_CHECK:
            Hxi, Hyi = rigid_cap.horizontal_forces(coords, ld, props)
            hmx = float(np.sqrt(Hxi ** 2 + Hyi ** 2).max())
            L.append(f"| {i+1} | {_fmt(nmax,1)} | {_fmt(nmin,1)} | {_fmt(hmx,1)} | "
                     f"{_ratio(nmax, Po)} | {'DAT' if ok_i else 'KHONG'} |")
        else:
            L.append(f"| {i+1} | {_fmt(nmax,1)} | {_fmt(nmin,1)} | "
                     f"{_ratio(nmax, Po)} | {'DAT' if ok_i else 'KHONG'} |")
        if nmax > gov_nmax:
            gov_nmax, gov_i = nmax, i + 1
    L.append("")
    L.append(f"**To hop chi phoi: TH{gov_i}** — N_max = {_fmt(gov_nmax,1)} T / "
             f"[Po] = {_fmt(Po,1)} T → he so su dung = "
             f"{(gov_nmax/Po if Po>0 else 0):.3f}.\n")

    # 6. Bảng tổng hợp R1-R8
    mmax = max(cfg.get('mxmax', 0), cfg.get('mymax', 0))
    hmax_cfg = cfg.get('hmax', rigid_cap.hmax(coords, loads))
    inter = (cfg['pmax'] / Po + mmax / Mlim) if (Po > 0 and Mlim > 0) else None
    L.append("## 6. BANG TONG HOP RANG BUOC\n")
    L.append("| Ma | Noi dung | Gia tri | Gioi han | KL |")
    L.append("|---|---|---:|---:|:--:|")
    L.append(f"| R1 | N_max <= [Po] | {_fmt(cfg['pmax'],1)} | {_fmt(Po,1)} | "
             f"{'DAT' if cfg['pmax'] <= Po else 'KHONG'} |")
    L.append(f"| R2 | N_min >= -[Ct] | {_fmt(cfg['pmin'],1)} | {_fmt(-Ct,1) if Ct>0 else '-'} | "
             f"{('DAT' if cfg['pmin'] >= -Ct else 'KHONG') if Ct>0 else '-'} |")
    L.append(f"| R3 | 3d <= khoang cach <= 6d | {_fmt(s_act)} | "
             f"[{_fmt(s_min_req)}, {_fmt(s_max_req)}] | "
             f"{'DAT' if s_min_req-1e-3 <= s_act <= s_max_req+1e-3 else 'KHONG'} |")
    L.append(f"| R4 | Tim coc cach mep >= c_min | OK | - | "
             f"{'DAT' if (max_x+SAFE_D<=params.get('L_X',0)/2+1e-3 and max_y+SAFE_D<=params.get('L_Y',0)/2+1e-3) else 'KHONG'} |")
    L.append(f"| R5/R6 | Mx, My <= [M] | {_fmt(mmax,1)} | {_fmt(Mlim,1) if Mlim>0 else '-'} | "
             f"{('DAT' if mmax<=Mlim else 'KHONG') if Mlim>0 else '-'} |")
    # R7 (lực ngang) & R8 (tương tác P-M) chỉ hiện khi được BẬT trong constants.
    if ENABLE_LATERAL_CHECK:
        r7_kl = ('DAT' if hmax_cfg <= Hlim else 'KHONG') if Hlim > 0 else '-'
        L.append(f"| R7 | H_max <= [H] | {_fmt(hmax_cfg,1)} | "
                 f"{_fmt(Hlim,1) if Hlim>0 else '-'} | {r7_kl} |")
    if ENABLE_PM_INTERACTION:
        r8_kl = ('DAT' if (inter is not None and inter <= 1) else 'KHONG') if inter is not None else '-'
        L.append(f"| R8 | Tuong tac P-M <= 1 | "
                 f"{(_fmt(inter,2) if inter is not None else '-')} | "
                 f"{'1.00' if inter is not None else '-'} | {r8_kl} |")
    L.append("")

    # 7. Kết luận
    status = "DAT" if cfg.get('ok', True) else "KHONG DAT"
    L.append("## 7. KET LUAN\n")
    L.append(f"Phuong an **{n} coc** — trang thai **{status}**, he so su dung lon nhat "
             f"{(gov_nmax/Po if Po>0 else 0):.3f}. De nghi tham tra lai bang MCOC truoc khi phat hanh.\n")

    # Phụ lục giới hạn mô hình
    L.append("---\n")
    L.append("## PHU LUC — PHAM VI & GIOI HAN MO HINH\n")
    L.append("- Luc doc truc (be cung, doi momen ve trong tam nhom coc): "
             "`P_i = N/n + (Mx - N*cy)*(y_i-cy)/Ix + (My - N*cx)*(x_i-cx)/Iy`.")
    if ENABLE_LATERAL_CHECK:
        L.append("- Luc ngang H_max phan phoi tu Hx, Hy, Mz (tinh hoc, coc dung do cung deu); "
                 "**momen than coc do tai ngang** can phan tich p-y rieng khi dang ke.")
    L.append("- Chua xet: hieu ung nhom coc, do lun, ket cau be (chong thung/uon).")
    L.append("- Ket qua dung cho bo tri so bo/toi uu; thiet ke chi tiet phai chay MCOC/FEM day du.")
    L.append("")
    return "\n".join(L)


# ============================================================================
# Ghi báo cáo ra tệp
# ============================================================================
def export_technical_report(filepath, results, params, loads, project_name="Cong trinh"):
    """Ghi báo cáo kỹ thuật (Markdown) ra filepath. Trả về filepath."""
    text = build_report_text(results, params, loads, project_name)
    if not filepath.lower().endswith(('.md', '.txt')):
        filepath = os.path.splitext(filepath)[0] + "_baocao_kythuat.md"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    return filepath
