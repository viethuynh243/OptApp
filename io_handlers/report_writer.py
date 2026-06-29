"""
report_writer.py - Xuất BẢN TÍNH KỸ THUẬT CHUẨN (Markdown) cho phương án cọc.

Khác với file_io.export_output_file (định dạng MCOC), báo cáo này hướng tới
THẨM TRA KỸ SƯ: có hệ số sử dụng, tổ hợp chi phối, bảng ràng buộc R1-R8 kèm
tỷ lệ, lực ngang Hmax, và phụ lục phạm vi/giới hạn mô hình.

Đơn vị: toàn bộ ở Tấn (T) và T.m theo MCOC (tải trọng, [Po]/[Ct]/[M], lực cọc).
Hàm tự đọc từ results['recommended'] + params + loads.
"""

import os
import numpy as np

from core import rigid_cap, tcvn
from core.version import __version__
from core.constants import (SPACING_MIN_FACTOR, SPACING_MAX_FACTOR,
                            get_safe_d, effective_min_spacing,
                            ENABLE_LATERAL_CHECK, ENABLE_PM_INTERACTION,
                            ENFORCE_SPACING_MAX)


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
def build_report_text(results, params, loads, project_name="Cong trinh",
                      enable_R7=None, enable_R8=None, ext_info=None):
    """Dựng nội dung báo cáo (str, Markdown). Tách riêng để dễ test.

    enable_R7/enable_R8: ép BẬT/TẮT hiển thị R7/R8 (None = theo cờ core.constants).
        Luồng tối ưu mở rộng truyền True để báo cáo thể hiện R7/R8 dù cờ lõi tắt.
    ext_info: (tùy chọn) thông tin quét đường kính + thu bệ để thêm mục 3b.
        {'winner_d', 'rows':[{'d','n','pmax','cost','ok'}], 'cap': cap_report}.
    """
    # Quyết định có hiển thị R7/R8 hay không (mặc định theo cờ lõi)
    show_R7 = ENABLE_LATERAL_CHECK if enable_R7 is None else bool(enable_R7)
    show_R8 = ENABLE_PM_INTERACTION if enable_R8 is None else bool(enable_R8)

    cfg = results.get('recommended')
    if not cfg:
        return f"# BAN TINH MONG COC — {project_name}\n\nKhong tim duoc phuong an thoa man.\n"

    from core import lrfd
    # Cơ sở thiết kế: TCVN 11823 (LRFD) đặt Po=φ·Rn + tải có hệ số; TCVN 10304 đặt Rc,d.
    params, loads = lrfd.apply_design_basis(params, loads)
    _design_basis = lrfd.design_basis(params)
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

    # Hình học — R3 theo CẤU TRÚC lưới để KHỚP với lõi (mechanics/nsga2):
    # Kiểu B (hoa mai) hàng kề lệch sx/2 nên cặp gần nhất là ĐƯỜNG CHÉO
    # √((sx/2)²+sy²); min_spacing bỏ sót cận TRÊN (sx,sy ≤ 6d vẫn cho chéo > 6d).
    _spac = rigid_cap.spacing_values(cfg.get('type'), cfg.get('nx', 0), cfg.get('ny', 0),
                                     cfg.get('sx', 0), cfg.get('sy', 0), coords)
    s_low = min((v for _, v, _ in _spac), default=rigid_cap.min_spacing(coords))
    _highs = [v for _, v, chk in _spac if chk]
    s_high = max(_highs) if _highs else None        # None = không xác định cận trên
    r3a_ok = s_low >= s_min_req - 1e-3
    r3b_ok = (s_high is None) or (s_high <= s_max_req + 1e-3)
    max_x = float(np.max(np.abs(coords[:, 0])))
    max_y = float(np.max(np.abs(coords[:, 1])))

    L = []
    L.append(f"# BAN TINH KIEM TRA & TOI UU BO TRI MONG COC")
    L.append(f"## Cong trinh: {project_name}\n")
    L.append(f"OptApp v{__version__}. Noi luc tinh bang MCOC (chinh xac). "
             "Don vi: Tan (T), T.m.\n")

    # 0. Cơ sở thiết kế — minh bạch tiêu chuẩn + hệ số để kỹ sư đối chiếu/nghiệm thu.
    from core import lrfd as _lrfd
    src = params.get('_capacity_source', 'input')
    Po_rep = params.get('P_LIMIT', 0.0) or 0.0
    L.append("## 0. CO SO THIET KE\n")
    if _design_basis == 'TCVN11823':
        lf = params.get('_lrfd_factors', {}) or {}
        L.append("**TCVN 11823:2017 (Thiet ke cau duong bo) — LRFD.** "
                 "Tieu chi trang thai gioi han: Σγ·Q ≤ φ·Rn. Noi luc van do MCOC tinh (oracle).\n")
        if src == 'tcvn_11823_10':
            note_sp = ", mong 1 coc → φ×0,8" if lf.get('single_pile') else ""
            L.append("- Suc khang co he so: φ = %.2f (coc %s, phuong phap '%s'%s); "
                     "P_LIMIT = φ·Rn = %.1f T (Rn = %.1f T)."
                     % (lf.get('phi_c', 0.0), lf.get('pile_type', '?'),
                        lf.get('method', '?'), note_sp, Po_rep, lf.get('R_n', 0.0)))
        else:
            L.append("- Suc khang: P_LIMIT = %.1f T (NHAP TAY, coi la φ·Rn — CHUA khai bao "
                     "Rn + phuong phap de tu tinh φ theo TCVN 11823-10)." % Po_rep)
        if _lrfd.lrfd_load_factoring_enabled(params):
            st = params.get('STRENGTH_STATE', _lrfd.DEFAULT_STRENGTH_STATE)
            L.append("- Tai co he so: da ap to hop %s (γ theo loai tai). pmax la hieu ung tai CO HE SO."
                     % st)
        else:
            L.append("- Tai co he so: **CHUA cau hinh** (chua gan load_type / LRFD_ENABLE) → γ=1,0; "
                     "pmax la tai DANH NGHIA. Day CHUA phai kiem LRFD day du.")
        L.append("\n> ⚠️ He so γ/φ la TRI THAM KHAO (theo AASHTO LRFD) — CAN KY SU doi chieu, "
                 "nghiem thu voi TCVN 11823-3:2017 (tai) & TCVN 11823-10:2017 (nen mong) truoc khi "
                 "dung cho ho so. Xem docs/project/MIGRATION_TCVN11823.md.\n")
    else:
        cap_note = "(Rc,d, Dieu 7.1.11)" if src == 'tcvn_7.1.11' else "(nhap tay)"
        L.append("**TCVN 10304:2014 (Mong coc) — suc chiu tai cho phep.** "
                 "Tieu chi: N ≤ Rc,d. P_LIMIT = %.1f T %s. Noi luc do MCOC tinh.\n"
                 % (Po_rep, cap_note))

    # 1. Số liệu đầu vào
    L.append("## 1. SO LIEU DAU VAO\n")
    L.append("| Thong so | Ky hieu | Gia tri | Don vi |")
    L.append("|---|---|---:|---|")
    L.append(f"| Rong be | Lx | {_fmt(params.get('L_X',0))} | m |")
    L.append(f"| Dai be | Ly | {_fmt(params.get('L_Y',0))} | m |")
    L.append(f"| Duong kinh coc | d | {_fmt(d)} | m |")
    L.append(f"| Tim coc -> mep be toi thieu | c_min | {_fmt(SAFE_D)} | m |")
    src = params.get('_capacity_source', 'input')
    po_label = "[Po] = Rc,d" if src == 'tcvn_7.1.11' else "[Po]"
    ct_label = "[Ct] = Rt,d" if src == 'tcvn_7.1.11' else "[Ct]"
    L.append(f"| Suc chiu nen | {po_label} | {_fmt(Po,1)} | T |")
    L.append(f"| Suc chiu nho | {ct_label} | {_fmt(Ct,1)} | T |")
    L.append(f"| Suc chiu uon | [M] | {_fmt(Mlim,1)} | T.m |")
    if show_R7:
        L.append(f"| Suc chiu luc ngang | [H] | {_fmt(Hlim,1)} | T |")
    L.append("")

    # 1b. Sức chịu tải thiết kế theo Điều 7.1.11 (chỉ khi nhập Rc,k + hệ số γ)
    if src == 'tcvn_7.1.11':
        g = params.get('_tcvn_factors', {})
        L.append("**Suc chiu tai thiet ke (TCVN 10304:2014, Dieu 7.1.11):** "
                 "`Rc,d = (g0/gn) * (Rc,k/gk)`\n")
        L.append("| Dai luong | Ky hieu | Gia tri |")
        L.append("|---|---|---:|")
        L.append(f"| SCT nen tieu chuan | Rc,k | {_fmt(g.get('R_ck',0),1)} T |")
        if g.get('R_tk'):
            L.append(f"| SCT keo tieu chuan | Rt,k | {_fmt(g.get('R_tk',0),1)} T |")
        L.append(f"| He so dieu kien lam viec | g0 | {_fmt(g.get('gamma_0',0),3)} |")
        L.append(f"| He so tin cay tam quan trong | gn | {_fmt(g.get('gamma_n',0),3)} |")
        L.append(f"| He so tin cay theo dat | gk | {_fmt(g.get('gamma_k',0),3)} |")
        gk_used = g.get('gamma_k', 0) or 0
        gk_rec = tcvn.resolve_gamma_k(n)
        L.append(f"| gk khuyen nghi theo so coc (n={n}) | gk_tcvn | {_fmt(gk_rec,3)} |")
        L.append(f"| => SCT nen thiet ke | Rc,d | {_fmt(Po,1)} T |")
        if gk_used and abs(gk_used - gk_rec) > 1e-6:
            L.append(f"\n> LUU Y (Dieu 7.1.11): gk dang dung = {_fmt(gk_used,3)} KHAC gk khuyen "
                     f"nghi theo so coc thuc te ({_fmt(gk_rec,3)}, n={n} coc). Nen cap nhat gk "
                     "roi tinh lai Rc,d=[Po] cho dung tieu chuan.")
        L.append("")
    else:
        L.append("> [Po]/[Ct] duoc NHAP truc tiep, coi la SUC CHIU TAI THIET KE Rc,d/Rt,d. "
                 "De chuong trinh tu tinh theo Dieu 7.1.11, hay khai bao Rc,k (R_C_K) "
                 "cung g0 (GAMMA_0), gn (GAMMA_N hoac IMPORTANCE_LEVEL), gk (GAMMA_K).\n")

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
        _buoc = f"- Buoc coc: sx = {_fmt(cfg['sx'])} m; sy = {_fmt(cfg['sy'])} m"
        if cfg.get('type') == 'B' and cfg.get('sy'):
            _buoc += f"; cheo = {_fmt(float(np.hypot(cfg['sx'] / 2.0, cfg['sy'])))} m"
        L.append(_buoc)
    L.append(f"- Ly do chon: {results.get('reason','')}")
    L.append("")

    # 3b. Tối ưu mở rộng: quét đường kính + thu bệ (chỉ khi có ext_info)
    if ext_info:
        L.append("## 3b. TOI UU MO RONG (duong kinh + R7/R8 + thu be)\n")
        L.append(f"- Duong kinh chon: **d = {_fmt(ext_info.get('winner_d', d))} m** "
                 "(quet theo bang ung vien, cham bang MCOC chinh xac).")
        L.append("")
        L.append("| d (m) | So coc | Pmax (T) | Chi phi VL | KL |")
        L.append("|---:|---:|---:|---:|:--:|")
        for r in ext_info.get('rows', []):
            kl = 'CHON' if abs(r['d'] - ext_info.get('winner_d', -1)) < 1e-9 else \
                 ('DAT' if r.get('ok') else 'khong')
            pmax_s = _fmt(r['pmax'], 1) if r.get('ok') else '-'
            cost_s = f"{r['cost']:.3f}" if r.get('ok') else '-'
            n_s = str(r['n']) if r.get('ok') else '-'
            L.append(f"| {_fmt(r['d'])} | {n_s} | {pmax_s} | {cost_s} | {kl} |")
        L.append("")
        L.append("Chi phi VL = so coc x dien tich tiet dien (pi*d^2/4) — ty le the "
                 "tich be tong coc tren 1 m dai; chon phuong an re nhat.\n")
        cap = ext_info.get('cap')
        if cap:
            act = 'da ap dung' if cap.get('applied') else 'chi de xuat'
            L.append(f"- **Thu kich thuoc be (TCVN, mep cach tim >= {_fmt(cap['safe_d'])} m):** "
                     f"{_fmt(cap['old_LX'])} x {_fmt(cap['old_LY'])} -> "
                     f"**{_fmt(cap['new_LX'])} x {_fmt(cap['new_LY'])} m** ({act}, "
                     f"lam tron {_fmt(cap['round_to'])} m).")
            if cap.get('saved_area', 0) > 1e-9:
                L.append(f"- Tiet kiem dien tich be: {_fmt(cap['saved_area'])} m2 "
                         f"({cap['saved_pct']:.1f}%).")
        L.append("")

    # 4. Kiểm tra hình học
    L.append("## 4. KIEM TRA HINH HOC\n")
    L.append("| Ma | Dieu kien | Gia tri | Gioi han | Ty le | KL |")
    L.append("|---|---|---:|---:|---:|:--:|")
    # R3a (cận dưới 3d, BẮT BUỘC theo TCVN): dùng NGUỒN DUY NHẤT spacing_values (s_low).
    L.append(f"| R3a | Khoang cach tim-tim >= {_fmt(s_min_req)} m | {_fmt(s_low)} | "
             f"{_fmt(s_min_req)} | {_ratio(s_min_req, s_low)} | "
             f"{'DAT' if r3a_ok else 'KHONG'} |")
    # R3b (cận trên 6d): KHONG phai gioi han TCVN -> chi CANH BAO khi vuot,
    # tru khi bat ENFORCE_SPACING_MAX. Kiểu B xét đường chéo (s_high từ spacing_values).
    _r3b_val = _fmt(s_high) if s_high is not None else '-'
    _r3b_ratio = _ratio(s_high, s_max_req) if s_high is not None else '-'
    if s_high is None:
        _r3b_kl = '-'                                   # không xác định cận trên
    elif r3b_ok:
        _r3b_kl = 'DAT'
    else:
        _r3b_kl = 'KHONG' if ENFORCE_SPACING_MAX else 'CANH BAO'
    L.append(f"| R3b | Khoang cach <= 6d (quy uoc; Kieu B: duong cheo) | {_r3b_val} | "
             f"{_fmt(s_max_req)} | {_r3b_ratio} | {_r3b_kl} |")
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
    if show_R7:
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
        if show_R7:
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
    # R3: cận dưới 3d (TCVN) bắt buộc; cận trên 6d chỉ là quy ước (cảnh báo mềm).
    # Giá trị hiển thị theo NGUỒN DUY NHẤT spacing_values (s_low / s_high, Kiểu B: chéo).
    _r3_val = _fmt(s_low) + (f" / {_fmt(s_high)}" if s_high is not None else "")
    if not r3a_ok:
        r3_kl = 'KHONG'                                  # vi pham 3d -> loai
    elif not r3b_ok:
        r3_kl = 'KHONG' if ENFORCE_SPACING_MAX else 'CANH BAO (>6d)'
    else:
        r3_kl = 'DAT'
    L.append(f"| R3 | k/c >= 3d (TCVN); <= 6d (quy uoc; Kieu B: chéo) | {_r3_val} | "
             f"[{_fmt(s_min_req)}, {_fmt(s_max_req)}] | {r3_kl} |")
    L.append(f"| R4 | Tim coc cach mep >= c_min | OK | - | "
             f"{'DAT' if (max_x+SAFE_D<=params.get('L_X',0)/2+1e-3 and max_y+SAFE_D<=params.get('L_Y',0)/2+1e-3) else 'KHONG'} |")
    L.append(f"| R5/R6 | Mx, My <= [M] | {_fmt(mmax,1)} | {_fmt(Mlim,1) if Mlim>0 else '-'} | "
             f"{('DAT' if mmax<=Mlim else 'KHONG') if Mlim>0 else '-'} |")
    # R7 (lực ngang) & R8 (tương tác P-M) chỉ hiện khi được BẬT trong constants.
    if show_R7:
        r7_kl = ('DAT' if hmax_cfg <= Hlim else 'KHONG') if Hlim > 0 else '-'
        L.append(f"| R7 | H_max <= [H] | {_fmt(hmax_cfg,1)} | "
                 f"{_fmt(Hlim,1) if Hlim>0 else '-'} | {r7_kl} |")
    if show_R8:
        r8_kl = ('DAT' if (inter is not None and inter <= 1) else 'KHONG') if inter is not None else '-'
        L.append(f"| R8 | Tuong tac P-M <= 1 | "
                 f"{(_fmt(inter,2) if inter is not None else '-')} | "
                 f"{'1.00' if inter is not None else '-'} | {r8_kl} |")
    L.append("")

    # 6b. Kiểm tra nhóm cọc: móng khối quy ước & lún (Điều 7.4)
    L.append("## 6b. MONG KHOI QUY UOC & DO LUN  (TCVN 10304:2014, Dieu 7.4)\n")
    block = tcvn.equivalent_block(coords, params)
    if block.get('evaluated'):
        L.append("| Dai luong | Ky hieu | Gia tri |")
        L.append("|---|---|---:|")
        L.append(f"| Chieu dai coc | Lc | {_fmt(block['Lc'])} m |")
        L.append(f"| Goc ma sat trung binh | phi_tb | {_fmt(block['phi_tb'],1)} do |")
        L.append(f"| Be rong khoi quy uoc | Bqu | {_fmt(block['B_qu'])} m |")
        L.append(f"| Chieu dai khoi quy uoc | Lqu | {_fmt(block['L_qu'])} m |")
        L.append(f"| Dien tich day khoi | Aqu | {_fmt(block['A_qu'])} m2 |")
        L.append(f"| Do sau day khoi | Df | {_fmt(block['base_depth'])} m |")
        if block.get('a_capped_2d'):
            L.append(f"| Mo rong moi ben | a | {_fmt(block.get('a_side',0))} m (da chan a<=2d, dat dinh yeu IL>0,6) |")
        L.append("")
        st = tcvn.settlement(coords, loads, params)
        if st.get('evaluated'):
            S_mm = st['S'] * 1000.0
            Sgh = st.get('S_limit')
            kl = '-' if Sgh is None else ('DAT' if st.get('ok') else 'KHONG')
            L.append(f"- Ap luc gay lun day khoi quy uoc: p_gl = {_fmt(st['p_gl'],2)} T/m2.")
            L.append(f"- Do lun tinh toan **S = {_fmt(S_mm,1)} mm** = Se + S_khoi "
                     f"(Dieu 7.4.4: bien dang dan hoi than coc + lun khoi quy uoc).")
            se_note = "" if st.get('se_evaluated') else " (bo qua: thieu E_b/dien tich coc)"
            L.append(f"    - Se (dan hoi than coc) = {_fmt(st.get('S_e',0)*1000.0,2)} mm{se_note};"
                     f" S_khoi = {_fmt(st.get('S_block',0)*1000.0,1)} mm.")
            L.append("    - S_khoi: cong lun tung lop theo TCVN 9362:2012 (beta=0,8), ung suat "
                     "tai tam khoi theo Boussinesq; vung nen toi khi sigma_z <= 0,2 sigma'vz.")
            if Sgh is not None:
                L.append(f"- Do lun gioi han S_gh = {_fmt(Sgh*1000.0,1)} mm -> **{kl}**.")
            else:
                L.append("- Chua khai bao do lun gioi han S_gh (S_LIMIT) de ket luan dat/khong.")
        else:
            L.append(f"> **CHUA KIEM DO LUN** — {st.get('reason','')}. "
                     "Khai bao `soil_below` (cac lop dat duoi mui: h, E, gamma) de tinh.")
    else:
        L.append(f"> **CHUA KIEM MONG KHOI QUY UOC / DO LUN** — {block.get('reason','')}.")
        L.append("> Theo Dieu 7.4, mong NHOM coc bat buoc kiem suc chiu tai khoi quy uoc "
                 "va do lun S <= S_gh. Hay bo sung: `pile_length` (Lc), `phi_tb`, "
                 "`soil_below` (lop dat duoi mui), `S_LIMIT`.")
    L.append("")

    # 6c. Kiểm tra cọc chịu NGANG theo phương pháp "m" (TCVN 10304:2014 Phụ lục A)
    try:
        from core import ssi_engine
        _hmag = lambda ld: (float(ld.get('Hx', 0)) ** 2 + float(ld.get('Hy', 0)) ** 2) ** 0.5
        gload = max(loads, key=_hmag) if loads else None
        if gload is not None and _hmag(gload) > 1e-9:
            ssi = ssi_engine.analyze(coords, params, gload)
            lat = ssi.get('lateral')
            if lat:
                model = ('phuong phap "m" (k = m.z.d, Phu luc A)'
                         if lat.get('model') == 'm' else 'lo xo nen hang so k = ks.d')
                L.append("## 6c. KIEM TRA COC CHIU NGANG  (TCVN 10304:2014, Phu luc A)\n")
                L.append(f"Mo hinh nen ngang: {model}. Coc bat loi nhat: #{lat.get('pile_index', 0) + 1}"
                         f"{' (co xet hieu ung nhom, p-mult=' + _fmt(lat.get('pmult', 1), 2) + ')' if ssi['meta'].get('group_effect') else ''}.")
                L.append("")
                L.append("| Dai luong | Ky hieu | Gia tri |")
                L.append("|---|---|---:|")
                L.append(f"| Luc ngang dau coc (bat loi) | H_coc | {_fmt(lat['H_pile'], 2)} T |")
                L.append(f"| Chuyen vi ngang dau coc | y0 | {_fmt(lat['y_head'] * 1000.0, 2)} mm |")
                L.append(f"| Momen uon lon nhat than coc | M_max | {_fmt(lat['M_max'], 2)} T.m |")
                L.append(f"| Tham so dac trung | beta | {_fmt(lat['beta'], 3)} 1/m |")
                L.append("")
                if ssi['meta'].get('Lc_illustrative'):
                    L.append("> LUU Y: chua khai bao chieu dai coc Lc -> dung gia tri minh hoa; "
                             "ket qua chuyen vi/momen ngang chi tham khao.")
                L.append("> R7 (Hmax <= [H]) o Muc 6 la kiem SANG LOC theo suc chiu luc ngang cho "
                         "phep; muc nay bo sung CHUYEN VI dau coc + MOMEN than coc theo Phu luc A.")
                L.append("")
    except Exception:
        pass

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
    if show_R7:
        L.append("- Luc ngang H_max phan phoi tu Hx, Hy, Mz (tinh hoc, coc dung do cung deu); "
                 "**momen than coc do tai ngang** can phan tich p-y rieng khi dang ke.")
    L.append("- Pham vi OptApp: kiem TTGH I theo LUC DOC TRUC tung coc "
             "(N_max <= Rc,d; N_min >= -Rt,d) + hinh hoc bo tri. "
             "Suc chiu tai Rc,d/Rt,d theo Dieu 7.1.11.")
    L.append("- Can kiem RIENG theo TCVN 10304:2014 (xem muc 6b neu da nhap so lieu dia chat):")
    L.append("  - Suc chiu tai theo VAT LIEU coc (Dieu 7.1.11 + 7.2): Rc,d = min(theo dat, theo vat lieu).")
    L.append("  - Suc chiu tai NHOM coc / mong khoi quy uoc va DO LUN (Dieu 7.4).")
    L.append("  - Coc & chuyen vi NGANG theo mo hinh nen (Phu luc A) khi Hx, Hy dang ke.")
    L.append("- Tai trong N, M phai la NOI LUC TINH TOAN (da to hop, nhan he so) theo "
             "TCVN 2737 / TCVN 11823.")
    L.append("- Ket qua dung cho bo tri so bo/toi uu; thiet ke chi tiet phai chay MCOC/FEM day du.")
    L.append("")
    return "\n".join(L)


