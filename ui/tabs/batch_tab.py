"""batch_tab.py - BatchTab: Tab 2 Hàng loạt (giao diện + logic chạy).

Tách từ ui/main_window.py (Plan 023, Pha 4a) — giữ NGUYÊN hành vi.
"""
import os
import re as _re
import subprocess
import threading

import numpy as np
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkinterdnd2 import DND_FILES
from io_handlers.file_io import parse_input_file
from core.blackbox import MCOCBlackbox
from ui import constants as uiconst
from ui.widgets.widget_utils import to_safe_filename


class BatchTab:
    """Tab 2 (Hàng loạt): dựng giao diện danh sách file + thiết lập xuất, quản lý danh sách (kéo-thả/thêm/xóa), và chạy hàng loạt nhiều file (MCOC+NSGA-II) rồi xuất PNG/Excel/PDF + gộp PDF."""

    def __init__(self, app):
        self.app = app

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
        self.app.tree_batch = ttk.Treeview(left, columns=cols_b, show="headings", selectmode="extended")
        self.app.tree_batch.heading("#",          text="#")
        self.app.tree_batch.heading("T\u00ean file",    text="T\u00ean file")
        self.app.tree_batch.heading("Th\u01b0 m\u1ee5c",   text="Th\u01b0 m\u1ee5c")
        self.app.tree_batch.heading("Tr\u1ea1ng th\u00e1i",  text="Tr\u1ea1ng th\u00e1i")
        self.app.tree_batch.column("#",          width=34,  anchor="center", stretch=False)
        self.app.tree_batch.column("T\u00ean file",    width=160, anchor="w")
        self.app.tree_batch.column("Th\u01b0 m\u1ee5c",   width=320, anchor="w")
        self.app.tree_batch.column("Tr\u1ea1ng th\u00e1i",  width=100, anchor="center", stretch=False)
        # Màu tag trạng thái
        self.app.tree_batch.tag_configure("done",    foreground="#27ae60")
        self.app.tree_batch.tag_configure("running", foreground="#2980b9")
        self.app.tree_batch.tag_configure("fail",    foreground="#e74c3c")
        self.app.tree_batch.tag_configure("wait",    foreground="#7f8c8d")

        sb_b = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.app.tree_batch.yview)
        self.app.tree_batch.configure(yscrollcommand=sb_b.set)
        self.app.tree_batch.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_b.pack(side=tk.RIGHT, fill=tk.Y)

        # Footer đếm file + nút xóa
        foot = tk.Frame(left)
        foot.pack(fill=tk.X, pady=(4, 0))
        self.app.lbl_batch_count = tk.Label(foot, text="0 file", fg="#555")
        self.app.lbl_batch_count.pack(side=tk.LEFT)
        ttk.Button(foot, text="X\u00f3a ch\u1ecdn", command=self.delete_selected_batch).pack(side=tk.RIGHT, padx=3)
        ttk.Button(foot, text="X\u00f3a t\u1ea5t c\u1ea3",  command=self.clear_all_batch).pack(side=tk.RIGHT, padx=3)

        # Drag-drop vào danh sách
        self.app.tree_batch.drop_target_register(DND_FILES)
        self.app.tree_batch.dnd_bind("<<Drop>>", self._batch_drop)

        # ── Panel phải: Thiết lập chạy ─────────────────────────
        right = tk.LabelFrame(body, text="Thi\u1ebft l\u1eadp ch\u1ea1y", padx=8, pady=6)
        body.add(right, weight=2)

        # Thư mục xuất kết quả
        tk.Label(right, text="Th\u01b0 m\u1ee5c xu\u1ea5t k\u1ebft qu\u1ea3", font=("", 9, "bold"), anchor="w").pack(fill=tk.X)
        dir_f = tk.Frame(right)
        dir_f.pack(fill=tk.X, pady=(2, 0))
        self.app.txt_out_dir = tk.Entry(dir_f)
        self.app.txt_out_dir.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_f, text="Ch\u1ecdn...", command=self.choose_out_dir).pack(side=tk.LEFT, padx=4)
        tk.Label(right, text="\u0110\u1ec3 tr\u1ed1ng: k\u1ebft qu\u1ea3 l\u01b0u c\u00f9ng th\u01b0 m\u1ee5c t\u1eebng file \u0111\u1ea7u v\u00e0o.",
                 fg="#888", font=("", 8)).pack(anchor="w")

        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, pady=6)

        # Tab xuất — bố cục 3 tab theo MCOC: Xuất kết quả / Báo cáo / spColumn
        nb_right = ttk.Notebook(right)
        nb_right.pack(fill=tk.BOTH, expand=True)

        tab_export = tk.Frame(nb_right, padx=6, pady=6)
        nb_right.add(tab_export, text="Xuất kết quả")
        tab_report = tk.Frame(nb_right, padx=6, pady=6)
        nb_right.add(tab_report, text="Báo cáo")
        tab_spcol = tk.Frame(nb_right, padx=6, pady=6)
        nb_right.add(tab_spcol, text="spColumn")

        self.app.var_export_pdf   = tk.BooleanVar(value=True)
        self.app.var_export_excel = tk.BooleanVar(value=True)
        self.app.var_export_png   = tk.BooleanVar(value=True)
        self.app.var_merge_pdf    = tk.BooleanVar(value=True)

        # ── Tab "Xuất kết quả": dữ liệu số (Excel/PNG) + tiền tố/hậu tố tên file ──
        tk.Checkbutton(tab_export, text="Xuất bảng Excel",
                       variable=self.app.var_export_excel).pack(anchor="w", pady=2)
        tk.Checkbutton(tab_export, text="Xuất mặt bằng cọc dạng PNG",
                       variable=self.app.var_export_png).pack(anchor="w", pady=2)

        ttk.Separator(tab_export, orient="horizontal").pack(fill=tk.X, pady=6)

        pf = tk.Frame(tab_export)
        pf.pack(fill=tk.X)
        tk.Label(pf, text="Prefix tên file", width=14, anchor="w").grid(row=0, column=0, sticky="w")
        self.app.txt_prefix = tk.Entry(pf, width=18)
        self.app.txt_prefix.grid(row=0, column=1, padx=4, pady=2)

        tk.Label(pf, text="Suffix tên file", width=14, anchor="w").grid(row=1, column=0, sticky="w")
        self.app.txt_suffix = tk.Entry(pf, width=18)
        self.app.txt_suffix.grid(row=1, column=1, padx=4, pady=2)

        ttk.Separator(tab_export, orient="horizontal").pack(fill=tk.X, pady=6)
        # Tùy chọn chạy: ghi đè thông số cọc từ Tab 1 lên mọi file
        self.app.var_override_params = tk.BooleanVar(value=False)
        tk.Checkbutton(
            tab_export,
            text="Ghi đè thông số cọc từ Tab 1 (d, Po, Ct, M) lên tất cả file",
            variable=self.app.var_override_params, wraplength=300, justify="left"
        ).pack(anchor="w", pady=2)

        # ── Tab "Báo cáo": xuất PDF + gộp PDF ──────────────────────────────
        tk.Checkbutton(tab_report, text="Xuất báo cáo PDF",
                       variable=self.app.var_export_pdf).pack(anchor="w", pady=2)
        tk.Checkbutton(tab_report, text="Gộp các PDF thành một file tổng hợp",
                       variable=self.app.var_merge_pdf).pack(anchor="w", pady=2)
        tk.Label(tab_report,
                 text="Báo cáo PDF gồm thuyết minh + bảng kiểm toán + mặt bằng cọc.",
                 fg="#888", font=("", 8), justify="left", wraplength=300).pack(anchor="w", pady=(4, 0))

        # ── Tab "spColumn": bố cục theo MCOC (chưa triển khai chức năng .cti) ──
        self.app.var_spcolumn = tk.BooleanVar(value=False)
        tk.Checkbutton(
            tab_spcol, text="Xuất tiết diện trụ sang spColumn (.cti)",
            variable=self.app.var_spcolumn, state="disabled").pack(anchor="w", pady=2)
        tk.Label(tab_spcol,
                 text="Đang phát triển — bố cục theo MCOC. Chức năng xuất file "
                      "spColumn (.cti) để thiết kế cốt thép trụ sẽ được bổ sung sau.",
                 fg="#888", font=("", 8), justify="left", wraplength=300).pack(anchor="w", pady=(4, 0))

        # ── Tiến trình: progress bar + log ──────────────────────
        prog_outer = tk.LabelFrame(parent_frame, text="Ti\u1ebfn tr\u00ecnh", padx=6, pady=4)
        prog_outer.pack(fill=tk.BOTH, expand=False, padx=6, pady=(0, 4))

        prog_top = tk.Frame(prog_outer)
        prog_top.pack(fill=tk.X, pady=(0, 4))
        self.app.progress_bar = ttk.Progressbar(prog_top, orient="horizontal", mode="determinate")
        self.app.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.app.lbl_progress = tk.Label(prog_top, text="0/0 Ho\u00e0n th\u00e0nh", width=18, anchor="e")
        self.app.lbl_progress.pack(side=tk.LEFT, padx=6)

        self.app.txt_batch_log = tk.Text(prog_outer, height=8, bg="#1e1e1e", fg="#d4d4d4",
                                     font=("Consolas", 9), relief="flat", wrap="word")
        sb_log = ttk.Scrollbar(prog_outer, orient=tk.VERTICAL, command=self.app.txt_batch_log.yview)
        self.app.txt_batch_log.configure(yscrollcommand=sb_log.set)
        self.app.txt_batch_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_log.pack(side=tk.RIGHT, fill=tk.Y)

        # Tag màu log
        self.app.txt_batch_log.tag_configure("ok",    foreground="#4ec9b0")
        self.app.txt_batch_log.tag_configure("err",   foreground="#f44747")
        self.app.txt_batch_log.tag_configure("info",  foreground="#9cdcfe")
        self.app.txt_batch_log.tag_configure("title", foreground="#dcdcaa", font=("Consolas", 9, "bold"))

        # ── Status bar ─────────────────────────────────────
        status_bar = tk.Frame(parent_frame, pady=6, padx=6)
        status_bar.pack(fill=tk.X)

        self.app.lbl_batch_status = tk.Label(status_bar, text="S\u1eb5n s\u00e0ng.", anchor="w", fg="#555")
        self.app.lbl_batch_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.app.btn_open_out = ttk.Button(status_bar, text="M\u1edf th\u01b0 m\u1ee5c k\u1ebft qu\u1ea3",
                                       command=self._open_out_dir, state="disabled")
        self.app.btn_open_out.pack(side=tk.LEFT, padx=4)

        self.app._batch_stop_flag = False
        self.app.btn_stop_batch = ttk.Button(status_bar, text="D\u1eebng", command=self._stop_batch, state="disabled")
        self.app.btn_stop_batch.pack(side=tk.LEFT, padx=4)

        self.app.btn_run_batch = tk.Button(status_bar, text="T\u00cdNH TO\u00c1N",
                                       bg="#27ae60", fg="white",
                                       font=("Arial", 11, "bold"),
                                       padx=20, command=self.run_batch)
        self.app.btn_run_batch.pack(side=tk.LEFT, padx=6)

        self.app.batch_files = []  # list of dicts: {'path': str, 'status': str}


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
            if any(f['path'] == fp for f in self.app.batch_files):
                continue
            self.app.batch_files.append({'path': fp, 'status': 'Ch\u1edd'})
            name   = os.path.basename(fp)
            folder = os.path.dirname(fp)
            idx    = len(self.app.batch_files)
            self.app.tree_batch.insert("", "end",
                                   values=(idx, name, folder, "Ch\u1edd"),
                                   tags=("wait",))
            added += 1
        self.app.lbl_batch_count.config(text=f"{len(self.app.batch_files)} file")


    def delete_selected_batch(self):
        """Xóa các file đang chọn khỏi danh sách hàng loạt và đánh số lại."""
        sel = self.app.tree_batch.selection()
        if not sel:
            return
        # Xác định tập đường dẫn cần xóa
        paths_to_remove = set()
        for item in sel:
            vals = self.app.tree_batch.item(item, 'values')
            fname = vals[1]; fdir = vals[2]
            paths_to_remove.add(os.path.join(str(fdir), str(fname)))
        self.app.batch_files = [f for f in self.app.batch_files if f['path'] not in paths_to_remove]
        for item in sel:
            self.app.tree_batch.delete(item)
        # Đánh số lại
        for i, item in enumerate(self.app.tree_batch.get_children(), 1):
            vals = self.app.tree_batch.item(item, 'values')
            self.app.tree_batch.item(item, values=(i, vals[1], vals[2], vals[3]))
        self.app.lbl_batch_count.config(text=f"{len(self.app.batch_files)} file")


    def clear_all_batch(self):
        """Xóa toàn bộ danh sách file hàng loạt."""
        self.app.batch_files.clear()
        for item in self.app.tree_batch.get_children():
            self.app.tree_batch.delete(item)
        self.app.lbl_batch_count.config(text="0 file")


    def choose_out_dir(self):
        """Chọn thư mục xuất kết quả cho chế độ hàng loạt."""
        folder = filedialog.askdirectory()
        if folder:
            self.app.txt_out_dir.delete(0, tk.END)
            self.app.txt_out_dir.insert(0, folder)


    def _open_out_dir(self):
        """Mở thư mục kết quả gần nhất bằng Explorer."""
        out = getattr(self.app, '_last_out_dir', None) or self.app.txt_out_dir.get().strip()
        if out and os.path.isdir(out):
            subprocess.Popen(f'explorer "{os.path.normpath(out)}"')
        else:
            messagebox.showinfo("Th\u00f4ng b\u00e1o", "Th\u01b0 m\u1ee5c xu\u1ea5t ch\u01b0a \u0111\u01b0\u1ee3c ch\u1ecdn ho\u1eb7c kh\u00f4ng t\u1ed3n t\u1ea1i.")


    def _stop_batch(self):
        """Bật cờ dừng để vòng lặp hàng loạt kết thúc sau file hiện tại."""
        self.app._batch_stop_flag = True
        self.log_batch(">>> \u0110\u00e3 g\u1eedi t\u00edn hi\u1ec7u D\u1eebng. Ch\u1edd file hi\u1ec7n t\u1ea1i ho\u00e0n th\u00e0nh...", tag="err")


    def log_batch(self, msg, tag="info"):
        """Ghi một dòng log vào ô log hàng loạt (kèm tag màu) và cuộn xuống cuối."""
        self.app.txt_batch_log.insert(tk.END, msg + "\n", tag)
        self.app.txt_batch_log.see(tk.END)
        self.app.root.update_idletasks()


    def update_batch_status(self, index, status):
        """Cập nhật trạng thái 1 file trong bảng hàng loạt và đổi màu tag tương ứng."""
        self.app.batch_files[index]['status'] = status
        items = self.app.tree_batch.get_children()
        if index >= len(items):
            return
        item = items[index]
        vals = self.app.tree_batch.item(item, 'values')
        tag_map = {"Xong": "done", "Ch\u1edd": "wait", "\u0110ang ch\u1ea1y...": "running",
                   "Kh\u00f4ng \u0110\u1ea1t": "fail", "L\u1ed7i": "fail"}
        tag = tag_map.get(status, "wait")
        self.app.tree_batch.item(item, values=(vals[0], vals[1], vals[2], status), tags=(tag,))
        self.app.root.update_idletasks()


    def run_batch(self):
        """Chạy tối ưu hàng loạt trên thread nền: với mỗi file, đọc đầu vào, đánh
        giá bằng MCOC + NSGA-II rồi xuất PNG/Excel/PDF; cuối cùng gộp PDF và tổng kết."""
        from io_handlers.export_utils import export_excel, export_pdf, export_png

        if not self.app.batch_files:
            messagebox.showwarning("C\u1ea3nh b\u00e1o", "Ch\u01b0a c\u00f3 file n\u00e0o trong danh s\u00e1ch.")
            return

        # BẮT BUỘC MCOC — chế độ Hàng loạt cũng đánh giá chính xác như Tab 1,
        # không chấp nhận phương án xấp xỉ (bệ cứng).
        exe = self.app.params['exe_path'].get().strip()
        if not exe or not os.path.exists(exe):
            messagebox.showwarning(
                "C\u1ea7n c\u1ea5u h\u00ecnh MCOC",
                "Ch\u1ebf \u0111\u1ed9 H\u00e0ng lo\u1ea1t \u0111\u00e1nh gi\u00e1 m\u1ecdi ph\u01b0\u01a1ng \u00e1n b\u1eb1ng MCOC (ch\u00ednh x\u00e1c).\n"
                "H\u00e3y ch\u1ecdn \u0111\u01b0\u1eddng d\u1eabn MCOC Batch \u1edf Tab 1, m\u1ee5c \"C\u1ea5u h\u00ecnh MCOC (b\u1eaft bu\u1ed9c)\".")
            return

        global_out_dir = self.app.txt_out_dir.get().strip()   # có thể rỗng

        def task():
            from core.nsga2_optimizer import run_nsga2
            from io_handlers.mcoc_writer import self_check
            self.app._batch_stop_flag = False
            self.app.btn_run_batch.config(state=tk.DISABLED)
            self.app.btn_stop_batch.config(state=tk.NORMAL)
            self.app.btn_open_out.config(state="disabled")
            self.app.progress_bar["maximum"] = len(self.app.batch_files)
            self.app.progress_bar["value"] = 0

            prefix_str = self.app.txt_prefix.get().strip()
            suffix_str = self.app.txt_suffix.get().strip()

            self.log_batch("=" * 55, "title")
            self.log_batch(f"  B\u1eaet \u0111\u1ea7u ch\u1ea1y h\u00e0ng lo\u1ea1t: {len(self.app.batch_files)} file", "title")
            self.log_batch("=" * 55, "title")

            n_ok = n_fail = n_err = 0
            generated_pdfs = []
            last_out_dir = global_out_dir

            for i, f in enumerate(self.app.batch_files):
                if self.app._batch_stop_flag:
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
                self.log_batch(f"\n[{i+1}/{len(self.app.batch_files)}] {filename}", "info")

                try:
                    params, loads, proj_name = parse_input_file(filepath)

                    # ── Sửa bug: SAFE_D phải được thiết lập đồng bộ với D_PILE ──────
                    d_pile = params.get('D_PILE', 1.0)
                    params['SAFE_D'] = d_pile   # Buộc cài — phòng fallback sai trong optimizer

                    # ── Ghi đè thông số từ Tab 1 nếu người dùng bật tùy chọn ─────
                    if self.app.var_override_params.get():
                        params['D_PILE']    = self.app._pget('D_PILE')
                        params['P_LIMIT']   = self.app._pget('P_LIMIT')
                        params['P_TENSION'] = self.app._pget('P_TENSION')
                        params['M_LIMIT']   = self.app._pget('M_LIMIT')
                        params['SAFE_D']    = self.app._pget('D_PILE')  # cập nhật lại sau khi ghi đè

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
                                        **uiconst.NSGA2_BATCH,
                                        secondary=self.app.var_secondary.get(), log=_blog)

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

                        self.app.plot_canvas.draw_simulation(rec['coords'], params)

                        png_path = None
                        if self.app.var_export_png.get() or self.app.var_export_pdf.get():
                            png_path = export_png(
                                self.app.plot_canvas, rec['coords'], params, out_dir, file_prefix)

                        if self.app.var_export_excel.get():
                            export_excel(rec, loads, params, out_dir, file_prefix)

                        if self.app.var_export_pdf.get():
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
                self.app.progress_bar["value"] = done
                self.app.lbl_progress.config(text=f"{done}/{len(self.app.batch_files)} Ho\u00e0n th\u00e0nh")

            # Gộp PDF
            if self.app.var_merge_pdf.get() and generated_pdfs:
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

            self.app.lbl_batch_status.config(text=f"Xong: {n_ok} OK / {n_fail} kh\u00f4ng \u0111\u1ea1t / {n_err} l\u1ed7i.")
            self.app.btn_run_batch.config(state=tk.NORMAL)
            self.app.btn_stop_batch.config(state=tk.DISABLED)
            if last_out_dir and os.path.isdir(last_out_dir):
                self.app._last_out_dir = last_out_dir
                self.app.btn_open_out.config(state="normal")

        threading.Thread(target=task, daemon=True).start()
