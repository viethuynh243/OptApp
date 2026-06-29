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
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
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
        """Khởi tạo figure/axes matplotlib và gắn vào widget Tkinter (master).

        Canvas + thanh công cụ (NavigationToolbar2Tk) được bọc trong MỘT Frame
        chung (self.container) để MainWindow chỉ cần pack self.widget như cũ mà
        vẫn có đầy đủ nút phóng to/thu nhỏ/di chuyển/lưu ảnh của matplotlib.
        """
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        # Khung chứa: gói canvas (trên) + thanh công cụ (dưới) thành 1 widget pack được
        self.container = tk.Frame(master)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.container)
        canvas_w = self.canvas.get_tk_widget()
        # Thanh công cụ matplotlib: phóng to / di chuyển / về gốc / lưu ảnh
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.container)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas_w.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # MainWindow pack widget này (khung chứa), không pack riêng canvas nữa
        self.widget = self.container
        self._canvas_w = canvas_w
        # Tự co giãn (auto-scale): nhớ lệnh vẽ gần nhất để VẼ LẠI khi cửa sổ đổi
        # kích thước; cỡ chữ tính theo kích thước figure (_font_scale) nên bảng/
        # nhãn không bị tràn hay đổi bố cục khi người dùng chỉnh layout.
        self._redraw_cb = None
        self._last_size = (0, 0)
        self._resize_after = None
        # Bind <Configure> trên CHÍNH widget canvas (không phải khung chứa) để
        # bắt đúng kích thước vùng vẽ, tránh sai số do thanh công cụ.
        self._canvas_w.bind('<Configure>', self._on_resize)

        # Đọc nhanh khi rê chuột (hover): lưu tọa độ/lực cọc của lần vẽ gần nhất
        self._hover_coords = None
        self._hover_forces = None
        # Tạo 1 chú thích (annotation) ẩn dùng lại cho mọi lần rê chuột
        self._make_hover_annot()
        self._hover_cid = self.canvas.mpl_connect("motion_notify_event", self._on_hover)

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

    def _make_hover_annot(self):
        """Tạo lại chú thích hover trên axes hiện tại (sau khi fig.clf() xóa axes
        cũ thì annotation cũ cũng mất). Mặc định ẩn."""
        self._hover_annot = self.ax.annotate(
            "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
            bbox=dict(boxstyle="round", fc="#ffffe0", ec="#888"), fontsize=8)
        self._hover_annot.set_visible(False)

    def _on_hover(self, event):
        """Rê chuột lên cọc để đọc nhanh số hiệu, tọa độ và lực P.

        Bọc try/except để thao tác chuột KHÔNG BAO GIỜ làm sập UI. Tìm cọc gần
        con trỏ nhất; nếu trong ngưỡng ~0.6 m thì hiện chú thích, ngoài thì ẩn.
        """
        try:
            coords = self._hover_coords
            if (event.inaxes != self.ax or coords is None or len(coords) == 0
                    or event.xdata is None or event.ydata is None):
                if self._hover_annot.get_visible():
                    self._hover_annot.set_visible(False)
                    self.canvas.draw_idle()
                return
            # Khoảng cách từ con trỏ tới từng cọc → chọn cọc gần nhất
            dx = coords[:, 0] - event.xdata
            dy = coords[:, 1] - event.ydata
            dist = np.hypot(dx, dy)
            i = int(np.argmin(dist))
            if dist[i] <= 0.6:
                x, y = float(coords[i, 0]), float(coords[i, 1])
                text = f"Cọc {i + 1}\n({x:.2f}, {y:.2f}) m"
                forces = self._hover_forces
                if forces is not None and i < len(forces):
                    text += f"\nP={float(forces[i]):.1f} T"
                self._hover_annot.xy = (x, y)
                self._hover_annot.set_text(text)
                self._hover_annot.set_visible(True)
                self.canvas.draw_idle()
            elif self._hover_annot.get_visible():
                self._hover_annot.set_visible(False)
                self.canvas.draw_idle()
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
        self._hover_coords = None
        self._hover_forces = None
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self._make_hover_annot()
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

        # Trục đối xứng qua GỐC TỌA ĐỘ (mảnh) + dấu "+" đánh dấu gốc (0,0)
        self.ax.axhline(0, color='#9aa6b2', lw=0.6, ls=(0, (4, 3)), zorder=1.5)
        self.ax.axvline(0, color='#9aa6b2', lw=0.6, ls=(0, (4, 3)), zorder=1.5)
        m = max(L_X, L_Y) * 0.05
        self.ax.plot([-m, m], [0, 0], color='#34495e', lw=1.0, zorder=6)
        self.ax.plot([0, 0], [-m, m], color='#34495e', lw=1.0, zorder=6)
        self.ax.plot(0, 0, marker='o', ms=2.5, color='#34495e', zorder=6)
        self.ax.annotate('O(0,0)', (0, 0), textcoords='offset points', xytext=(4, 4),
                         fontsize=7, color='#34495e', zorder=6)

    def _finalize(self, L_X, L_Y, title=None, has_colorbar=False, view_extent=None):
        """Thiết lập trục, lưới, tiêu đề, chú thích chung và vẽ lại canvas.

        view_extent = (hx, hy): nửa bề rộng/cao KHUNG NHÌN CHUNG (đối xứng quanh
        tâm) dùng cho MỌI phương án -> cùng tỉ lệ pixel/mét khi chuyển phương án,
        cọc giữ nguyên cỡ, dễ so sánh tiến hóa. None -> khung theo bệ hiện tại.
        """
        if view_extent is not None:
            hx, hy = view_extent
            self.ax.set_xlim(-hx, hx)
            self.ax.set_ylim(-hy, hy)
        else:
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
    def draw_simulation(self, coords, params, forces=None, m_forces=None, view_extent=None):
        """Vẽ mặt bằng bố trí cọc; tô màu theo lực P nếu có nội lực kèm theo.

        view_extent: khung nhìn chung (hx, hy) để mọi phương án cùng tỉ lệ — xem
        _finalize. None -> khung theo bệ phương án hiện tại.
        """
        # Ghi nhớ để VẼ LẠI khi cửa sổ đổi kích thước (auto-scale)
        self._redraw_cb = lambda: self.draw_simulation(coords, params, forces, m_forces, view_extent)
        # Xóa nội dung cũ, tạo lại axes sạch cho lần vẽ mới
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self._make_hover_annot()
        # Lưu tọa độ/lực để đọc nhanh khi rê chuột (hover)
        if coords is None or len(coords) == 0:
            self._hover_coords = None
            self._hover_forces = None
        else:
            self._hover_coords = np.asarray(coords, dtype=float)
            self._hover_forces = forces

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
            self._finalize(L_X, L_Y, view_extent=view_extent)
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
            self._finalize(L_X, L_Y, title=f"Bố trí {n_piles} cọc", view_extent=view_extent)
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
        self._finalize(L_X, L_Y, title=title, has_colorbar=True, view_extent=view_extent)

    # ========================================================================
    # Vẽ MÔ HÌNH 3D: đài + cọc + lớp đất + móng khối quy ước (xem tổng thể)
    # ========================================================================
    @staticmethod
    def _box_faces(x0, x1, y0, y1, z0, z1):
        """6 mặt tứ giác của một hộp chữ nhật trục (cho Poly3DCollection)."""
        p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        return [[p[0], p[1], p[2], p[3]], [p[4], p[5], p[6], p[7]],
                [p[0], p[1], p[5], p[4]], [p[2], p[3], p[7], p[6]],
                [p[1], p[2], p[6], p[5]], [p[0], p[3], p[7], p[4]]]

    def draw_model_3d(self, coords, params, forces=None, m_forces=None):
        """Dựng mô hình 3D để "thấy toàn bộ tổng thể": đài bệ (khối trên), các cọc
        (cột đứng tô màu theo lực P), lớp đất (nếu có soil_below) và móng khối quy
        ước theo TCVN (nếu đủ pile_length + phi_tb).

        Toàn bộ bằng matplotlib 3D (mpl_toolkits.mplot3d) — KHÔNG thêm thư viện
        mới, nhúng thẳng vào canvas Tkinter hiện có. Kéo chuột để xoay mô hình.
        """
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        # Ghi nhớ để VẼ LẠI khi cửa sổ đổi kích thước (auto-scale)
        self._redraw_cb = lambda: self.draw_model_3d(coords, params, forces, m_forces)
        # 3D không hỗ trợ hover annotation 2D → tắt đọc nhanh khi rê chuột
        self._hover_coords = None
        self._hover_forces = None

        self.fig.clf()
        ax = self.ax = self.fig.add_subplot(111, projection='3d')

        # ── Đọc kích thước; thiếu chiều dài/độ sâu thì dùng giá trị MINH HOẠ ──
        L_X = float(params.get('L_X', 6.0))
        L_Y = float(params.get('L_Y', 9.0))
        d = float(params.get('D_PILE', 1.0))
        P_LIMIT = float(params.get('P_LIMIT', 500.0))
        P_TENSION = float(params.get('P_TENSION', 0.0) or 0.0)
        cap_h = float(params.get('cap_thickness') or params.get('CAP_H') or 1.5)
        col_b = float(params.get('col_b') or 0.0)
        col_h = float(params.get('col_h') or 0.0)
        Lc = float(params.get('pile_length') or params.get('PILE_LENGTH') or 0.0)
        lc_illustrative = Lc <= 0
        if lc_illustrative:
            Lc = max(8.0, 2.5 * max(L_X, L_Y))   # chỉ để vẽ, ghi rõ "minh hoạ"

        z_cap_top = 0.0
        z_cap_bot = -cap_h
        z_tip = z_cap_bot - Lc
        has_col = col_b > 0 and col_h > 0
        col_top = z_cap_top + (max(2.5, 0.7 * max(col_b, col_h)) if has_col else 0.0)
        z_view_top = max(z_cap_top + 0.5, col_top + 0.5)

        if coords is None:
            coords_arr = np.empty((0, 2))
        else:
            coords_arr = np.array(coords, dtype=float)
        n_piles = len(coords_arr)

        # ── Nền đất (khối liên tục, nhiều lớp — sát thực tế hơn) ────────────
        ext = max(L_X, L_Y) * 0.6 + d
        # (a) Mặt đất ngang đỉnh đài
        ax.add_collection3d(Poly3DCollection(
            [[(-ext, -ext, z_cap_top), (ext, -ext, z_cap_top),
              (ext, ext, z_cap_top), (-ext, ext, z_cap_top)]],
            facecolor='#cdbd92', edgecolor='#8a7440', alpha=0.18, linewidths=0.5))
        # (b) Dải đất QUANH CỌC (đáy đài → mũi) — vùng kháng ngang (pp "m")
        ax.add_collection3d(Poly3DCollection(
            self._box_faces(-ext, ext, -ext, ext, z_cap_bot, z_tip),
            facecolor='#dcc89a', edgecolor='#b9a06a', alpha=0.13, linewidths=0.4))
        ax.text(ext * 0.98, -ext, (z_cap_bot + z_tip) / 2,
                "đất quanh cọc\n(kháng ngang – pp m)", fontsize=6.5,
                color='#6b5a2a', ha='left', va='center')
        # (c) Các lớp đất DƯỚI MŨI cọc (soil_below) — vùng tính lún, ghi E
        layers = params.get('soil_below') or params.get('SOIL_BELOW')
        soil_palette = ['#cdb892', '#bda572', '#a89968', '#8d7e54']
        if layers:
            z = z_tip
            for i, lay in enumerate(layers):
                h = float(lay.get('h') or lay.get('thickness') or lay.get('H') or 2.0)
                E = lay.get('E')
                z_top, z_bot = z, z - h
                ax.add_collection3d(Poly3DCollection(
                    self._box_faces(-ext, ext, -ext, ext, z_top, z_bot),
                    facecolor=soil_palette[i % len(soil_palette)], edgecolor='#7a6a45',
                    alpha=0.30, linewidths=0.5))
                lbl = f"lớp {i + 1}" + (f"  E={float(E):.0f}" if E else "")
                ax.text(-ext, ext * 0.98, (z_top + z_bot) / 2, lbl, fontsize=6.5,
                        color='#5a4a25', ha='right', va='center')
                z = z_bot

        # ── Móng khối quy ước theo TCVN (khung dây mờ) nếu tính được ─────────
        block = None
        try:
            from core.tcvn import equivalent_block
            block = equivalent_block(coords_arr, params)
            if not block.get('evaluated'):
                block = None
        except Exception:
            block = None
        if block:
            bx, by = block['B_qu'] / 2.0, block['L_qu'] / 2.0
            faces = self._box_faces(-bx, bx, -by, by, z_cap_bot, z_tip)
            pc = Poly3DCollection(faces, facecolor='#3498db', edgecolor='#1f6dad',
                                  alpha=0.06, linewidths=1.0, linestyle='--')
            ax.add_collection3d(pc)

        # ── Đài bệ (khối xám mờ phía trên) ──────────────────────────────────
        cap_faces = self._box_faces(-L_X / 2, L_X / 2, -L_Y / 2, L_Y / 2,
                                    z_cap_top, z_cap_bot)
        ax.add_collection3d(Poly3DCollection(
            cap_faces, facecolor='#bfc4c9', edgecolor='#5b5f63',
            alpha=0.45, linewidths=1.0))
        # ── Cột/trụ trên đỉnh đài (bê tông đặc) ─────────────────────────────
        if has_col:
            ax.add_collection3d(Poly3DCollection(
                self._box_faces(-col_b / 2, col_b / 2, -col_h / 2, col_h / 2,
                                z_cap_top, col_top),
                facecolor='#9aa0a6', edgecolor='#3d4145', alpha=0.75, linewidths=1.0))
            ax.text(0, 0, col_top + 0.3, f"trụ {col_b:g}×{col_h:g}m", fontsize=7,
                    color='#3d4145', ha='center', va='bottom', fontweight='bold')

        # ── Cọc: cột tròn tô màu theo lực (cùng thang màu với mặt bằng 2D) ──
        has_forces = (forces is not None and len(forces) == n_piles and n_piles > 0)
        norm = None
        n_over = n_pull = 0
        if has_forces:
            fa = np.array(forces, dtype=float)
            vmax = max(float(np.max(fa)), P_LIMIT)
            norm = mcolors.Normalize(vmin=0, vmax=vmax)

        theta = np.linspace(0, 2 * np.pi, 16)
        zc = np.array([z_cap_bot, z_tip])
        T, Z = np.meshgrid(theta, zc)
        r = d / 2.0
        for i, (x, y) in enumerate(coords_arr):
            if has_forces:
                p = float(forces[i])
                is_pull = P_TENSION > 0 and p < -P_TENSION
                if is_pull:
                    col = _COLOR_UPLIFT; n_pull += 1
                elif p < 0:
                    col = _COLOR_TENSION
                else:
                    col = _PILE_CMAP(norm(p))
                if p > P_LIMIT + 1e-4:
                    n_over += 1
            else:
                col = '#4caf50'
            Xs = x + r * np.cos(T)
            Ys = y + r * np.sin(T)
            ax.plot_surface(Xs, Ys, Z, color=col, alpha=0.95,
                            linewidth=0, shade=True, zorder=3)
            # Nắp tròn ở đầu cọc (mặt trên) cho gọn
            ax.text(x, y, z_cap_bot + 0.01, str(i + 1), color='black',
                    fontsize=7, ha='center', va='bottom', zorder=5)

        # ── Thang màu lực (đặt cách xa trục z để KHÔNG đè nhãn "Cao độ z") ──
        if has_forces:
            sm = ScalarMappable(cmap=_PILE_CMAP, norm=norm)
            sm.set_array([])
            cbar = self.fig.colorbar(sm, ax=ax, orientation='vertical',
                                     fraction=0.026, pad=0.10, shrink=0.7)
            cbar.set_label(f'Lực cọc P (T) — [Po]={P_LIMIT:.0f} T', fontsize=7.5)
            cbar.ax.tick_params(labelsize=7)

        # ── Dấu "+" GỐC TỌA ĐỘ trên mặt đất + trục tâm thẳng đứng (mảnh) ────
        mm = ext * 0.12
        ax.plot([-mm, mm], [0, 0], [z_cap_top, z_cap_top], color='#2c3e50', lw=1.3, zorder=10)
        ax.plot([0, 0], [-mm, mm], [z_cap_top, z_cap_top], color='#2c3e50', lw=1.3, zorder=10)
        ax.plot([0, 0], [0, 0], [z_view_top, z_tip], color='#9aa6b2', lw=0.6,
                ls=(0, (4, 3)), zorder=1)

        # ── Trục, tỉ lệ, tiêu đề ────────────────────────────────────────────
        ax.set_xlabel('X (m)', fontsize=8, labelpad=2)
        ax.set_ylabel('Y (m)', fontsize=8, labelpad=2)
        ax.set_zlabel('Cao độ z (m)', fontsize=8, labelpad=6)
        ax.tick_params(labelsize=7)
        ax.set_xlim(-ext, ext)
        ax.set_ylim(-ext, ext)
        ax.set_zlim(z_tip, z_view_top)
        try:
            ax.set_box_aspect((2 * ext, 2 * ext, (z_view_top - z_tip)), zoom=0.84)
        except TypeError:
            ax.set_box_aspect((2 * ext, 2 * ext, (z_view_top - z_tip)))
        except Exception:
            pass
        ax.view_init(elev=20, azim=-58)

        title = f"Mô hình 3D — {n_piles} cọc"
        if has_forces:
            pmax = float(np.max(forces)); pmin = float(np.min(forces))
            ok = (n_over == 0 and n_pull == 0)
            title += f"  |  Pmax={pmax:.1f}T / Pmin={pmin:.1f}T  |  {'ĐẠT' if ok else 'KHÔNG ĐẠT'}"
        notes = []
        if lc_illustrative:
            notes.append(f"Lc={Lc:.1f}m (minh hoạ)")
        if block:
            notes.append(f"Khối quy ước {block['B_qu']:.1f}×{block['L_qu']:.1f}m")
        notes.append("kéo chuột để xoay")
        title += "\n" + "  ·  ".join(notes)
        ax.set_title(title, fontsize=9, fontweight='bold', pad=2)

        # subplots_adjust (KHÔNG tight_layout — 3D + colorbar dễ bị cắt hình)
        self.fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.02)
        self.canvas.draw_idle()

    # ========================================================================
    # Vẽ KẾT QUẢ SSI: chuyển vị + mômen dọc thân cọc (ngang) + tóm tắt dọc trục
    # ========================================================================
    def draw_ssi_view(self, coords, params, load, loads=None):
        """Vẽ kết quả tương tác đất–cọc (core/ssi_engine) cho 1 tổ hợp tải:
          - Trái: chuyển vị ngang theo độ sâu (mm).
          - Phải: mômen uốn thân cọc theo độ sâu (T·m).
          - Tiêu đề: Pmax/Pmin dọc trục, lún bệ + LÚN móng khối quy ước (TCVN 10304
            Đ.7.4 — khi có số liệu trụ địa chất), cọc chịu ngang lớn nhất.

        Engine thuần Tấn–m; tự dùng EI=Eb·Jo & hệ số nền m của file (pp "m" TCVN
        10304 PL A). Cọc đứng: giả thiết tách dọc trục ⊥ ngang (thiết kế sơ bộ).
        `loads` (mọi tổ hợp) dùng để tính lún theo N lớn nhất; thiếu thì dùng [load].
        """
        from core import ssi_engine as ssi
        self._redraw_cb = lambda: self.draw_ssi_view(coords, params, load, loads)
        self._hover_coords = None
        self._hover_forces = None
        self.fig.clf()
        self._make_hover_annot()

        coords_arr = None if coords is None else np.asarray(coords, dtype=float)
        if coords_arr is None or len(coords_arr) == 0 or not load:
            ax = self.ax = self.fig.add_subplot(111)
            ax.axis('off')
            ax.text(0.5, 0.5, "Chưa có phương án/tổ hợp tải để phân tích SSI.\n"
                              "Hãy chạy tối ưu rồi chọn tổ hợp tải.",
                    ha='center', va='center', fontsize=11, color='gray')
            self.canvas.draw_idle()
            return

        # Engine làm việc THUẦN Tấn–m → truyền thẳng tải (Tấn); kết quả: lực Tấn,
        # chuyển vị m (×1000 ra mm), mômen T·m. Tự dùng EI=Eb·Jo & hệ số nền m của file.
        res = ssi.analyze(coords_arr, params, load)
        axl = res['axial']; lat = res['lateral']; meta = res['meta']

        f_t = axl['forces']
        pmax, pmin = float(np.max(f_t)), float(np.min(f_t))
        settle_mm = axl['settle_cap'] * 1000.0

        gs = self.fig.add_gridspec(1, 2, wspace=0.32)
        ax1 = self.ax = self.fig.add_subplot(gs[0, 0])
        ax2 = self.fig.add_subplot(gs[0, 1])

        if lat is not None:
            prof = lat['profile']
            z = -prof['s']
            ax1.plot(prof['w'] * 1000.0, z, '-o', color='#2980b9', ms=2.5, lw=1.5)
            ax1.axvline(0, color='#aaa', lw=0.8)
            ax1.set_xlabel('Chuyển vị ngang (mm)')
            ax1.set_ylabel('Độ sâu z (m)')
            ax1.set_title('Chuyển vị thân cọc', fontsize=9, fontweight='bold')
            ax1.grid(True, ls=':', alpha=0.5)

            ax2.plot(prof['M'], z, '-o', color='#c0392b', ms=2.5, lw=1.5)
            ax2.axvline(0, color='#aaa', lw=0.8)
            ax2.set_xlabel('Mômen uốn (T·m)')
            ax2.set_title('Mômen thân cọc', fontsize=9, fontweight='bold')
            ax2.grid(True, ls=':', alpha=0.5)

        lc_note = " (Lc minh hoạ)" if meta['Lc_illustrative'] else ""
        sup = (f"Phân tích SSI — dọc trục: Pmax={pmax:.1f}T / Pmin={pmin:.1f}T  ·  "
               f"lún bệ ≈ {settle_mm:.1f} mm")
        if meta.get('group_effect'):
            sup += f"  ·  lún nhóm ≈ {axl['settle_group'] * 1000:.1f} mm (R_s={meta['Rs']:.2f})"
        # Lún MÓNG KHỐI QUY ƯỚC (TCVN 10304 Đ.7.4) khi có số liệu trụ địa chất.
        try:
            from core.tcvn import settlement as _settle
            st = _settle(coords_arr, (loads or [load]), params)
            if st.get('evaluated'):
                blk = st['block']
                sup += (f"\nLún khối quy ước (TCVN 10304 Đ.7.4): khối "
                        f"{blk['B_qu']:.1f}×{blk['L_qu']:.1f}m  ·  S={st['S'] * 1000:.0f} mm")
                if st.get('S_limit'):
                    sup += (f" / Sgh={st['S_limit'] * 1000:.0f} mm  → "
                            f"{'ĐẠT' if st.get('ok') else 'KHÔNG ĐẠT'}")
        except Exception:
            pass
        if lat is not None:
            sup += (f"\nNgang (cọc #{lat['pile_index'] + 1}): H={lat['H_pile']:.1f}T  ·  "
                    f"y_đầu={lat['y_head'] * 1000:.1f} mm  ·  M_max={lat['M_max']:.1f} T·m")
            if meta.get('group_effect') and lat.get('pmult') is not None:
                sup += f"  ·  p-mult={lat['pmult']:.2f}"
                if lat.get('s_over_D'):
                    sup += f" ({lat.get('rows')} hàng @ {lat['s_over_D']:.1f}D)"
            if meta.get('lateral_model') == 'm':
                sup += f"  ·  nền: pp “m” TCVN 10304 (m={meta['m_soil']:.0f} T/m⁴)"
            else:
                sup += f"  ·  nền: ks={meta['ks']:.0f} T/m³"
            sup += f"  ·  Lc={meta['Lc']:.1f}m{lc_note}"
        self.fig.suptitle(sup, fontsize=8.0, fontweight='bold', color='#1a3c5e')

        # subplots_adjust (không tight_layout) — tránh cảnh báo với suptitle + gridspec
        self.fig.subplots_adjust(left=0.09, right=0.97, top=0.82, bottom=0.10, wspace=0.32)
        self.canvas.draw_idle()

    # ========================================================================
    # Vẽ KẾT QUẢ THIẾT KẾ ĐÀI CỌC (TCVN 5574:2018)
    # ========================================================================
    def draw_cap_design_view(self, coords, params, loads):
        """Vẽ bảng kết quả thiết kế kết cấu đài (core/cap_design): vật liệu, cốt
        thép uốn, chọc thủng (cột + cọc), cắt một phương, cờ đài sâu (STM)."""
        from core import cap_design as cap
        TF = cap.TF_TO_KN * cap.KN_TO_N          # N cho 1 Tấn
        NMM_PER_TM = cap.TF_TO_KN * 1e6          # N·mm cho 1 T·m

        self._redraw_cb = lambda: self.draw_cap_design_view(coords, params, loads)
        self._hover_coords = None
        self._hover_forces = None
        fs = self._font_scale()
        self.fig.clf()
        ax = self.ax = self.fig.add_subplot(111)
        self._make_hover_annot()
        ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        self.fig.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.03)

        res = cap.design_cap(coords, params, loads)
        std = res.get('standard', 'TCVN 5574:2018')   # cơ sở thiết kế (11823-5 cầu / 5574)
        if not res.get('ok'):
            miss = "\n".join("  • " + m for m in res.get('missing', []))
            ax.set_title(f"THIẾT KẾ ĐÀI CỌC ({std})", fontsize=11 * fs,
                         fontweight='bold', color='#b03a2e', pad=8)
            ax.text(0.5, 0.6, "Thiếu dữ liệu để thiết kế đài — hãy nhập ở khung "
                              "“Nền & đài cọc”:", ha='center', va='center',
                    fontsize=10 * fs, color='#333')
            ax.text(0.5, 0.45, miss, ha='center', va='top', fontsize=10 * fs, color='#b03a2e')
            self.canvas.draw_idle()
            return

        m = res['mat']; g = res['geom']
        fx, fy = res['flexure']['x'], res['flexure']['y']
        pc, pp = res['punching']['column'], res['punching']['pile']
        sx, sy = res['shear']['x'], res['shear']['y']
        stm = res['stm']
        tcol = 'navy' if res['status'] == 'ĐẠT' else '#b03a2e'
        ax.set_title(f"THIẾT KẾ ĐÀI CỌC ({std})  —  {res['status']}",
                     fontsize=11 * fs, fontweight='bold', color=tcol, pad=8)

        if std.startswith('TCVN 11823'):
            # ── TCVN 11823-5:2017 (LRFD): φ·Rn ─────────────────────────────
            rows = [
                ('— Vật liệu —',
                 f"{m['conc']} (f'c={m['fc']:.0f}, fy={m['fy']:.0f} MPa) · {m['steel']} "
                 f"· β1={m['beta1']:.2f} · φ_uốn={m['phi_f']}, φ_cắt={m['phi_v']}", None),
                ('— Hình học —',
                 f"đài {g['Lx']:.1f}×{g['Ly']:.1f}×H{g['H']:.1f} m · de={g['h0_mm'] / 1000:.2f} m"
                 f" · dv={g['dv_mm'] / 1000:.2f} m · cột {g['col_b']:.1f}×{g['col_h']:.1f} m"
                 f" · N_cột={g['N_col_T']:.0f} T", None),
                ('Uốn phương X',
                 f"Mu={fx['Mu'] / NMM_PER_TM:.0f} T·m → As={fx['As'] / 100:.0f} cm² "
                 f"(min {fx['As_min'] / 100:.0f}) · c/de={fx['c_over_de']:.2f}≤0,42 · "
                 f"φMn={fx['Mr'] / NMM_PER_TM:.0f} T·m", fx['ok']),
                ('Uốn phương Y',
                 f"Mu={fy['Mu'] / NMM_PER_TM:.0f} T·m → As={fy['As'] / 100:.0f} cm² "
                 f"(min {fy['As_min'] / 100:.0f}) · c/de={fy['c_over_de']:.2f}≤0,42 · "
                 f"φMn={fy['Mr'] / NMM_PER_TM:.0f} T·m", fy['ok']),
                ('Chọc thủng cột',
                 f"Vu={pc['Vu'] / TF:.0f} T / φVn={pc['Vr'] / TF:.0f} T · "
                 f"bo={pc['bo'] / 1000:.2f} m · η={pc['ratio']:.2f}"
                 f" ({pc['n_inside']} cọc trong chu vi)", pc['ok']),
                ('Chọc thủng cọc',
                 f"P={pp['Vu'] / TF:.0f} T / φVn={pp['Vr'] / TF:.0f} T · η={pp['ratio']:.2f}"
                 f" (cọc #{pp['pile_index'] + 1})", pp['ok']),
                ('Cắt 1 phương X',
                 f"Vu={sx['Vu'] / TF:.0f} T vs φVn={sx['Vr'] / TF:.0f} T"
                 + ("  → cần cốt đai" if sx['need_stirrups'] else "  → bê tông đủ"), sx['ok']),
                ('Cắt 1 phương Y',
                 f"Vu={sy['Vu'] / TF:.0f} T vs φVn={sy['Vr'] / TF:.0f} T"
                 + ("  → cần cốt đai" if sy['need_stirrups'] else "  → bê tông đủ"), sy['ok']),
                ('Giàn ảo (STM)',
                 (f"ĐÀI SÂU (a/de<1) — nên kiểm bằng STM · " if stm['deep'] else "đài không sâu · ")
                 + f"T={stm['T'] / TF:.0f} T → As_tie={stm['As_tie'] / 100:.0f} cm² · θ={stm['theta_deg']:.0f}°",
                 None if not stm['deep'] else True),
            ]
            note = ("Ghi chú: thiết kế sơ bộ theo TCVN 11823-5:2017 — bê tông cầu, LRFD "
                    "(uốn 5.6.3, cắt 5.7.3, chọc thủng 5.12.8). φ·Rn = sức kháng có hệ số; "
                    "η = Vu/φVn. ⚠️ Hệ số φ là TRỊ THAM KHẢO (AASHTO) — cần kỹ sư nghiệm thu "
                    "với TCVN 11823-5. (TCVN 5574 KHÔNG dùng cho cầu.)")
        else:
            # ── TCVN 5574:2018 (sức chịu tải cho phép) — đường đối chiếu 10304 ─
            rows = [
                ('— Vật liệu —',
                 f"{m['conc']} (Rb={m['Rb']}, Rbt={m['Rbt']} MPa) · {m['steel']} "
                 f"(Rs={m['Rs']:.0f} MPa) · ξ_R={m['xi_R']:.3f}", None),
                ('— Hình học —',
                 f"đài {g['Lx']:.1f}×{g['Ly']:.1f}×H{g['H']:.1f} m · h0={g['h0_mm'] / 1000:.2f} m"
                 f" · cột {g['col_b']:.1f}×{g['col_h']:.1f} m · N_cột={g['N_col_T']:.0f} T", None),
                ('Uốn phương X',
                 f"M={fx['M'] / NMM_PER_TM:.0f} T·m → As={fx['As'] / 100:.0f} cm² "
                 f"(min {fx['As_min'] / 100:.0f}) · ξ={fx['xi']:.3f}≤{fx['xi_R']:.3f}", fx['ok']),
                ('Uốn phương Y',
                 f"M={fy['M'] / NMM_PER_TM:.0f} T·m → As={fy['As'] / 100:.0f} cm² "
                 f"(min {fy['As_min'] / 100:.0f}) · ξ={fy['xi']:.3f}≤{fy['xi_R']:.3f}", fy['ok']),
                ('Chọc thủng cột',
                 f"F={pc['F'] / TF:.0f} T / F_ult={pc['F_ult'] / TF:.0f} T · "
                 f"u_m={pc['u_m'] / 1000:.2f} m · η={pc['ratio']:.2f}"
                 f" ({pc['n_inside']} cọc trong tháp)", pc['ok']),
                ('Chọc thủng cọc',
                 f"P={pp['F'] / TF:.0f} T / F_ult={pp['F_ult'] / TF:.0f} T · η={pp['ratio']:.2f}"
                 f" (cọc #{pp['pile_index'] + 1})", pp['ok']),
                ('Cắt 1 phương X',
                 f"Q={sx['Q'] / TF:.0f} T vs [0.5·Rbt·b·h0]={sx['Q_concrete'] / TF:.0f} T"
                 + ("  → cần cốt đai" if sx['need_stirrups'] else "  → bê tông đủ"), sx['ok']),
                ('Cắt 1 phương Y',
                 f"Q={sy['Q'] / TF:.0f} T vs [0.5·Rbt·b·h0]={sy['Q_concrete'] / TF:.0f} T"
                 + ("  → cần cốt đai" if sy['need_stirrups'] else "  → bê tông đủ"), sy['ok']),
                ('Giàn ảo (STM)',
                 (f"ĐÀI SÂU (a/h0<1) — nên kiểm bằng STM · " if stm['deep'] else "đài không sâu · ")
                 + f"T={stm['T'] / TF:.0f} T → As_tie={stm['As_tie'] / 100:.0f} cm² · θ={stm['theta_deg']:.0f}°",
                 None if not stm['deep'] else True),
            ]
            note = ("Ghi chú: thiết kế sơ bộ theo TCVN 5574:2018 (uốn 8.1.2, cắt 8.1.3, "
                    "chọc thủng 8.1.6). η = tỷ số huy động. Cọc đối xứng, tải đúng tâm → "
                    "bỏ số hạng mô men trong chọc thủng (thiên an toàn).")

        C_PASS, C_FAIL = '#27ae60', '#c0392b'
        y = 0.92
        dy = 0.092
        for label, val, ok in rows:
            header = label.startswith('—')
            ax.text(0.02, y, label, ha='left', va='center',
                    fontsize=(9.5 if header else 9) * fs,
                    fontweight='bold', color='#34495e' if not header else '#7f8c8d')
            ax.text(0.26, y, val, ha='left', va='center', fontsize=8.7 * fs, color='#222')
            if ok is not None:
                badge = "ĐẠT" if ok else "KHÔNG ĐẠT"
                bc = C_PASS if ok else C_FAIL
                ax.text(0.985, y, badge, ha='right', va='center', fontsize=8.5 * fs,
                        fontweight='bold', color='white',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor=bc, edgecolor='none'))
            y -= dy

        ax.text(0.02, y - 0.005, note,
                ha='left', va='top', fontsize=7.3 * fs, color='#888', wrap=True)
        self.canvas.draw_idle()

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
        # Bảng kiểm toán không có cọc để rê chuột → tắt dữ liệu hover
        self._hover_coords = None
        self._hover_forces = None
        fs = self._font_scale()   # hệ số co giãn cỡ chữ theo kích thước figure
        self.fig.clf()
        ax = self.ax = self.fig.add_subplot(111)
        self._make_hover_annot()
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

        # LỀ CỐ ĐỊNH (KHÔNG dùng tight_layout): bảng vẽ bằng tọa độ trục [0,1].
        # tight_layout gọi lặp lại (mỗi lần đổi tổ hợp / resize) làm CO DỒN lề phải
        # tích lũy -> trục co về dải mảnh. Đặt lề tường minh để bảng luôn đầy khung.
        self.fig.subplots_adjust(left=0.03, right=0.99, top=0.93, bottom=0.03)

        if not rows:
            ax.text(0.5, 0.5, "Chưa có dữ liệu tổ hợp tải trọng để kiểm toán.",
                    ha='center', va='center', fontsize=11 * fs, color='gray')
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
        ax.text(0.0, bottom - 0.016,
                "Số trong ô R1/R2 = tỷ lệ huy động (giá trị / giới hạn cho phép).",
                ha='left', va='top', fontsize=7.5 * fs, color='#555')

        # Chú thích màu (legend): ô màu + nhãn trạng thái — đặt thấp hơn để KHÔNG
        # đè dòng ghi chú phía trên (trước đây ô màu chồng lên chữ gây cảm giác sát).
        ly, sw, sh = bottom - 0.092, 0.020, 0.028
        ax.add_patch(patches.Rectangle((0.0, ly), sw, sh, facecolor=C_PASS, edgecolor='none'))
        ax.text(0.028, ly + sh / 2, "ĐẠT (tỷ lệ ≤ 1.0)", ha='left', va='center', fontsize=7.5 * fs, color='#333')
        ax.add_patch(patches.Rectangle((0.30, ly), sw, sh, facecolor=C_FAIL, edgecolor='none'))
        ax.text(0.328, ly + sh / 2, "KHÔNG ĐẠT (vượt giới hạn)", ha='left', va='center', fontsize=7.5 * fs, color='#333')
        ax.add_patch(patches.Rectangle((0.68, ly), sw, sh, fill=False, edgecolor='#c0392b', lw=2.0))
        ax.text(0.708, ly + sh / 2, "tổ hợp chi phối", ha='left', va='center', fontsize=7.5 * fs, color='#333')

        # Tổng hợp hình học R3/R4 + uốn R5/R6 + R7/R8 (không đổi theo tổ hợp).
        # GÓI XUỐNG DÒNG theo bề rộng để KHÔNG bị cắt ngang khi đủ R3–R8 (≤~66 ký tự/dòng).
        items = [s for s in data.get('geom_summary', []) if s]
        gs_lines, cur = [], ""
        for it in items:
            cand = it if not cur else cur + "   |   " + it
            if cur and len(cand) > 66:
                gs_lines.append(cur)
                cur = it
            else:
                cur = cand
        if cur:
            gs_lines.append(cur)
        ax.text(0.0, bottom - 0.135, "\n".join(gs_lines),
                ha='left', va='top', fontsize=7.5 * fs, color='#222',
                fontweight='bold', linespacing=1.45)

        # KHÔNG tight_layout ở đây (đã đặt lề cố định ở trên) — tránh co dồn tích lũy.
        self.canvas.draw_idle()
