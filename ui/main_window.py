import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import DND_FILES
from core.optimizer import run_optimization
from core.mechanics import check_layout
from core.generator import generate_coords
from io_handlers.file_io import parse_input_file, export_output_file
from ui.plot_canvas import PlotCanvas

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
                  
        row = 0
        col = 0
        for k, text in labels_1.items():
            ttk.Label(frame_geom, text=text).grid(row=row, column=col*2, sticky="w", padx=2)
            entry = ttk.Entry(frame_geom, textvariable=self.params[k], width=10)
            entry.grid(row=row, column=col*2+1, pady=2, padx=2)
            if k in ["L_X", "L_Y"]:
                entry.config(state="readonly")
            
            row += 1
            if row > 2:
                row = 0
                col += 1
        
        # Loads
        frame_loads = tk.LabelFrame(tab_params, text="Tổ hợp Tải trọng", padx=10, pady=5)
        frame_loads.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tree_loads = ttk.Treeview(frame_loads, columns=("Hx", "Hy", "P", "Mx", "My", "Mz"), show="headings", height=5)
        self.tree_loads.heading("Hx", text="Hx (kN)")
        self.tree_loads.heading("Hy", text="Hy (kN)")
        self.tree_loads.heading("P", text="P (kN)")
        self.tree_loads.heading("Mx", text="Mx (kNm)")
        self.tree_loads.heading("My", text="My (kNm)")
        self.tree_loads.heading("Mz", text="Mz (kNm)")
        self.tree_loads.column("Hx", width=50)
        self.tree_loads.column("Hy", width=50)
        self.tree_loads.column("P", width=50)
        self.tree_loads.column("Mx", width=50)
        self.tree_loads.column("My", width=50)
        self.tree_loads.column("Mz", width=50)
        self.tree_loads.pack(fill=tk.BOTH, expand=True)
        
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
        for load in self.loads:
            self.tree_loads.insert("", tk.END, values=(
                load.get('Hx', 0.0), load.get('Hy', 0.0), load.get('N', 0.0), 
                load.get('Mx', 0.0), load.get('My', 0.0), load.get('Mz', 0.0)
            ))
            
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
            
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if filepath:
            try:
                export_output_file(filepath, self.current_config, self.get_params_dict(), self.loads, getattr(self, 'project_name', 'Du An Toi Uu Coc'), self.output_option.get())
                
                import os
                base_dir = os.path.dirname(filepath)
                base_name = os.path.splitext(os.path.basename(filepath))[0]
                
                # Sinh file .cti cho spColumn
                if self.var_export_cti.get():
                    cti_path = os.path.join(base_dir, f"{base_name}.cti")
                    with open(cti_path, 'w', encoding='utf-8') as f:
                        f.write("# spColumn Text Input (CTI) File - Generated by OptApp\n")
                        f.write(f"Concrete: {self.cb_concrete.get()}\n")
                        f.write(f"Rebar_Shape: {self.cb_rebar_shape.get()}\n")
                        f.write(f"Rebar_Count: {self.spin_rebar_num.get()}\n")
                        f.write(f"Rebar_Diameter: {self.spin_rebar_d.get()}\n")
                        f.write(f"Cover: {self.spin_cover.get()}\n\n")
                        f.write("# TAI TRONG KIEM TOAN (Tu MCOC)\n")
                        for i, ld in enumerate(self.loads):
                            f.write(f"Load_Case_{i+1}: N={ld['N']}, Mx={ld['Mx']}, My={ld['My']}\n")
                            
                if self.output_option.get() == "ALL":
                    for name in self.cb_config['values']:
                        self.cb_config.set(name)
                        self.update_simulation()
                        img_name = name.replace(' ', '_').replace('ư', 'u').replace('ơ', 'o').replace('á', 'a').replace('đ', 'd').replace('ề', 'e').replace('ố', 'o').replace('ộ', 'o')
                        img_path = os.path.join(base_dir, f"{base_name}_{img_name}.png")
                        self.plot_canvas.fig.savefig(img_path, dpi=300, bbox_inches='tight')
                else:
                    self.cb_config.set("Phương án đề xuất")
                    self.update_simulation()
                    img_path = os.path.join(base_dir, f"{base_name}_De_xuat.png")
                    self.plot_canvas.fig.savefig(img_path, dpi=300, bbox_inches='tight')
                    
                messagebox.showinfo("Thành công", "Đã xuất file text và các bản vẽ mô phỏng thành công!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất file: {str(e)}")

    def run_interactive_sim(self):
        nx = int(self.sim_nx.get())
        ny = int(self.sim_ny.get())
        sx = round(self.sim_sx.get(), 2)
        sy = round(self.sim_sy.get(), 2)
        
        if not self.loads:
            self.lbl_sim_status.config(text="CHƯA CÓ TẢI TRỌNG", fg="gray")
            return
            
        layout = self.sim_layout.get()
        coords = generate_coords(nx, ny, sx, sy, layout)
        n_piles = len(coords)
        
        ok, pmax, pmin, forces, msg = check_layout(coords, nx, ny, sx, sy, layout, self.get_params_dict(), self.loads)
        
        self.lbl_sim_status.config(text="ĐẠT (TỐT)" if ok else "KHÔNG ĐẠT", fg="#27ae60" if ok else "#e74c3c")
        
        self.txt_sim_result.delete(1.0, tk.END)
        self.txt_sim_result.insert(tk.END, f"Số lượng cọc: {n_piles}\n")
        self.txt_sim_result.insert(tk.END, f"Pmax = {pmax:.1f} kN\n")
        self.txt_sim_result.insert(tk.END, f"Pmin = {pmin:.1f} kN\n")
        self.txt_sim_result.insert(tk.END, f"Thông báo: {msg}\n")
        
        # Determine the selected load case index for forces visualization
        idx_load = 0
        if self.cb_load_case.get().startswith("Tổ hợp"):
            try:
                idx_load = int(self.cb_load_case.get().split()[2]) - 1
            except: pass
            
        # Recalculate forces for the specific load case for heatmap
        load = self.loads[idx_load]
        N, Mx, My = load.get('N', 0), load.get('Mx', 0), load.get('My', 0)
        import numpy as np
        cg_x, cg_y = np.mean(coords[:, 0]), np.mean(coords[:, 1])
        I_x = np.sum((coords[:, 1] - cg_y)**2)
        I_y = np.sum((coords[:, 0] - cg_x)**2)
        I_x = I_x if I_x > 0 else 1e-9
        I_y = I_y if I_y > 0 else 1e-9
        Mx_cg = Mx - N * cg_y
        My_cg = My - N * cg_x
        sim_forces = []
        for (x, y) in coords:
            dx = x - cg_x
            dy = y - cg_y
            p = N/n_piles + Mx_cg * dy / I_x + My_cg * dx / I_y
            sim_forces.append(p)
            
        self.plot_canvas.draw_simulation(coords, self.get_params_dict(), sim_forces)

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
            self.txt_result.insert(tk.END, f"  Pmax = {orig['pmax']:.2f} kN  (Gioi han: {P_LIMIT:.0f} kN)\n")
            self.txt_result.insert(tk.END, f"  Pmin = {orig['pmin']:.2f} kN  (Gioi han chiu nho: -{P_TENSION:.0f} kN)\n")
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
            self.txt_result.insert(tk.END, f"     Pmax = {rec['pmax']:.2f} kN\n")
            self.txt_result.insert(tk.END, f"     Pmin = {rec['pmin']:.2f} kN\n")
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
        # Frame Top: Danh sách file
        frame_list = tk.LabelFrame(parent_frame, text="Dữ liệu đầu vào", padx=10, pady=10)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("STT", "Tên file", "Thư mục", "Trạng thái")
        self.tree_batch = ttk.Treeview(frame_list, columns=columns, show="headings", height=10)
        self.tree_batch.heading("STT", text="#")
        self.tree_batch.heading("Tên file", text="Tên file")
        self.tree_batch.heading("Thư mục", text="Thư mục")
        self.tree_batch.heading("Trạng thái", text="Trạng thái")
        self.tree_batch.column("STT", width=50, anchor='center')
        self.tree_batch.column("Tên file", width=200)
        self.tree_batch.column("Thư mục", width=400)
        self.tree_batch.column("Trạng thái", width=150, anchor='center')
        self.tree_batch.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(frame_list, orient=tk.VERTICAL, command=self.tree_batch.yview)
        self.tree_batch.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        frame_list_btns = tk.Frame(parent_frame, padx=10)
        frame_list_btns.pack(fill=tk.X)
        ttk.Button(frame_list_btns, text="Thêm File", command=self.load_file_batch).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_list_btns, text="Xóa chọn", command=self.delete_selected_batch).pack(side=tk.RIGHT, padx=5)
        ttk.Button(frame_list_btns, text="Xóa tất cả", command=self.clear_all_batch).pack(side=tk.RIGHT, padx=5)
        
        # Frame Middle: Thiết lập chạy
        frame_settings = tk.LabelFrame(parent_frame, text="Thiết lập chạy & Xuất kết quả", padx=10, pady=10)
        frame_settings.pack(fill=tk.X, padx=10, pady=5)
        
        dir_frame = tk.Frame(frame_settings)
        dir_frame.pack(fill=tk.X, pady=5)
        tk.Label(dir_frame, text="Thư mục lưu:").pack(side=tk.LEFT)
        self.txt_out_dir = tk.Entry(dir_frame, width=50)
        self.txt_out_dir.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="Chọn...", command=self.choose_out_dir).pack(side=tk.LEFT)
        
        opts_frame = tk.Frame(frame_settings)
        opts_frame.pack(fill=tk.X, pady=5)
        self.var_export_excel = tk.BooleanVar(value=True)
        self.var_export_pdf = tk.BooleanVar(value=True)
        self.var_export_png = tk.BooleanVar(value=True)
        
        tk.Checkbutton(opts_frame, text="Xuất bảng tính Excel (Chi tiết R1-R6)", variable=self.var_export_excel).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(opts_frame, text="Xuất báo cáo PDF", variable=self.var_export_pdf).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(opts_frame, text="Xuất ảnh mặt bằng (PNG)", variable=self.var_export_png).pack(side=tk.LEFT, padx=10)
        self.var_merge_pdf = tk.BooleanVar(value=False)
        tk.Checkbutton(opts_frame, text="Gộp các báo cáo thành 1 file PDF tổng hợp", variable=self.var_merge_pdf).pack(side=tk.LEFT, padx=10)
        
        # Frame Bottom: Tiến trình
        frame_progress = tk.LabelFrame(parent_frame, text="Tiến trình", padx=10, pady=10)
        frame_progress.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.txt_batch_log = tk.Text(frame_progress, height=8, bg="black", fg="white", font=("Consolas", 10))
        self.txt_batch_log.pack(fill=tk.BOTH, expand=True)
        
        frame_run = tk.Frame(parent_frame, padx=10, pady=10)
        frame_run.pack(fill=tk.X)
        self.btn_run_batch = tk.Button(frame_run, text="TÍNH TOÁN", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), height=2, command=self.run_batch)
        self.btn_run_batch.pack(side=tk.RIGHT, padx=10, ipadx=20)
        
        self.batch_files = [] # list of dicts: {'path': filepath, 'status': str}

    def load_file_batch(self):
        from tkinter import filedialog
        filepaths = filedialog.askopenfilenames(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        self.add_files_to_batch(filepaths)

    def add_files_to_batch(self, filepaths):
        import os
        for fp in filepaths:
            # Check if already added
            if any(f['path'] == fp for f in self.batch_files): continue
            
            self.batch_files.append({'path': fp, 'status': 'Chờ'})
            name = os.path.basename(fp)
            folder = os.path.dirname(fp)
            self.tree_batch.insert("", "end", values=(len(self.batch_files), name, folder, "Chờ"))
            
    def delete_selected_batch(self):
        selected_items = self.tree_batch.selection()
        for item in selected_items:
            values = self.tree_batch.item(item, 'values')
            path_to_remove = None
            for f in self.batch_files:
                if f['path'].endswith(values[1]):
                    path_to_remove = f
                    break
            if path_to_remove:
                self.batch_files.remove(path_to_remove)
            self.tree_batch.delete(item)
            
    def clear_all_batch(self):
        self.batch_files.clear()
        for item in self.tree_batch.get_children():
            self.tree_batch.delete(item)
            
    def choose_out_dir(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory()
        if folder:
            self.txt_out_dir.delete(0, tk.END)
            self.txt_out_dir.insert(0, folder)
            
    def log_batch(self, msg):
        self.txt_batch_log.insert(tk.END, msg + "\n")
        self.txt_batch_log.see(tk.END)
        self.root.update()

    def update_batch_status(self, index, status):
        self.batch_files[index]['status'] = status
        item = self.tree_batch.get_children()[index]
        vals = self.tree_batch.item(item, 'values')
        self.tree_batch.item(item, values=(vals[0], vals[1], vals[2], status))
        self.root.update()

    def run_batch(self):
        import os
        import threading
        from core.optimizer import run_optimization
        from io_handlers.file_io import parse_input_file
        from io_handlers.export_utils import export_excel, export_pdf, export_png

        out_dir = self.txt_out_dir.get().strip()
        if not out_dir:
            from tkinter import messagebox
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục lưu kết quả!")
            return
            
        def task():
            self.btn_run_batch.config(state=tk.DISABLED)
            self.log_batch("=== BẮT ĐẦU CHẠY HÀNG LOẠT ===")
            
            generated_pdfs = []
            for i, f in enumerate(self.batch_files):
                if f['status'] == 'Xong': continue
                
                filepath = f['path']
                filename = os.path.basename(filepath)
                prefix = filename.split('.')[0]
                
                self.update_batch_status(i, "Đang chạy...")
                self.log_batch(f"[{i+1}/{len(self.batch_files)}] Đang xử lý: {filename}")
                
                try:
                    params, loads, proj_name = parse_input_file(filepath)
                    
                    # Cập nhật giới hạn thiết kế từ giao diện (Tab 1) cho tất cả các file
                    params['D_PILE'] = self.params['D_PILE'].get()
                    params['P_LIMIT'] = self.params['P_LIMIT'].get()
                    params['P_TENSION'] = self.params['P_TENSION'].get()
                    params['M_LIMIT'] = self.params['M_LIMIT'].get()
                    params['mock_mode'] = self.params['mock_mode'].get()
                    params['result_filepath'] = filepath
                    
                    results = run_optimization(params, loads)
                    rec = results.get('recommended')
                    
                    if rec:
                        # Draw to canvas to get image
                        self.plot_canvas.draw_simulation(rec['coords'], params)
                        
                        png_path = None
                        if self.var_export_png.get() or self.var_export_pdf.get():
                            png_path = export_png(self.plot_canvas, rec['coords'], params, out_dir, prefix)
                            
                        if self.var_export_excel.get():
                            export_excel(rec, loads, params, out_dir, prefix)
                            
                        if self.var_export_pdf.get():
                            pdf_path = export_pdf(rec, loads, params, out_dir, prefix, png_path)
                            generated_pdfs.append(pdf_path)
                            
                        self.log_batch(f"  -> Xong! Tối ưu: Kieu {rec['type']} ({rec['n']} cọc).")
                        self.update_batch_status(i, "Xong")
                    else:
                        self.log_batch(f"  -> Lỗi: Không tìm thấy phương án thỏa mãn.")
                        self.update_batch_status(i, "Không Đạt")
                except Exception as e:
                    import traceback
                    self.log_batch(f"  -> Lỗi khi xử lý {filename}: {str(e)}")
                    print(traceback.format_exc())
                    self.update_batch_status(i, "Lỗi")
                    
            
            if self.var_merge_pdf.get() and generated_pdfs:
                try:
                    self.log_batch("Đang gộp file PDF...")
                    from PyPDF2 import PdfMerger
                    merger = PdfMerger()
                    for pdf in generated_pdfs:
                        merger.append(pdf)
                    merged_path = os.path.join(out_dir, "TONG_HOP_REPORT.pdf")
                    merger.write(merged_path)
                    merger.close()
                    self.log_batch(f"Đã gộp thành công: TONG_HOP_REPORT.pdf")
                except Exception as e:
                    self.log_batch(f"Lỗi khi gộp PDF: {str(e)}")
                    
            self.log_batch("=== HOÀN THÀNH ===")
            self.btn_run_batch.config(state=tk.NORMAL)
            
        threading.Thread(target=task, daemon=True).start()
