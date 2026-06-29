"""
main_window.py - Cửa sổ chính (VỎ điều phối — composition, Plan 023).

MainWindow là "shared context": nó GIỮ state chia sẻ (params, loads,
current_config, các cờ vòng đời) cùng các widget chung, dựng khung 2 tab + menu
+ status bar, và TẠO các component. Logic được tách thành (mỗi component nhận
tham chiếu `self` để thao tác state/widget qua `app.<...>`):

    controllers/                     tabs/
      ParamsController   tham số+TCVN   InteractiveTab  dựng Tab 1
      LoadsController    CRUD tải        BatchTab        dựng Tab 2 + chạy hàng loạt
      FileController     nạp/xuất file
      ResultsView        render kết quả + KPI + combobox
      SimulationView     vẽ mô phỏng + dữ liệu audit R1–R8
      OptimizationController  chạy NSGA-II / mở rộng / tinh chỉnh (thread)

File này KHÔNG chứa logic tính toán: thuật toán ở core/, xuất/nhập ở io_handlers/.
Các method công khai (test/harness/UI gọi) được giữ làm DELEGATOR mỏng tới
component tương ứng, nên API ngoài bất biến. Xem docs/reference/ARCHITECTURE.md.

Quản lý 2 tab:
    - Tab 1 (Interactive): nhập thông số/tải trọng, chạy tối ưu, vẽ mô phỏng,
      xuất kết quả; hỗ trợ chế độ "MCOC thực - tinh chỉnh từng bước".
    - Tab 2 (Batch): chạy hàng loạt nhiều file, xuất PDF/Excel/PNG.
"""

import os
import threading

import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES

