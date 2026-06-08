import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np

class PlotCanvas:
    def __init__(self, master):
        self.fig, self.ax = plt.subplots(figsize=(6, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.widget = self.canvas.get_tk_widget()
        
    def draw_simulation(self, coords, params, forces=None, m_forces=None):
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        
        L_X = params.get('L_X', 6.0)
        L_Y = params.get('L_Y', 9.0)
        d = params.get('D_PILE', 1.0)
        SAFE_D = params.get('SAFE_D', d)
        P_LIMIT   = params.get('P_LIMIT', 500.0)
        P_TENSION = params.get('P_TENSION', 0.0)
        M_LIMIT_raw = params.get('M_LIMIT', 0.0)
        M_LIMIT = float('inf') if (M_LIMIT_raw is None or M_LIMIT_raw <= 0) else M_LIMIT_raw
        
        # Vẽ bệ móng
        rect = patches.Rectangle((-L_X/2, -L_Y/2), L_X, L_Y,
                                  linewidth=2, edgecolor='black', facecolor='lightgray', label='Bệ Móng')
        self.ax.add_patch(rect)
        
        # Vẽ giới hạn tâm cọc (R4)
        safe_x = max(L_X/2 - SAFE_D, 0.01)
        safe_y = max(L_Y/2 - SAFE_D, 0.01)
        safe_rect = patches.Rectangle((-safe_x, -safe_y), 2*safe_x, 2*safe_y,
                                       linewidth=1.5, edgecolor='red', linestyle='--',
                                       fill=False, label='Giới hạn tâm cọc')
        self.ax.add_patch(safe_rect)
        
        # Đảm bảo coords là numpy array 2D
        if coords is None or len(coords) == 0:
            self.ax.set_xlim(-L_X/2 - 1, L_X/2 + 1)
            self.ax.set_ylim(-L_Y/2 - 1, L_Y/2 + 1)
            self.ax.set_aspect('equal')
            self.ax.grid(True, linestyle=':', alpha=0.6)
            self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=2)
            self.fig.tight_layout()
            self.canvas.draw_idle()
            return
            
        coords_arr = np.array(coords)
        n_piles = len(coords_arr)
        
        has_forces = (forces is not None and len(forces) == n_piles)
        
        if has_forces:
            forces_arr = np.array(forces, dtype=float)
            vmin = min(min(forces_arr), 0)
            vmax = max(max(forces_arr), P_LIMIT)
            norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=P_LIMIT, vmax=max(vmax, P_LIMIT + 1))
            cmap = cm.get_cmap('RdYlGn_r')  # Xanh lá=an toàn, Đỏ=vượt tải
            
            for i, (x, y) in enumerate(coords_arr):
                p = forces_arr[i]
                
                max_m = max(m_forces[0], m_forces[1]) if m_forces else 0
                is_m_over = max_m > M_LIMIT
                is_over = p > (P_LIMIT + 1e-4) or is_m_over
                is_pull = P_TENSION > 0 and p < -P_TENSION
                
                # Màu cọc theo mức tải P
                if is_pull:
                    face_color = 'purple'
                else:
                    t = min(p / P_LIMIT, 1.0)
                    # Xanh lá → vàng → đỏ
                    face_color = (min(2*t, 1.0), max(1 - 2*(t-0.5), 0) if t > 0.5 else 1.0, 0.0)
                
                # Nếu vi phạm M_LIMIT nhưng P bình thường, đổi face_color thành đỏ cam
                if is_m_over and not (p > P_LIMIT or is_pull):
                    face_color = '#ff6600'
                
                edge_color = 'red' if (is_over or is_pull) else 'black'
                lw = 2.5 if (is_over or is_pull) else 1
                
                circle = patches.Circle((x, y), d/2, edgecolor=edge_color, facecolor=face_color,
                                         linewidth=lw, alpha=0.85, zorder=3)
                self.ax.add_patch(circle)
                
                # Nhãn số thứ tự
                txt_clr = 'white'
                self.ax.text(x, y + 0.05, str(i+1), ha='center', va='center',
                              fontsize=10, color=txt_clr, fontweight='bold', zorder=4)
                
                label_p = f"P={p:.1f}T"
                p_clr = 'red' if p > (P_LIMIT + 1e-4) else ('purple' if is_pull else 'navy')
                p_weight = 'bold' if (p > (P_LIMIT + 1e-4) or is_pull) else 'normal'
                
                # Vẽ nhãn P
                self.ax.text(x, y - d/2 - 0.12, label_p, ha='center', va='top',
                              fontsize=7.5, color=p_clr, fontweight=p_weight,
                              bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1), zorder=4)
                              
                # Đã bỏ nhãn M ở từng cọc vì Mmax là giá trị lớn nhất của toàn bệ,
                # không phải của từng cọc cụ thể.
            
            if m_forces and max_m > 0:
                is_m_over_global = max_m > M_LIMIT
                self.ax.text(0.98, 0.02, f"Max Momen = {max_m:.1f} T.m",
                             transform=self.ax.transAxes, ha='right', va='bottom',
                             fontsize=9, color='red' if is_m_over_global else 'navy',
                             fontweight='bold', bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray'), zorder=5)

            # Colorbar (P_LIMIT làm ranh giới)
            from matplotlib.colors import LinearSegmentedColormap
            colors_cmap = ['#00b300', '#ffdd00', '#ff4400']
            custom_cmap = LinearSegmentedColormap.from_list('pile_heat', colors_cmap)
            sm = cm.ScalarMappable(cmap=custom_cmap,
                                    norm=mcolors.Normalize(vmin=0, vmax=max(max(forces_arr), P_LIMIT)))
            sm.set_array([])
            cbar = self.fig.colorbar(sm, ax=self.ax, orientation='vertical', fraction=0.04, pad=0.02)
            cbar.ax.axhline(y=P_LIMIT, color='red', linewidth=2, linestyle='--')
            cbar.set_label(f'Lực cọc P (T)\n── Giới hạn Po={P_LIMIT:.0f} T', fontsize=8)
        else:
            # Chưa có nội lực → vẽ xanh lá đơn giản
            for i, (x, y) in enumerate(coords_arr):
                circle = patches.Circle((x, y), d/2, edgecolor='#1a6300', facecolor='#4caf50',
                                         alpha=0.8, zorder=3)
                self.ax.add_patch(circle)
                self.ax.text(x, y, str(i+1), ha='center', va='center',
                              color='white', fontweight='bold', fontsize=10, zorder=4)
                
        self.ax.set_xlim(-L_X/2 - 1, L_X/2 + 1)
        self.ax.set_ylim(-L_Y/2 - 1, L_Y/2 + 1)
        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle=':', alpha=0.4)
        self.ax.set_xlabel('Trục X (m)')
        self.ax.set_ylabel('Trục Y (m)')
        self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=2, fontsize=8)
        self.fig.tight_layout()
        
        # Dùng draw_idle() để KHÔNG block UI (tránh đơ)
        self.canvas.draw_idle()
