import os

filepath = 'ui/main_window.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace setup_ui definition
old_setup_ui = """    def setup_ui(self):
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)"""

new_setup_ui = """    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tab_interactive = tk.Frame(self.notebook)
        self.notebook.add(self.tab_interactive, text="1. Tương tác (Interactive)")
        self.setup_interactive_ui(self.tab_interactive)
        
        self.tab_batch = tk.Frame(self.notebook)
        self.notebook.add(self.tab_batch, text="2. Hàng loạt (Batch Mode)")
        self.setup_batch_ui(self.tab_batch)
        
    def setup_interactive_ui(self, parent_frame):
        main_paned = ttk.PanedWindow(parent_frame, orient=tk.HORIZONTAL)"""

content = content.replace(old_setup_ui, new_setup_ui)

# 2. Add setup_batch_ui at the end of the file
batch_ui_code = """
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
        
        # Frame Bottom: Tiến trình
        frame_progress = tk.LabelFrame(parent_frame, text="Tiến trình", padx=10, pady=10)
        frame_progress.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.txt_batch_log = tk.Text(frame_progress, height=8, bg="black", fg="white", font=("Consolas", 10))
        self.txt_batch_log.pack(fill=tk.BOTH, expand=True)
        
        frame_run = tk.Frame(parent_frame, padx=10, pady=10)
        frame_run.pack(fill=tk.X)
        self.btn_run_batch = tk.Button(frame_run, text="TÍNH TOÁN BATCH", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), height=2, command=self.run_batch)
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
        self.txt_batch_log.insert(tk.END, msg + "\\n")
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
                            export_pdf(rec, loads, params, out_dir, prefix, png_path)
                            
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
                    
            self.log_batch("=== HOÀN THÀNH ===")
            self.btn_run_batch.config(state=tk.NORMAL)
            
        threading.Thread(target=task, daemon=True).start()
"""

content = content + batch_ui_code

# 3. Add handle_drop modification to support dropping files anywhere, and depending on active tab
handle_drop_old = """    def handle_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        self.process_multiple_files(files)"""

handle_drop_new = """    def handle_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        
        try:
            current_tab = self.notebook.index(self.notebook.select())
        except:
            current_tab = 0
            
        if current_tab == 1:
            self.add_files_to_batch(files)
        else:
            self.process_multiple_files(files)"""

content = content.replace(handle_drop_old, handle_drop_new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Refactoring completed.")
