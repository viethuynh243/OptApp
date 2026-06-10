import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import DND_FILES
from core.optimizer import run_optimization
from core.mechanics import check_layout
from core.generator import generate_coords
from io_handlers.file_io import parse_input_file, export_output_file
from ui.plot_canvas import PlotCanvas
import unicodedata
import re as _re


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

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Tối Ưu Hóa Bố Trí Cọc Móng Cầu (Modular)")
        self.root.geometry("1100x750")
        
        # Biến hệ thống
        self.params = {
            'L_X': tk.DoubleVar(value=6.0),
            'L_Y': tk.DoubleVar(value=9.6),
            'D_PILE': tk.DoubleVar(value=1.2),
            'P_LIMIT': tk.DoubleVar(value=500.0),
            'P_TENSION': tk.DoubleVar(value=0.0),
            'M_LIMIT': tk.DoubleVar(value=0.0), # 0 = không kiểm tra (T.m)
            'exe_path': tk.StringVar(value=''),
            'mock_mode': tk.BooleanVar(value=True)
        }
        # Cờ xuất file (chỉ dùng trong save_file)
        self.var_export_cti = tk.BooleanVar(value=False)
        
        self.loads = []
        self.current_config = None
        
        self.setup_ui()
        self.add_default_loads()
        
        # Drag and drop support
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)
        
    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tab_interactive = tk.Frame(self.notebook)
        self.notebook.add(self.tab_interactive, text="1. Tương tác (Interactive)")
        self.setup_interactive_ui(self.tab_interactive)
        
        self.tab_batch = tk.Frame(self.notebook)
        self.notebook.add(self.tab_batch, text="2. Hàng loạt (Batch Mode)")
        self.setup_batch_ui(self.tab_batch)
        
    def setup_interactive_ui(self, parent_frame):
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
        ttk.Button(frame_io, text="Kéo thả File hoặc Chọn Input (1 File)", command=self.load_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(frame_io, text="Xóa Tải trọng", command=self.clear_loads).pack(side=tk.LEFT, fill=tk.X, expand=False, padx=2)
        ttk.Button(frame_io, text="Xuất Kết Quả", command=self.save_file).pack(side=tk.RIGHT, fill=tk.X, expand=False, padx=2)
        
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
        
        # Loads
        frame_loads = tk.LabelFrame(tab_params, text="Tổ hợp Tải trọng", padx=10, pady=5)
        frame_loads.pack(fill=tk.BOTH, expand=True, pady=5)
        
        cols = ("TH", "Hx", "Hy", "P", "Mx", "My", "Mz")
        self.tree_loads = ttk.Treeview(frame_loads, columns=cols, show="headings", height=5)
        col_cfg = {
            "TH":  ("#",       35),
            "Hx":  ("Hx(kN)",  60),
            "Hy":  ("Hy(kN)",  60),
            "P":   ("P(kN)",   65),
            "Mx":  ("Mx(kNm)", 70),
            "My":  ("My(kNm)", 70),
            "Mz":  ("Mz(kNm)", 70),
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
        ttk.Button(frame_load_btns, text="+ Thêm tổ hợp",  command=self.add_load_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="✎ Sửa chọn",    command=self.edit_load).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="✕ Xóa chọn",    command=self.delete_load).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="Nhập từ CSV",    command=self.paste_loads_csv).pack(side=tk.RIGHT, padx=2)
        
        # --- ĐIỀU KHIỂN & KẾT QUẢ TỐI ƯU ---
        frame_run = tk.LabelFrame(tab_params, text="Điều Khiển Tối Ưu", padx=10, pady=5)
        frame_run.pack(fill=tk.X, pady=5)
        
        self.output_option = tk.StringVar(value="BEST")
        ttk.Radiobutton(frame_run, text="Chỉ xuất tối ưu", variable=self.output_option, value="BEST").pack(side=tk.LEFT)
        ttk.Radiobutton(frame_run, text="Xuất tất cả", variable=self.output_option, value="ALL").pack(side=tk.LEFT, padx=10)
        
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
        self.cb_load_case = ttk.Combobox(frame_sim, state="readonly", width=15)
        self.cb_load_case.pack(side=tk.LEFT, padx=5)
        self.cb_load_case.bind("<<ComboboxSelected>>", self.update_simulation)
        
        self.plot_canvas = PlotCanvas(right_frame)
        self.plot_canvas.widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
    def add_default_loads(self):
        self.loads = [{'Hx': 0.0, 'Hy': 0.0, 'N': 2577.0, 'Mx': 1500.0, 'My': 1500.0, 'Mz': 0.0}]
        self.refresh_loads_ui()
        
    def refresh_loads_ui(self):
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
            ("Hx (kN) — lực ngang X",  "Hx",  0.0),
            ("Hy (kN) — lực ngang Y",  "Hy",  0.0),
            ("P  (kN) — lực đứng",     "N",   0.0),
            ("Mx (kNm) — momen trục X","Mx",  0.0),
            ("My (kNm) — momen trục Y","My",  0.0),
            ("Mz (kNm) — momen xoắn",  "Mz",  0.0),
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
            
    def get_params_dict(self):
        d = {k: v.get() for k, v in self.params.items()}
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
        return d


    def browse_exe(self):
        filepath = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")])
        if filepath:
            self.txt_exe_path.delete(0, tk.END)
            self.txt_exe_path.insert(0, filepath)

    def load_file(self):
        filepaths = filedialog.askopenfilenames(filetypes=[
            ("All Supported Files", "*.csv;*.txt"), 
            ("Text Files", "*.txt"),
            ("CSV Files", "*.csv"), 
            ("All Files", "*.*")
        ])
        if filepaths:
            self.process_multiple_files(filepaths)
            
    def handle_drop(self, event):
        filepath = event.data
        
        import re
        # Lấy danh sách các file (xử lý trường hợp kéo thả nhiều file)
        # Các file có dấu cách thường được bọc trong ngoặc nhọn {}
        paths = re.findall(r'{[^}]+}|[^{ ]+', filepath)
        if not paths: return
        
        filepaths = [p.strip('{}') for p in paths]
        self.process_multiple_files(filepaths)
        
    def process_multiple_files(self, filepaths):
        success_count = 0
        total_new_loads = 0
        last_proj_name = ""
        
        for filepath in filepaths:
            try:
                params, loads, proj_name = parse_input_file(filepath)
                
                # Cập nhật tất cả thông số từ file lên UI
                keys_to_update = ['L_X', 'L_Y', 'D_PILE', 'P_LIMIT', 'P_TENSION']
                for k in keys_to_update:
                    if k in params and params[k] > 0:
                        self.params[k].set(params[k])
                            
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
            # Reset ket qua cu — du lieu moi, ket qua moi
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

            # Xóa bớt mô phỏng cũ đi, để trống màn hình chờ người dùng ấn Tối Ưu
            self.plot_canvas.draw_simulation([], self.get_params_dict())

            
    def clear_loads(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa toàn bộ danh sách tổ hợp tải trọng không?"):
            self.loads = []
            self.refresh_loads_ui()
            
            # Reset UI như lúc load file mới
            self.current_config = None
            self.txt_result.delete(1.0, tk.END)
            self.cb_config.set('')
            self.cb_config['values'] = []
            self.plot_canvas.draw_simulation([], self.get_params_dict())

    def save_file(self):
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
            import os
            base_dir  = os.path.dirname(filepath)
            base_name = os.path.splitext(os.path.basename(filepath))[0]

            # 1. Xuất file TXT kết quả
            export_output_file(
                filepath,
                self.current_config,
                self.get_params_dict(),
                self.loads,
                getattr(self, 'project_name', 'Du An Toi Uu Coc'),
                self.output_option.get()
            )

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

            messagebox.showinfo(
                "Thành công",
                f"Đã xuất:\n• {os.path.basename(filepath)}\n"
                + "\n".join(f"• {os.path.basename(p)}" for p in exported_imgs)
            )
        except Exception as e:
            import traceback
            messagebox.showerror("Lỗi", f"Không thể xuất file: {str(e)}\n\n{traceback.format_exc()[-300:]})")

    def run_optimize(self):
        self.txt_result.delete(1.0, tk.END)
        self.txt_result.insert(tk.END, "Dang tim kiem...\n")
        self.root.update()
        
        results = run_optimization(self.get_params_dict(), self.loads)
        self.current_config = results
        self.txt_result.delete(1.0, tk.END)
        
        P_LIMIT = self.params['P_LIMIT'].get()
        P_TENSION = self.params['P_TENSION'].get()
        
        # --- Phan 1: Trang thai phuong an goc ---
        orig = results.get('original_config')
        if orig:
            status = "DAT" if orig['ok'] else "KHONG DAT"
            self.txt_result.insert(tk.END, f"=== PHUONG AN GOC TRONG FILE ({status}) ===\n")
            self.txt_result.insert(tk.END, f"  So coc: {orig['n']}\n")
            self.txt_result.insert(tk.END, f"  Pmax = {orig['pmax']:.2f} T  (Gioi han: {P_LIMIT:.0f} T)\n")
            self.txt_result.insert(tk.END, f"  Pmin = {orig['pmin']:.2f} T  (Gioi han chiu nho: -{P_TENSION:.0f} T)\n")
            mmax_orig = max(orig.get('mxmax',0), orig.get('mymax',0))
            if self.params['M_LIMIT'].get() > 0:
                self.txt_result.insert(tk.END, f"  Mmax = {mmax_orig:.2f} T.m  (Gioi han uon: {self.params['M_LIMIT'].get():.0f} T.m)\n")
            else:
                self.txt_result.insert(tk.END, f"  Mmax = {mmax_orig:.2f} T.m  (Khong kiem tra uon)\n")
            if not orig['ok']:
                self.txt_result.insert(tk.END, f"  >> Ly do: {orig['msg']}\n")
            self.txt_result.insert(tk.END, "\n")
        
        # --- Phan 2: Ket qua kiem tra toan bo khong gian ---
        all_cands = results.get('all_candidates', [])
        if self.output_option.get() == "BEST":
            all_cands = [c for c in all_cands if c['ok']]
            
        if all_cands:
            self.txt_result.insert(tk.END, f"=== KIEM TRA TOAN BO LUOI PHAN BO ({len(all_cands)} phuong an) ===\n")
            self.txt_result.insert(tk.END, f"{'Kieu':<5} {'nx':>3} {'ny':>3} {'n':>4} {'sx':>6} {'sy':>6} {'Pmax':>8} {'Pmin':>8} {'Mmax':>8}  {'Trang thai'}\n")
            self.txt_result.insert(tk.END, "-" * 75 + "\n")
            for c in all_cands:
                status_str = "DAT" if c['ok'] else "KHONG DAT"
                # Hiển thị toàn bộ lý do (msg) để đảm bảo tính đồng nhất
                clean_msg = c['msg'].replace('Không đạt: ', '') if c['msg'] else ""
                reason_str = "" if c['ok'] else f"  <- {clean_msg}"
                mmax_val = max(c.get('mxmax', 0), c.get('mymax', 0))
                self.txt_result.insert(tk.END,
                    f"  {c['type']:<4} {c['nx']:>3} {c['ny']:>3} {c['n']:>4} "
                    f"{c['sx']:>6.2f} {c['sy']:>6.2f} {c['pmax']:>8.1f} {c['pmin']:>8.1f} {mmax_val:>8.1f}  "
                    f"{status_str}{reason_str}\n"
                )
            self.txt_result.insert(tk.END, "\n")
        else:
            self.txt_result.insert(tk.END, "Khong co phuong an luoi nao hop le trong kich thuoc be nay.\n\n")
        
        # --- Phan 3: Ket luan ---
        rec = results.get('recommended')
        if rec:
            self.txt_result.insert(tk.END, "=== PHUONG AN KIEN NGHI ===\n")
            if rec['type'] == 'Goc':
                self.txt_result.insert(tk.END, f"  >> Giu nguyen phuong an goc ({rec['n']} coc)\n")
            else:
                type_str = "Truc giao" if rec['type'] == 'A' else "So le"
                self.txt_result.insert(tk.END, f"  >> Kieu {rec['type']} ({type_str}): {rec['nx']}x{rec['ny']} = {rec['n']} coc\n")
                self.txt_result.insert(tk.END, f"     sx = {rec['sx']:.2f} m, sy = {rec['sy']:.2f} m\n")
            self.txt_result.insert(tk.END, f"     Pmax = {rec['pmax']:.2f} T\n")
            self.txt_result.insert(tk.END, f"     Pmin = {rec['pmin']:.2f} T\n")
            if self.params['M_LIMIT'].get() > 0:
                self.txt_result.insert(tk.END, f"     Mmax = {max(rec.get('mxmax',0), rec.get('mymax',0)):.2f} T.m\n")
            else:
                self.txt_result.insert(tk.END, f"     Mmax = {max(rec.get('mxmax',0), rec.get('mymax',0)):.2f} T.m\n")
            self.txt_result.insert(tk.END, f"  Ly do: {results.get('reason', '')}\n")
            
            self.populate_comboboxes(results)
        else:
            self.txt_result.insert(tk.END, "=== KET LUAN ===\n")
            self.txt_result.insert(tk.END, f"  {results.get('reason', 'Khong tim thay phuong an nao thoa man.')}\n")
            # Van populate comboboxes va ve mo phong cho phuong an goc (du KHONG DAT)
            self.populate_comboboxes(results)

    def update_simulation(self, event=None):
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
        
        import numpy as np
        coords = np.array(selected_cfg['coords'])  # Ep ve numpy array, xu ly ca list lan array
        if coords.ndim != 2 or coords.shape[0] == 0: return
        
        n_piles = len(coords)
        forces = None
        
        calibration_factor = 1.0
        params_dict = self.get_params_dict()
        orig_pmax_actual = params_dict.get('orig_pmax', 519.63)
            
        if hasattr(self, 'original_coords') and self.original_coords and self.loads:
            from core.blackbox import MCOCBlackbox
            orig_arr = np.array(self.original_coords)
            orig_rigid_pmax = MCOCBlackbox._rigid_cap_pmax(orig_arr, self.loads)
            if orig_rigid_pmax > 0:
                calibration_factor = orig_pmax_actual / orig_rigid_pmax
        
        # Luon tinh forces bang mo hinh be cung - ke ca khi KHONG DAT
        if self.loads and len(self.loads) > 0:
            load_idx = min(idx_load, len(self.loads) - 1)
            load = self.loads[load_idx]
            N  = load.get('N', 0)
            Mx = load.get('Mx', 0)
            My = load.get('My', 0)
            
            cg_x = float(np.mean(coords[:, 0]))
            cg_y = float(np.mean(coords[:, 1]))
            I_x = float(np.sum((coords[:, 1] - cg_y)**2)) or 1e-9
            I_y = float(np.sum((coords[:, 0] - cg_x)**2)) or 1e-9
            
            forces = []
            for (x, y) in coords:
                dx = x - cg_x
                dy = y - cg_y
                p = N / n_piles + Mx * dy / I_x + My * dx / I_y
                forces.append(p * calibration_factor)
                
        mxmax = selected_cfg.get('mxmax', 0)
        mymax = selected_cfg.get('mymax', 0)
            
        self.plot_canvas.draw_simulation(coords, self.get_params_dict(), forces, m_forces=(mxmax, mymax))
        
    def populate_comboboxes(self, results):
        cases = [f"Tổ hợp {i+1}" for i in range(len(self.loads))]
        self.cb_load_case['values'] = cases
        if cases:
            self.cb_load_case.current(0)
            
        config_names = []
        if results.get('original_config'):
            config_names.append("Phương án gốc")
            
        config_names.append("Phương án đề xuất")
        
        for i in range(len(results.get('all_valid_configs', []))):
            config_names.append(f"Phương án {i+1}")
            
        self.cb_config['values'] = config_names
        if config_names:
            # Uu tien hien Phuong an de xuat; neu khong co, hien Phuong an goc
            if "Ph\u01b0\u01a1ng \u00e1n \u0111\u1ec1 xu\u1ea5t" in config_names and results.get('recommended'):
                self.cb_config.set("Ph\u01b0\u01a1ng \u00e1n \u0111\u1ec1 xu\u1ea5t")
            elif "Ph\u01b0\u01a1ng \u00e1n g\u1ed1c" in config_names:
                self.cb_config.set("Ph\u01b0\u01a1ng \u00e1n g\u1ed1c")
            else:
                self.cb_config.current(0)
                
        self.update_simulation()

    # ================= BATCH MODE =================

    def setup_batch_ui(self, parent_frame):
        """Giao di\u1ec7n Tab 2 \u2014 thi\u1ebft k\u1ebf theo layout MCOC."""
        # \u2500\u2500 Toolbar tr\u00ean c\u00f9ng \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        toolbar = tk.Frame(parent_frame, pady=4, padx=6)
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text="Th\u00eam file",    command=self.load_file_batch).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Th\u00eam th\u01b0 m\u1ee5c", command=self.load_folder_batch).pack(side=tk.LEFT, padx=3)
        tk.Label(toolbar, text="K\u00e9o th\u1ea3 nhi\u1ec1u file ho\u1eb7c th\u01b0 m\u1ee5c v\u00e0o v\u00f9ng d\u1eef li\u1ec7u \u0111\u1ea7u v\u00e0o.",
                 fg="#555").pack(side=tk.RIGHT, padx=6)

        # \u2500\u2500 Body: chia \u0111\u00f4i tr\u00e1i / ph\u1ea3i \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        body = ttk.PanedWindow(parent_frame, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))

        # \u2500\u2500 Panel tr\u00e1i: Danh s\u00e1ch file \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
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
        # M\u00e0u tag tr\u1ea1ng th\u00e1i
        self.tree_batch.tag_configure("done",    foreground="#27ae60")
        self.tree_batch.tag_configure("running", foreground="#2980b9")
        self.tree_batch.tag_configure("fail",    foreground="#e74c3c")
        self.tree_batch.tag_configure("wait",    foreground="#7f8c8d")

        sb_b = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree_batch.yview)
        self.tree_batch.configure(yscrollcommand=sb_b.set)
        self.tree_batch.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_b.pack(side=tk.RIGHT, fill=tk.Y)

        # Footer \u0111\u1ebfm file + n\u00fat x\u00f3a
        foot = tk.Frame(left)
        foot.pack(fill=tk.X, pady=(4, 0))
        self.lbl_batch_count = tk.Label(foot, text="0 file", fg="#555")
        self.lbl_batch_count.pack(side=tk.LEFT)
        ttk.Button(foot, text="X\u00f3a ch\u1ecdn", command=self.delete_selected_batch).pack(side=tk.RIGHT, padx=3)
        ttk.Button(foot, text="X\u00f3a t\u1ea5t c\u1ea3",  command=self.clear_all_batch).pack(side=tk.RIGHT, padx=3)

        # Drag-drop v\u00e0o danh s\u00e1ch
        self.tree_batch.drop_target_register(DND_FILES)
        self.tree_batch.dnd_bind("<<Drop>>", self._batch_drop)

        # \u2500\u2500 Panel ph\u1ea3i: Thi\u1ebft l\u1eadp ch\u1ea1y \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        right = tk.LabelFrame(body, text="Thi\u1ebft l\u1eadp ch\u1ea1y", padx=8, pady=6)
        body.add(right, weight=2)

        # Th\u01b0 m\u1ee5c xu\u1ea5t k\u1ebft qu\u1ea3
        tk.Label(right, text="Th\u01b0 m\u1ee5c xu\u1ea5t k\u1ebft qu\u1ea3", font=("", 9, "bold"), anchor="w").pack(fill=tk.X)
        dir_f = tk.Frame(right)
        dir_f.pack(fill=tk.X, pady=(2, 0))
        self.txt_out_dir = tk.Entry(dir_f)
        self.txt_out_dir.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_f, text="Ch\u1ecdn...", command=self.choose_out_dir).pack(side=tk.LEFT, padx=4)
        tk.Label(right, text="\u0110\u1ec3 tr\u1ed1ng: k\u1ebft qu\u1ea3 l\u01b0u c\u00f9ng th\u01b0 m\u1ee5c t\u1eebng file \u0111\u1ea7u v\u00e0o.",
                 fg="#888", font=("", 8)).pack(anchor="w")

        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, pady=6)

        # Tab xu\u1ea5t (Xu\u1ea5t k\u1ebft qu\u1ea3 / Thi\u1ebft l\u1eadp n\u00e2ng cao)
        nb_right = ttk.Notebook(right)
        nb_right.pack(fill=tk.BOTH, expand=True)

        tab_export = tk.Frame(nb_right, padx=6, pady=6)
        nb_right.add(tab_export, text="Xu\u1ea5t k\u1ebft qu\u1ea3")

        tab_adv = tk.Frame(nb_right, padx=6, pady=6)
        nb_right.add(tab_adv, text="N\u00e2ng cao")

        # Tab xu\u1ea5t k\u1ebft qu\u1ea3
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

        # Tab n\u00e2ng cao
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

        # \u2500\u2500 Ti\u1ebfn tr\u00ecnh: progress bar + log \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
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

        # Tag m\u00e0u log
        self.txt_batch_log.tag_configure("ok",    foreground="#4ec9b0")
        self.txt_batch_log.tag_configure("err",   foreground="#f44747")
        self.txt_batch_log.tag_configure("info",  foreground="#9cdcfe")
        self.txt_batch_log.tag_configure("title", foreground="#dcdcaa", font=("Consolas", 9, "bold"))

        # \u2500\u2500 Status bar \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
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

    # \u2500\u2500 Batch helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    def _batch_drop(self, event):
        import re, os
        paths = re.findall(r'\{[^}]+\}|[^{ ]+', event.data)
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
        fps = filedialog.askopenfilenames(
            filetypes=[("Text / CSV Files", "*.txt *.csv"), ("All Files", "*.*")])
        self.add_files_to_batch(fps)

    def load_folder_batch(self):
        import os
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
        import os
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
        sel = self.tree_batch.selection()
        if not sel:
            return
        # X\u00e1c \u0111\u1ecbnh t\u1eadp \u0111\u01b0\u1eddng d\u1eabn c\u1ea7n x\u00f3a
        paths_to_remove = set()
        for item in sel:
            vals = self.tree_batch.item(item, 'values')
            fname = vals[1]; fdir = vals[2]
            import os
            paths_to_remove.add(os.path.join(str(fdir), str(fname)))
        self.batch_files = [f for f in self.batch_files if f['path'] not in paths_to_remove]
        for item in sel:
            self.tree_batch.delete(item)
        # \u0110\u00e1nh s\u1ed1 l\u1ea1i
        for i, item in enumerate(self.tree_batch.get_children(), 1):
            vals = self.tree_batch.item(item, 'values')
            self.tree_batch.item(item, values=(i, vals[1], vals[2], vals[3]))
        self.lbl_batch_count.config(text=f"{len(self.batch_files)} file")

    def clear_all_batch(self):
        self.batch_files.clear()
        for item in self.tree_batch.get_children():
            self.tree_batch.delete(item)
        self.lbl_batch_count.config(text="0 file")

    def choose_out_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.txt_out_dir.delete(0, tk.END)
            self.txt_out_dir.insert(0, folder)

    def _open_out_dir(self):
        import os, subprocess
        out = getattr(self, '_last_out_dir', None) or self.txt_out_dir.get().strip()
        if out and os.path.isdir(out):
            subprocess.Popen(f'explorer "{os.path.normpath(out)}"')
        else:
            from tkinter import messagebox
            messagebox.showinfo("Th\u00f4ng b\u00e1o", "Th\u01b0 m\u1ee5c xu\u1ea5t ch\u01b0a \u0111\u01b0\u1ee3c ch\u1ecdn ho\u1eb7c kh\u00f4ng t\u1ed3n t\u1ea1i.")

    def _stop_batch(self):
        self._batch_stop_flag = True
        self.log_batch(">>> \u0110\u00e3 g\u1eedi t\u00edn hi\u1ec7u D\u1eebng. Ch\u1edd file hi\u1ec7n t\u1ea1i ho\u00e0n th\u00e0nh...", tag="err")

    def log_batch(self, msg, tag="info"):
        self.txt_batch_log.insert(tk.END, msg + "\n", tag)
        self.txt_batch_log.see(tk.END)
        self.root.update_idletasks()

    def update_batch_status(self, index, status):
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

    # \u2500\u2500 Logic ch\u1ea1y h\u00e0ng lo\u1ea1t \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    def run_batch(self):
        import os, threading
        from core.optimizer import run_optimization
        from io_handlers.file_io import parse_input_file
        from io_handlers.export_utils import export_excel, export_pdf, export_png

        if not self.batch_files:
            messagebox.showwarning("C\u1ea3nh b\u00e1o", "Ch\u01b0a c\u00f3 file n\u00e0o trong danh s\u00e1ch.")
            return

        global_out_dir = self.txt_out_dir.get().strip()   # c\u00f3 th\u1ec3 r\u1ed7ng

        def task():
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
                # Th\u01b0 m\u1ee5c xu\u1ea5t: n\u1ebfu \u0111\u1ec3 tr\u1ed1ng th\u00ec l\u00e0 c\u00f9ng th\u01b0 m\u1ee5c file \u0111\u1ea7u v\u00e0o
                out_dir = global_out_dir or os.path.dirname(filepath)
                last_out_dir = out_dir

                raw_stem  = filename.rsplit('.', 1)[0]
                safe_stem = to_safe_filename(raw_stem) or raw_stem
                file_prefix = f"{prefix_str}{safe_stem}{suffix_str}"

                self.update_batch_status(i, "\u0110ang ch\u1ea1y...")
                self.log_batch(f"\n[{i+1}/{len(self.batch_files)}] {filename}", "info")

                try:
                    params, loads, proj_name = parse_input_file(filepath)

                    # \u2500\u2500 S\u1eeda bug: SAFE_D ph\u1ea3i \u0111\u01b0\u1ee3c thi\u1ebft l\u1eadp \u0111\u1ed3ng b\u1ed9 v\u1edbi D_PILE \u2500\u2500\u2500\u2500\u2500\u2500
                    d_pile = params.get('D_PILE', 1.0)
                    params['SAFE_D'] = d_pile   # Bu\u1ed9c c\u00e0i \u2014 ph\u00f2ng fallback sai trong optimizer

                    # \u2500\u2500 Ghi \u0111\u00e8 th\u00f4ng s\u1ed1 t\u1eeb Tab 1 n\u1ebfu ng\u01b0\u1eddi d\u00f9ng b\u1eadt t\u00f9y ch\u1ecdn \u2500\u2500\u2500\u2500\u2500
                    if self.var_override_params.get():
                        params['D_PILE']    = self.params['D_PILE'].get()
                        params['P_LIMIT']   = self.params['P_LIMIT'].get()
                        params['P_TENSION'] = self.params['P_TENSION'].get()
                        params['M_LIMIT']   = self.params['M_LIMIT'].get()
                        params['SAFE_D']    = self.params['D_PILE'].get()  # c\u1eadp nh\u1eadt l\u1ea1i sau khi ghi \u0111\u00e8

                    params['mock_mode']       = True
                    params['result_filepath'] = filepath

                    # Ki\u1ec3m tra d\u1eef li\u1ec7u \u0111\u1ea7u v\u00e0o t\u1ed1i thi\u1ec3u
                    if not loads:
                        raise ValueError("File kh\u00f4ng c\u00f3 t\u1ed5 h\u1ee3p t\u1ea3i tr\u1ecdng n\u00e0o.")
                    if 'L_X' not in params or 'L_Y' not in params:
                        raise ValueError("File thi\u1ebfu k\u00edch th\u01b0\u1edbc b\u1ec7 (L_X, L_Y).")

                    self.log_batch(
                        f"  L_X={params['L_X']:.2f}m  L_Y={params['L_Y']:.2f}m  "
                        f"d={params.get('D_PILE',0):.2f}m  Po={params.get('P_LIMIT',0):.0f}T  "
                        f"Loads={len(loads)}", "info"
                    )

                    results   = run_optimization(params, loads)
                    rec       = results.get('recommended')
                    orig      = results.get('original_config')
                    all_valid = results.get('all_valid_configs', [])

                    # Log ph\u01b0\u01a1ng \u00e1n g\u1ed1c (n\u1ebfu c\u00f3)
                    if orig:
                        orig_status = "\u0110\u1ea0T" if orig['ok'] else "KH\u00d4NG \u0110\u1ea0T"
                        self.log_batch(
                            f"  Phuong an goc ({orig['n']} coc): {orig_status}  "
                            f"Pmax={orig['pmax']:.1f}T", "info"
                        )

                    if rec:
                        # Xu\u1ea5t file
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
                        # Log th\u00eam chi ti\u1ebft n\u1ebfu kh\u00f4ng c\u00f3 ph\u01b0\u01a1ng \u00e1n n\u00e0o \u0111\u1ea1t
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

                # C\u1eadp nh\u1eadt progress
                done = i + 1
                self.progress_bar["value"] = done
                self.lbl_progress.config(text=f"{done}/{len(self.batch_files)} Ho\u00e0n th\u00e0nh")

            # G\u1ed9p PDF
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

            # T\u1ed5ng k\u1ebft
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
