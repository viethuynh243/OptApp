"""params.py - ParamsController: tham số bài toán + TCVN + DEMO.

Tách từ ui/main_window.py (Plan 023, Pha 3b) — giữ NGUYÊN hành vi. Thao tác trên
state chia sẻ app.params / app.var_* và các widget nhập liệu Tab 1.
"""
import tkinter as tk
import numpy as np
from core import rigid_cap
from ui.widgets.widget_utils import set_state_recursive


class ParamsController:
    """Quản lý THAM SỐ bài toán: gom dict tham số cho core/io, đọc số an toàn, kiểm tra tức thời, panel TCVN (toggle + xem trước), và nạp bộ DEMO đầy đủ."""

    def __init__(self, app):
        self.app = app

    def _load_demo_geotech(self):
        """Điền bộ DEMO ĐẦY ĐỦ để chạy thử ngay (CHỈ điền ô đang TRỐNG, không ghi
        đè giá trị bạn đã nhập): [Po]/[Ct] (hoặc Rc,k nếu bật TCVN) cỡ theo tải file,
        tiết diện cột + mác, và trụ địa chất (φ tb, độ sâu đáy đài, lớp đất dưới mũi).

        Tự chọn theo loại cọc (Lc/d): cọc dài d~1.2 (T1–T6,T22) hay cọc ngắn d~2.0
        (T8–T14 trụ lớn). Người dùng chỉnh lại theo hồ sơ thật của công trình.
        """
        def fill(var, val):
            try:
                if not str(var.get()).strip():
                    var.set(str(val))
            except Exception:
                pass

        def _f(s, dflt):
            try:
                return float(str(s).strip())
            except (ValueError, TypeError):
                return dflt

        d = _f(self.app.params['D_PILE'].get(), 1.2)
        Lc = _f(self.app.var_pile_length.get(), self.app._file_params.get('pile_length') or 20.0)
        big = d >= 1.5

        # [Po] demo phải > Pmax bệ cứng để R1 (nén) đạt; [Ct] > |Pmin| để R2 đạt.
        pmax = pmin = 0.0
        try:
            if getattr(self.app, 'original_coords', None) and self.app.loads:
                pmax, pmin = rigid_cap.pmax_pmin(np.asarray(self.app.original_coords, float), self.app.loads)
        except Exception:
            pass
        po = max(pmax * 1.10, 2200.0 if big else 520.0)
        po = int((po + 9) // 10 * 10)
        ct = max(abs(pmin) * 1.30, po * 0.30)
        ct = int((ct + 9) // 10 * 10)
        if self.app.var_tcvn_enable.get():
            fill(self.app.var_rck, int(po * 1.40))      # Rc,k → Rc,d ≈ [Po] (γ0/γn·Rc,k/γk)
        else:
            fill(self.app.params['P_LIMIT'], po)
        fill(self.app.params['P_TENSION'], ct)

        # Tiết diện cột (hợp lý theo họ trụ) + chiều cao đài H TỰ TĂNG để CHỌC THỦNG
        # đạt (đài cầu thường dày — chỉnh H thực tế hơn là phình cột).
        import math
        cb, ch = (8.0, 16.0) if big else (2.5, 4.0)
        fill(self.app.var_col_b, cb); fill(self.app.var_col_h, ch)
        cb = _f(self.app.var_col_b.get(), cb); ch = _f(self.app.var_col_h.get(), ch)
        cov = _f(self.app.var_cover.get(), 0.12)
        # Rbt tính toán (T/m² ≈ MPa·102) theo mác bê tông đài
        RBT_TM = {'B20': 91.8, 'B25': 107.0, 'B30': 117.3, 'B35': 132.6, 'B40': 142.8}
        rbt = RBT_TM.get(self.app.var_conc_grade.get() or 'B25', 107.0)
        Nmax = max((_f(L.get('N', 0), 0.0) for L in (self.app.loads or [])), default=pmax)
        # Giải h0 từ F_ult = rbt·2(cb+ch+2h0)·h0 ≥ 1.15·Nmax  → 2h0² + (cb+ch)h0 − K ≥ 0
        K = 1.15 * Nmax / (2.0 * rbt) if rbt > 0 else 0.0
        bsum = cb + ch
        h0_req = (-bsum + math.sqrt(bsum * bsum + 8.0 * K)) / 4.0 if K > 0 else 0.5
        H_req = math.ceil((h0_req + cov) * 2.0) / 2.0          # làm tròn lên 0.5 m
        file_H = float(self.app._file_params.get('H_cap') or (4.0 if big else 1.8))
        self.app.var_cap_h.set(str(max(file_H, H_req)))            # ĐẶT để demo chắc chắn đạt

        # Trụ địa chất (để TRỐNG gamma_avg → cộng lún hết lớp, demo lún rõ)
        if Lc >= 16:
            fill(self.app.var_phi_tb, 18); fill(self.app.var_cap_depth, 3.0)
            soil = "7, 4500, 2.00\n10, 8000, 2.05\n12, 12000, 2.05"
        else:
            fill(self.app.var_phi_tb, 22); fill(self.app.var_cap_depth, 4.0)
            soil = "6, 5000, 2.00\n10, 9000, 2.05\n12, 14000, 2.10"
        if not self.app.txt_soil_layers.get('1.0', tk.END).strip():
            self.app.txt_soil_layers.insert('1.0', soil)
        self.app._set_status("Đã nạp DEMO đầy đủ (chỉ ô trống) — bấm ▶ Chạy rồi xem 3D / SSI / Thiết kế đài.")


    def _pget(self, key, default=0.0):
        """Đọc 1 thông số số từ UI; ô trống / sai định dạng -> default."""
        raw = self.app.params[key].get()
        raw = raw.strip() if isinstance(raw, str) else raw
        if raw == '' or raw is None:
            return default
        try:
            return float(raw)
        except (ValueError, TypeError):
            return default


    def get_params_dict(self):
        """Gom toàn bộ thông số từ UI thành dict cho core/io_handlers.

        Tham số số được ép qua _pget; các thuộc tính 'gốc' (toạ độ/lực gốc đọc
        từ file) được đính kèm nếu có. Trả về dict đầy đủ kèm SAFE_D mặc định.
        """
        d = {}
        for k, v in self.app.params.items():
            if k in self.app.NUMERIC_PARAMS:
                d[k] = self._pget(k)
            else:
                d[k] = v.get()
        if hasattr(self.app, 'original_coords') and self.app.original_coords:
            d['original_coords'] = self.app.original_coords
        if hasattr(self.app, 'original_d'): d['original_d'] = self.app.original_d
        if hasattr(self.app, 'original_p'): d['original_p'] = self.app.original_p
        if hasattr(self.app, 'orig_pmax'): d['orig_pmax'] = self.app.orig_pmax
        if hasattr(self.app, 'orig_pmin'): d['orig_pmin'] = self.app.orig_pmin
        if hasattr(self.app, 'orig_mxmax'): d['orig_mxmax'] = self.app.orig_mxmax
        if hasattr(self.app, 'orig_mymax'): d['orig_mymax'] = self.app.orig_mymax
        if hasattr(self.app, 'result_filepath'): d['result_filepath'] = self.app.result_filepath
        d['SAFE_D'] = d.get('D_PILE', 1.2)
        # Hệ số k/c tối thiểu do người dùng chọn (mặc định 3.0 = giữ nguyên TCVN).
        try:
            d['SPACING_MIN_FACTOR'] = float(self.app.var_min_spacing.get())
        except (ValueError, AttributeError):
            d['SPACING_MIN_FACTOR'] = 3.0
        # Thông số nền & đài cho SSI + thiết kế kết cấu đài (ô trống -> engine dùng
        # mặc định/minh hoạ). _fnum: ép số an toàn, trả None nếu trống/sai.
        def _fnum(var):
            try:
                s = (var.get() or '').strip()
                return float(s) if s else None
            except (ValueError, AttributeError):
                return None
        d['pile_length'] = _fnum(self.app.var_pile_length)
        d['ks_soil'] = _fnum(self.app.var_ks_soil) or 1.0e4
        d['group_effect'] = bool(self.app.var_group_effect.get())
        d['cap_thickness'] = _fnum(self.app.var_cap_h)
        d['col_b'] = _fnum(self.app.var_col_b)
        d['col_h'] = _fnum(self.app.var_col_h)
        d['cover'] = _fnum(self.app.var_cover) or 0.10
        d['conc_grade'] = self.app.var_conc_grade.get()
        d['steel_grade'] = self.app.var_steel_grade.get()
        # Trụ địa chất & lún (TCVN 10304 Đ.7.4): scalar + bảng lớp đất dưới mũi cọc.
        d['phi_tb'] = _fnum(self.app.var_phi_tb)
        d['cap_depth'] = _fnum(self.app.var_cap_depth)
        d['gamma_avg'] = _fnum(self.app.var_gamma_avg)
        d['S_LIMIT'] = _fnum(self.app.var_s_limit)
        # Đất dính yếu IL>0,6 dưới mũi -> chặn a≤2d móng khối quy ước (TCVN 10304 Đ.7.4.4)
        d['soft_clay_below'] = bool(self.app.var_soft_clay.get())
        soil_below = []
        if hasattr(self.app, 'txt_soil_layers'):
            for ln in self.app.txt_soil_layers.get('1.0', tk.END).strip().splitlines():
                parts = [x.strip() for x in ln.replace(';', ',').split(',') if x.strip()]
                if len(parts) >= 2:
                    try:
                        lay = {'h': float(parts[0]), 'E': float(parts[1])}
                        if len(parts) >= 3:
                            lay['gamma'] = float(parts[2])
                        soil_below.append(lay)
                    except ValueError:
                        pass
        if soil_below:
            d['soil_below'] = soil_below
        # Hợp nhất đặc trưng từ file MCOC (Eb, m, Jo, Fo, Lc, H đài) — chỉ điền khi
        # UI chưa có giá trị, để engine SSI dùng EI=Eb·Jo và phương pháp "m" của file.
        _key_map = {'E_b': 'E_b', 'm_soil': 'm_soil', 'J_o': 'J_o', 'F_o': 'F_o',
                    'pile_length': 'pile_length', 'H_cap': 'cap_thickness'}
        for _fk, _dk in _key_map.items():
            _v = getattr(self.app, '_file_params', {}).get(_fk)
            if _v is not None and d.get(_dk) is None:
                d[_dk] = _v
        # Nếu người dùng bật panel TCVN trên GUI: nạp Rc,k + hệ số tin cậy vào d
        # để apply_design_capacities() suy ra Rc,d/Rt,d (Điều 7.1.11). Chỉ áp khi
        # Rc,k hợp lệ (>0); ô trống → giữ mặc định của core.
        try:
            if self.app.var_tcvn_enable.get():
                rck = (self.app.var_rck.get() or '').strip()
                rck_val = float(rck) if rck else 0.0
                if rck_val > 0:
                    d['R_C_K'] = rck_val
                    rtk = (self.app.var_rtk.get() or '').strip()
                    if rtk:
                        d['R_T_K'] = float(rtk)
                    g0 = (self.app.var_g0.get() or '').strip()
                    d['GAMMA_0'] = float(g0) if g0 else 1.15
                    gk = (self.app.var_gk.get() or '').strip()
                    d['GAMMA_K'] = float(gk) if gk else 1.40
                    gk_t = (self.app.var_gk_t.get() or '').strip()
                    if gk_t:
                        d['GAMMA_K_T'] = float(gk_t)
                    d['IMPORTANCE_LEVEL'] = self.app.var_imp_level.get()
        except (ValueError, AttributeError):
            pass
        # Chuẩn hóa [Po]/[Ct] -> Rc,d/Rt,d theo TCVN 10304:2014 Điều 7.1.11 nếu
        # người dùng đã khai báo Rc,k + hệ số tin cậy (qua file/CSV/GUI). Idempotent.
        from core import tcvn
        tcvn.apply_design_capacities(d)
        return d


    def _validate_inputs(self, *_args):
        """Kiểm tra tức thời 4 thông số BẮT BUỘC (L_X, L_Y, D_PILE, P_LIMIT).

        Trả về True khi cả 4 đều là số > 0; ngược lại False. Đồng thời:
          - tô đỏ ô không hợp lệ bằng style ttk "Invalid.TEntry" (fieldbackground);
          - cập nhật thanh trạng thái với tóm tắt trường thiếu/sai.
        KHÔNG hiển thị popup và KHÔNG khóa nút Chạy (giữ cổng kiểm tra ở run_optimize).
        """
        required = {'L_X': "Lx", 'L_Y': "Ly", 'D_PILE': "d", 'P_LIMIT': "[Po]"}
        bad = []
        for k, short in required.items():
            raw = self.app.params[k].get().strip()
            ok = False
            if raw != '':
                try:
                    ok = float(raw) > 0
                except ValueError:
                    ok = False
            entry = self.app._param_entries.get(k)
            if entry is not None:
                try:
                    entry.config(style=("TEntry" if ok else "Invalid.TEntry"))
                except Exception:
                    pass
            if not ok:
                bad.append(short)

        if bad:
            self.app._set_status("Thiếu/không hợp lệ: " + ", ".join(bad))
            return False
        self.app._set_status("Thông số hợp lệ.")
        return True


    def _toggle_tcvn(self):
        """Bật/tắt panel TCVN: hiện thân, mờ/sáng các ô con và KHÓA [Po]/[Ct].

        Khi bật tự tính: [Po]/[Ct] do chương trình suy ra nên khóa 2 ô nhập tay
        (state='readonly'); khi tắt thì mở lại ('normal'). Giữ vững khi thiếu key.
        """
        # THU GỌN thân khi tắt (giảm chiều cao cột trái, thấy các khung khác cùng
        # lúc); BẬT lại khi tích chọn. Header + checkbox vẫn luôn hiện.
        on = self.app.var_tcvn_enable.get()
        try:
            if on:
                self.app.frame_tcvn_body.pack(fill=tk.X, pady=(4, 0))
            else:
                self.app.frame_tcvn_body.pack_forget()
        except Exception:
            pass
        set_state_recursive(self.app.frame_tcvn_body, on)
        # Nhãn xem trước nên luôn đọc được (không làm mờ) — bật lại nếu vừa bị mờ.
        try:
            self.app.lbl_tcvn_preview.state(['!disabled'])
        except Exception:
            pass
        # Khóa/mở 2 ô [Po]/[Ct] theo trạng thái bật của panel.
        for key in ('P_LIMIT', 'P_TENSION'):
            e = getattr(self.app, '_param_entries', {}).get(key)
            if e is None:
                continue
            try:
                e.config(state=('readonly' if on else 'normal'))
            except Exception:
                pass


    def _update_tcvn_preview(self, *_args):
        """Cập nhật nhãn xem trước Rc,d (+Rt,d) từ các tham số TCVN đang nhập.

        Null-safe trong lúc dựng UI (nhãn có thể chưa tồn tại). Ô trống/không hợp
        lệ → hiển thị gợi ý nhập Rc,k.
        """
        lbl = getattr(self.app, 'lbl_tcvn_preview', None)
        if lbl is None:
            return
        from core import tcvn

        def _f(var, default=None):
            raw = (var.get() or '').strip()
            if raw == '':
                return default
            try:
                return float(raw)
            except (ValueError, TypeError):
                return default

        rck = _f(self.app.var_rck)
        if not rck or rck <= 0:
            lbl.config(text="→ nhập Rc,k để tính")
            return
        g0 = _f(self.app.var_g0, 1.15)
        gk = _f(self.app.var_gk, 1.40)
        level = (self.app.var_imp_level.get() or 'II').strip().upper()
        gn = tcvn.GAMMA_N_BY_LEVEL.get(level, 1.15)
        po = tcvn.design_axial_capacity(rck, g0, gn, gk)
        text = f"→ Rc,d = {po:.1f} T"
        rtk = _f(self.app.var_rtk)
        if rtk and rtk > 0:
            gk_t = _f(self.app.var_gk_t, gk)
            ct = tcvn.design_axial_capacity(rtk, g0, gn, gk_t)
            text += f"; Rt,d = {ct:.1f} T"
        lbl.config(text=text)
