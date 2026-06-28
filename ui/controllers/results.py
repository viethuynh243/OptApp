"""results.py - ResultsView: render kết quả + KPI + combobox.

Tách từ ui/main_window.py (Plan 023, Pha 3d) — giữ NGUYÊN hành vi. Ghi ra
app.txt_result / app.lbl_kpi / app.cb_config / app.cb_load_case.
"""
import tkinter as tk
import numpy as np
from core import rigid_cap
from ui import strings as S


class ResultsView:
    """Trình bày KẾT QUẢ ra ô văn bản + dải KPI + combobox phương án/tổ hợp: luồng thường (NSGA-II), mở rộng (quét đường kính), tinh chỉnh MCOC; gợi ý nới bệ."""

    def __init__(self, app):
        self.app = app

    def _show_nsga2_results(self, results):
        """Hiển thị kết quả NSGA-II + MCOC: chuyển về cấu trúc dùng chung."""
        self.app._ext_active = False   # luồng chuẩn: audit R1–R8 nhưng R7 = "không kiểm" ([H]=0)
        P_LIMIT = self.app._pget('P_LIMIT')
        orig_cfg = None
        oe = results.get('_orig_eval')
        if oe:
            n0, r0 = oe
            # Trạng thái phương án gốc xét ĐẦY ĐỦ (lực + hình học) để KHỚP bảng audit
            # R1–R8, tránh mâu thuẫn "DAT (chỉ lực) vs KHÔNG ĐẠT (R3/R4)".
            orig_cfg = {
                'type': 'Goc', 'nx': 0, 'ny': 0, 'sx': 0, 'sy': 0, 'n': n0,
                'coords': self.app.original_coords,
                'pmax': r0.get('pmax', 0), 'pmin': r0.get('pmin', 0),
                'mxmax': r0.get('mxmax', 0), 'mymax': r0.get('mymax', 0),
                'msg': 'Phuong an goc (MCOC)',
            }
            # Bệ gốc đủ chứa cọc gốc (kể cả khi ô L_X/L_Y bị thu nhỏ hơn) — tránh
            # cọc tràn ra ngoài bệ khi vẽ. Để trống thì update_simulation dùng ô UI.
            pco = np.asarray(self.app.original_coords, float)
            if pco.ndim == 2 and len(pco):
                sd = self.app._pget('D_PILE') or 1.2
                from core.ext.cap_resize import recommend_cap_size
                flx, fly = recommend_cap_size(self.app.original_coords, sd, 0.1)
                orig_cfg['cap_lx'] = max(self.app._pget('L_X') or 0.0, flx)
                orig_cfg['cap_ly'] = max(self.app._pget('L_Y') or 0.0, fly)
            orig_cfg['ok'] = self.app._config_fully_ok(orig_cfg)
        # LUÔN giữ TẤT CẢ phương án chấp nhận được (không chỉ Pareto) để người
        # dùng so sánh "tiến hóa" + tự chọn theo điều kiện. Radio BEST/ALL chỉ
        # chi phối khâu XUẤT FILE (save_file), không cắt danh sách trên màn hình.
        valid = results.get('all_valid_configs', [])
        self.app.current_config = {
            'recommended': results.get('recommended'),
            'original_config': orig_cfg,
            'all_valid_configs': valid,
            'pareto_front': results.get('pareto_front', []),
            'all_candidates': [],
            'best_A': results.get('best_A'), 'best_B': results.get('best_B'),
            'reason': results.get('reason', ''),
        }
        self.app.txt_result.delete(1.0, tk.END)
        self._render_results(self.app.current_config, results.get('n_evals'))
        self._maybe_suggest_cap(self.app.current_config)
        self.populate_comboboxes(self.app.current_config)


    def _maybe_suggest_cap(self, results):
        """Khi KHÔNG có phương án (bệ chật) và người dùng bật 'Đề xuất nới bệ',
        in gợi ý: bệ hiện chứa tối đa bao nhiêu cọc + bệ tối thiểu khả thi.

        TÙY CHỌN, do người dùng kiểm soát — chỉ trình bày số liệu, KHÔNG tự áp
        dụng và KHÔNG đổi thuật toán tối ưu. Dùng mô hình bệ cứng (không gọi MCOC).
        """
        if results.get('recommended'):
            return
        if not getattr(self.app, 'var_suggest_cap', None) or not self.app.var_suggest_cap.get():
            return
        if not self.app.loads:
            return
        try:
            from core.cap_suggest import cap_max_piles, suggest_min_cap
            params = self.app.get_params_dict()
            cm = cap_max_piles(params)
            sug = suggest_min_cap(params, self.app.loads)
        except Exception:
            return
        ins = lambda s="": self.app.txt_result.insert(tk.END, s + "\n")
        ins("")
        ins("-" * 60)
        ins("  GOI Y XU LY BE CHAT (tham khao — chua ap dung)")
        ins("-" * 60)
        if cm['n']:
            ins("  Be hien tai %g x %g m chua TOI DA %d coc (luoi %dx%d @ k/c >= %.2f m)."
                % (params.get('L_X', 0), params.get('L_Y', 0), cm['n'],
                   cm['nx'], cm['ny'], cm['s_min']))
        if sug:
            ins("  De dat o k/c toi thieu, NOI be toi thieu ~ %.1f x %.1f m"
                % (sug['cap_lx'], sug['cap_ly']))
            ins("     (luoi %dx%d = %d coc, Pmax ~ %.0f T <= [Po])."
                % (sug['nx'], sug['ny'], sug['n'], sug['pmax']))
            ins("  Hoac: tang duong kinh coc (luong mo rong), hoac giam k/c toi")
            ins("  thieu neu loai coc cho phep (o 'K/c toi thieu ×d').")
        else:
            ins("  Chua tim duoc be kha thi trong gioi han quet — xem lai [Po]/tai.")


    def _render_results(self, results, n_evals=None):
        """In kết quả ra ô 'Kết quả Đánh giá' theo bố cục gọn, kèm bảng tọa độ."""
        P_LIMIT = self.app._pget('P_LIMIT')
        M_LIMIT = self.app._pget('M_LIMIT')
        P_TENSION = self.app._pget('P_TENSION')
        W = 60
        def ins(s="", tag=None):
            start = self.app.txt_result.index(tk.END)
            self.app.txt_result.insert(tk.END, s + "\n")
            if tag:
                self.app.txt_result.tag_add(tag, start, self.app.txt_result.index(tk.END))
        rec = results.get('recommended')
        orig = results.get('original_config')

        ins("=" * W, "head")
        ins("  PHUONG AN KIEN NGHI", "head")
        ins("=" * W, "head")
        if rec:
            type_str = {'A': 'Truc giao (A)', 'B': 'So le (B)',
                        'Goc': 'Giu nguyen phuong an goc'}.get(rec['type'], rec['type'])
            ins(f"  Kieu        : {type_str}")
            ins(f"  So coc      : {rec['n']} coc"
                + (f"   (luoi {rec['nx']} x {rec['ny']})" if rec.get('nx') else ""))
            if rec.get('sx'):
                ins(f"  Khoang cach : sx = {rec['sx']:.2f} m   sy = {rec['sy']:.2f} m")
            util = f"   ({rec['pmax']/P_LIMIT*100:.1f}% [Po])" if P_LIMIT > 0 else ""
            ins(f"  Pmax        : {rec['pmax']:.2f} T{util}")
            ins(f"  Pmin        : {rec['pmin']:.2f} T")
            if rec.get('cap_lx') and rec.get('cap_ly'):
                ins(f"  Kich thuoc be: {rec['cap_lx']:g} x {rec['cap_ly']:g} m")
            if M_LIMIT > 0:
                ins(f"  Mmax        : {max(rec.get('mxmax',0), rec.get('mymax',0)):.2f} T.m")
            ins(f"  Ly do       : {results.get('reason', '')}")
            ins("")
            ins("  TOA DO DAU COC (m):")
            ins(f"     {'#':>3}  {'X':>9}  {'Y':>9}")
            ins("     " + "-" * 25)
            for i, (x, y) in enumerate(rec['coords']):
                ins(f"     {i+1:>3}  {float(x):>9.3f}  {float(y):>9.3f}")
        else:
            ins("  Khong tim thay phuong an thoa man.", "bad")
            ins(f"  Ly do: {results.get('reason', '')}")
        ins("")

        if orig:
            status = "DAT" if orig['ok'] else "KHONG DAT"
            ins("-" * W, "head")
            ins(f"  PHUONG AN GOC : {status}", "ok" if orig['ok'] else "bad")
            ins("-" * W, "head")
            ins(f"  So coc = {orig['n']}    Pmax = {orig['pmax']:.2f} T   (Po = {P_LIMIT:.0f} T)")
            ins(f"  Pmin = {orig['pmin']:.2f} T")
            if orig.get('cap_lx') and orig.get('cap_ly'):
                ins(f"  Kich thuoc be goc: {orig['cap_lx']:g} x {orig['cap_ly']:g} m")
            ins("")

        show = results.get('all_valid_configs', [])
        ins("-" * W, "head")
        ins(f"  CAC PHUONG AN DAT (MCOC)  -  {len(show)} phuong an", "head")
        ins("-" * W, "head")
        if show:
            # Cột Pmin chỉ hiện khi có kiểm nhổ ([Ct] > 0); cột Mmax khi có [M] > 0.
            show_pmin = P_TENSION > 0
            show_m = M_LIMIT > 0
            header = f"  {'Kieu':<5}{'nx':>3}{'ny':>3}{'n':>5}{'sx':>7}{'sy':>7}{'Pmax':>9}"
            if show_pmin:
                header += f"{'Pmin':>9}"
            if show_m:
                header += f"{'Mmax':>9}"
            ins(header)
            for c in show:
                row = (f"  {c['type']:<5}{c.get('nx',0):>3}{c.get('ny',0):>3}{c['n']:>5}"
                       f"{c.get('sx',0):>7.2f}{c.get('sy',0):>7.2f}{c['pmax']:>9.1f}")
                if show_pmin:
                    row += f"{c.get('pmin',0):>9.1f}"
                if show_m:
                    row += f"{max(c.get('mxmax',0), c.get('mymax',0)):>9.1f}"
                ins(row)
            # Chú thích giới hạn để tiện đối chiếu
            notes = [f"Po={P_LIMIT:.0f} T"]
            if show_pmin:
                notes.append(f"[Ct]={P_TENSION:.0f} T (Pmin >= -[Ct])")
            if show_m:
                notes.append(f"[M]={M_LIMIT:.0f} T.m")
            ins(f"  (Gioi han: {', '.join(notes)})", "muted")
        else:
            ins("  Khong co phuong an nao DAT trong kich thuoc be nay.", "bad")
        if n_evals is not None:
            ins(f"\n  So lan goi MCOC: {n_evals}")


    def _show_ext_results(self, out, cfg):
        """Hiển thị kết quả tối ưu mở rộng + cập nhật UI theo đường kính thắng."""
        ins = lambda s="": self.app.txt_result.insert(tk.END, s + "\n")
        self.app.txt_result.delete(1.0, tk.END)

        per = out.get('per_diameter', [])
        rec = out.get('recommended')
        dwin = out.get('winner_diameter')
        ins("=" * 60)
        ins("  TOI UU MO RONG  —  SO SANH CAC PHUONG AN THEO DUONG KINH")
        ins("=" * 60)
        ins(f"   {'d(m)':>6}{'so coc':>8}{'Pmax(T)':>10}{'chi phi':>10}   trang thai")
        ins("  " + "-" * 56)
        for r in per:
            dia = r['dia']
            is_win = (dwin is not None and abs(dia.d - dwin) < 1e-9)
            mark = "* " if is_win else "  "
            if r['best']:
                ins(f"{mark}{dia.d:>6g}{r['best']['n']:>8}{r['best']['pmax']:>10.1f}"
                    f"{r['cost']:>10.3f}   " + ("THANG" if is_win else "DAT"))
            else:
                ins(f"{mark}{dia.d:>6g}{'-':>8}{'-':>10}{'-':>10}   khong kha thi (R1-R8)")
        ins("  " + "-" * 56)
        ins("  (* = phuong an THANG; cac phuong an khac van duoc luu de so sanh)")
        ins("")

        if not rec:
            ins("  KHONG co duong kinh nao cho phuong an thoa man R1-R8.")
            # Vẫn HIỆN phương án gốc để người dùng so sánh / tự điều chỉnh.
            orig_cfg = out.get('original_config')
            if orig_cfg is not None:
                st = "DAT" if orig_cfg.get('ok') else "KHONG DAT"
                ins("")
                ins("  PHUONG AN GOC (d=%.3g m): %s | %d coc | Pmax=%.1f T"
                    % (orig_cfg.get('d_orig', 0), st, orig_cfg['n'], orig_cfg['pmax']))
            self.app._ext_active = False
            self.app.current_config = {
                'recommended': None, 'original_config': orig_cfg,
                'all_valid_configs': [], 'all_candidates': [],
                'reason': 'Khong co phuong an moi thoa R1-R8.',
            }
            self._render_results(self.app.current_config)
            self._maybe_suggest_cap(self.app.current_config)
            self.populate_comboboxes(self.app.current_config)
            return

        winner = out['winner']
        dia_win = winner['dia']
        cap = out['cap_report']
        ins("-" * 60)
        ins(f"  THANG: d = {dwin:g} m | {rec['n']} coc | Pmax = {rec['pmax']:.1f} T"
            f" | chi phi = {winner['cost']:.3f}")
        ins(f"  Suc chiu: [Po]={dia_win.Po:g}  [Ct]={dia_win.Ct:g}  [M]={dia_win.M:g}"
            f"  [H]={dia_win.H:g} (T, T.m)")
        # Báo cáo đổi kích thước bệ
        act = "da ap dung" if cap['applied'] else "chi de xuat"
        ins(f"  BE: {cap['old_LX']:g} x {cap['old_LY']:g}  ->  "
            f"{cap['new_LX']:g} x {cap['new_LY']:g} m ({act}, "
            f"mep cach tim >= {cap['safe_d']:g}, lam tron {cap['round_to']:g})")
        if cap['saved_area'] > 1e-9:
            ins(f"       Tiet kiem dien tich be: {cap['saved_area']:.2f} m2 ({cap['saved_pct']:.1f}%)")
        ins("")

        # Cập nhật THÔNG SỐ BÀI TOÁN trên UI theo đường kính thắng để bảng audit /
        # mặt bằng phản ánh đúng phương án (d, sức chịu, kích thước bệ mới).
        self.app.params['D_PILE'].set(f"{dwin:g}")
        self.app.params['P_LIMIT'].set(f"{dia_win.Po:g}")
        self.app.params['P_TENSION'].set(f"{dia_win.Ct:g}")
        self.app.params['M_LIMIT'].set(f"{dia_win.M:g}" if dia_win.M > 0 else "")
        if cap['applied']:
            self.app.params['L_X'].set(f"{cap['new_LX']:g}")
            self.app.params['L_Y'].set(f"{cap['new_LY']:g}")

        # Bật cờ audit mở rộng + lưu [H] để bảng R1–R8 hiển thị R7
        self.app._ext_active = True
        self.app._ext_hlimit = dia_win.H
        self.app._last_ext_out = out         # phục vụ xuất báo cáo (mục 3b + R7/R8)
        self.app._last_ext_cfg = cfg

        # LUÔN giữ TẤT CẢ phương án chấp nhận được (không chỉ Pareto) để so sánh
        # "tiến hóa". Phương án GỐC (đường kính gốc) đã được orchestrator chấm.
        res = winner['result']
        # Mỗi phương án thay thế cũng mang bệ RIÊNG của nó (thu vừa khít nếu
        # đang bật resize, ngược lại giữ bệ gốc) để so sánh tiến hóa kích thước.
        from core.ext.cap_resize import recommend_cap_size
        for vc in res.get('all_valid_configs', []):
            if vc.get('cap_lx') and vc.get('cap_ly'):
                continue
            vc_coords = vc.get('coords')
            has_coords = vc_coords is not None and len(np.asarray(vc_coords)) > 0
            if cap['applied'] and has_coords:
                lx, ly = recommend_cap_size(vc_coords, cap['safe_d'], cap['round_to'])
                vc['cap_lx'], vc['cap_ly'] = lx, ly
            else:
                vc['cap_lx'], vc['cap_ly'] = cap['old_LX'], cap['old_LY']
        # 'ok' của phương án gốc do orchestrator chấm theo đường kính/[Po] GỐC
        # (không dùng _config_fully_ok vì params UI đã đổi sang đường kính thắng).
        orig_cfg = out.get('original_config')
        self.app.current_config = {
            'recommended': rec,
            'original_config': orig_cfg,
            'all_valid_configs': res.get('all_valid_configs', []),
            'all_candidates': [],
            'best_A': res.get('best_A'), 'best_B': res.get('best_B'),
            'reason': res.get('reason', ''),
        }
        n_evals = sum(r['result'].get('n_evals', 0) for r in per)
        self._render_results(self.app.current_config, n_evals)
        self.populate_comboboxes(self.app.current_config)


    def _log_refine(self, msg):
        """Ghi log từ thread tinh chỉnh lên ô kết quả (thread-safe)."""
        def _append():
            self.app.txt_result.insert(tk.END, msg + "\n")
            self.app.txt_result.see(tk.END)
        self.app.root.after(0, _append)


    def _show_refine_results(self, results):
        """Chuyển kết quả tinh chỉnh về cấu trúc cũ để tái dùng combobox/canvas."""
        def to_cfg(rec, type_name):
            if rec is None:
                return None
            return {
                'type': type_name, 'nx': 0, 'ny': 0, 'sx': 0, 'sy': 0,
                'n': rec['n'], 'coords': rec['coords'],
                'pmax': rec['pmax'], 'pmin': rec['pmin'],
                'mxmax': rec['mxmax'], 'mymax': rec['mymax'],
                'forces': [], 'ok': rec['ok'],
                'msg': rec['label'] + ("" if rec['ok'] else ": " + "; ".join(rec['errs'])),
            }

        valid_steps = [to_cfg(r, 'TinhChinh') for r in results['history'] if r['ok']]
        self.app.current_config = {
            'original_config': to_cfg(results['original'], 'Goc'),
            'recommended': to_cfg(results['best'], 'TinhChinh'),
            'best_A': None, 'best_B': None,
            'all_valid_configs': valid_steps,
            'all_candidates': [],
            'reason': results['reason'],
        }

        best = results['best']
        ins = lambda s="": self.app.txt_result.insert(tk.END, s + "\n")
        P_LIMIT = self.app._pget('P_LIMIT')
        ins("\n" + "=" * 60)
        ins("  KET LUAN (MCOC)")
        ins("=" * 60)
        if best:
            orig = results['original']
            util = f"   ({best['pmax']/P_LIMIT*100:.1f}% [Po])" if P_LIMIT > 0 else ""
            ins("  Goc    : %d coc, Pmax = %.2f T" % (orig['n'], orig['pmax']))
            ins("  Toi uu : %d coc, Pmax = %.2f T%s, Pmin = %.2f T"
                % (best['n'], best['pmax'], util, best['pmin']))
            ins("  So lan goi MCOC: %d" % results['n_calls'])

            # --- Bảng toạ độ đầu cọc cho phương án tối ưu ---
            ins("")
            ins("  TOA DO DAU COC (m):")
            ins(f"     {'#':>3}  {'X':>9}  {'Y':>9}")
            ins("     " + "-" * 25)
            for i, (x, y) in enumerate(best['coords']):
                ins(f"     {i+1:>3}  {float(x):>9.3f}  {float(y):>9.3f}")
            ins("")
        ins("  %s" % results['reason'])
        self.populate_comboboxes(self.app.current_config)


    def _update_kpi(self, cdata):
        """Cập nhật dải KPI: số cọc (mục tiêu), hệ số sử dụng max, tổ hợp chi phối."""
        gov = cdata['governing']
        txt = (f"Số cọc: {cdata['n_piles']}      |      "
               f"Hệ số sử dụng lớn nhất: {cdata['util_max']:.3f}"
               + (f"  (TH{gov} chi phối)" if gov else "")
               + f"      |      Trạng thái: {cdata['status']}")
        self.app.lbl_kpi.config(text=txt, fg=("#1a3c5e" if cdata['status'] == 'ĐẠT' else "#b03a2e"))


    def populate_comboboxes(self, results):
        """Nạp combobox phương án + tổ hợp tải; mặc định chọn tổ hợp bất lợi nhất
        và phương án đề xuất rồi vẽ mô phỏng."""
        cases = [f"Tổ hợp {i+1}" for i in range(len(self.app.loads))]
        self.app.cb_load_case['values'] = cases
        if cases:
            # Mặc định về TỔ HỢP BẤT LỢI NHẤT (cho Pmax lớn nhất) của phương án đề xuất
            worst = 0
            rec = results.get('recommended')
            if rec and self.app.loads:
                P = rigid_cap.forces_all_loads(np.asarray(rec['coords'], float), self.app.loads)
                if getattr(P, 'size', 0):
                    worst = int(np.argmax(P.max(axis=1)))
            self.app.cb_load_case.current(min(worst, len(cases) - 1))

        config_names = []
        if results.get('original_config'):
            config_names.append(S.CFG_GOC)

        config_names.append(S.CFG_DEXUAT)

        for i in range(len(results.get('all_valid_configs', []))):
            config_names.append(f"{S.CFG_PREFIX}{i+1}")

        self.app.cb_config['values'] = config_names
        if config_names:
            # Ưu tiên hiện Phương án đề xuất; nếu không có, hiện Phương án gốc
            if S.CFG_DEXUAT in config_names and results.get('recommended'):
                self.app.cb_config.set(S.CFG_DEXUAT)
            elif S.CFG_GOC in config_names:
                self.app.cb_config.set(S.CFG_GOC)
            else:
                self.app.cb_config.current(0)

        self.app.update_simulation()
