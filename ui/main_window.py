"""
main_window.py - Cửa sổ chính của ứng dụng (Controller trong mô hình MVC).

Đây là lớp giao diện Tkinter / tkinterdnd2 (View + Controller). Nó KHÔNG chứa
logic tính toán: mọi thuật toán nằm ở core/ (rigid_cap, refine_optimizer,
nsga2_optimizer, mechanics, generator, blackbox) và mọi xuất/nhập file nằm ở
io_handlers/ (file_io, mcoc_writer, report_writer, export_utils). File này chỉ
lo dựng giao diện, thu thập dữ liệu người dùng và điều phối các lời gọi đó.

Quản lý 2 tab:
    - Tab 1 (Interactive): nhập thông số/tải trọng, chạy tối ưu, vẽ mô phỏng,
      xuất kết quả; hỗ trợ chế độ "MCOC thực - tinh chỉnh từng bước".
    - Tab 2 (Batch): chạy hàng loạt nhiều file, xuất PDF/Excel/PNG.
"""

import os
import threading
import subprocess
import re as _re
import unicodedata

import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import DND_FILES

from core import rigid_cap
from core.version import WINDOW_TITLE
from core.refine_optimizer import run_refinement, run_pareto_refinement
from core.blackbox import MCOCBlackbox
from core.mechanics import check_layout
from core.generator import generate_coords
from io_handlers.file_io import parse_input_file, export_output_file
from io_handlers.report_writer import export_technical_report, export_technical_report_pdf
from ui.plot_canvas import PlotCanvas


# ============================================================================
# TIỆN ÍCH CẤP MODULE
# ============================================================================
def to_safe_filename(text: str) -> str:
    """
    Chuyển chuỗi tiếng Việt (có dấu) sang tên file an toàn (ASCII, không dấu).
    Ví dụ:
        'Phương án đề xuất' -> 'Phuong_an_de_xuat'
        'Kết quả Tối Ưu' -> 'Ket_qua_Toi_uu'
    """
    # Bước 1: chuẩn hóa Unicode NFD — tách dấu ra khỏi ký tự cơ sở
    nfd = unicodedata.normalize('NFD', text)
    # Bước 2: loại bỏ các combining diacritical marks (category Mn)
    ascii_approx = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    # Bước 3: xử lý riêng đ/Đ (không phải combining, phải xử lý trước)
    ascii_approx = ascii_approx.replace('đ', 'd').replace('Đ', 'D')
    # Bước 4: thay khoảng trắng bằng gạch dưới, xóa ký tự đặc biệt
    safe = _re.sub(r'[^A-Za-z0-9_\-]', '_', ascii_approx)
    # Bước 5: rút gọn nhiều gạch dưới liên tiếp
    safe = _re.sub(r'_+', '_', safe).strip('_')
    return safe