# ============================================================================
# Ghi báo cáo ra tệp
# ============================================================================
def export_technical_report(filepath, results, params, loads, project_name="Cong trinh",
                            enable_R7=None, enable_R8=None, ext_info=None):
    """Ghi báo cáo kỹ thuật (Markdown) ra filepath. Trả về filepath."""
    text = build_report_text(results, params, loads, project_name,
                             enable_R7=enable_R7, enable_R8=enable_R8, ext_info=ext_info)
    if not filepath.lower().endswith(('.md', '.txt')):
        filepath = os.path.splitext(filepath)[0] + "_baocao_kythuat.md"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    return filepath


# ============================================================================
# Xuất báo cáo kỹ thuật dạng PDF (render bằng reportlab, hỗ trợ tiếng Việt)
# ============================================================================
# Cache tên font đã đăng ký để khỏi đăng ký lại mỗi lần xuất.
_PDF_FONT = None


def _register_pdf_fonts():
    """Đăng ký font có dấu tiếng Việt cho reportlab.

    Dùng DejaVuSans đi kèm matplotlib (đã có sẵn trong gói) để không phải thêm
    tệp font riêng. Nếu không tìm thấy, lùi về Helvetica (mất dấu nhưng vẫn chạy).
    Trả về (font_thuong, font_dam).
    """
    global _PDF_FONT
    if _PDF_FONT:
        return _PDF_FONT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    try:
        import matplotlib
        base = os.path.join(os.path.dirname(matplotlib.__file__),
                            'mpl-data', 'fonts', 'ttf')
        pdfmetrics.registerFont(TTFont('DejaVu', os.path.join(base, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', os.path.join(base, 'DejaVuSans-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('DejaVu-Mono', os.path.join(base, 'DejaVuSansMono.ttf')))
        pdfmetrics.registerFontFamily('DejaVu', normal='DejaVu', bold='DejaVu-Bold',
                                      italic='DejaVu', boldItalic='DejaVu-Bold')
        _PDF_FONT = ('DejaVu', 'DejaVu-Bold', 'DejaVu-Mono')
    except Exception:
        _PDF_FONT = ('Helvetica', 'Helvetica-Bold', 'Courier')
    return _PDF_FONT


def _render_markdown_pdf(md_text, out_path, base_dir=None):
    """Render văn bản Markdown thành PDF (reportlab, hỗ trợ tiếng Việt).

    Hỗ trợ: tiêu đề (#/##/###), bảng (| … | kể cả pipe thoát \\|), trích dẫn (>),
    đường kẻ ngang (---), khối mã ```…```, ảnh ![alt](đường_dẫn) và in đậm (**…**).
    `base_dir` dùng để giải đường dẫn ảnh tương đối (mặc định = thư mục out_path).
    """
    import re
    import html as _html
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, HRFlowable, Preformatted, Image)

    fn, fb, fm = _register_pdf_fonts()
    base_dir = base_dir or os.path.dirname(os.path.abspath(out_path))
    navy = colors.HexColor('#1a3c5e')
    CONTENT_W = 180 * mm                                 # A4 trừ lề 15mm hai bên
    S = {
        'h1':   ParagraphStyle('h1', fontName=fb, fontSize=15, leading=19, spaceAfter=6, textColor=navy),
        'h2':   ParagraphStyle('h2', fontName=fb, fontSize=12, leading=15, spaceBefore=8, spaceAfter=4, textColor=navy),
        'h3':   ParagraphStyle('h3', fontName=fb, fontSize=10.5, leading=13, spaceBefore=6, spaceAfter=3),
        'body': ParagraphStyle('body', fontName=fn, fontSize=9, leading=12, spaceAfter=2),
        'note': ParagraphStyle('note', fontName=fn, fontSize=8.5, leading=11, leftIndent=6, textColor=colors.HexColor('#555')),
        # Dùng font thường (DejaVuSans) cho khối mã: DejaVuSansMono THIẾU nhiều
        # glyph tiếng Việt (ầ/ể/ổ…) nên dựng sai dấu. Giữ nền xám để vẫn ra "code".
        'code': ParagraphStyle('code', fontName=fn, fontSize=8, leading=11, leftIndent=6,
                               backColor=colors.HexColor('#f4f6f8'), textColor=colors.HexColor('#222')),
        'cap':  ParagraphStyle('cap', fontName=fn, fontSize=8.5, leading=11, alignment=1, textColor=colors.HexColor('#555')),
        'cell': ParagraphStyle('cell', fontName=fn, fontSize=8, leading=10),
        'cellh': ParagraphStyle('cellh', fontName=fb, fontSize=8, leading=10, alignment=1, textColor=colors.white),
    }
    img_re = re.compile(r'^!\[(.*?)\]\((.*?)\)\s*$')

    def inline(s):
        """Thoát ký tự XML, bỏ pipe thoát \\| và nháy mã `, đổi **đậm** -> <b>."""
        s = _html.escape(s).replace('\\|', '|').replace('`', '')
        return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)

    def is_sep(cells):
        return all(set(c) <= set('-: ') and '-' in c for c in cells)

    def split_cells(row):
        # Tách theo dấu | KHÔNG đứng sau '\' (giữ \| là pipe trong nội dung ô)
        return [c.strip() for c in re.split(r'(?<!\\)\|', row.strip().strip('|'))]

    def make_table(block):
        parsed = [split_cells(r) for r in block]
        parsed = [r for r in parsed if not is_sep(r)]
        if not parsed:
            return Spacer(1, 1)
        ncol = max(len(r) for r in parsed)
        for r in parsed:
            r += [''] * (ncol - len(r))
        data = [[Paragraph(inline(c), S['cellh']) for c in parsed[0]]]
        for r in parsed[1:]:
            data.append([Paragraph(inline(c), S['cell']) for c in r])
        t = Table(data, colWidths=[CONTENT_W / ncol] * ncol, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#b0b8c0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#eef1f4')]),
        ]))
        return t

    def make_image(path, alt):
        full = path if os.path.isabs(path) else os.path.join(base_dir, path)
        if not os.path.exists(full):
            return Paragraph(inline(f"[Thiếu ảnh: {alt or path}]"), S['note'])
        iw, ih = ImageReader(full).getSize()
        w = min(CONTENT_W, iw * 72.0 / 96.0)            # không phóng to quá khổ
        return Image(full, width=w, height=w * ih / float(iw))

    flow = []
    lines = md_text.split('\n')
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            flow.append(Spacer(1, 4)); i += 1; continue
        if ln.lstrip().startswith('```'):               # khối mã
            i += 1; code = []
            while i < len(lines) and not lines[i].lstrip().startswith('```'):
                code.append(lines[i]); i += 1
            i += 1                                        # bỏ dòng ``` đóng
            flow.append(Preformatted('\n'.join(code) or ' ', S['code']))
            flow.append(Spacer(1, 4)); continue
        if ln.lstrip().startswith('|'):                 # khối bảng
            block = []
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                block.append(lines[i]); i += 1
            flow.append(make_table(block)); flow.append(Spacer(1, 6)); continue
        m = img_re.match(ln.strip())
        if m:                                            # ảnh
            flow.append(make_image(m.group(2), m.group(1))); flow.append(Spacer(1, 4)); i += 1; continue
        if ln.startswith('### '):
            flow.append(Paragraph(inline(ln[4:]), S['h3']))
        elif ln.startswith('## '):
            flow.append(Paragraph(inline(ln[3:]), S['h2']))
        elif ln.startswith('# '):
            flow.append(Paragraph(inline(ln[2:]), S['h1']))
        elif ln.strip() == '---':
            flow.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#cccccc'),
                                   spaceBefore=3, spaceAfter=3))
        elif ln.startswith('>'):
            flow.append(Paragraph(inline(ln.lstrip('> ')), S['note']))
        elif re.match(r'^\*\*Hình', ln) or re.match(r'^\*\*Bảng', ln):
            flow.append(Paragraph(inline(ln), S['cap']))   # chú thích hình/bảng canh giữa
        else:
            flow.append(Paragraph(inline(ln), S['body']))
        i += 1

    doc = SimpleDocTemplate(out_path, pagesize=A4, title="Bao cao OptApp",
                            leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm)
    doc.build(flow)


def export_markdown_pdf(md_path, pdf_path=None):
    """Chuyển một tệp Markdown bất kỳ sang PDF. Trả về đường dẫn PDF.

    Ảnh tương đối trong tài liệu được giải theo thư mục chứa tệp .md.
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        md = f.read()
    if not pdf_path:
        pdf_path = os.path.splitext(md_path)[0] + ".pdf"
    _render_markdown_pdf(md, pdf_path, base_dir=os.path.dirname(os.path.abspath(md_path)))
    return pdf_path


def export_technical_report_pdf(filepath, results, params, loads, project_name="Cong trinh",
                                enable_R7=None, enable_R8=None, ext_info=None):
    """Ghi báo cáo kỹ thuật dạng PDF (cùng nội dung bản Markdown). Trả về filepath.

    Tái dùng build_report_text làm nguồn DUY NHẤT để PDF và .md luôn khớp nhau.
    """
    text = build_report_text(results, params, loads, project_name,
                             enable_R7=enable_R7, enable_R8=enable_R8, ext_info=ext_info)
    if not filepath.lower().endswith('.pdf'):
        filepath = os.path.splitext(filepath)[0] + ".pdf"
    _render_markdown_pdf(text, filepath)
    return filepath