from core.version import WINDOW_TITLE, __version__
from ui import constants as uiconst
from ui.controllers.loads import LoadsController
from ui.controllers.params import ParamsController
from ui.controllers.file_ops import FileController
from ui.controllers.results import ResultsView
from ui.controllers.simulation import SimulationView
from ui.controllers.optimization import OptimizationController
from ui.tabs.batch_tab import BatchTab
from ui.tabs.interactive_tab import InteractiveTab


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
        self.root.geometry(uiconst.WINDOW_GEOMETRY)
        self.root.minsize(uiconst.WINDOW_MIN_W, uiconst.WINDOW_MIN_H)
        # Mở MAXIMIZE để thấy nhiều thông tin cùng lúc (Windows). Bọc try cho an toàn.
        try:
            self.root.state('zoomed')
        except Exception:
            pass

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

        # --- Tối ưu MỞ RỘNG (R7/R8 + đổi đường kính + thu bệ) — gói core/ext ---
        self.ext_diameters = []                       # [{'d','Po','Ct','M','H'}, ...]
        self.var_ext_enable = tk.BooleanVar(value=False)   # bật luồng mở rộng
        self.var_ext_r7 = tk.BooleanVar(value=True)        # R7 lực ngang
        self.var_ext_r8 = tk.BooleanVar(value=True)        # R8 tương tác P-M
        self.var_ext_capresize = tk.BooleanVar(value=True) # tự thu bệ
        self.var_ext_round = tk.StringVar(value='0.1')     # bội số làm tròn bệ (m)
        self._ext_active = False     # phiên kết quả hiện tại là của luồng mở rộng?
        self._ext_hlimit = 0.0       # [H] của đường kính thắng (cho audit R7)

        # --- Xử lý BỆ CHẬT (tùy chọn, do người dùng kiểm soát — KHÔNG đổi mặc định) ---
        self.var_min_spacing = tk.StringVar(value='3.0')   # hệ số k/c tối thiểu ×d
        self.var_suggest_cap = tk.BooleanVar(value=True)   # đề xuất nới bệ khi vô nghiệm

        # --- Sức chịu tải theo TCVN 10304:2014 (tùy chọn — tự tính [Po]/[Ct]) ---
        # Khi bật, chương trình suy ra Rc,d/Rt,d từ Rc,k + hệ số tin cậy theo
        # Điều 7.1.11 và GHI ĐÈ [Po]/[Ct] (xem core/tcvn.apply_design_capacities).
        self.var_tcvn_enable = tk.BooleanVar(value=False)  # bật tự tính
        self.var_rck = tk.StringVar(value='')              # Rc,k — nén tiêu chuẩn (T)
        self.var_rtk = tk.StringVar(value='')              # Rt,k — kéo tiêu chuẩn (T, tùy chọn)
        self.var_g0 = tk.StringVar(value='1.15')           # γ0 — điều kiện làm việc
        self.var_gk = tk.StringVar(value='1.40')           # γk — theo đất
        self.var_gk_t = tk.StringVar(value='')             # γk,t — theo đất khi kéo (tùy chọn)
        self.var_imp_level = tk.StringVar(value='II')      # cấp công trình I/II/III → γn

        # --- Thông số NỀN & ĐÀI cọc (cho phân tích SSI và thiết kế kết cấu đài) ---
        self.var_pile_length = tk.StringVar(value='')        # Lc — chiều dài cọc (m)
        self.var_ks_soil = tk.StringVar(value='2000')        # ks — mô đun nền ngang (T/m³), DỰ PHÒNG
        self.var_group_effect = tk.BooleanVar(value=True)    # xét hiệu ứng nhóm cọc (p-mult)
        # Đặc trưng vật liệu/đất đọc từ file MCOC (Eb, m, Jo, Fo, Lc, H đài) cho engine SSI
        self._file_params = {}
        self.var_cap_h = tk.StringVar(value='')              # chiều cao đài H (m)
        self.var_col_b = tk.StringVar(value='')              # bề rộng cột/trụ bx (m)
        self.var_col_h = tk.StringVar(value='')              # chiều cao tiết diện cột by (m)
        self.var_conc_grade = tk.StringVar(value='B25')      # cấp bền bê tông đài
        self.var_steel_grade = tk.StringVar(value='CB400-V') # nhóm cốt thép
        self.var_cover = tk.StringVar(value='0.10')          # lớp bảo vệ a (m) tới trọng tâm thép
        # --- Trụ địa chất & lún (TCVN 10304 Điều 7.4 — móng khối quy ước) ---
        self.var_phi_tb = tk.StringVar(value='')       # φ trung bình dọc cọc (độ)
        self.var_cap_depth = tk.StringVar(value='')    # độ sâu đáy đài (m)
        self.var_gamma_avg = tk.StringVar(value='')    # γ' đẩy nổi TB trên đáy khối (T/m³)
        self.var_s_limit = tk.StringVar(value='0.08')  # lún giới hạn Sgh (m)
        # Đất dính yếu IL>0,6 dưới mũi cọc -> chặn a≤2d khi tính móng khối quy ước (Đ.7.4.4)
        self.var_soft_clay = tk.BooleanVar(value=False)

        self.loads = []
        self.current_config = None

        # --- Vòng đời 1 lần CHẠY tối ưu (Tab 1): khóa nút Chạy + tiến trình + Dừng ---
        self._run_cancel = threading.Event()  # đặt cờ -> evaluator bọc sẽ dừng vòng lặp
        self._is_running = False               # đang có 1 luồng tối ưu chạy?
        self._active_evaluator = None          # evaluator hiện hành (để đếm n_calls)

        # Các controller (Plan 023 — composition): thao tác qua tham chiếu `self`.
        # Tạo TRƯỚC setup_ui để mọi callback dựng UI gọi được qua delegator.
        self.params_ctl = ParamsController(self)
        self.loads_ctl = LoadsController(self)
        self.file_ctl = FileController(self)
        self.results_view = ResultsView(self)
        self.sim_view = SimulationView(self)
        self.opt_ctl = OptimizationController(self)
        self.interactive_tab = InteractiveTab(self)
        self.batch_tab = BatchTab(self)

        self.setup_ui()
        self.loads_ctl.add_default_loads()

        # Đặt vị trí sash panel trái/phải Tab 1 cho CÂN ĐỐI (panel trái đủ rộng cho
        # 2 cột nhập liệu, panel mô phỏng phải chiếm phần còn lại). PanedWindow bỏ
        # qua width của frame nên phải set sashpos sau khi cửa sổ đã có kích thước.
        self.root.after(180, self._init_sash)

        # Style ô nhập KHÔNG hợp lệ (nền hồng) — dùng cho kiểm tra tức thời.
        try:
            ttk.Style().configure("Invalid.TEntry", fieldbackground="#ffd6d6")
        except Exception:
            pass
        # Kiểm tra tức thời 4 thông số bắt buộc khi người dùng gõ (cập nhật trạng thái).
        for _k in ('L_X', 'L_Y', 'D_PILE', 'P_LIMIT'):
            try:
                self.params[_k].trace_add("write", self._validate_inputs)
            except Exception:
                pass

        # Phím tắt: Ctrl+O mở file, Ctrl+R chạy, Ctrl+S lưu, F1 hướng dẫn.
        self.root.bind("<Control-o>", lambda e: self.load_file())
        self.root.bind("<Control-r>", lambda e: (None if self._is_running else self.run_optimize()))
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<F1>", lambda e: self._show_help())

        # Hỗ trợ kéo-thả file vào cửa sổ
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

    def setup_ui(self):
        """Tạo Notebook 2 tab (Tương tác / Hàng loạt) và dựng giao diện từng tab."""
        # Thanh menu kiểu MCOC (File / Tính toán / Trợ giúp) — dựng trước tiên.
        self._build_menu()

        # Icon cửa sổ = logo TEDI (chạy dev lẫn đóng gói PyInstaller). iconbitmap
        # đặt icon thanh tiêu đề/taskbar trên Windows; iconphoto để đa nền tảng.
        try:
            import sys as _sys
            _base = getattr(_sys, '_MEIPASS',
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            _ico = os.path.join(_base, 'packaging', 'tedi.ico')
            if os.path.exists(_ico):
                self.root.iconbitmap(default=_ico)
            _png = os.path.join(_base, 'packaging', 'tedi_logo.png')
            if os.path.exists(_png):
                self._app_icon = tk.PhotoImage(file=_png)
                self.root.iconphoto(True, self._app_icon)
        except Exception:
            pass

        # Thanh trạng thái ghim ĐÁY cửa sổ (pack trước, side=BOTTOM, để Notebook ở
        # trên không đè lên). (trái) thông báo + (phải) nhãn phiên bản kiểu MCOC.
        status_wrap = tk.Frame(self.root, relief="sunken", bd=1)
        status_wrap.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(status_wrap, text=f"OptApp v{__version__} | Windows desktop",
                 anchor="e", padx=8, font=("Arial", 8), fg="#888").pack(side=tk.RIGHT)
        self.lbl_status = tk.Label(status_wrap, text="Sẵn sàng.", anchor="w", padx=6,
                                   font=("Arial", 9), fg="#333")
        self.lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_interactive = tk.Frame(self.notebook)
        self.notebook.add(self.tab_interactive, text="1. Tương tác (Interactive)")
        self.setup_interactive_ui(self.tab_interactive)

        self.tab_batch = tk.Frame(self.notebook)
        self.notebook.add(self.tab_batch, text="2. Hàng loạt (Batch Mode)")
        self.setup_batch_ui(self.tab_batch)

    # ========================================================================
    # THANH MENU (kiểu MCOC: File / Tính toán / Trợ giúp)
    # ========================================================================
    def _build_menu(self):
        """Dựng thanh menu giống MCOC Python.

        Các lệnh NHẬN BIẾT tab đang mở (Tương tác ↔ Hàng loạt) rồi gọi đúng
        hành động: ví dụ "Tính toán" sẽ chạy tối ưu ở Tab 1 hoặc chạy hàng
        loạt ở Tab 2; "Thêm thư mục" là khái niệm hàng loạt nên chuyển sang
        Tab 2. Accelerator chỉ là NHÃN — phím tắt thật được bind ở cuối.
        """
        menubar = tk.Menu(self.root)

        # ── File ──────────────────────────────────────────────────────
        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="Thêm file…", accelerator="Ctrl+O",
                           command=self._menu_add_file)
        m_file.add_command(label="Thêm thư mục…", accelerator="Ctrl+Shift+O",
                           command=self._menu_add_folder)
        m_file.add_separator()
        m_file.add_command(label="Xoá danh sách", command=self._menu_clear)
        m_file.add_separator()
        m_file.add_command(label="Thoát", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=m_file)

        # ── Tính toán ─────────────────────────────────────────────────
        m_run = tk.Menu(menubar, tearoff=0)
        m_run.add_command(label="Tính toán", accelerator="Ctrl+Enter",
                          command=self._menu_run)
        m_run.add_command(label="Dừng", accelerator="Esc",
                          command=self._menu_stop)
        m_run.add_separator()
        m_run.add_command(label="Mở thư mục kết quả", command=self._open_out_dir)
        menubar.add_cascade(label="Tính toán", menu=m_run)

        # ── Trợ giúp ──────────────────────────────────────────────────
        m_help = tk.Menu(menubar, tearoff=0)
        m_help.add_command(label="Hướng dẫn", accelerator="F1",
                           command=self._show_help)
        m_help.add_command(label="Giới thiệu", command=self._show_about)
        menubar.add_cascade(label="Trợ giúp", menu=m_help)

        self.root.config(menu=menubar)

        # Phím tắt cho các lệnh menu (accelerator ở trên chỉ là nhãn hiển thị).
        self.root.bind("<Control-Shift-O>", lambda e: self._menu_add_folder())
        self.root.bind("<Control-Return>", lambda e: self._menu_run())
        self.root.bind("<Escape>", lambda e: self._menu_stop())

    def _active_tab(self):
        """Chỉ số tab đang mở: 0 = Tương tác, 1 = Hàng loạt."""
        try:
            return self.notebook.index(self.notebook.select())
        except Exception:
            return 0

    def _init_sash(self):
        """Đặt sash panel trái Tab 1 ≈ 42% bề rộng (kẹp 560–820px) để 2 cột nhập
        liệu đủ chỗ và panel mô phỏng phải cân đối. Thử lại nếu cửa sổ chưa realize."""
        try:
            total = self.main_paned.winfo_width()
            if total < 300:
                self.root.after(120, self._init_sash)
                return
            target = min(900, max(600, int(total * 0.47)))
            self.main_paned.sashpos(0, target)
        except Exception:
            pass

    # --- Delegators -> ParamsController (Plan 023) ---
    def _load_demo_geotech(self, *a, **k):
        return self.params_ctl._load_demo_geotech(*a, **k)

    def _pget(self, *a, **k):
        return self.params_ctl._pget(*a, **k)

    def get_params_dict(self, *a, **k):
        return self.params_ctl.get_params_dict(*a, **k)

    def _validate_inputs(self, *a, **k):
        return self.params_ctl._validate_inputs(*a, **k)

    def _toggle_tcvn(self, *a, **k):
        return self.params_ctl._toggle_tcvn(*a, **k)

    def _update_tcvn_preview(self, *a, **k):
        return self.params_ctl._update_tcvn_preview(*a, **k)

    def _menu_add_file(self):
        """Thêm file — theo tab: Tab 2 nạp vào danh sách hàng loạt, Tab 1 mở
        file đầu vào tương tác."""
        if self._active_tab() == 1:
            self.load_file_batch()
        else:
            self.load_file()

    def _menu_add_folder(self):
        """Thêm cả thư mục — khái niệm hàng loạt nên chuyển sang Tab 2 rồi nạp."""
        self.notebook.select(self.tab_batch)
        self.load_folder_batch()

    def _menu_clear(self):
        """Xoá danh sách — theo tab đang mở."""
        if self._active_tab() == 1:
            self.clear_all_batch()
        else:
            self.clear_loads()

    def _menu_run(self):
        """Tính toán — Tab 2 chạy hàng loạt; Tab 1 chạy tối ưu (bỏ qua nếu đang chạy)."""
        if self._active_tab() == 1:
            self.run_batch()
        elif not self._is_running:
            self.run_optimize()

    def _menu_stop(self):
        """Dừng — theo tab: Tab 2 dừng hàng loạt, Tab 1 dừng tối ưu."""
        if self._active_tab() == 1:
            self._stop_batch()
        else:
            self._request_stop_opt()

    def _show_about(self):
        """Hộp thoại Giới thiệu (menu Trợ giúp)."""
        from core.version import APP_NAME, RELEASE_DATE
        messagebox.showinfo(
            "Giới thiệu",
            f"{APP_NAME}\n"
            f"Phiên bản {__version__}  (phát hành {RELEASE_DATE})\n\n"
            "Công cụ tối ưu bố trí cọc móng cầu — kiểm toán theo TCVN 10304:2014.\n"
            "Tương thích quy trình & đơn vị MCOC (lực = Tấn, momen = T.m).\n\n"
            "TEDI · Windows desktop")

    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: DỰNG GIAO DIỆN
    # ========================================================================
    # --- Delegators -> InteractiveTab (Plan 023) ---
    def setup_interactive_ui(self, *a, **k):
        return self.interactive_tab.setup_interactive_ui(*a, **k)

    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: NHẬP / SỬA TẢI TRỌNG
    # ========================================================================
    # Các method tải trọng đã chuyển sang ui/controllers/loads.LoadsController.
    # Giữ delegator mỏng cho nút bấm Tab 1 + harness/golden gọi trực tiếp.
    def refresh_loads_ui(self):
        return self.loads_ctl.refresh_loads_ui()

    def add_load_dialog(self):
        return self.loads_ctl.add_load_dialog()

    def edit_load(self):
        return self.loads_ctl.edit_load()

    def delete_load(self):
        return self.loads_ctl.delete_load()

    def paste_loads_csv(self):
        return self.loads_ctl.paste_loads_csv()

    # ========================================================================
    # ĐỌC THAM SỐ & NHẬP / XUẤT FILE
    # ========================================================================
    # --- Delegators -> FileController (Plan 023) ---
    def browse_exe(self, *a, **k):
        return self.file_ctl.browse_exe(*a, **k)

    def load_file(self, *a, **k):
        return self.file_ctl.load_file(*a, **k)

    def handle_drop(self, *a, **k):
        return self.file_ctl.handle_drop(*a, **k)

    def process_multiple_files(self, *a, **k):
        return self.file_ctl.process_multiple_files(*a, **k)

    def clear_loads(self, *a, **k):
        return self.file_ctl.clear_loads(*a, **k)

    def save_file(self, *a, **k):
        return self.file_ctl.save_file(*a, **k)

    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: CHẠY TỐI ƯU & HIỂN THỊ KẾT QUẢ
    # ========================================================================
    # --- Delegators -> OptimizationController (Plan 023) ---
    def _request_stop_opt(self, *a, **k):
        return self.opt_ctl._request_stop_opt(*a, **k)

    def run_optimize(self, *a, **k):
        return self.opt_ctl.run_optimize(*a, **k)

    def _toggle_ext(self, *a, **k):
        return self.opt_ctl._toggle_ext(*a, **k)

    def open_diameter_dialog(self, *a, **k):
        return self.opt_ctl.open_diameter_dialog(*a, **k)

    def _update_ext_dia_label(self, *a, **k):
        return self.opt_ctl._update_ext_dia_label(*a, **k)

    # ========================================================================
    # TAB 1 - VÒNG ĐỜI 1 LẦN CHẠY: khóa nút Chạy, tiến trình trực tiếp, Dừng
    # ========================================================================
    # ========================================================================
    # TAB 1 - THANH TRẠNG THÁI & KIỂM TRA THÔNG SỐ TỨC THỜI
    # ========================================================================
    def _set_status(self, text):
        """Cập nhật nội dung thanh trạng thái đáy cửa sổ (an toàn nếu chưa dựng)."""
        if hasattr(self, 'lbl_status'):
            self.lbl_status.config(text=text)

    def _show_help(self):
        """Hộp thoại hướng dẫn nhanh (F1): quy trình 4 bước + đơn vị + phím tắt."""
        messagebox.showinfo(
            "Hướng dẫn nhanh",
            "QUY TRÌNH 4 BƯỚC:\n"
            "  ① Cấu hình MCOC (chọn MCOC Batch).\n"
            "  ② Mở file đầu vào MCOC gốc (.txt — có tọa độ cọc gốc).\n"
            "  ③ Nhập thông số bài toán (Lx, Ly, d, [Po]) và tổ hợp tải.\n"
            "  ④ Bấm ▶ CHẠY TỐI ƯU HÓA.\n\n"
            "ĐƠN VỊ (theo MCOC): lực = Tấn (T); momen = T.m.\n"
            "Lưu ý: [Po]/[Ct]/[M] trong file chỉ là MẶC ĐỊNH — nhập sức chịu "
            "tải THẬT theo đường kính cọc.\n\n"
            "PHÍM TẮT:\n"
            "  Ctrl+O: Mở file    Ctrl+R: Chạy\n"
            "  Ctrl+S: Xuất kết quả    F1: Hướng dẫn này")

    def _show_nsga2_results(self, *a, **k):
        return self.results_view._show_nsga2_results(*a, **k)

    def _show_ext_results(self, *a, **k):
        return self.results_view._show_ext_results(*a, **k)

    def _log_refine(self, *a, **k):
        return self.results_view._log_refine(*a, **k)

    def _show_refine_results(self, *a, **k):
        return self.results_view._show_refine_results(*a, **k)

    def _update_kpi(self, *a, **k):
        return self.results_view._update_kpi(*a, **k)

    def populate_comboboxes(self, *a, **k):
        return self.results_view.populate_comboboxes(*a, **k)

    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: TỐI ƯU MỞ RỘNG (R7/R8 + đổi đường kính + thu bệ)
    # ========================================================================
    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: HỘP ĐEN MCOC THỰC (tinh chỉnh từng bước)
    # ========================================================================
    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: MÔ PHỎNG & COMBOBOX
    # ========================================================================
    # --- Delegators -> SimulationView (Plan 023) ---
    def update_simulation(self, *a, **k):
        return self.sim_view.update_simulation(*a, **k)

    def _config_fully_ok(self, *a, **k):
        return self.sim_view._config_fully_ok(*a, **k)

    # ========================================================================
    # TAB 2 - HÀNG LOẠT: DỰNG GIAO DIỆN
    # ========================================================================
    # --- Delegators -> BatchTab (Plan 023) ---
    def setup_batch_ui(self, *a, **k):
        return self.batch_tab.setup_batch_ui(*a, **k)

    def load_file_batch(self, *a, **k):
        return self.batch_tab.load_file_batch(*a, **k)

    def load_folder_batch(self, *a, **k):
        return self.batch_tab.load_folder_batch(*a, **k)

    def clear_all_batch(self, *a, **k):
        return self.batch_tab.clear_all_batch(*a, **k)

    def _open_out_dir(self, *a, **k):
        return self.batch_tab._open_out_dir(*a, **k)

    def _stop_batch(self, *a, **k):
        return self.batch_tab._stop_batch(*a, **k)

    def run_batch(self, *a, **k):
        return self.batch_tab.run_batch(*a, **k)

    # ========================================================================
    # TAB 2 - HÀNG LOẠT: QUẢN LÝ DANH SÁCH FILE & TRẠNG THÁI
    # ========================================================================
    # ========================================================================
    # TAB 2 - HÀNG LOẠT: LOGIC CHẠY & XUẤT KẾT QUẢ
    # ========================================================================