# ============================================================================
# CỬA SỔ CHÍNH (Controller)
# ============================================================================
class MainWindow:
    """Cửa sổ chính: dựng UI 2 tab và điều phối tới core/ + io_handlers/."""

    # ========================================================================
    # KHỞI TẠO & DỰNG GIAO DIỆN
    # ========================================================================
    def __init__(self, root):
        """Khởi tạo cửa sổ: tạo biến trạng thái, dựng UI, đăng ký kéo-thả file."""
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry("1100x750")

        # Biến hệ thống — thông số bài toán để TRỐNG khi mở (người dùng tự nhập
        # hoặc nạp từ file). Dùng StringVar để cho phép ô trống.
        self.NUMERIC_PARAMS = ('L_X', 'L_Y', 'D_PILE', 'P_LIMIT', 'P_TENSION', 'M_LIMIT')
        self.params = {
            'L_X': tk.StringVar(value=''),
            'L_Y': tk.StringVar(value=''),
            'D_PILE': tk.StringVar(value=''),
            'P_LIMIT': tk.StringVar(value=''),
            'P_TENSION': tk.StringVar(value=''),
            'M_LIMIT': tk.StringVar(value=''),  # trống/0 = không kiểm tra (T.m)
            'exe_path': tk.StringVar(value=''),
            'mock_mode': tk.BooleanVar(value=True)
        }
        # Chế độ Hộp đen MCOC thực (tinh chỉnh từng bước)
        self.var_use_real = tk.BooleanVar(value=False)
        self.input_filepath = ''   # file input MCOC gốc (template sinh phương án mới)
        # Cờ xuất file (chỉ dùng trong save_file)
        self.var_export_cti = tk.BooleanVar(value=False)

        self.loads = []
        self.current_config = None

        self.setup_ui()
        self.add_default_loads()

        # Hỗ trợ kéo-thả file vào cửa sổ
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

    def setup_ui(self):
        """Tạo Notebook 2 tab (Tương tác / Hàng loạt) và dựng giao diện từng tab."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_interactive = tk.Frame(self.notebook)
        self.notebook.add(self.tab_interactive, text="1. Tương tác (Interactive)")
        self.setup_interactive_ui(self.tab_interactive)

        self.tab_batch = tk.Frame(self.notebook)
        self.notebook.add(self.tab_batch, text="2. Hàng loạt (Batch Mode)")
        self.setup_batch_ui(self.tab_batch)

    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: DỰNG GIAO DIỆN
    # ========================================================================
    def setup_interactive_ui(self, parent_frame):
        """Dựng toàn bộ giao diện Tab 1: panel trái (nhập liệu/điều khiển) và
        panel phải (mô phỏng mặt bằng cọc)."""
        main_paned = ttk.PanedWindow(parent_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left Panel
        left_frame = tk.Frame(main_paned, width=400)
        main_paned.add(left_frame, weight=0)

        # Tab: Thông số
        tab_params = tk.Frame(left_frame, padx=10, pady=10)
        tab_params.pack(fill=tk.BOTH, expand=True)

        # Buttons IO
        frame_io = tk.Frame(tab_params)
        frame_io.pack(fill=tk.X, pady=5)
        ttk.Button(frame_io, text="Mở file đầu vào  (hoặc kéo-thả)", command=self.load_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(frame_io, text="Làm mới", command=self.clear_loads).pack(side=tk.LEFT, fill=tk.X, expand=False, padx=2)
        ttk.Button(frame_io, text="Xuất kết quả", command=self.save_file).pack(side=tk.RIGHT, fill=tk.X, expand=False, padx=2)

        # Geometrics
        frame_geom = tk.LabelFrame(tab_params, text="Thông số Bài toán", padx=10, pady=5)
        frame_geom.pack(fill=tk.X, pady=5)

        labels_1 = {"L_X": "Rộng bệ Lx (m)", "L_Y": "Dài bệ Ly (m)",
                    "D_PILE": "Đ.kính cọc d (m)", "P_LIMIT": "Sức nén [Po] (T)",
                    "P_TENSION": "Sức nhổ [Ct] (T)", "M_LIMIT": "Sức uốn [M] (T.m)"}
        self._param_entries = {}
        row = 0
        col = 0
        for k, text in labels_1.items():
            ttk.Label(frame_geom, text=text).grid(row=row, column=col*2, sticky="w", padx=2)
            entry = ttk.Entry(frame_geom, textvariable=self.params[k], width=10)
            entry.grid(row=row, column=col*2+1, pady=2, padx=2)
            self._param_entries[k] = entry
            row += 1
            if row > 2:
                row = 0
                col += 1

        # Ghi chú đơn vị — tránh nhầm giữa tải trọng (kN) và sức chịu tải (Tấn)
        ttk.Label(frame_geom,
                  text="Đơn vị (theo MCOC): lực = Tấn (T); momen = T.m. Áp dụng cho cả tải trọng và [Po]/[Ct]/[M].",
                  foreground="#888").grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))

        # Loads
        frame_loads = tk.LabelFrame(tab_params, text="Tổ hợp Tải trọng", padx=10, pady=5)
        frame_loads.pack(fill=tk.BOTH, expand=True, pady=5)

        cols = ("TH", "Hx", "Hy", "P", "Mx", "My", "Mz")
        self.tree_loads = ttk.Treeview(frame_loads, columns=cols, show="headings", height=5)
        col_cfg = {
            "TH":  ("#",      35),
            "Hx":  ("Hx(T)",  60),
            "Hy":  ("Hy(T)",  60),
            "P":   ("P(T)",   65),
            "Mx":  ("Mx(T.m)", 70),
            "My":  ("My(T.m)", 70),
            "Mz":  ("Mz(T.m)", 70),
        }
        for c, (hdr, w) in col_cfg.items():
            self.tree_loads.heading(c, text=hdr)
            self.tree_loads.column(c, width=w, anchor="e")
        self.tree_loads.column("TH", anchor="center")

        # Scrollbar
        sb_loads = ttk.Scrollbar(frame_loads, orient="vertical", command=self.tree_loads.yview)
        self.tree_loads.configure(yscrollcommand=sb_loads.set)
        self.tree_loads.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_loads.pack(side=tk.RIGHT, fill=tk.Y)

        # Double-click để sửa
        self.tree_loads.bind("<Double-1>", lambda e: self.edit_load())

        # Nút CRUD tải trọng
        frame_load_btns = tk.Frame(tab_params)
        frame_load_btns.pack(fill=tk.X, pady=(0, 3))
        ttk.Button(frame_load_btns, text="Thêm tổ hợp",   command=self.add_load_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="Sửa dòng chọn", command=self.edit_load).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="Xóa dòng chọn", command=self.delete_load).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="Dán nhiều dòng (CSV)", command=self.paste_loads_csv).pack(side=tk.RIGHT, padx=2)

        # --- ĐIỀU KHIỂN & KẾT QUẢ TỐI ƯU ---
        frame_run = tk.LabelFrame(tab_params, text="Điều Khiển Tối Ưu", padx=10, pady=5)
        frame_run.pack(fill=tk.X, pady=5)

        self.output_option = tk.StringVar(value="BEST")
        row_out = tk.Frame(frame_run); row_out.pack(fill=tk.X)
        ttk.Radiobutton(row_out, text="Chỉ phương án tối ưu", variable=self.output_option, value="BEST").pack(side=tk.LEFT)
        ttk.Radiobutton(row_out, text="Hiện tất cả phương án", variable=self.output_option, value="ALL").pack(side=tk.LEFT, padx=10)

        # Mục tiêu phụ (sau khi đủ số cọc + đạt Pmax<=Po)
        self.var_secondary = tk.StringVar(value="compact")
        row_sec = tk.Frame(frame_run); row_sec.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(row_sec, text="Ưu tiên:").pack(side=tk.LEFT)
        ttk.Radiobutton(row_sec, text="Tiết kiệm (bệ gọn)", variable=self.var_secondary,
                        value="compact").pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(row_sec, text="An toàn (giảm Pmax)", variable=self.var_secondary,
                        value="pmax").pack(side=tk.LEFT, padx=10)

        # --- Cấu hình MCOC (bắt buộc — mọi phương án được chấm bằng MCOC chính xác) ---
        frame_mcoc = tk.LabelFrame(tab_params, text="Cấu hình MCOC (bắt buộc)", padx=10, pady=5)
        frame_mcoc.pack(fill=tk.X, pady=5)

        row_exe = tk.Frame(frame_mcoc)
        row_exe.pack(fill=tk.X, pady=2)
        ttk.Label(row_exe, text="MCOC Batch:").pack(side=tk.LEFT)
        self.txt_exe_path = ttk.Entry(row_exe, textvariable=self.params['exe_path'])
        self.txt_exe_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(row_exe, text="...", width=3, command=self.browse_exe).pack(side=tk.LEFT)

        self.lbl_template = ttk.Label(frame_mcoc, text="File input gốc: (chưa có)", foreground="gray")
        self.lbl_template.pack(anchor="w", pady=(2, 0))
        ttk.Label(frame_mcoc,
                  text="Mọi phương án đều được chấm bằng MCOC (chính xác) — cần MCOC Batch + file input MCOC gốc.",
                  foreground="#888").pack(anchor="w")
        # Giữ biến để tương thích (không dùng trong chế độ NSGA-II + MCOC)
        self.var_refine_mode = tk.StringVar(value="full")

        tk.Button(tab_params, text="▶ CHẠY TỐI ƯU HÓA", font=("Arial", 14, "bold"), bg="#27ae60", fg="white", command=self.run_optimize).pack(fill=tk.X, pady=15, ipady=8)

        frame_res = tk.LabelFrame(tab_params, text="Kết quả Đánh giá", padx=10, pady=5)
        frame_res.pack(fill=tk.BOTH, expand=True, pady=5)

        self.txt_result = tk.Text(frame_res, height=10, width=40, font=("Consolas", 10))
        self.txt_result.pack(fill=tk.BOTH, expand=True)

        # Right Panel
        right_frame = tk.Frame(main_paned, bg="white")
        main_paned.add(right_frame, weight=1)

        # Thêm Combobox để chọn Tổ hợp tải trọng mô phỏng
        frame_sim = tk.Frame(right_frame, bg="white")
        frame_sim.pack(side=tk.TOP, fill=tk.X, pady=5)

        tk.Label(frame_sim, text="Phương án:", bg="white").pack(side=tk.LEFT, padx=5)
        self.cb_config = ttk.Combobox(frame_sim, state="readonly", width=25)
        self.cb_config.pack(side=tk.LEFT, padx=5)
        self.cb_config.bind("<<ComboboxSelected>>", self.update_simulation)

        tk.Label(frame_sim, text="Tổ hợp:", bg="white").pack(side=tk.LEFT, padx=5)
        self.cb_load_case = ttk.Combobox(frame_sim, state="readonly", width=12)
        self.cb_load_case.pack(side=tk.LEFT, padx=5)
        self.cb_load_case.bind("<<ComboboxSelected>>", self.update_simulation)

        # Chế độ hiển thị: Mặt bằng bố trí ⇄ Bảng kiểm tra điều kiện R1–R6 (chuẩn tư vấn)
        self.view_mode = tk.StringVar(value="layout")
        ttk.Radiobutton(frame_sim, text="Mặt bằng", variable=self.view_mode,
                        value="layout", command=self.update_simulation).pack(side=tk.LEFT, padx=(12, 2))
        ttk.Radiobutton(frame_sim, text="Kiểm tra điều kiện R1–R6", variable=self.view_mode,
                        value="audit", command=self.update_simulation).pack(side=tk.LEFT, padx=2)

        # Dải KPI: mục tiêu (số cọc) + hệ số sử dụng max + tổ hợp chi phối — luôn hiện
        self.lbl_kpi = tk.Label(right_frame, text="", bg="#eef3f8", fg="#1a3c5e",
                                font=("Arial", 10, "bold"), anchor="w", padx=8, pady=4)
        self.lbl_kpi.pack(side=tk.TOP, fill=tk.X, padx=2)

        # Ghi chú phạm vi & giới hạn mô hình (bắt buộc theo chuẩn tư vấn thiết kế)
        self.lbl_scope = tk.Label(
            right_frame,
            text=("Phạm vi mô hình: bệ cứng — chỉ phân phối lực dọc trục; CHƯA xét "
                  "Hx/Hy/Mz, hiệu ứng nhóm cọc, độ lún, kết cấu bệ. Dùng cho bố trí "
                  "sơ bộ/tối ưu số cọc; thiết kế chi tiết phải chạy MCOC/FEM đầy đủ."),
            bg="white", fg="#888", font=("Arial", 8), anchor="w",
            justify="left", wraplength=720)
        self.lbl_scope.pack(side=tk.BOTTOM, fill=tk.X, padx=4, pady=(0, 2))

        self.plot_canvas = PlotCanvas(right_frame)
        self.plot_canvas.widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: NHẬP / SỬA TẢI TRỌNG
    # ========================================================================
    def add_default_loads(self):
        """Khởi đầu bằng danh sách tải trọng TRỐNG (người dùng tự thêm/nhập)."""
        # Khởi đầu bằng TẢI TRỌNG TRỐNG (sạch) — người dùng tự thêm/nhập.
        self.loads = []
        self.refresh_loads_ui()

    def refresh_loads_ui(self):
        """Vẽ lại bảng tải trọng (Treeview) từ danh sách self.loads hiện hành."""
        for item in self.tree_loads.get_children():
            self.tree_loads.delete(item)
        for i, load in enumerate(self.loads):
            self.tree_loads.insert("", tk.END, values=(
                i + 1,
                load.get('Hx', 0.0), load.get('Hy', 0.0), load.get('N', 0.0),
                load.get('Mx', 0.0), load.get('My', 0.0), load.get('Mz', 0.0)
            ))

    # ── Nhập liệu tải trọng thủ công ──────────────────────────────────────

    def _load_dialog(self, title, init=None):
        """Hộp thoại nhập / sửa 1 tổ hợp tải trọng.
        Trả về dict hoặc None nếu hủy.
        """
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.resizable(False, False)
        dlg.grab_set()          # Modal
        dlg.transient(self.root)

        fields = [
            ("Hx (T) — lực ngang X",    "Hx",  0.0),
            ("Hy (T) — lực ngang Y",    "Hy",  0.0),
            ("P  (T) — lực đứng",       "N",   0.0),
            ("Mx (T.m) — momen trục X", "Mx",  0.0),
            ("My (T.m) — momen trục Y", "My",  0.0),
            ("Mz (T.m) — momen xoắn",   "Mz",  0.0),
        ]
        vars_ = {}
        for row_i, (label, key, default) in enumerate(fields):
            ttk.Label(dlg, text=label, width=26, anchor="w").grid(
                row=row_i, column=0, padx=10, pady=4, sticky="w")
            v = tk.StringVar(value=str(init.get(key, default)) if init else str(default))
            vars_[key] = v
            ttk.Entry(dlg, textvariable=v, width=14).grid(
                row=row_i, column=1, padx=10, pady=4)

        result = [None]

        def on_ok():
            try:
                d = {k: float(v.get()) for k, v in vars_.items()}
                result[0] = d
                dlg.destroy()
            except ValueError:
                messagebox.showerror("Lỗi", "Vui lòng nhập số hợp lệ cho tất cả các trường.", parent=dlg)

        btn_frame = tk.Frame(dlg)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="  OK  ", command=on_ok).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Hủy",   command=dlg.destroy).pack(side=tk.LEFT, padx=6)

        dlg.wait_window()
        return result[0]

    def add_load_dialog(self):
        """Thêm tổ hợp tải trọng mới qua hộp thoại."""
        d = self._load_dialog("Thêm tổ hợp tải trọng")
        if d is not None:
            self.loads.append(d)
            self.refresh_loads_ui()

    def edit_load(self):
        """Sửa tổ hợp tải trọng đang chọn."""
        sel = self.tree_loads.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một tổ hợp để sửa.")
            return
        idx = self.tree_loads.index(sel[0])
        d = self._load_dialog(f"Sửa tổ hợp {idx + 1}", init=self.loads[idx])
        if d is not None:
            self.loads[idx] = d
            self.refresh_loads_ui()

    def delete_load(self):
        """Xóa các tổ hợp tải trọng đang chọn."""
        sel = self.tree_loads.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Vui lòng chọn tổ hợp cần xóa.")
            return
        if not messagebox.askyesno("Xác nhận", f"Xóa {len(sel)} tổ hợp đã chọn?"):
            return
        idxs = sorted([self.tree_loads.index(s) for s in sel], reverse=True)
        for i in idxs:
            self.loads.pop(i)
        self.refresh_loads_ui()

    def paste_loads_csv(self):
        """Nhập nhiều tổ hợp từ văn bản CSV dán vào (clipboard hoặc text area)."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Nhập tải trọng từ văn bản CSV")
        dlg.geometry("560x360")
        dlg.grab_set()
        dlg.transient(self.root)

        tk.Label(
            dlg,
            text="Dán dữ liệu CSV (mỗi dòng = 1 tổ hợp):\n"
                 "Format: Hx, Hy, P, Mx, My, Mz\n"
                 "(Có thể bỏ qua Hx/Hy/Mz — mặc định = 0)",
            justify="left", anchor="w"
        ).pack(fill=tk.X, padx=10, pady=(8, 2))

        txt = tk.Text(dlg, height=12, font=("Consolas", 10))
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        # Thử dán từ clipboard
        try:
            clip = dlg.clipboard_get()
            if clip.strip():
                txt.insert("1.0", clip)
        except Exception:
            pass

        # Mẫu gợi ý
        hint = "Ví dụ:\n0, 0, 2577, 1500, 1500, 0\n0, 0, 2400, 800, 2000, 0"
        txt.insert("end", "\n" + hint)

        var_replace = tk.BooleanVar(value=False)
        tk.Checkbutton(dlg, text="Thay thế toàn bộ (bỏ check = gộp thêm vào)",
                       variable=var_replace).pack(anchor="w", padx=10)

        def on_import():
            raw = txt.get("1.0", "end")
            new_loads = []
            errors = []
            for line_no, line in enumerate(raw.splitlines(), 1):
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("Ví") or line.startswith("Vi"):
                    continue
                parts = [p.strip() for p in line.replace(';', ',').split(',')]
                try:
                    vals = [float(p) for p in parts if p != '']
                    if len(vals) == 3:
                        new_loads.append({'Hx':0,'Hy':0,'N':vals[0],'Mx':vals[1],'My':vals[2],'Mz':0})
                    elif len(vals) == 5:
                        new_loads.append({'Hx':0,'Hy':0,'N':vals[0],'Mx':vals[1],'My':vals[2],'Mz':vals[3],'_extra':vals[4]})
                    elif len(vals) >= 6:
                        new_loads.append({'Hx':vals[0],'Hy':vals[1],'N':vals[2],'Mx':vals[3],'My':vals[4],'Mz':vals[5]})
                    else:
                        errors.append(f"Dòng {line_no}: cần ≥3 cột, bỏ qua.")
                except ValueError:
                    errors.append(f"Dòng {line_no}: không phải số, bỏ qua.")

            if not new_loads:
                messagebox.showwarning("Cảnh báo", "Không đọc được dòng nào hợp lệ.", parent=dlg)
                return

            if var_replace.get():
                self.loads = new_loads
            else:
                self.loads.extend(new_loads)
            self.refresh_loads_ui()

            msg = f"Đã nhập {len(new_loads)} tổ hợp."
            if errors:
                msg += "\n" + "\n".join(errors[:5])
            messagebox.showinfo("Hoàn thành", msg, parent=dlg)
            dlg.destroy()

        btn_f = tk.Frame(dlg)
        btn_f.pack(fill=tk.X, padx=10, pady=6)
        ttk.Button(btn_f, text="  Nhập  ", command=on_import).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_f, text="Hủy", command=dlg.destroy).pack(side=tk.LEFT, padx=4)

        dlg.wait_window()

    # ========================================================================
    # ĐỌC THAM SỐ & NHẬP / XUẤT FILE
    # ========================================================================
    def _pget(self, key, default=0.0):
        """Đọc 1 thông số số từ UI; ô trống / sai định dạng -> default."""
        raw = self.params[key].get()
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
        for k, v in self.params.items():
            if k in self.NUMERIC_PARAMS:
                d[k] = self._pget(k)
            else:
                d[k] = v.get()
        if hasattr(self, 'original_coords') and self.original_coords:
            d['original_coords'] = self.original_coords
        if hasattr(self, 'original_d'): d['original_d'] = self.original_d
        if hasattr(self, 'original_p'): d['original_p'] = self.original_p
        if hasattr(self, 'orig_pmax'): d['orig_pmax'] = self.orig_pmax
        if hasattr(self, 'orig_pmin'): d['orig_pmin'] = self.orig_pmin
        if hasattr(self, 'orig_mxmax'): d['orig_mxmax'] = self.orig_mxmax
        if hasattr(self, 'orig_mymax'): d['orig_mymax'] = self.orig_mymax
        if hasattr(self, 'result_filepath'): d['result_filepath'] = self.result_filepath
        d['SAFE_D'] = d.get('D_PILE', 1.2)
        # Chuẩn hóa [Po]/[Ct] -> Rc,d/Rt,d theo TCVN 10304:2014 Điều 7.1.11 nếu
        # người dùng đã khai báo Rc,k + hệ số tin cậy (qua file/CSV). Idempotent.
        from core import tcvn
        tcvn.apply_design_capacities(d)
        return d

    def browse_exe(self):
        """Mở hộp thoại chọn đường dẫn MCOC Batch và lưu vào tham số exe_path."""
        filepath = filedialog.askopenfilename(
            title="Chọn MCOC Batch (Command Line)",
            filetypes=[("MCOC Batch", "*.lnk;*.exe;*.bat;*.cmd;*.py"), ("All Files", "*.*")])
        if filepath:
            self.params['exe_path'].set(filepath)

    def load_file(self):
        """Mở hộp thoại chọn nhiều file đầu vào rồi nạp chúng lên UI."""
        filepaths = filedialog.askopenfilenames(filetypes=[
            ("All Supported Files", "*.csv;*.txt"),
            ("Text Files", "*.txt"),
            ("CSV Files", "*.csv"),
            ("All Files", "*.*")
        ])
        if filepaths:
            self.process_multiple_files(filepaths)

    def handle_drop(self, event):
        """Xử lý sự kiện kéo-thả file vào cửa sổ chính."""
        # Lấy danh sách file khi kéo-thả nhiều file; file có dấu cách
        # thường được bọc trong ngoặc nhọn {}.
        paths = _re.findall(r'{[^}]+}|[^{ ]+', event.data)
        if not paths: return

        filepaths = [p.strip('{}') for p in paths]
        self.process_multiple_files(filepaths)

    def process_multiple_files(self, filepaths):
        """Đọc và nạp nhiều file đầu vào: cập nhật thông số, tải trọng, toạ độ
        gốc lên UI; nhận diện file template MCOC; reset kết quả cũ."""
        success_count = 0
        total_new_loads = 0
        last_proj_name = ""

        for filepath in filepaths:
            try:
                params, loads, proj_name = parse_input_file(filepath)

                # Cập nhật tất cả thông số từ file lên UI
                keys_to_update = ['L_X', 'L_Y', 'D_PILE', 'P_LIMIT', 'P_TENSION', 'M_LIMIT']
                for k in keys_to_update:
                    if k in params and params[k] is not None and params[k] > 0:
                        # StringVar: hiển thị gọn (bỏ ".0" thừa)
                        val = params[k]
                        self.params[k].set(f"{val:g}")

                if 'original_coords' in params:
                    self.original_coords = params['original_coords']
                    if 'D_PILE' in params: self.original_d = params['D_PILE']
                    if 'P_LIMIT' in params: self.original_p = params['P_LIMIT']

                # Lưu Nmax/Nmin/Mxmax/Mymax thực tế từ file kết quả
                if 'orig_pmax' in params: self.orig_pmax = params['orig_pmax']
                if 'orig_pmin' in params: self.orig_pmin = params['orig_pmin']
                if 'orig_mxmax' in params: self.orig_mxmax = params['orig_mxmax']
                if 'orig_mymax' in params: self.orig_mymax = params['orig_mymax']
                self.result_filepath = filepath  # Lưu đường dẫn để blackbox đọc đúng file

                # Nếu là file INPUT MCOC (không phải file kết quả/CSV) -> dùng làm
                # template sinh phương án mới khi gọi MCOC thực
                if proj_name != 'Imported from Result' and not filepath.lower().endswith('.csv') \
                        and 'original_coords' in params:
                    self.input_filepath = filepath
                    if hasattr(self, 'lbl_template'):
                        self.lbl_template.config(
                            text="File input gốc: " + os.path.basename(filepath), foreground="black")

                self.loads = loads
                total_new_loads += len(loads)
                success_count += 1
                if proj_name and proj_name != "Du An Toi Uu Coc":
                    last_proj_name = proj_name
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file {filepath}:\n{str(e)}")

        if success_count > 0:
            if last_proj_name:
                self.project_name = last_proj_name
            # Reset kết quả cũ — dữ liệu mới, kết quả mới
            self.current_config = None
            self.refresh_loads_ui()

            # Sau khi load file, mở khóa L_X / L_Y để người dùng có thể điều chỉnh
            for k in ('L_X', 'L_Y'):
                if k in self._param_entries:
                    self._param_entries[k].config(state='normal')

            # Xóa UI kết quả cũ
            self.txt_result.delete(1.0, tk.END)
            self.cb_config.set('')
            self.cb_config['values'] = []

            # Để trống khung vẽ, chờ người dùng ấn "Chạy tối ưu hóa"
            self.plot_canvas.clear()

    def clear_loads(self):
        """Xóa toàn bộ danh sách tải trọng và reset UI kết quả về trạng thái mới."""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa toàn bộ danh sách tổ hợp tải trọng không?"):
            self.loads = []
            self.refresh_loads_ui()

            # Reset UI như lúc load file mới
            self.current_config = None
            self.txt_result.delete(1.0, tk.END)
            self.cb_config.set('')
            self.cb_config['values'] = []
            self.plot_canvas.clear()   # vẽ trắng như lúc mới mở

    def save_file(self):
        """Xuất kết quả phương án hiện hành: file TXT (MCOC), báo cáo .md và ảnh
        mặt bằng PNG cho từng phương án (BEST hoặc ALL)."""
        if not self.current_config:
            messagebox.showwarning("Cảnh báo", "Chưa có kết quả để xuất. Vui lòng chạy Tối ưu hóa trước.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=to_safe_filename(getattr(self, 'project_name', 'Ket_qua_toi_uu')),
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        try:
            base_dir  = os.path.dirname(filepath)
            base_name = os.path.splitext(os.path.basename(filepath))[0]

            # 1. Xuất file TXT kết quả (định dạng MCOC)
            export_output_file(
                filepath,
                self.current_config,
                self.get_params_dict(),
                self.loads,
                getattr(self, 'project_name', 'Du An Toi Uu Coc'),
                self.output_option.get()
            )

            # 1b. Xuất BÁO CÁO KỸ THUẬT chuẩn (.md) — hệ số sử dụng, R1-R6, phụ lục
            report_path = os.path.join(base_dir, f"{base_name}_baocao_kythuat.md")
            try:
                export_technical_report(
                    report_path, self.current_config, self.get_params_dict(),
                    self.loads, getattr(self, 'project_name', 'Du An Toi Uu Coc'))
            except Exception:
                report_path = None

            # 1c. Xuất BÁO CÁO KỸ THUẬT dạng PDF (cùng nội dung, có bảng R1-R6, font Việt)
            pdf_report_path = os.path.join(base_dir, f"{base_name}_baocao_kythuat.pdf")
            try:
                export_technical_report_pdf(
                    pdf_report_path, self.current_config, self.get_params_dict(),
                    self.loads, getattr(self, 'project_name', 'Du An Toi Uu Coc'))
            except Exception:
                pdf_report_path = None

            # 2. Xuất ảnh mặt bằng PNG
            exported_imgs = []
            if self.output_option.get() == "ALL":
                for name in self.cb_config['values']:
                    self.cb_config.set(name)
                    self.update_simulation()
                    safe = to_safe_filename(name)
                    img_path = os.path.join(base_dir, f"{base_name}_{safe}.png")
                    self.plot_canvas.fig.savefig(img_path, dpi=300, bbox_inches='tight')
                    exported_imgs.append(img_path)
            else:
                # Luôn vẽ lại phương án đề xuất trước khi lưu
                if "Phương án đề xuất" in self.cb_config['values']:
                    self.cb_config.set("Phương án đề xuất")
                elif self.cb_config['values']:
                    self.cb_config.current(0)
                self.update_simulation()
                img_path = os.path.join(base_dir, f"{base_name}_De_xuat.png")
                self.plot_canvas.fig.savefig(img_path, dpi=300, bbox_inches='tight')
                exported_imgs.append(img_path)

            extra = [p for p in (report_path, pdf_report_path) if p]
            messagebox.showinfo(
                "Thành công",
                f"Đã xuất:\n• {os.path.basename(filepath)}\n"
                + "\n".join(f"• {os.path.basename(p)}" for p in extra + exported_imgs)
            )
        except Exception as e:
            import traceback
            messagebox.showerror("Lỗi", f"Không thể xuất file: {str(e)}\n\n{traceback.format_exc()[-300:]})")

    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: CHẠY TỐI ƯU & HIỂN THỊ KẾT QUẢ
    # ========================================================================
    def run_optimize(self):
        """Chạy tối ưu — mặc định ĐÁNH GIÁ CHÍNH XÁC bằng MCOC (NSGA-II)."""
        # 0) Phải nhập đủ thông số bài toán bắt buộc (> 0)
        required = {'L_X': "Rộng bệ Lx", 'L_Y': "Dài bệ Ly",
                    'D_PILE': "Đ.kính cọc d", 'P_LIMIT': "Sức nén [Po]"}
        missing = [name for k, name in required.items() if self._pget(k) <= 0]
        if missing:
            messagebox.showwarning(
                "Chưa nhập đủ thông số",
                "Vui lòng nhập (giá trị > 0) cho: " + ", ".join(missing) + ".")
            return

        # 1) Phải có tải trọng
        if not self.loads:
            messagebox.showwarning(
                "Chưa có tải trọng",
                "Vui lòng thêm ít nhất một tổ hợp tải trọng "
                "(nút \"Thêm tổ hợp\", \"Dán nhiều dòng (CSV)\" hoặc mở file đầu vào).")
            return

        # 2) BẮT BUỘC MCOC — không chấp nhận phương án xấp xỉ
        exe = self.params['exe_path'].get().strip()
        if not exe or not os.path.exists(exe):
            messagebox.showwarning(
                "Cần cấu hình MCOC",
                "Chương trình đánh giá mọi phương án bằng MCOC (chính xác).\n"
                "Hãy chọn đường dẫn MCOC Batch ở mục \"Cấu hình MCOC (bắt buộc)\".")
            return
        if (not self.input_filepath or not os.path.exists(self.input_filepath)
                or not getattr(self, 'original_coords', None)):
            messagebox.showwarning(
                "Thiếu file MCOC gốc",
                "Cần mở FILE INPUT MCOC gốc (.txt, có tọa độ cọc gốc) làm template.\n"
                "Dùng \"Mở file đầu vào\" để nạp file input MCOC — không phải file _result hay CSV.")
            return

        params = self.get_params_dict()
        params['input_filepath'] = self.input_filepath
        params['mock_mode'] = False
        loads = list(self.loads)

        self.txt_result.delete(1.0, tk.END)
        self._log_refine("=== TỐI ƯU BẰNG MCOC (NSGA-II — đánh giá chính xác) ===")
        self._log_refine("Đang chạy MCOC, vui lòng đợi...")

        def worker():
            try:
                from io_handlers.mcoc_writer import self_check
                from core.nsga2_optimizer import run_nsga2
                ok, msg = self_check(self.input_filepath, params['original_coords'])
                if not ok:
                    self._log_refine("LỖI TEMPLATE: " + msg)
                    return
                # Tải trọng lấy TỪ UI (ghi đè tải trong file MCOC gốc) — UI là nguồn duy nhất
                evaluator = MCOCBlackbox.make_real_evaluator(params, loads=loads, log=self._log_refine)
                # Chấm phương án gốc (để so sánh) — cùng bộ tải UI
                orig_res = evaluator(np.array(params['original_coords'], dtype=float))
                results = run_nsga2(params, loads, evaluator=evaluator,
                                    pop_size=16, n_gen=10, max_evals=50,
                                    secondary=self.var_secondary.get(),
                                    log=self._log_refine)
                results['_orig_eval'] = (len(params['original_coords']), orig_res)
                self.root.after(0, lambda: self._show_nsga2_results(results))
            except Exception as e:
                import traceback
                self._log_refine("LỖI: %s" % e)
                self._log_refine(traceback.format_exc()[-300:])

        threading.Thread(target=worker, daemon=True).start()

    def _show_nsga2_results(self, results):
        """Hiển thị kết quả NSGA-II + MCOC: chuyển về cấu trúc dùng chung."""
        P_LIMIT = self._pget('P_LIMIT')
        orig_cfg = None
        oe = results.get('_orig_eval')
        if oe:
            n0, r0 = oe
            orig_cfg = {
                'type': 'Goc', 'nx': 0, 'ny': 0, 'sx': 0, 'sy': 0, 'n': n0,
                'coords': self.original_coords,
                'pmax': r0.get('pmax', 0), 'pmin': r0.get('pmin', 0),
                'mxmax': r0.get('mxmax', 0), 'mymax': r0.get('mymax', 0),
                'ok': r0.get('pmax', 1e9) <= P_LIMIT, 'msg': 'Phuong an goc (MCOC)',
            }
        all_mode = self.output_option.get() != "BEST"
        valid = results.get('all_valid_configs', []) if all_mode else results.get('pareto_front', [])
        self.current_config = {
            'recommended': results.get('recommended'),
            'original_config': orig_cfg,
            'all_valid_configs': valid,
            'all_candidates': [],
            'best_A': results.get('best_A'), 'best_B': results.get('best_B'),
            'reason': results.get('reason', ''),
        }
        self.txt_result.delete(1.0, tk.END)
        self._render_results(self.current_config, results.get('n_evals'))
        self.populate_comboboxes(self.current_config)

    def _render_results(self, results, n_evals=None):
        """In kết quả ra ô 'Kết quả Đánh giá' theo bố cục gọn, kèm bảng tọa độ."""
        P_LIMIT = self._pget('P_LIMIT')
        M_LIMIT = self._pget('M_LIMIT')
        P_TENSION = self._pget('P_TENSION')
        W = 60
        ins = lambda s="": self.txt_result.insert(tk.END, s + "\n")
        rec = results.get('recommended')
        orig = results.get('original_config')

        ins("=" * W)
        ins("  PHUONG AN KIEN NGHI")
        ins("=" * W)
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
            ins("  Khong tim thay phuong an thoa man.")
            ins(f"  Ly do: {results.get('reason', '')}")
        ins("")

        if orig:
            status = "DAT" if orig['ok'] else "KHONG DAT"
            ins("-" * W)
            ins(f"  PHUONG AN GOC : {status}")
            ins("-" * W)
            ins(f"  So coc = {orig['n']}    Pmax = {orig['pmax']:.2f} T   (Po = {P_LIMIT:.0f} T)")
            ins(f"  Pmin = {orig['pmin']:.2f} T")
            ins("")

        show = results.get('all_valid_configs', [])
        ins("-" * W)
        ins(f"  CAC PHUONG AN DAT (MCOC)  -  {len(show)} phuong an")
        ins("-" * W)
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
            ins(f"  (Gioi han: {', '.join(notes)})")
        else:
            ins("  Khong co phuong an nao DAT trong kich thuoc be nay.")
        if n_evals is not None:
            ins(f"\n  So lan goi MCOC: {n_evals}")

    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: HỘP ĐEN MCOC THỰC (tinh chỉnh từng bước)
    # ========================================================================
    def _log_refine(self, msg):
        """Ghi log từ thread tinh chỉnh lên ô kết quả (thread-safe)."""
        def _append():
            self.txt_result.insert(tk.END, msg + "\n")
            self.txt_result.see(tk.END)
        self.root.after(0, _append)

    def run_refine_real(self):
        """Chạy chế độ MCOC thực: tinh chỉnh Pareto từng bước trên thread nền,
        dùng file input MCOC gốc làm template."""
        exe = self.params['exe_path'].get().strip()
        if not exe:
            messagebox.showwarning("Thiếu MCOC", "Chưa chọn đường dẫn MCOC Batch (Command Line).")
            return
        if not self.input_filepath or not os.path.exists(self.input_filepath):
            messagebox.showwarning(
                "Thiếu file input gốc",
                "Chế độ MCOC thực cần file INPUT MCOC gốc làm template.\n"
                "Hãy load file input (.txt/.dat) của MCOC — không phải file _result.")
            return
        if not getattr(self, 'original_coords', None):
            messagebox.showwarning("Thiếu phương án gốc", "File input chưa có tọa độ cọc gốc.")
            return

        self.txt_result.delete(1.0, tk.END)
        self.txt_result.insert(tk.END, "=== HOP DEN MCOC THUC - TINH CHINH TUNG BUOC ===\n")

        params = self.get_params_dict()
        params['input_filepath'] = self.input_filepath
        params['mock_mode'] = False
        params['refine_mode'] = self.var_refine_mode.get()
        loads = list(self.loads)

        def worker():
            try:
                # Kiểm tra template trước khi chạy
                from io_handlers.mcoc_writer import self_check
                ok, msg = self_check(self.input_filepath, params['original_coords'])
                if not ok:
                    self._log_refine("LOI TEMPLATE: " + msg)
                    return
                self._log_refine("Template: " + msg)

                evaluator = MCOCBlackbox.make_real_evaluator(params, log=self._log_refine)
                results = run_pareto_refinement(params, loads, evaluator, log=self._log_refine)
                self.root.after(0, lambda: self._show_refine_results(results))
            except Exception as e:
                self._log_refine("LOI: %s" % e)

        threading.Thread(target=worker, daemon=True).start()

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
        self.current_config = {
            'original_config': to_cfg(results['original'], 'Goc'),
            'recommended': to_cfg(results['best'], 'TinhChinh'),
            'best_A': None, 'best_B': None,
            'all_valid_configs': valid_steps,
            'all_candidates': [],
            'reason': results['reason'],
        }

        best = results['best']
        ins = lambda s="": self.txt_result.insert(tk.END, s + "\n")
        P_LIMIT = self._pget('P_LIMIT')
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
        self.populate_comboboxes(self.current_config)

    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: MÔ PHỎNG & COMBOBOX
    # ========================================================================
    def update_simulation(self, event=None):
        """Vẽ lại mô phỏng mặt bằng cho phương án + tổ hợp tải đang chọn.

        Lấy lực cọc theo mô hình bệ cứng rồi hiệu chỉnh theo hệ số khớp Pmax
        thực (MCOC) để hình vẽ đồng nhất với phần kết luận.
        """
        if not self.current_config: return

        idx_load = self.cb_load_case.current()
        if idx_load < 0: idx_load = 0

        config_name = self.cb_config.get()
        selected_cfg = None

        if config_name == "Ph\u01b0\u01a1ng \u00e1n g\u1ed1c":
            selected_cfg = self.current_config.get('original_config')
        elif config_name == "Ph\u01b0\u01a1ng \u00e1n \u0111\u1ec1 xu\u1ea5t":
            selected_cfg = self.current_config.get('recommended')
        elif config_name.startswith("Ph\u01b0\u01a1ng \u00e1n "):
            try:
                num = int(config_name.split()[2])
                selected_cfg = self.current_config['all_valid_configs'][num - 1]
            except:
                pass

        if not selected_cfg: return

        coords = np.array(selected_cfg['coords'])  # Ép về numpy array, xử lý cả list lẫn array
        if coords.ndim != 2 or coords.shape[0] == 0: return

        forces = None
        params_dict = self.get_params_dict()

        # Hệ số hiệu chỉnh: ưu tiên khớp Pmax THỰC (MCOC) của phương án đang xem,
        # để lực vẽ trên canvas đồng nhất với kết quả ở phần kết luận.
        calibration_factor = 1.0
        cfg_pmax = selected_cfg.get('pmax', 0) or 0
        cfg_rigid_pmax = rigid_cap.pmax_pmin(coords, self.loads)[0] if self.loads else 0.0
        if cfg_pmax > 0 and cfg_rigid_pmax > 0:
            calibration_factor = rigid_cap.calibration_factor(cfg_rigid_pmax, cfg_pmax)
        elif getattr(self, 'original_coords', None) and self.loads:
            orig_pmax_actual = params_dict.get('orig_pmax', 519.63)
            orig_rigid_pmax = rigid_cap.pmax_pmin(self.original_coords, self.loads)[0]
            calibration_factor = rigid_cap.calibration_factor(orig_rigid_pmax, orig_pmax_actual)

        # Luôn tính forces bằng mô hình bệ cứng — kể cả khi KHÔNG ĐẠT
        if self.loads:
            load = self.loads[min(idx_load, len(self.loads) - 1)]
            raw = rigid_cap.pile_forces(coords, load)          # công thức dùng chung
            forces = [float(p) * calibration_factor for p in raw]

        mxmax = selected_cfg.get('mxmax', 0)
        mymax = selected_cfg.get('mymax', 0)

        # Số liệu kiểm tra điều kiện R1–R6 theo từng tổ hợp (chuẩn tư vấn) + cập nhật KPI.
        # Tính luôn cho cả 2 chế độ để dải KPI nhất quán dù đang xem mặt bằng.
        cdata = self._build_constraint_data(selected_cfg, coords, params_dict, calibration_factor)
        self._update_kpi(cdata)

        if self.view_mode.get() == "audit":
            self.plot_canvas.draw_constraint_view(cdata)
        else:
            self.plot_canvas.draw_simulation(coords, params_dict, forces, m_forces=(mxmax, mymax))

    # ── Kiểm tra điều kiện R1–R6 (chuẩn tư vấn) ──────────────────────────
    def _build_constraint_data(self, cfg, coords, params, calib):
        """Tổng hợp số liệu kiểm tra điều kiện R1–R6 theo từng tổ hợp cho phương án đang xem.

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
        if self.loads:
            P = rigid_cap.forces_all_loads(np.asarray(coords, float), self.loads)
            for i in range(len(self.loads)):
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

        # R3 (3d ≤ k/c ≤ 6d) và R4 (tim cọc → mép ≥ d) — thuần hình học, không đổi theo tổ hợp
        s_act = float(rigid_cap.min_spacing(coords)) if len(coords) > 1 else 0.0
        s_min_req, s_max_req = 3 * d, 6 * d
        r3_ok = (len(coords) <= 1) or (s_min_req - 1e-3 <= s_act <= s_max_req + 1e-3)
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
            f"R3 k/c: {s_act:.2f} m ∈ [{s_min_req:.2f}, {s_max_req:.2f}] "
            + ('✓' if r3_ok else '✗'),
            f"R4 tim→mép: {max(r4x, r4y) * 100:.0f}% " + ('✓' if r4_ok else '✗'),
            (f"R5/R6 uốn M: max({mxmax:.1f}, {mymax:.1f}) ≤ {Mlim:.1f} T·m "
             + ('✓' if m_ok else '✗')) if Mlim > 0 else "R5/R6 uốn M: không kiểm ([M]=0)",
        ]

        all_ok = bool(rows) and all(r['ok'] for r in rows) and r3_ok and r4_ok and m_ok
        return {
            'n_piles': len(coords), 'rows': rows, 'governing': gov_i,
            'util_max': util_max, 'status': 'ĐẠT' if all_ok else 'KHÔNG ĐẠT',
            'geom_summary': geom_summary, 'Po': Po, 'Ct': Ct,
        }

    def _update_kpi(self, cdata):
        """Cập nhật dải KPI: số cọc (mục tiêu), hệ số sử dụng max, tổ hợp chi phối."""
        gov = cdata['governing']
        txt = (f"Số cọc: {cdata['n_piles']}      |      "
               f"Hệ số sử dụng lớn nhất: {cdata['util_max']:.3f}"
               + (f"  (TH{gov} chi phối)" if gov else "")
               + f"      |      Trạng thái: {cdata['status']}")
        self.lbl_kpi.config(text=txt, fg=("#1a3c5e" if cdata['status'] == 'ĐẠT' else "#b03a2e"))

    def populate_comboboxes(self, results):
        """Nạp combobox phương án + tổ hợp tải; mặc định chọn tổ hợp bất lợi nhất
        và phương án đề xuất rồi vẽ mô phỏng."""
        cases = [f"Tổ hợp {i+1}" for i in range(len(self.loads))]
        self.cb_load_case['values'] = cases
        if cases:
            # Mặc định về TỔ HỢP BẤT LỢI NHẤT (cho Pmax lớn nhất) của phương án đề xuất
            worst = 0
            rec = results.get('recommended')
            if rec and self.loads:
                P = rigid_cap.forces_all_loads(np.asarray(rec['coords'], float), self.loads)
                if getattr(P, 'size', 0):
                    worst = int(np.argmax(P.max(axis=1)))
            self.cb_load_case.current(min(worst, len(cases) - 1))

        config_names = []
        if results.get('original_config'):
            config_names.append("Phương án gốc")

        config_names.append("Phương án đề xuất")

        for i in range(len(results.get('all_valid_configs', []))):
            config_names.append(f"Phương án {i+1}")

        self.cb_config['values'] = config_names
        if config_names:
            # Ưu tiên hiện Phương án đề xuất; nếu không có, hiện Phương án gốc
            if "Ph\u01b0\u01a1ng \u00e1n \u0111\u1ec1 xu\u1ea5t" in config_names and results.get('recommended'):
                self.cb_config.set("Ph\u01b0\u01a1ng \u00e1n \u0111\u1ec1 xu\u1ea5t")
            elif "Ph\u01b0\u01a1ng \u00e1n g\u1ed1c" in config_names:
                self.cb_config.set("Ph\u01b0\u01a1ng \u00e1n g\u1ed1c")
            else:
                self.cb_config.current(0)

        self.update_simulation()

    # ========================================================================
    # TAB 2 - HÀNG LOẠT: DỰNG GIAO DIỆN
    # ========================================================================
    def setup_batch_ui(self, parent_frame):
        """Giao di\u1ec7n Tab 2 \u2014 thi\u1ebft k\u1ebf theo layout MCOC."""
        # ── Toolbar trên cùng ──────────────────────────────────────────
        toolbar = tk.Frame(parent_frame, pady=4, padx=6)
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text="Th\u00eam file",    command=self.load_file_batch).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Th\u00eam th\u01b0 m\u1ee5c", command=self.load_folder_batch).pack(side=tk.LEFT, padx=3)
        tk.Label(toolbar, text="K\u00e9o th\u1ea3 nhi\u1ec1u file ho\u1eb7c th\u01b0 m\u1ee5c v\u00e0o v\u00f9ng d\u1eef li\u1ec7u \u0111\u1ea7u v\u00e0o.",
                 fg="#555").pack(side=tk.RIGHT, padx=6)

        # ── Body: chia đôi trái / phải ──────────────────────────────
        body = ttk.PanedWindow(parent_frame, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))

        # ── Panel trái: Danh sách file ───────────────────────────
        left = tk.LabelFrame(body, text="D\u1eef li\u1ec7u \u0111\u1ea7u v\u00e0o", padx=4, pady=4)
        body.add(left, weight=3)

        cols_b = ("#", "T\u00ean file", "Th\u01b0 m\u1ee5c", "Tr\u1ea1ng th\u00e1i")
        self.tree_batch = ttk.Treeview(left, columns=cols_b, show="headings", selectmode="extended")
        self.tree_batch.heading("#",          text="#")
        self.tree_batch.heading("T\u00ean file",    text="T\u00ean file")
        self.tree_batch.heading("Th\u01b0 m\u1ee5c",   text="Th\u01b0 m\u1ee5c")
        self.tree_batch.heading("Tr\u1ea1ng th\u00e1i",  text="Tr\u1ea1ng th\u00e1i")
        self.tree_batch.column("#",          width=34,  anchor="center", stretch=False)
        self.tree_batch.column("T\u00ean file",    width=160, anchor="w")
        self.tree_batch.column("Th\u01b0 m\u1ee5c",   width=320, anchor="w")
        self.tree_batch.column("Tr\u1ea1ng th\u00e1i",  width=100, anchor="center", stretch=False)
        # Màu tag trạng thái
        self.tree_batch.tag_configure("done",    foreground="#27ae60")
        self.tree_batch.tag_configure("running", foreground="#2980b9")
        self.tree_batch.tag_configure("fail",    foreground="#e74c3c")
        self.tree_batch.tag_configure("wait",    foreground="#7f8c8d")

        sb_b = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree_batch.yview)
        self.tree_batch.configure(yscrollcommand=sb_b.set)
        self.tree_batch.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_b.pack(side=tk.RIGHT, fill=tk.Y)

        # Footer đếm file + nút xóa
        foot = tk.Frame(left)
        foot.pack(fill=tk.X, pady=(4, 0))
        self.lbl_batch_count = tk.Label(foot, text="0 file", fg="#555")
        self.lbl_batch_count.pack(side=tk.LEFT)
        ttk.Button(foot, text="X\u00f3a ch\u1ecdn", command=self.delete_selected_batch).pack(side=tk.RIGHT, padx=3)
        ttk.Button(foot, text="X\u00f3a t\u1ea5t c\u1ea3",  command=self.clear_all_batch).pack(side=tk.RIGHT, padx=3)

        # Drag-drop vào danh sách
        self.tree_batch.drop_target_register(DND_FILES)
        self.tree_batch.dnd_bind("<<Drop>>", self._batch_drop)

        # ── Panel phải: Thiết lập chạy ─────────────────────────
        right = tk.LabelFrame(body, text="Thi\u1ebft l\u1eadp ch\u1ea1y", padx=8, pady=6)
        body.add(right, weight=2)

        # Thư mục xuất kết quả
        tk.Label(right, text="Th\u01b0 m\u1ee5c xu\u1ea5t k\u1ebft qu\u1ea3", font=("", 9, "bold"), anchor="w").pack(fill=tk.X)
        dir_f = tk.Frame(right)
        dir_f.pack(fill=tk.X, pady=(2, 0))
        self.txt_out_dir = tk.Entry(dir_f)
        self.txt_out_dir.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_f, text="Ch\u1ecdn...", command=self.choose_out_dir).pack(side=tk.LEFT, padx=4)
        tk.Label(right, text="\u0110\u1ec3 tr\u1ed1ng: k\u1ebft qu\u1ea3 l\u01b0u c\u00f9ng th\u01b0 m\u1ee5c t\u1eebng file \u0111\u1ea7u v\u00e0o.",
                 fg="#888", font=("", 8)).pack(anchor="w")

        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, pady=6)

        # Tab xuất (Xuất kết quả / Thiết lập nâng cao)
        nb_right = ttk.Notebook(right)
        nb_right.pack(fill=tk.BOTH, expand=True)

        tab_export = tk.Frame(nb_right, padx=6, pady=6)
        nb_right.add(tab_export, text="Xu\u1ea5t k\u1ebft qu\u1ea3")

        tab_adv = tk.Frame(nb_right, padx=6, pady=6)
        nb_right.add(tab_adv, text="N\u00e2ng cao")

        # Tab xuất kết quả
        self.var_export_pdf   = tk.BooleanVar(value=True)
        self.var_export_excel = tk.BooleanVar(value=True)
        self.var_export_png   = tk.BooleanVar(value=True)
        self.var_merge_pdf    = tk.BooleanVar(value=True)

        tk.Checkbutton(tab_export, text="Xu\u1ea5t b\u00e1o c\u00e1o PDF",
                       variable=self.var_export_pdf).pack(anchor="w", pady=2)
        tk.Checkbutton(tab_export, text="Xu\u1ea5t b\u1ea3ng Excel",
                       variable=self.var_export_excel).pack(anchor="w", pady=2)
        tk.Checkbutton(tab_export, text="Xu\u1ea5t m\u1eb7t b\u1eb1ng c\u1ecdc d\u1ea1ng PNG",
                       variable=self.var_export_png).pack(anchor="w", pady=2)
        tk.Checkbutton(tab_export, text="G\u1ed9p c\u00e1c PDF th\u00e0nh m\u1ed9t file t\u1ed5ng h\u1ee3p",
                       variable=self.var_merge_pdf).pack(anchor="w", pady=2)

        ttk.Separator(tab_export, orient="horizontal").pack(fill=tk.X, pady=6)

        pf = tk.Frame(tab_export)
        pf.pack(fill=tk.X)
        tk.Label(pf, text="Prefix t\u00ean file", width=14, anchor="w").grid(row=0, column=0, sticky="w")
        self.txt_prefix = tk.Entry(pf, width=18)
        self.txt_prefix.grid(row=0, column=1, padx=4, pady=2)

        tk.Label(pf, text="Suffix t\u00ean file", width=14, anchor="w").grid(row=1, column=0, sticky="w")
        self.txt_suffix = tk.Entry(pf, width=18)
        self.txt_suffix.grid(row=1, column=1, padx=4, pady=2)

        # Tab nâng cao
        self.var_override_params = tk.BooleanVar(value=False)
        tk.Checkbutton(
            tab_adv,
            text="Ghi \u0111\u00e8 th\u00f4ng s\u1ed1 c\u1ecdc t\u1eeb Tab 1 (d, Po, Ct, M) l\u00ean t\u1ea5t c\u1ea3 file",
            variable=self.var_override_params
        ).pack(anchor="w", pady=4)
        tk.Label(tab_adv,
                 text="M\u1eb7c \u0111\u1ecbnh: d\u00f9ng th\u00f4ng s\u1ed1 c\u1eed c\u1ee7a t\u1eebng file (d, Po, Ct).\n"
                      "B\u1eadt l\u00ean khi mu\u1ed1n so s\u00e1nh nhi\u1ec1u ph\u01b0\u01a1ng \u00e1n c\u00f9ng m\u1ed9t gi\u1edbi h\u1ea1n.",
                 fg="#555", justify="left").pack(anchor="w")

        # ── Tiến trình: progress bar + log ──────────────────────
        prog_outer = tk.LabelFrame(parent_frame, text="Ti\u1ebfn tr\u00ecnh", padx=6, pady=4)
        prog_outer.pack(fill=tk.BOTH, expand=False, padx=6, pady=(0, 4))

        prog_top = tk.Frame(prog_outer)
        prog_top.pack(fill=tk.X, pady=(0, 4))
        self.progress_bar = ttk.Progressbar(prog_top, orient="horizontal", mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_progress = tk.Label(prog_top, text="0/0 Ho\u00e0n th\u00e0nh", width=18, anchor="e")
        self.lbl_progress.pack(side=tk.LEFT, padx=6)

        self.txt_batch_log = tk.Text(prog_outer, height=8, bg="#1e1e1e", fg="#d4d4d4",
                                     font=("Consolas", 9), relief="flat", wrap="word")
        sb_log = ttk.Scrollbar(prog_outer, orient=tk.VERTICAL, command=self.txt_batch_log.yview)
        self.txt_batch_log.configure(yscrollcommand=sb_log.set)
        self.txt_batch_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_log.pack(side=tk.RIGHT, fill=tk.Y)

        # Tag màu log
        self.txt_batch_log.tag_configure("ok",    foreground="#4ec9b0")
        self.txt_batch_log.tag_configure("err",   foreground="#f44747")
        self.txt_batch_log.tag_configure("info",  foreground="#9cdcfe")
        self.txt_batch_log.tag_configure("title", foreground="#dcdcaa", font=("Consolas", 9, "bold"))

        # ── Status bar ─────────────────────────────────────
        status_bar = tk.Frame(parent_frame, pady=6, padx=6)
        status_bar.pack(fill=tk.X)

        self.lbl_batch_status = tk.Label(status_bar, text="S\u1eb5n s\u00e0ng.", anchor="w", fg="#555")
        self.lbl_batch_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.btn_open_out = ttk.Button(status_bar, text="M\u1edf th\u01b0 m\u1ee5c k\u1ebft qu\u1ea3",
                                       command=self._open_out_dir, state="disabled")
        self.btn_open_out.pack(side=tk.LEFT, padx=4)

        self._batch_stop_flag = False
        self.btn_stop_batch = ttk.Button(status_bar, text="D\u1eebng", command=self._stop_batch, state="disabled")
        self.btn_stop_batch.pack(side=tk.LEFT, padx=4)

        self.btn_run_batch = tk.Button(status_bar, text="T\u00cdNH TO\u00c1N",
                                       bg="#27ae60", fg="white",
                                       font=("Arial", 11, "bold"),
                                       padx=20, command=self.run_batch)
        self.btn_run_batch.pack(side=tk.LEFT, padx=6)

        self.batch_files = []  # list of dicts: {'path': str, 'status': str}

    # ========================================================================
    # TAB 2 - HÀNG LOẠT: QUẢN LÝ DANH SÁCH FILE & TRẠNG THÁI
    # ========================================================================
    def _batch_drop(self, event):
        """Xử lý kéo-thả file/thư mục vào danh sách hàng loạt (lọc .txt trong thư mục)."""
        paths = _re.findall(r'\{[^}]+\}|[^{ ]+', event.data)
        filepaths = []
        for p in paths:
            p = p.strip('{}')
            if os.path.isdir(p):
                for fn in os.listdir(p):
                    if fn.lower().endswith('.txt'):
                        filepaths.append(os.path.join(p, fn))
            elif os.path.isfile(p):
                filepaths.append(p)
        self.add_files_to_batch(filepaths)

    def load_file_batch(self):
        """Chọn nhiều file (.txt/.csv) thêm vào danh sách hàng loạt."""
        fps = filedialog.askopenfilenames(
            filetypes=[("Text / CSV Files", "*.txt *.csv"), ("All Files", "*.*")])
        self.add_files_to_batch(fps)

    def load_folder_batch(self):
        """Chọn một thư mục và thêm mọi file .txt/.csv trong đó vào danh sách."""
        folder = filedialog.askdirectory(title="Ch\u1ecdn th\u01b0 m\u1ee5c ch\u1ee9a c\u00e1c file \u0111\u1ea7u v\u00e0o")
        if not folder:
            return
        fps = [os.path.join(folder, fn)
               for fn in sorted(os.listdir(folder))
               if fn.lower().endswith(('.txt', '.csv'))]
        if not fps:
            messagebox.showinfo("Th\u00f4ng b\u00e1o", "Th\u01b0 m\u1ee5c kh\u00f4ng c\u00f3 file .txt / .csv n\u00e0o.")
            return
        self.add_files_to_batch(fps)

    def add_files_to_batch(self, filepaths):
        """Thêm danh sách đường dẫn vào hàng loạt (bỏ qua file trùng) và cập nhật bảng."""
        added = 0
        for fp in filepaths:
            if any(f['path'] == fp for f in self.batch_files):
                continue
            self.batch_files.append({'path': fp, 'status': 'Ch\u1edd'})
            name   = os.path.basename(fp)
            folder = os.path.dirname(fp)
            idx    = len(self.batch_files)
            self.tree_batch.insert("", "end",
                                   values=(idx, name, folder, "Ch\u1edd"),
                                   tags=("wait",))
            added += 1
        self.lbl_batch_count.config(text=f"{len(self.batch_files)} file")

    def delete_selected_batch(self):
        """Xóa các file đang chọn khỏi danh sách hàng loạt và đánh số lại."""
        sel = self.tree_batch.selection()
        if not sel:
            return
        # Xác định tập đường dẫn cần xóa
        paths_to_remove = set()
        for item in sel:
            vals = self.tree_batch.item(item, 'values')
            fname = vals[1]; fdir = vals[2]
            paths_to_remove.add(os.path.join(str(fdir), str(fname)))
        self.batch_files = [f for f in self.batch_files if f['path'] not in paths_to_remove]
        for item in sel:
            self.tree_batch.delete(item)
        # Đánh số lại
        for i, item in enumerate(self.tree_batch.get_children(), 1):
            vals = self.tree_batch.item(item, 'values')
            self.tree_batch.item(item, values=(i, vals[1], vals[2], vals[3]))
        self.lbl_batch_count.config(text=f"{len(self.batch_files)} file")

    def clear_all_batch(self):
        """Xóa toàn bộ danh sách file hàng loạt."""
        self.batch_files.clear()
        for item in self.tree_batch.get_children():
            self.tree_batch.delete(item)
        self.lbl_batch_count.config(text="0 file")

    def choose_out_dir(self):
        """Chọn thư mục xuất kết quả cho chế độ hàng loạt."""
        folder = filedialog.askdirectory()
        if folder:
            self.txt_out_dir.delete(0, tk.END)
            self.txt_out_dir.insert(0, folder)

    def _open_out_dir(self):
        """Mở thư mục kết quả gần nhất bằng Explorer."""
        out = getattr(self, '_last_out_dir', None) or self.txt_out_dir.get().strip()
        if out and os.path.isdir(out):
            subprocess.Popen(f'explorer "{os.path.normpath(out)}"')
        else:
            messagebox.showinfo("Th\u00f4ng b\u00e1o", "Th\u01b0 m\u1ee5c xu\u1ea5t ch\u01b0a \u0111\u01b0\u1ee3c ch\u1ecdn ho\u1eb7c kh\u00f4ng t\u1ed3n t\u1ea1i.")

    def _stop_batch(self):
        """Bật cờ dừng để vòng lặp hàng loạt kết thúc sau file hiện tại."""
        self._batch_stop_flag = True
        self.log_batch(">>> \u0110\u00e3 g\u1eedi t\u00edn hi\u1ec7u D\u1eebng. Ch\u1edd file hi\u1ec7n t\u1ea1i ho\u00e0n th\u00e0nh...", tag="err")

    def log_batch(self, msg, tag="info"):
        """Ghi một dòng log vào ô log hàng loạt (kèm tag màu) và cuộn xuống cuối."""
        self.txt_batch_log.insert(tk.END, msg + "\n", tag)
        self.txt_batch_log.see(tk.END)
        self.root.update_idletasks()

    def update_batch_status(self, index, status):
        """Cập nhật trạng thái 1 file trong bảng hàng loạt và đổi màu tag tương ứng."""
        self.batch_files[index]['status'] = status
        items = self.tree_batch.get_children()
        if index >= len(items):
            return
        item = items[index]
        vals = self.tree_batch.item(item, 'values')
        tag_map = {"Xong": "done", "Ch\u1edd": "wait", "\u0110ang ch\u1ea1y...": "running",
                   "Kh\u00f4ng \u0110\u1ea1t": "fail", "L\u1ed7i": "fail"}
        tag = tag_map.get(status, "wait")
        self.tree_batch.item(item, values=(vals[0], vals[1], vals[2], status), tags=(tag,))
        self.root.update_idletasks()

    # ========================================================================
    # TAB 2 - HÀNG LOẠT: LOGIC CHẠY & XUẤT KẾT QUẢ
    # ========================================================================
    def run_batch(self):
        """Chạy tối ưu hàng loạt trên thread nền: với mỗi file, đọc đầu vào, đánh
        giá bằng MCOC + NSGA-II rồi xuất PNG/Excel/PDF; cuối cùng gộp PDF và tổng kết."""
        from io_handlers.export_utils import export_excel, export_pdf, export_png

        if not self.batch_files:
            messagebox.showwarning("C\u1ea3nh b\u00e1o", "Ch\u01b0a c\u00f3 file n\u00e0o trong danh s\u00e1ch.")
            return

        # BẮT BUỘC MCOC — chế độ Hàng loạt cũng đánh giá chính xác như Tab 1,
        # không chấp nhận phương án xấp xỉ (bệ cứng).
        exe = self.params['exe_path'].get().strip()
        if not exe or not os.path.exists(exe):
            messagebox.showwarning(
                "C\u1ea7n c\u1ea5u h\u00ecnh MCOC",
                "Ch\u1ebf \u0111\u1ed9 H\u00e0ng lo\u1ea1t \u0111\u00e1nh gi\u00e1 m\u1ecdi ph\u01b0\u01a1ng \u00e1n b\u1eb1ng MCOC (ch\u00ednh x\u00e1c).\n"
                "H\u00e3y ch\u1ecdn \u0111\u01b0\u1eddng d\u1eabn MCOC Batch \u1edf Tab 1, m\u1ee5c \"C\u1ea5u h\u00ecnh MCOC (b\u1eaft bu\u1ed9c)\".")
            return

        global_out_dir = self.txt_out_dir.get().strip()   # có thể rỗng

        def task():
            from core.nsga2_optimizer import run_nsga2
            from io_handlers.mcoc_writer import self_check
            self._batch_stop_flag = False
            self.btn_run_batch.config(state=tk.DISABLED)
            self.btn_stop_batch.config(state=tk.NORMAL)
            self.btn_open_out.config(state="disabled")
            self.progress_bar["maximum"] = len(self.batch_files)
            self.progress_bar["value"] = 0

            prefix_str = self.txt_prefix.get().strip()
            suffix_str = self.txt_suffix.get().strip()

            self.log_batch("=" * 55, "title")
            self.log_batch(f"  B\u1eaet \u0111\u1ea7u ch\u1ea1y h\u00e0ng lo\u1ea1t: {len(self.batch_files)} file", "title")
            self.log_batch("=" * 55, "title")

            n_ok = n_fail = n_err = 0
            generated_pdfs = []
            last_out_dir = global_out_dir

            for i, f in enumerate(self.batch_files):
                if self._batch_stop_flag:
                    self.log_batch(">>> D\u1eebng theo y\u00eau c\u1ea7u ng\u01b0\u1eddi d\u00f9ng.", "err")
                    break

                filepath = f['path']
                filename = os.path.basename(filepath)
                # Thư mục xuất: nếu để trống thì là cùng thư mục file đầu vào
                out_dir = global_out_dir or os.path.dirname(filepath)
                last_out_dir = out_dir

                raw_stem  = filename.rsplit('.', 1)[0]
                safe_stem = to_safe_filename(raw_stem) or raw_stem
                file_prefix = f"{prefix_str}{safe_stem}{suffix_str}"

                self.update_batch_status(i, "\u0110ang ch\u1ea1y...")
                self.log_batch(f"\n[{i+1}/{len(self.batch_files)}] {filename}", "info")

                try:
                    params, loads, proj_name = parse_input_file(filepath)

                    # ── Sửa bug: SAFE_D phải được thiết lập đồng bộ với D_PILE ──────
                    d_pile = params.get('D_PILE', 1.0)
                    params['SAFE_D'] = d_pile   # Buộc cài — phòng fallback sai trong optimizer

                    # ── Ghi đè thông số từ Tab 1 nếu người dùng bật tùy chọn ─────
                    if self.var_override_params.get():
                        params['D_PILE']    = self._pget('D_PILE')
                        params['P_LIMIT']   = self._pget('P_LIMIT')
                        params['P_TENSION'] = self._pget('P_TENSION')
                        params['M_LIMIT']   = self._pget('M_LIMIT')
                        params['SAFE_D']    = self._pget('D_PILE')  # cập nhật lại sau khi ghi đè

                    # BẮT BUỘC MCOC — theo luồng chính (Tab 1): đánh giá chính xác
                    params['exe_path']        = exe
                    params['input_filepath']  = filepath
                    params['mock_mode']       = False
                    params['result_filepath'] = filepath

                    # Kiểm tra dữ liệu đầu vào tối thiểu
                    if not loads:
                        raise ValueError("File kh\u00f4ng c\u00f3 t\u1ed5 h\u1ee3p t\u1ea3i tr\u1ecdng n\u00e0o.")
                    if 'L_X' not in params or 'L_Y' not in params:
                        raise ValueError("File thi\u1ebfu k\u00edch th\u01b0\u1edbc b\u1ec7 (L_X, L_Y).")
                    if not params.get('original_coords'):
                        raise ValueError("File kh\u00f4ng c\u00f3 t\u1ecda \u0111\u1ed9 c\u1ecdc g\u1ed1c \u0111\u1ec3 l\u00e0m template MCOC.")

                    # Kiểm tra template MCOC khớp với toạ độ gốc
                    ok_tpl, msg_tpl = self_check(filepath, params['original_coords'])
                    if not ok_tpl:
                        raise ValueError("Template MCOC l\u1ed7i: " + msg_tpl)

                    self.log_batch(
                        f"  L_X={params['L_X']:.2f}m  L_Y={params['L_Y']:.2f}m  "
                        f"d={params.get('D_PILE',0):.2f}m  Po={params.get('P_LIMIT',0):.0f}T  "
                        f"Loads={len(loads)}  [MCOC chinh xac]", "info"
                    )

                    # Đánh giá bằng MCOC exact + tối ưu NSGA-II (cùng luồng Tab 1)
                    _blog = lambda m: self.log_batch("    " + m, "info")
                    evaluator = MCOCBlackbox.make_real_evaluator(params, loads=loads, log=_blog)
                    orig_coords = np.array(params['original_coords'], dtype=float)
                    orig_res = evaluator(orig_coords)   # chấm phương án gốc để so sánh
                    results = run_nsga2(params, loads, evaluator=evaluator,
                                        pop_size=16, n_gen=10, max_evals=50,
                                        secondary=self.var_secondary.get(), log=_blog)

                    P_LIMIT = params.get('P_LIMIT', 500.0)
                    results['original_config'] = {
                        'type': 'Goc', 'n': len(orig_coords), 'coords': orig_coords,
                        'pmax': orig_res.get('pmax', 0), 'pmin': orig_res.get('pmin', 0),
                        'mxmax': orig_res.get('mxmax', 0), 'mymax': orig_res.get('mymax', 0),
                        'ok': orig_res.get('pmax', 1e9) <= P_LIMIT, 'msg': 'Phuong an goc (MCOC)',
                    }
                    rec       = results.get('recommended')
                    orig      = results.get('original_config')
                    all_valid = results.get('all_valid_configs', [])

                    # Log phương án gốc (nếu có)
                    if orig:
                        orig_status = "\u0110\u1ea0T" if orig['ok'] else "KH\u00d4NG \u0110\u1ea0T"
                        self.log_batch(
                            f"  Phuong an goc ({orig['n']} coc): {orig_status}  "
                            f"Pmax={orig['pmax']:.1f}T", "info"
                        )

                    if rec:
                        # Xuất file
                        if not os.path.exists(out_dir):
                            os.makedirs(out_dir)

                        self.plot_canvas.draw_simulation(rec['coords'], params)

                        png_path = None
                        if self.var_export_png.get() or self.var_export_pdf.get():
                            png_path = export_png(
                                self.plot_canvas, rec['coords'], params, out_dir, file_prefix)

                        if self.var_export_excel.get():
                            export_excel(rec, loads, params, out_dir, file_prefix)

                        if self.var_export_pdf.get():
                            pdf_path = export_pdf(rec, loads, params, out_dir, file_prefix, png_path)
                            generated_pdfs.append(pdf_path)

                        self.log_batch(
                            f"  -> OK  Kieu {rec['type']} ({rec['n']} coc)  "
                            f"Pmax={rec['pmax']:.1f}T  [ti\u1ebft ki\u1ec7m so v\u1edbi {orig['n'] if orig else '?'} coc goc]",
                            "ok"
                        )
                        self.update_batch_status(i, "Xong")
                        n_ok += 1
                    else:
                        reason = results.get('reason', 'Kh\u00f4ng r\u00f5')
                        valid_count = len(all_valid)
                        self.log_batch(
                            f"  -> KHONG DAT  (valid={valid_count})  Ly do: {reason}", "err")
                        # Log thêm chi tiết nếu không có phương án nào đạt
                        if valid_count == 0 and results.get('all_candidates'):
                            sample = results['all_candidates'][:3]
                            for c in sample:
                                self.log_batch(
                                    f"     Vi du: kieu {c['type']} {c['nx']}x{c['ny']}  "
                                    f"Pmax={c['pmax']:.1f}T  -> {c.get('msg','')[:60]}", "err"
                                )
                        self.update_batch_status(i, "Kh\u00f4ng \u0110\u1ea1t")
                        n_fail += 1

                except Exception as e:
                    import traceback
                    self.log_batch(f"  -> LOI: {str(e)}", "err")
                    self.log_batch(traceback.format_exc()[-300:], "err")
                    self.update_batch_status(i, "L\u1ed7i")
                    n_err += 1

                # Cập nhật progress
                done = i + 1
                self.progress_bar["value"] = done
                self.lbl_progress.config(text=f"{done}/{len(self.batch_files)} Ho\u00e0n th\u00e0nh")

            # Gộp PDF
            if self.var_merge_pdf.get() and generated_pdfs:
                try:
                    self.log_batch("\nDang gop file PDF...", "info")
                    from PyPDF2 import PdfMerger
                    merger = PdfMerger()
                    for pdf in generated_pdfs:
                        merger.append(pdf)
                    merged_name = f"{prefix_str}MCOC_tong_hop{suffix_str}.pdf"
                    merged_path = os.path.join(last_out_dir, merged_name)
                    merger.write(merged_path)
                    merger.close()
                    self.log_batch(f"Da gop PDF: {merged_name}", "ok")
                except Exception as e:
                    self.log_batch(f"Loi gop PDF: {str(e)}", "err")

            # Tổng kết
            total = n_ok + n_fail + n_err
            self.log_batch("\n" + "=" * 55, "title")
            self.log_batch(
                f"  HOAN THANH: {n_ok}/{total} OK, {n_fail} khong dat, {n_err} loi", "title")
            if last_out_dir:
                self.log_batch(f"  Ket qua: {last_out_dir}", "title")
            self.log_batch("=" * 55, "title")

            self.lbl_batch_status.config(text=f"Xong: {n_ok} OK / {n_fail} kh\u00f4ng \u0111\u1ea1t / {n_err} l\u1ed7i.")
            self.btn_run_batch.config(state=tk.NORMAL)
            self.btn_stop_batch.config(state=tk.DISABLED)
            if last_out_dir and os.path.isdir(last_out_dir):
                self._last_out_dir = last_out_dir
                self.btn_open_out.config(state="normal")

        threading.Thread(target=task, daemon=True).start()
