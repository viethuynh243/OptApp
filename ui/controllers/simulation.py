"""simulation.py - SimulationView: vẽ mô phỏng + dữ liệu audit R1–R8.

Tách từ ui/main_window.py (Plan 023, Pha 3e) — giữ NGUYÊN hành vi. Vẽ lên
app.plot_canvas theo app.view_mode / app.cb_config / app.cb_load_case.
"""
import numpy as np
from core import rigid_cap
from core.constants import effective_min_spacing
from ui import strings as S


class SimulationView:
    """Vẽ MÔ PHỎNG trên plot_canvas (mặt bằng / audit R1–R8 / 3D / SSI / thiết kế đài), tính khung nhìn chung, kiểm tra phương án ĐẠT đầy đủ, và tổng hợp số liệu R1–R8."""

    def __init__(self, app):
        self.app = app

    def update_simulation(self, event=None):
        """Vẽ lại mô phỏng mặt bằng cho phương án + tổ hợp tải đang chọn.

        Lấy lực cọc theo mô hình bệ cứng rồi hiệu chỉnh theo hệ số khớp Pmax
        thực (MCOC) để hình vẽ đồng nhất với phần kết luận.
        """
        if not self.app.current_config: return

        idx_load = self.app.cb_load_case.current()
        if idx_load < 0: idx_load = 0

        config_name = self.app.cb_config.get()
        selected_cfg = None

        if config_name == S.CFG_GOC:
            selected_cfg = self.app.current_config.get('original_config')
        elif config_name == S.CFG_DEXUAT:
            selected_cfg = self.app.current_config.get('recommended')
        elif config_name.startswith(S.CFG_PREFIX):
            try:
                num = int(config_name.split()[2])
                selected_cfg = self.app.current_config['all_valid_configs'][num - 1]
            except:
                pass

        if not selected_cfg: return

        coords = np.array(selected_cfg['coords'])  # Ép về numpy array, xử lý cả list lẫn array
        if coords.ndim != 2 or coords.shape[0] == 0: return

        forces = None
        params_dict = self.app.get_params_dict()

        # Bệ của phương án nào PHẢI đi theo phương án đó: nếu config mang theo
        # kích thước bệ riêng (vd phương án gốc giữ bệ gốc, phương án đề xuất
        # mang bệ đã thu), ưu tiên dùng nó thay cho L_X/L_Y trên UI — nhờ vậy
        # mặt bằng + bảng audit R4 phản ánh đúng tiến hóa kích thước bệ.
        cap_lx = selected_cfg.get('cap_lx'); cap_ly = selected_cfg.get('cap_ly')
        if cap_lx and cap_ly:
            params_dict['L_X'] = float(cap_lx)
            params_dict['L_Y'] = float(cap_ly)
        # ...và ĐƯỜNG KÍNH / sức chịu cũng đi theo phương án: phương án gốc audit
        # R3 (3d–6d), R4 (mép ≥ d), R5/R6 theo d/[Po]/[Ct]/[M] GỐC — không theo
        # đường kính thắng (tránh báo KHÔNG ĐẠT oan khi UI đã đổi sang d thắng).
        if selected_cfg.get('d_orig'):
            params_dict['D_PILE'] = float(selected_cfg['d_orig'])
            params_dict['SAFE_D'] = float(selected_cfg.get('safe_d_orig')
                                          or selected_cfg['d_orig'])
            if selected_cfg.get('Po_orig'):
                params_dict['P_LIMIT'] = float(selected_cfg['Po_orig'])
            if selected_cfg.get('ct_orig') is not None:
                params_dict['P_TENSION'] = float(selected_cfg['ct_orig'])
            if selected_cfg.get('m_orig') is not None:
                params_dict['M_LIMIT'] = float(selected_cfg['m_orig'])

        # Hệ số hiệu chỉnh: ưu tiên khớp Pmax THỰC (MCOC) của phương án đang xem,
        # để lực vẽ trên canvas đồng nhất với kết quả ở phần kết luận.
        calibration_factor = 1.0
        cfg_pmax = selected_cfg.get('pmax', 0) or 0
        cfg_rigid_pmax = rigid_cap.pmax_pmin(coords, self.app.loads)[0] if self.app.loads else 0.0
        if cfg_pmax > 0 and cfg_rigid_pmax > 0:
            calibration_factor = rigid_cap.calibration_factor(cfg_rigid_pmax, cfg_pmax)
        elif getattr(self.app, 'original_coords', None) and self.app.loads:
            orig_pmax_actual = params_dict.get('orig_pmax', 519.63)
            orig_rigid_pmax = rigid_cap.pmax_pmin(self.app.original_coords, self.app.loads)[0]
            calibration_factor = rigid_cap.calibration_factor(orig_rigid_pmax, orig_pmax_actual)

        # Luôn tính forces bằng mô hình bệ cứng — kể cả khi KHÔNG ĐẠT
        if self.app.loads:
            load = self.app.loads[min(idx_load, len(self.app.loads) - 1)]
            raw = rigid_cap.pile_forces(coords, load)          # công thức dùng chung
            forces = [float(p) * calibration_factor for p in raw]

        mxmax = selected_cfg.get('mxmax', 0)
        mymax = selected_cfg.get('mymax', 0)

        # Số liệu kiểm tra điều kiện R1–R8 theo từng tổ hợp (chuẩn tư vấn) + cập nhật KPI.
        # Tính luôn cho cả 2 chế độ để dải KPI nhất quán dù đang xem mặt bằng.
        cdata = self._build_constraint_data(selected_cfg, coords, params_dict, calibration_factor)
        self.app._update_kpi(cdata)

        if self.app.view_mode.get() == S.VIEW_AUDIT:
            self.app.plot_canvas.draw_constraint_view(cdata)
        elif self.app.view_mode.get() == S.VIEW_MODEL3D:
            self.app.plot_canvas.draw_model_3d(coords, params_dict, forces,
                                           m_forces=(mxmax, mymax))
        elif self.app.view_mode.get() == S.VIEW_SSI:
            ssi_load = self.app.loads[min(idx_load, len(self.app.loads) - 1)] if self.app.loads else None
            self.app.plot_canvas.draw_ssi_view(coords, params_dict, ssi_load, self.app.loads)
        elif self.app.view_mode.get() == S.VIEW_CAPDESIGN:
            self.app.plot_canvas.draw_cap_design_view(coords, params_dict, self.app.loads)
        else:
            # Khung nhìn CHUNG cho mọi phương án -> cùng tỉ lệ khi chuyển phương án.
            view_extent = self._global_view_extent(params_dict)
            self.app.plot_canvas.draw_simulation(coords, params_dict, forces,
                                             m_forces=(mxmax, mymax), view_extent=view_extent)


    def _global_view_extent(self, params, margin=1.0):
        """Nửa bề rộng/cao KHUNG NHÌN CHUNG (đối xứng quanh tâm) bao mọi phương án.

        Lấy max bao của BỆ + CỌC qua tất cả phương án (gốc, đề xuất, các phương án
        đạt) để khi chuyển phương án, tỉ lệ pixel/mét KHÔNG đổi — cọc giữ nguyên
        cỡ, kỹ thuật viên dễ quan sát thay đổi. Trả về (hx, hy) đã cộng lề."""
        cc = self.app.current_config or {}
        cfgs = []
        if cc.get('original_config'): cfgs.append(cc['original_config'])
        if cc.get('recommended'): cfgs.append(cc['recommended'])
        cfgs += cc.get('all_valid_configs', []) or []
        d = params.get('D_PILE', 1.2) or 1.2
        hx = hy = 0.0
        for cfg in cfgs:
            lx = cfg.get('cap_lx') or params.get('L_X', 0) or 0
            ly = cfg.get('cap_ly') or params.get('L_Y', 0) or 0
            hx = max(hx, float(lx) / 2.0); hy = max(hy, float(ly) / 2.0)
            co = np.asarray(cfg.get('coords', []), float)
            if co.ndim == 2 and len(co):
                hx = max(hx, float(np.max(np.abs(co[:, 0]))) + d / 2.0)
                hy = max(hy, float(np.max(np.abs(co[:, 1]))) + d / 2.0)
        if hx <= 0 or hy <= 0:   # phòng khi thiếu dữ liệu: lùi về bệ hiện tại
            hx = (params.get('L_X', 6.0) or 6.0) / 2.0
            hy = (params.get('L_Y', 9.0) or 9.0) / 2.0
        return hx + margin, hy + margin


    def _config_fully_ok(self, cfg):
        """Phương án ĐẠT ĐẦY ĐỦ (R3/R4 hình học + R5/R5b/R6/R8 lực) — trả 1 boolean
        để TRẠNG THÁI nhất quán với bảng audit R1–R8 (tránh 'DAT chỉ xét lực').

        Lực lấy trực tiếp từ cfg (pmax/pmin/mx/my đã do MCOC chấm); hình học dùng
        chung rigid_cap.spacing_values + mép bệ như _build_constraint_data."""
        params = self.app.get_params_dict()
        Po = params.get('P_LIMIT', 0) or 0
        Ct = params.get('P_TENSION', 0) or 0
        Mlim = params.get('M_LIMIT', 0) or 0
        d = params.get('D_PILE', 1.0) or 1.0
        c_min = params.get('SAFE_D', d)
        coords = np.asarray(cfg.get('coords', []), float)
        if coords.ndim != 2 or len(coords) == 0:
            return False
        pmax = cfg.get('pmax', 0) or 0; pmin = cfg.get('pmin', 0) or 0
        mxmax = cfg.get('mxmax', 0) or 0; mymax = cfg.get('mymax', 0) or 0
        ok = (pmax <= Po) if Po > 0 else True               # R5 nén
        if Ct > 0:
            ok = ok and (pmin >= -Ct)                       # R5b nhổ
        if Mlim > 0:
            ok = ok and (max(mxmax, mymax) <= Mlim)         # R6 uốn
            if Po > 0:                                      # R8 tương tác P–M
                ok = ok and (pmax / Po + max(mxmax, mymax) / Mlim <= 1.0 + 1e-6)
        # R3 khoảng cách (cùng nguồn) + R4 mép bệ
        s_min_req = effective_min_spacing(params); s_max_req = 6 * d
        for _nm, _v, _chk_up in rigid_cap.spacing_values(
                cfg.get('type'), cfg.get('nx', 0), cfg.get('ny', 0),
                cfg.get('sx', 0), cfg.get('sy', 0), coords):
            if _v < s_min_req - 1e-3 or (_chk_up and _v > s_max_req + 1e-3):
                ok = False
        # R4 mép bệ: dùng bệ RIÊNG của phương án (cap_lx/cap_ly) nếu có — khớp với
        # mặt bằng + header; tránh báo R4 oan khi ô L_X/L_Y trên UI đã bị thu nhỏ.
        Lx = cfg.get('cap_lx') or params.get('L_X', 0) or 0
        Ly = cfg.get('cap_ly') or params.get('L_Y', 0) or 0
        if Lx and Ly:
            if (float(np.max(np.abs(coords[:, 0]))) + c_min > Lx / 2 + 1e-3 or
                    float(np.max(np.abs(coords[:, 1]))) + c_min > Ly / 2 + 1e-3):
                ok = False                                  # R4 mép bệ
        return bool(ok)

    # ── Kiểm tra điều kiện R1–R8 (chuẩn tư vấn) ──────────────────────────


    def _build_constraint_data(self, cfg, coords, params, calib):
        """Tổng hợp số liệu kiểm tra điều kiện R1–R8 theo từng tổ hợp cho phương án đang xem.

        Phản chiếu Mục 5–6 của báo cáo kỹ thuật (report_writer) để bản vẽ trên
        màn hình và bản thuyết minh nhất quán: nội lực N_max/N_min từng tổ hợp
        (mô hình bệ cứng × hệ số khớp MCOC), tỷ lệ huy động R1/R2, tổ hợp chi
        phối, và tổng hợp hình học R3/R4 + uốn R5/R6.
        """
        Po = params.get('P_LIMIT', 0) or 0
        Ct = params.get('P_TENSION', 0) or 0
        Mlim = params.get('M_LIMIT', 0) or 0
        d = params.get('D_PILE', 1.0) or 1.0
        c_min = params.get('SAFE_D', d)            # R4: tim cọc cách mép ≥ d

        # R1/R2 theo từng tổ hợp + tổ hợp chi phối (N_max lớn nhất)
        rows = []
        gov_i, gov_nmax = 0, -1e18
        if self.app.loads:
            P = rigid_cap.forces_all_loads(np.asarray(coords, float), self.app.loads)
            for i in range(len(self.app.loads)):
                nmax = float(P[i].max()) * calib
                nmin = float(P[i].min()) * calib
                r1 = (nmax / Po) if Po > 0 else None
                # R2 nhổ: chỉ tính khi cọc THỰC SỰ bị kéo (N_min < 0); nén thì = 0 (an toàn)
                r2 = (max(0.0, -nmin) / Ct) if (Ct > 0) else None
                ok_i = (nmax <= Po if Po > 0 else True) and (nmin >= -Ct if Ct > 0 else True)
                rows.append({'th': i + 1, 'nmax': nmax, 'nmin': nmin,
                             'r1': r1, 'r2': r2, 'ok': ok_i})
                if nmax > gov_nmax:
                    gov_nmax, gov_i = nmax, i + 1
        util_max = (gov_nmax / Po) if (Po > 0 and gov_nmax > -1e17) else 0.0

        # R3 (3d ≤ k/c ≤ 6d): dùng NGUỒN DUY NHẤT rigid_cap.spacing_values để KHỚP
        # với lõi (mechanics/nsga2) và báo cáo. Kiểu B (hoa mai) xét ĐƯỜNG CHÉO
        # √((sx/2)²+sy²) — min_spacing bỏ sót cận TRÊN. Cận dưới = effective_min_spacing
        # (max(3d, d+thông thủy)) đồng nhất với báo cáo.
        s_min_req = effective_min_spacing(params)
        s_max_req = 6 * d
        spac = rigid_cap.spacing_values(cfg.get('type'), cfg.get('nx', 0), cfg.get('ny', 0),
                                        cfg.get('sx', 0), cfg.get('sy', 0), coords)
        r3_ok = True
        for _nm, _v, _chk_up in spac:
            if _v < s_min_req - 1e-3:
                r3_ok = False
            if _chk_up and _v > s_max_req + 1e-3:
                r3_ok = False
        s_show = ", ".join(f"{nm}={v:.2f}" for nm, v, _ in spac) or "—"

        # R4 (tim cọc → mép ≥ d) — thuần hình học, không đổi theo tổ hợp
        max_x = float(np.max(np.abs(coords[:, 0]))) if len(coords) else 0.0
        max_y = float(np.max(np.abs(coords[:, 1]))) if len(coords) else 0.0
        Lx = params.get('L_X', 0) or 0
        Ly = params.get('L_Y', 0) or 0
        r4x = (max_x + c_min) / (Lx / 2) if Lx else 0.0
        r4y = (max_y + c_min) / (Ly / 2) if Ly else 0.0
        r4_ok = (r4x <= 1 + 1e-3) and (r4y <= 1 + 1e-3) if (Lx and Ly) else True

        mxmax = cfg.get('mxmax', 0) or 0
        mymax = cfg.get('mymax', 0) or 0
        m_ok = (max(mxmax, mymax) <= Mlim) if Mlim > 0 else True

        # Dòng tổng hợp hình học + uốn (mirror Mục 6 báo cáo)
        geom_summary = [
            f"R3 k/c: {s_show} m ∈ [{s_min_req:.2f}, {s_max_req:.2f}] "
            + ('✓' if r3_ok else '✗'),
            f"R4 tim→mép: {max(r4x, r4y) * 100:.0f}% " + ('✓' if r4_ok else '✗'),
            (f"R5/R6 uốn M: max({mxmax:.1f}, {mymax:.1f}) ≤ {Mlim:.1f} T·m "
             + ('✓' if m_ok else '✗')) if Mlim > 0 else "R5/R6 uốn M: không kiểm ([M]=0)",
        ]

        all_ok = bool(rows) and all(r['ok'] for r in rows) and r3_ok and r4_ok and m_ok

        # R7 (lực ngang) & R8 (tương tác P–M) — LUÔN trình bày khung R1–R8.
        # R7 cần [H] (chỉ có ở luồng MỞ RỘNG) → luồng chuẩn hiện "không kiểm".
        # R8 (P–M) tính được ở mọi luồng khi đã khai báo [M] và [Po].
        Hlim = (getattr(self.app, '_ext_hlimit', 0.0) or 0.0) if getattr(self.app, '_ext_active', False) else 0.0
        if Hlim > 0:
            hmax = float(rigid_cap.hmax(np.asarray(coords, float), self.app.loads)) \
                if self.app.loads else 0.0
            r7_ok = hmax <= Hlim + 1e-6
            geom_summary.append(
                f"R7 Hmax: {hmax:.1f} ≤ {Hlim:.1f} T " + ('✓' if r7_ok else '✗'))
            all_ok = all_ok and r7_ok
        else:
            geom_summary.append("R7 lực ngang: không kiểm ([H]=0)")
        if Mlim > 0 and Po > 0:
            it = gov_nmax / Po + max(mxmax, mymax) / Mlim
            r8_ok = it <= 1.0 + 1e-6
            geom_summary.append(
                f"R8 P–M: {it:.2f} ≤ 1.0 " + ('✓' if r8_ok else '✗'))
            all_ok = all_ok and r8_ok
        else:
            geom_summary.append("R8 P–M: không kiểm ([M]=0)")

        return {
            'n_piles': len(coords), 'rows': rows, 'governing': gov_i,
            'util_max': util_max, 'status': 'ĐẠT' if all_ok else 'KHÔNG ĐẠT',
            'geom_summary': geom_summary, 'Po': Po, 'Ct': Ct,
            'cons_label': 'R1–R8',
        }
