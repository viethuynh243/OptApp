"""file_ops.py - FileController: nạp/xuất file & làm mới Tab 1.

Tách từ ui/main_window.py (Plan 023, Pha 3c) — giữ NGUYÊN hành vi.
"""
import os
import re as _re
import tkinter as tk
from tkinter import messagebox, filedialog
from io_handlers.file_io import parse_input_file, export_output_file
from io_handlers.report_writer import export_technical_report, export_technical_report_pdf
from ui import strings as S
from ui.widgets.widget_utils import to_safe_filename


class FileController:
    """Nhập/xuất file: chọn MCOC Batch, nạp 1 hay nhiều file đầu vào (kéo-thả), làm mới toàn bộ, và xuất kết quả (TXT MCOC + báo cáo .md/.pdf + ảnh PNG)."""

    def __init__(self, app):
        self.app = app

    def browse_exe(self):
        """Mở hộp thoại chọn đường dẫn MCOC Batch và lưu vào tham số exe_path."""
        filepath = filedialog.askopenfilename(
            title="Chọn MCOC Batch (Command Line)",
            filetypes=[("MCOC Batch", "*.lnk;*.exe;*.bat;*.cmd;*.py"), ("All Files", "*.*")])
        if filepath:
            self.app.params['exe_path'].set(filepath)


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

                # Cập nhật thông số HÌNH HỌC từ file (Lx/Ly/d là số liệu THẬT).
                for k in ('L_X', 'L_Y', 'D_PILE'):
                    if k in params and params[k] is not None and params[k] > 0:
                        # StringVar: hiển thị gọn (bỏ ".0" thừa)
                        self.app.params[k].set(f"{params[k]:g}")

                # Giới hạn SỨC CHỊU TẢI ([Po]/[Ct]/[M]) trong file MCOC chỉ là GIÁ
                # TRỊ MẶC ĐỊNH (thường 500) — MCOC không dùng để chấm. Vì vậy CHỈ
                # điền khi ô đang TRỐNG, KHÔNG ghi đè giá trị người dùng đã nhập
                # (tránh bẫy: nạp file làm [Po] bị về 500 -> mọi phương án "trượt").
                for k in ('P_LIMIT', 'P_TENSION', 'M_LIMIT'):
                    cur = self.app.params[k].get().strip()
                    if (not cur) and k in params and params[k] is not None and params[k] > 0:
                        self.app.params[k].set(f"{params[k]:g}")

                # Đặc trưng vật liệu/đất từ file MCOC cho engine SSI (Eb, m, Jo, Fo,
                # Lc, H đài). Tự điền ô Lc & H đài nếu đang trống để người dùng thấy.
                self.app._file_params = {kk: params.get(kk) for kk in
                                     ('E_b', 'm_soil', 'J_o', 'F_o', 'pile_length', 'H_cap')}
                if params.get('pile_length') and not self.app.var_pile_length.get().strip():
                    self.app.var_pile_length.set(f"{params['pile_length']:g}")
                if params.get('H_cap') and not self.app.var_cap_h.get().strip():
                    self.app.var_cap_h.set(f"{params['H_cap']:g}")

                if 'original_coords' in params:
                    self.app.original_coords = params['original_coords']
                    if 'D_PILE' in params: self.app.original_d = params['D_PILE']
                    if 'P_LIMIT' in params: self.app.original_p = params['P_LIMIT']

                # Lưu Nmax/Nmin/Mxmax/Mymax thực tế từ file kết quả
                if 'orig_pmax' in params: self.app.orig_pmax = params['orig_pmax']
                if 'orig_pmin' in params: self.app.orig_pmin = params['orig_pmin']
                if 'orig_mxmax' in params: self.app.orig_mxmax = params['orig_mxmax']
                if 'orig_mymax' in params: self.app.orig_mymax = params['orig_mymax']
                self.app.result_filepath = filepath  # Lưu đường dẫn để blackbox đọc đúng file

                # Nếu là file INPUT MCOC (không phải file kết quả/CSV) -> dùng làm
                # template sinh phương án mới khi gọi MCOC thực
                if proj_name != 'Imported from Result' and not filepath.lower().endswith('.csv') \
                        and 'original_coords' in params:
                    self.app.input_filepath = filepath
                    if hasattr(self.app, 'lbl_template'):
                        self.app.lbl_template.config(
                            text="File input gốc: " + os.path.basename(filepath), foreground="black")

                self.app.loads = loads
                total_new_loads += len(loads)
                success_count += 1
                if proj_name and proj_name != "Du An Toi Uu Coc":
                    last_proj_name = proj_name
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file {filepath}:\n{str(e)}")

        if success_count > 0:
            if last_proj_name:
                self.app.project_name = last_proj_name
            # Reset kết quả cũ — dữ liệu mới, kết quả mới
            self.app.current_config = None
            self.app.refresh_loads_ui()

            # Sau khi load file, mở khóa L_X / L_Y để người dùng có thể điều chỉnh
            for k in ('L_X', 'L_Y'):
                if k in self.app._param_entries:
                    self.app._param_entries[k].config(state='normal')

            # Xóa UI kết quả cũ
            self.app.txt_result.delete(1.0, tk.END)
            self.app.cb_config.set('')
            self.app.cb_config['values'] = []

            # Để trống khung vẽ, chờ người dùng ấn "Chạy tối ưu hóa"
            self.app.plot_canvas.clear()

            self.app._set_status(
                "Đã nạp %d file (%d tổ hợp tải)." % (success_count, total_new_loads))
            self.app._validate_inputs()


    def clear_loads(self):
        """Làm mới: xóa tải trọng, THÔNG SỐ BÀI TOÁN, file gốc và kết quả.

        Đưa Tab Tương tác về trạng thái trắng như lúc vừa mở app (trừ cấu hình
        MCOC Batch — là tùy chọn công cụ, giữ lại cho tiện)."""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn LÀM MỚI toàn bộ (tải trọng, thông số bài toán, file gốc và kết quả) không?"):
            self.app.loads = []
            self.app.refresh_loads_ui()

            # 1) Xóa trắng các ô THÔNG SỐ BÀI TOÁN (L_X, L_Y, d, [Po], [Ct], [M])
            for k in self.app.NUMERIC_PARAMS:
                if k in self.app.params:
                    self.app.params[k].set('')
            # Mở khóa lại L_X / L_Y (có thể đã bị khóa sau khi nạp file)
            for k in ('L_X', 'L_Y'):
                if k in self.app._param_entries:
                    self.app._param_entries[k].config(state='normal')

            # 2) Reset trạng thái FILE GỐC (template MCOC) + nhãn hiển thị
            self.app.input_filepath = ''
            self.app.original_coords = []
            self.app.project_name = "Du An Toi Uu Coc"
            if hasattr(self.app, 'lbl_template'):
                self.app.lbl_template.config(text="File input gốc: (chưa có)", foreground="gray")

            # 3) Xóa các giá trị "gốc" nội bộ đọc từ file (để không lẫn sang lần sau)
            for attr in ('original_d', 'original_p', 'orig_pmax', 'orig_pmin',
                         'orig_mxmax', 'orig_mymax', 'result_filepath'):
                if hasattr(self.app, attr):
                    delattr(self.app, attr)

            # 4) Reset trạng thái TỐI ƯU MỞ RỘNG (bảng đường kính + cờ audit)
            self.app.ext_diameters = []
            self.app._ext_active = False
            self.app._ext_hlimit = 0.0
            self.app._last_ext_out = None
            if hasattr(self.app, 'lbl_ext_dia'):
                self.app._update_ext_dia_label()

            # 5) Reset UI kết quả như lúc mới mở
            self.app.current_config = None
            self.app.txt_result.delete(1.0, tk.END)
            self.app.cb_config.set('')
            self.app.cb_config['values'] = []
            # Xóa luôn ô Tổ hợp + dải KPI (số cọc/hệ số sử dụng/trạng thái) — nếu
            # không, chúng giữ giá trị phương án cũ dù đã làm mới.
            self.app.cb_load_case.set('')
            self.app.cb_load_case['values'] = []
            self.app.lbl_kpi.config(text="", fg="#1a3c5e")
            self.app.view_mode.set(S.VIEW_LAYOUT)
            self.app.plot_canvas.clear()   # vẽ trắng như lúc mới mở


    def save_file(self):
        """Xuất kết quả phương án hiện hành: file TXT (MCOC), báo cáo .md và ảnh
        mặt bằng PNG cho từng phương án (BEST hoặc ALL)."""
        if not self.app.current_config:
            messagebox.showwarning("Cảnh báo", "Chưa có kết quả để xuất. Vui lòng chạy Tối ưu hóa trước.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=to_safe_filename(getattr(self.app, 'project_name', 'Ket_qua_toi_uu')),
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
                self.app.current_config,
                self.app.get_params_dict(),
                self.app.loads,
                getattr(self.app, 'project_name', 'Du An Toi Uu Coc'),
                self.app.output_option.get()
            )

            # Tham số + tùy chọn báo cáo. Nếu là phiên TỐI ƯU MỞ RỘNG: thêm [H],
            # bật R7/R8 và đính kèm mục 3b (quét đường kính + thu bệ).
            report_params = self.app.get_params_dict()
            report_kwargs = {}
            if getattr(self.app, '_ext_active', False) and getattr(self.app, '_last_ext_out', None):
                report_params['H_LIMIT'] = getattr(self.app, '_ext_hlimit', 0.0)
                out = self.app._last_ext_out
                cfg_ext = getattr(self.app, '_last_ext_cfg', None)
                report_kwargs = {
                    'enable_R7': bool(cfg_ext.enable_R7) if cfg_ext else True,
                    'enable_R8': bool(cfg_ext.enable_R8) if cfg_ext else True,
                    'ext_info': {
                        'winner_d': out.get('winner_diameter'),
                        'rows': [{'d': r['dia'].d,
                                  'n': (r['best']['n'] if r['best'] else 0),
                                  'pmax': (r['best']['pmax'] if r['best'] else 0.0),
                                  'cost': r['cost'], 'ok': r['best'] is not None}
                                 for r in out.get('per_diameter', [])],
                        'cap': out.get('cap_report'),
                    },
                }

            # 1b. Xuất BÁO CÁO KỸ THUẬT chuẩn (.md) — hệ số sử dụng, R1-R8, phụ lục
            report_path = os.path.join(base_dir, f"{base_name}_baocao_kythuat.md")
            try:
                export_technical_report(
                    report_path, self.app.current_config, report_params,
                    self.app.loads, getattr(self.app, 'project_name', 'Du An Toi Uu Coc'),
                    **report_kwargs)
            except Exception:
                report_path = None

            # 1c. Xuất BÁO CÁO KỸ THUẬT dạng PDF (cùng nội dung, có bảng R1-R8, font Việt)
            pdf_report_path = os.path.join(base_dir, f"{base_name}_baocao_kythuat.pdf")
            try:
                export_technical_report_pdf(
                    pdf_report_path, self.app.current_config, report_params,
                    self.app.loads, getattr(self.app, 'project_name', 'Du An Toi Uu Coc'),
                    **report_kwargs)
            except Exception:
                pdf_report_path = None

            # 2. Xuất ảnh mặt bằng PNG
            exported_imgs = []
            if self.app.output_option.get() == "ALL":
                for name in self.app.cb_config['values']:
                    self.app.cb_config.set(name)
                    self.app.update_simulation()
                    safe = to_safe_filename(name)
                    img_path = os.path.join(base_dir, f"{base_name}_{safe}.png")
                    self.app.plot_canvas.fig.savefig(img_path, dpi=300, bbox_inches='tight')
                    exported_imgs.append(img_path)
            else:
                # Luôn vẽ lại phương án đề xuất trước khi lưu
                if S.CFG_DEXUAT in self.app.cb_config['values']:
                    self.app.cb_config.set(S.CFG_DEXUAT)
                elif self.app.cb_config['values']:
                    self.app.cb_config.current(0)
                self.app.update_simulation()
                img_path = os.path.join(base_dir, f"{base_name}_De_xuat.png")
                self.app.plot_canvas.fig.savefig(img_path, dpi=300, bbox_inches='tight')
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
