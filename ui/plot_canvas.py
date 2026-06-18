"""
plot_canvas.py - Vẽ mô phỏng bố trí cọc trên bệ móng bằng matplotlib.

Mục đích: dựng một canvas matplotlib nhúng vào Tkinter (View) để vẽ mặt bằng
bố trí cọc. `draw_simulation` vẽ: bệ móng, viền giới hạn tâm cọc (R4), các cọc
tô màu theo lực (heatmap xanh->vàng->đỏ), nhãn lực P từng cọc và colorbar có
vạch Po.
"""

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
import numpy as np

# Bảng màu nhiệt dùng chung cho cả mặt cọc và thanh màu (colorbar)
# Xanh lá (an toàn) → Vàng (cảnh báo) → Đỏ (vượt tải)
_PILE_CMAP = LinearSegmentedColormap.from_list('pile_heat', ['#00b300', '#ffdd00', '#ff4400'])

# Màu riêng cho cọc chịu kéo
_COLOR_TENSION = '#5dade2'   # Xanh dương nhạt: kéo nhưng còn trong giới hạn
_COLOR_UPLIFT = '#8e44ad'    # Tím: nhổ vượt giới hạn [Ct]


class PlotCanvas:
    # ========================================================================
    # Khởi tạo & vòng đời canvas
    # ========================================================================
    def __init__(self, master):
        """Khởi tạo figure/axes matplotlib và gắn vào widget Tkinter (master)."""
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.widget = self.canvas.get_tk_widget()
        # Tự co giãn (auto-scale): nhớ lệnh vẽ gần nhất để VẼ LẠI khi cửa sổ đổi
        # kích thước; cỡ chữ tính theo kích thước figure (_font_scale) nên bảng/
        # nhãn không bị tràn hay đổi bố cục khi người dùng chỉnh layout.
        self._redraw_cb = None
        self._last_size = (0, 0)
        self._resize_after = None
        self.widget.bind('<Configure>', self._on_resize)

    def _on_resize(self, event):
        """Vẽ lại nội dung hiện tại khi widget đổi kích thước (có debounce).

        Chỉ kích hoạt khi kích thước THỰC SỰ đổi để tránh đệ quy (thao tác vẽ
        cũng phát sinh sự kiện <Configure>)."""
        size = (event.width, event.height)
        if self._redraw_cb is None or (abs(size[0] - self._last_size[0]) < 2
                                       and abs(size[1] - self._last_size[1]) < 2):
            return
        self._last_size = size
        if self._resize_after is not None:
            try:
                self.widget.after_cancel(self._resize_after)
            except Exception:
                pass
        self._resize_after = self.widget.after(120, self._run_redraw)

    def _run_redraw(self):
        """Thực thi lệnh vẽ gần nhất (bọc try để resize không làm sập UI)."""
        self._resize_after = None
        cb = self._redraw_cb
        if cb is not None:
            try:
                cb()
            except Exception:
                pass

    def _font_scale(self):
        """Hệ số co giãn cỡ chữ theo chiều cao figure (px) so với mốc 600px —
        giữ tỉ lệ chữ/ô không đổi khi figure phóng to/thu nhỏ."""
        try:
            h_px = self.fig.get_size_inches()[1] * self.fig.dpi
            return float(np.clip(h_px / 600.0, 0.6, 2.4))
        except Exception:
            return 1.0

    def clear(self):
        """Đưa khung vẽ về trạng thái TRỐNG như lúc mới mở (không vẽ bệ/cọc)."""
        self._redraw_cb = None
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.canvas.draw_idle()

    # ========================================================================
    # Các thành phần nền (bệ móng, trục, chú thích)
    # ========================================================================
    def _draw_base(self, L_X, L_Y, SAFE_D):
        """Vẽ bệ móng và giới hạn tâm cọc (R4). Trả về 2 patch để legend."""
        # Hình chữ nhật bệ móng (canh tâm tại gốc tọa độ)
        rect = patches.Rectangle((-L_X / 2, -L_Y / 2), L_X, L_Y,
                                 linewidth=2, edgecolor='black', facecolor='lightgray',
                                 label='Bệ Móng', zorder=1)
        self.ax.add_patch(rect)

        # Viền giới hạn tâm cọc: thu vào trong bệ một đoạn SAFE_D mỗi cạnh (R4)
        safe_x = max(L_X / 2 - SAFE_D, 0.01)
        safe_y = max(L_Y / 2 - SAFE_D, 0.01)
        safe_rect = patches.Rectangle((-safe_x, -safe_y), 2 * safe_x, 2 * safe_y,
                                      linewidth=1.5, edgecolor='red', linestyle='--',
                                      fill=False, label='Giới hạn tâm cọc', zorder=2)
        self.ax.add_patch(safe_rect)

    def _finalize(self, L_X, L_Y, title=None, has_colorbar=False):
        """Thiết lập trục, lưới, tiêu đề, chú thích chung và vẽ lại canvas."""
        # Giới hạn trục với lề 1 m quanh bệ, giữ tỉ lệ thật (aspect='equal')
        self.ax.set_xlim(-L_X / 2 - 1, L_X / 2 + 1)
        self.ax.set_ylim(-L_Y / 2 - 1, L_Y / 2 + 1)
        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle=':', alpha=0.5)
        self.ax.set_xlabel('Trục X (m)')
        self.ax.set_ylabel('Trục Y (m)')
        if title:
            self.ax.set_title(title, fontsize=10, fontweight='bold', pad=10)
        # Chú thích đặt phía dưới để không đè lên tiêu đề
        self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=2, fontsize=8,
                       frameon=True, fancybox=True)
        if has_colorbar:
            # Có colorbar (xem tương tác): tight_layout xử lý gọn colorbar + tiêu đề dài.
            self.fig.tight_layout()
        else:
            # Không colorbar (xuất hàng loạt): lề CỐ ĐỊNH để mọi hình cùng bố cục,
            # giúp ảnh đồng đều dù tỉ lệ bệ (L_X:L_Y) khác nhau. Dữ liệu giữ
            # aspect='equal' nên được canh giữa trong vùng vẽ cố định.
            self.fig.subplots_adjust(left=0.10, right=0.95, top=0.90, bottom=0.16)
        # Dùng draw_idle() để KHÔNG block UI (tránh đơ)
        self.canvas.draw_idle()

    # ========================================================================
    # Vẽ mô phỏng bố trí cọc
    # ========================================================================
    def draw_simulation(self, coords, params, forces=None, m_forces=None):
        """Vẽ mặt bằng bố trí cọc; tô màu theo lực P nếu có nội lực kèm theo."""
        # Ghi nhớ để VẼ LẠI khi cửa sổ đổi kích thước (auto-scale)
        self._redraw_cb = lambda: self.draw_simulation(coords, params, forces, m_forces)
        # Xóa nội dung cũ, tạo lại axes sạch cho lần vẽ mới
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)

        # Đọc thông số bệ/cọc/giới hạn từ params (có giá trị mặc định)
        L_X = params.get('L_X', 6.0)
        L_Y = params.get('L_Y', 9.0)
        d = params.get('D_PILE', 1.0)
        SAFE_D = params.get('SAFE_D', d)
        P_LIMIT = params.get('P_LIMIT', 500.0)
        P_TENSION = params.get('P_TENSION', 0.0)
        M_LIMIT_raw = params.get('M_LIMIT', 0.0)
        # Không khai báo [M] (<=0) ⇒ coi như vô cực để bỏ qua kiểm momen
        M_LIMIT = float('inf') if (M_LIMIT_raw is None or M_LIMIT_raw <= 0) else M_LIMIT_raw

        # Bước 1: vẽ nền (bệ móng + viền giới hạn tâm cọc)
        self._draw_base(L_X, L_Y, SAFE_D)

        # Không có cọc → chỉ vẽ bệ trống
        if coords is None or len(coords) == 0:
            self._finalize(L_X, L_Y)
            return

        coords_arr = np.array(coords, dtype=float)
        n_piles = len(coords_arr)
        # Chỉ tô màu theo lực khi số phần tử forces khớp số cọc
        has_forces = (forces is not None and len(forces) == n_piles)

        if not has_forces:
            # Chưa có nội lực → vẽ cọc xanh lá đơn giản
            for i, (x, y) in enumerate(coords_arr):
                # Mỗi cọc là một vòng tròn bán kính d/2 kèm số thứ tự
                circle = patches.Circle((x, y), d / 2, edgecolor='#1a6300', facecolor='#4caf50',
                                        alpha=0.85, zorder=3)
                self.ax.add_patch(circle)
                self.ax.text(x, y, str(i + 1), ha='center', va='center',
                             color='white', fontweight='bold', fontsize=10, zorder=4)
            self._finalize(L_X, L_Y, title=f"Bố trí {n_piles} cọc")
            return

        # ── Có nội lực: vẽ heatmap ───────────────────────────────────────────
        forces_arr = np.array(forces, dtype=float)
        # Momen lớn nhất toàn bệ và cờ vượt giới hạn [M]
        max_m = max(m_forces[0], m_forces[1]) if m_forces else 0.0
        is_m_over_global = max_m > M_LIMIT

        # Thang màu chung cho mặt cọc và colorbar (0 → giá trị lớn nhất)
        vmax = max(float(np.max(forces_arr)), P_LIMIT)
        norm = mcolors.Normalize(vmin=0, vmax=vmax)

        n_over = 0   # số cọc vượt nén
        n_pull = 0   # số cọc nhổ vượt giới hạn

        # Bước 2: duyệt từng cọc, chọn màu theo trạng thái lực rồi vẽ
        for i, (x, y) in enumerate(coords_arr):
            p = float(forces_arr[i])

            # Phân loại trạng thái: vượt nén (hoặc vượt momen) / nhổ vượt [Ct]
            is_over = p > (P_LIMIT + 1e-4) or is_m_over_global
            is_pull = P_TENSION > 0 and p < -P_TENSION

            # Màu mặt cọc — khớp với thanh màu bên phải
            if is_pull:
                face_color = _COLOR_UPLIFT
                n_pull += 1
            elif p < 0:
                face_color = _COLOR_TENSION   # kéo nhẹ, còn trong giới hạn
            else:
                face_color = _PILE_CMAP(norm(p))

            if is_m_over_global and not (p > P_LIMIT or is_pull):
                face_color = '#ff6600'   # vi phạm momen nhưng nén bình thường

            if p > (P_LIMIT + 1e-4):
                n_over += 1

            # Viền đỏ & nét dày để nhấn mạnh cọc vi phạm
            edge_color = 'red' if (is_over or is_pull) else 'black'
            lw = 2.5 if (is_over or is_pull) else 1

            circle = patches.Circle((x, y), d / 2, edgecolor=edge_color, facecolor=face_color,
                                    linewidth=lw, alpha=0.9, zorder=3)
            self.ax.add_patch(circle)

            # Nhãn số thứ tự
            self.ax.text(x, y + 0.05, str(i + 1), ha='center', va='center',
                         fontsize=10, color='white', fontweight='bold', zorder=4)

            # Nhãn lực cọc P
            label_p = f"P={p:.1f}T"
            # Màu nhãn P theo trạng thái: đỏ (vượt nén) / tím (nhổ) / xanh navy
            if p > (P_LIMIT + 1e-4):
                p_clr, p_weight = 'red', 'bold'
            elif is_pull:
                p_clr, p_weight = _COLOR_UPLIFT, 'bold'
            else:
                p_clr, p_weight = 'navy', 'normal'
            self.ax.text(x, y - d / 2 - 0.12, label_p, ha='center', va='top',
                         fontsize=7.5, color=p_clr, fontweight=p_weight,
                         bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1), zorder=4)

        # Bước 3: nhãn Mmax toàn bệ (góc dưới phải)
        if m_forces and max_m > 0:
            self.ax.text(0.98, 0.02, f"Max Momen = {max_m:.1f} T.m",
                         transform=self.ax.transAxes, ha='right', va='bottom',
                         fontsize=9, color='red' if is_m_over_global else 'navy',
                         fontweight='bold',
                         bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray'), zorder=5)

        # Bước 4: colorbar dùng chung thang màu với mặt cọc
        sm = ScalarMappable(cmap=_PILE_CMAP, norm=norm)
        sm.set_array([])
        cbar = self.fig.colorbar(sm, ax=self.ax, orientation='vertical', fraction=0.04, pad=0.02)
        # Vạch giới hạn Po trên colorbar (theo tỉ lệ vị trí trong [0, vmax])
        cbar.ax.axhline(y=P_LIMIT / vmax if vmax > 0 else 1.0,
                        color='red', linewidth=2, linestyle='--')
        cbar.set_label(f'Lực cọc P (T)\n── Giới hạn Po={P_LIMIT:.0f} T', fontsize=8)

        # Bước 5: tiêu đề tổng hợp trạng thái
        pmax = float(np.max(forces_arr))
        pmin = float(np.min(forces_arr))
        # ĐẠT khi không có cọc vượt nén, không cọc nhổ và không vượt momen
        is_ok = (n_over == 0 and n_pull == 0 and not is_m_over_global)
        status = "ĐẠT" if is_ok else "KHÔNG ĐẠT"
        title = (f"{n_piles} cọc  |  Pmax={pmax:.1f}T / Pmin={pmin:.1f}T  |  {status}")
        if n_over:
            title += f"  ({n_over} cọc vượt nén)"
        if n_pull:
            title += f"  ({n_pull} cọc nhổ)"

        # Bước 6: hoàn thiện trục/lưới/chú thích và vẽ lại canvas
        self._finalize(L_X, L_Y, title=title, has_colorbar=True)

    # ========================================================================
    # Vẽ bảng kiểm toán ràng buộc (chuẩn tư vấn thiết kế)
    # ========================================================================
    def draw_constraint_view(self, data):
        """Vẽ BẢNG KIỂM TRA ĐIỀU KIỆN R1–R6 theo từng tổ hợp tải trọng.

        Phản chiếu Mục 5–6 của báo cáo kỹ thuật (report_writer) để màn hình và
        bản thuyết minh kể cùng một câu chuyện:
          - Hàng = tổ hợp tải trọng; cột nội lực N_max/N_min và cột R1 (nén),
            R2 (nhổ — chỉ khi khai báo [Ct]).
          - Mỗi ô ràng buộc tô màu theo TỶ LỆ HUY ĐỘNG (giá trị/giới hạn):
            xanh = an toàn → đỏ = sát/vượt 1.0.
          - Tổ hợp CHI PHỐI được tô viền đỏ đậm.
          - Hình học R3/R4 và uốn R5/R6 (không đổi theo tổ hợp) tổng hợp ở dưới.
        `data` lấy từ MainWindow._build_constraint_data.
        """
        # Ghi nhớ để VẼ LẠI khi cửa sổ đổi kích thước (auto-scale)
        self._redraw_cb = lambda: self.draw_constraint_view(data)
        fs = self._font_scale()   # hệ số co giãn cỡ chữ theo kích thước figure
        self.fig.clf()
        ax = self.ax = self.fig.add_subplot(111)
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        rows = data.get('rows', [])
        show_r2 = (data.get('Ct', 0) or 0) > 0

        # Tiêu đề tổng hợp: mục tiêu (số cọc) + hệ số sử dụng + tổ hợp chi phối
        cons_label = data.get('cons_label', 'R1–R6')
        title = (f"BẢNG KIỂM TRA ĐIỀU KIỆN {cons_label}  —  {data['n_piles']} cọc  |  "
                 f"hệ số sử dụng max = {data['util_max']:.3f}"
                 + (f" (TH{data['governing']} chi phối)" if data['governing'] else "")
                 + f"  |  {data['status']}")
        tcol = 'navy' if data['status'] == 'ĐẠT' else '#b03a2e'
        ax.set_title(title, fontsize=9.5 * fs, fontweight='bold', color=tcol, pad=8)

        if not rows:
            ax.text(0.5, 0.5, "Chưa có dữ liệu tổ hợp tải trọng để kiểm toán.",
                    ha='center', va='center', fontsize=11 * fs, color='gray')
            self.fig.tight_layout()
            self.canvas.draw_idle()
            return

        # Cấu trúc cột (R2 chỉ hiện khi có [Ct])
        headers = ['TH', 'N_max (T)', 'N_min (T)', 'R1 nén\nN_max/[Po]']
        if show_r2:
            headers.append('R2 nhổ\n|N_min|/[Ct]')
        ncol = len(headers)
        col_x = np.linspace(0.0, 1.0, ncol + 1)

        # Vùng bảng: chừa chỗ tiêu đề (trên) và phần tổng hợp hình học (dưới)
        top, bottom = 0.97, 0.30
        nrow = len(rows) + 1                      # + dòng tiêu đề
        row_h = (top - bottom) / nrow

        # Màu nhị phân theo TRẠNG THÁI (chuẩn tư vấn): xanh = ĐẠT, đỏ = KHÔNG ĐẠT.
        # Con số tỷ lệ huy động vẫn in trong ô để thấy mức độ; màu chỉ báo đạt/không.
        C_PASS, C_FAIL = '#27ae60', '#c0392b'

        def cell_color(r):
            if r is None:
                return '#e8e8e8'
            return C_FAIL if r > 1.0 + 1e-9 else C_PASS

        # Dòng tiêu đề bảng
        yhdr = top - row_h
        for c in range(ncol):
            ax.add_patch(patches.Rectangle((col_x[c], yhdr), col_x[c + 1] - col_x[c], row_h,
                                           facecolor='#34495e', edgecolor='white', lw=1, zorder=1))
            ax.text((col_x[c] + col_x[c + 1]) / 2, yhdr + row_h / 2, headers[c],
                    ha='center', va='center', color='white', fontsize=7.5 * fs, fontweight='bold', zorder=2)

        # Các dòng tổ hợp
        for ri, rec in enumerate(rows):
            y = top - row_h * (ri + 2)
            is_gov = (rec['th'] == data['governing'])

            vals = [str(rec['th']), f"{rec['nmax']:.1f}", f"{rec['nmin']:.1f}",
                    (f"{rec['r1']:.2f}" if rec['r1'] is not None else '-')]
            ratios = [None, None, None, rec['r1']]
            if show_r2:
                vals.append(f"{rec['r2']:.2f}" if rec['r2'] is not None else '-')
                ratios.append(rec['r2'])

            for c in range(ncol):
                ratio = ratios[c]
                if c >= 3 and ratio is not None:
                    fc = cell_color(ratio)
                    tc = 'white'
                else:
                    fc = '#fbfcfd' if (ri % 2 == 0) else '#eef1f4'
                    tc = 'black'
                ax.add_patch(patches.Rectangle((col_x[c], y), col_x[c + 1] - col_x[c], row_h,
                                               facecolor=fc, edgecolor='#cfd6dd', lw=0.6, zorder=1))
                ax.text((col_x[c] + col_x[c + 1]) / 2, y + row_h / 2, vals[c],
                        ha='center', va='center', color=tc, fontsize=7.5 * fs,
                        fontweight='bold' if (is_gov or c >= 3) else 'normal', zorder=2)

            # Nhấn mạnh tổ hợp chi phối
            if is_gov:
                ax.add_patch(patches.Rectangle((col_x[0], y), 1.0, row_h, fill=False,
                                               edgecolor='#c0392b', lw=2.0, zorder=3))

        # Ghi chú ý nghĩa con số trong ô
        ax.text(0.0, bottom - 0.012,
                "Số trong ô R1/R2 = tỷ lệ huy động (giá trị / giới hạn cho phép).",
                ha='left', va='top', fontsize=7.5 * fs, color='#555')

        # Chú thích màu (legend): ô màu + nhãn trạng thái
        ly, sw, sh = bottom - 0.055, 0.020, 0.030
        ax.add_patch(patches.Rectangle((0.0, ly), sw, sh, facecolor=C_PASS, edgecolor='none'))
        ax.text(0.028, ly + sh / 2, "ĐẠT (tỷ lệ ≤ 1.0)", ha='left', va='center', fontsize=7.5 * fs, color='#333')
        ax.add_patch(patches.Rectangle((0.30, ly), sw, sh, facecolor=C_FAIL, edgecolor='none'))
        ax.text(0.328, ly + sh / 2, "KHÔNG ĐẠT (vượt giới hạn)", ha='left', va='center', fontsize=7.5 * fs, color='#333')
        ax.add_patch(patches.Rectangle((0.68, ly), sw, sh, fill=False, edgecolor='#c0392b', lw=2.0))
        ax.text(0.708, ly + sh / 2, "tổ hợp chi phối", ha='left', va='center', fontsize=7.5 * fs, color='#333')

        # Tổng hợp hình học R3/R4 + uốn R5/R6 (không đổi theo tổ hợp)
        ax.text(0.0, bottom - 0.115, "   |   ".join(data.get('geom_summary', [])),
                ha='left', va='top', fontsize=8 * fs, color='#222', fontweight='bold')

        self.fig.tight_layout()
        self.canvas.draw_idle()
