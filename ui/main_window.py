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
from core.constants import effective_min_spacing
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
# TIỆN ÍCH: TOOLTIP (chú thích bật lên khi rê chuột)
# ============================================================================
class Tooltip:
    """Chú thích nhỏ hiện ra khi rê chuột vào widget (di chuột ra thì ẩn).

    Dùng Toplevel không viền chứa 1 Label. Gắn vào widget bằng cách khởi tạo:
        Tooltip(widget, "Nội dung chú thích").
    """

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self._tip = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _show(self, _event=None):
        if self._tip or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 16
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        except Exception:
            return
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self._tip, text=self.text, justify="left",
                 background="#ffffe0", foreground="#333",
                 relief="solid", borderwidth=1,
                 font=("Arial", 8), wraplength=260, padx=6, pady=3).pack()

    def _hide(self, _event=None):
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


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

        self.loads = []
        self.current_config = None

        # --- Vòng đời 1 lần CHẠY tối ưu (Tab 1): khóa nút Chạy + tiến trình + Dừng ---
        self._run_cancel = threading.Event()  # đặt cờ -> evaluator bọc sẽ dừng vòng lặp
        self._is_running = False               # đang có 1 luồng tối ưu chạy?
        self._active_evaluator = None          # evaluator hiện hành (để đếm n_calls)

        self.setup_ui()
        self.add_default_loads()

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
        # Thanh trạng thái ghim ĐÁY cửa sổ (pack trước, side=BOTTOM, để Notebook ở
        # trên không đè lên). Cập nhật từ nạp file / kiểm tra thông số / chạy.
        self.lbl_status = tk.Label(self.root, text="Sẵn sàng.", anchor="w",
                                   relief="sunken", bd=1, padx=6,
                                   font=("Arial", 9), fg="#333")
        self.lbl_status.pack(side=tk.BOTTOM, fill=tk.X)

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

        # Left Panel — chia DỌC: (trên) nút IO + vùng nhập liệu CUỘN ĐƯỢC + nút Chạy;
        # (dưới) ô "Kết quả Đánh giá" tách riêng, kéo sash để đổi cỡ nên không bị bóp.
        left_frame = tk.Frame(main_paned, width=440)
        main_paned.add(left_frame, weight=0)

        left_paned = ttk.PanedWindow(left_frame, orient=tk.VERTICAL)
        left_paned.pack(fill=tk.BOTH, expand=True)

        # ── Pane trên: IO (ghim) + vùng cuộn nhập liệu + nút Chạy (ghim đáy) ──
        top_pane = tk.Frame(left_paned)
        left_paned.add(top_pane, weight=3)

        # Buttons IO — ghim trên cùng (không cuộn)
        frame_io = tk.Frame(top_pane, padx=10)
        frame_io.pack(side=tk.TOP, fill=tk.X, pady=(10, 2))
        ttk.Button(frame_io, text="Mở file đầu vào  (hoặc kéo-thả)", command=self.load_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(frame_io, text="Làm mới", command=self.clear_loads).pack(side=tk.LEFT, fill=tk.X, expand=False, padx=2)
        ttk.Button(frame_io, text="Xuất kết quả", command=self.save_file).pack(side=tk.RIGHT, fill=tk.X, expand=False, padx=2)

        # Nút CHẠY — ghim đáy pane trên (gọn), luôn thấy dù vùng nhập liệu đang cuộn
        # Cụm tiến trình + nút DỪNG — ghim đáy DƯỚI nút Chạy (pack BOTTOM xếp chồng
        # ngược nên cụm này được khai báo TRƯỚC để nằm dưới cùng).
        run_state_frame = tk.Frame(top_pane)
        run_state_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 8))
        self.progress_run = ttk.Progressbar(run_state_frame, mode="indeterminate")
        self.progress_run.pack(side=tk.TOP, fill=tk.X)
        bottom_row = tk.Frame(run_state_frame)
        bottom_row.pack(side=tk.TOP, fill=tk.X, pady=(2, 0))
        self.lbl_run_status = ttk.Label(bottom_row, text="")
        self.lbl_run_status.pack(side=tk.LEFT)
        self.btn_stop_opt = ttk.Button(bottom_row, text="■ Dừng", state="disabled",
                                       command=self._request_stop_opt)
        self.btn_stop_opt.pack(side=tk.RIGHT)

        # Nút CHẠY — ghim đáy pane trên (gọn), luôn thấy dù vùng nhập liệu đang cuộn
        self.btn_run_opt = tk.Button(top_pane, text="▶ CHẠY TỐI ƯU HÓA",
                                     font=("Arial", 11, "bold"), bg="#27ae60", fg="white",
                                     command=self.run_optimize)
        self.btn_run_opt.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(4, 4), ipady=4)

        # Vùng CUỘN ở giữa: Canvas + Scrollbar; mọi mục nhập liệu nằm trong `inner`.
        scroll_holder = tk.Frame(top_pane)
        scroll_holder.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scroll_canvas = tk.Canvas(scroll_holder, borderwidth=0, highlightthickness=0)
        scroll_vsb = ttk.Scrollbar(scroll_holder, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scroll_vsb.set)
        scroll_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = tk.Frame(scroll_canvas, padx=10, pady=4)
        inner_id = scroll_canvas.create_window((0, 0), window=inner, anchor="nw")
        # scrollregion theo nội dung; ép bề rộng inner = bề rộng canvas (không tràn ngang)
        inner.bind("<Configure>",
                   lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.bind("<Configure>",
                           lambda e: scroll_canvas.itemconfig(inner_id, width=e.width))

        # Lăn chuột chỉ khi con trỏ ở trong vùng cuộn (không cướp wheel của hình/Tab 2)
        def _on_wheel(e):
            scroll_canvas.yview_scroll(int(-e.delta / 120), "units")
        scroll_canvas.bind("<Enter>", lambda e: scroll_canvas.bind_all("<MouseWheel>", _on_wheel))
        scroll_canvas.bind("<Leave>", lambda e: scroll_canvas.unbind_all("<MouseWheel>"))

        # Băng hướng dẫn quy trình (gọn, màu xám) — luôn ở đầu vùng nhập liệu
        ttk.Label(
            inner,
            text="Quy trình: ① Cấu hình MCOC  →  ② Mở file đầu vào  →  "
                 "③ Nhập thông số & tải  →  ④ ▶ Chạy",
            foreground="#666", wraplength=400, justify="left").pack(
            anchor="w", pady=(0, 4))

        # Geometrics
        frame_geom = tk.LabelFrame(inner, text="Thông số Bài toán", padx=10, pady=5)
        frame_geom.pack(fill=tk.X, pady=5)

        # Bố cục 2 CỘT CÂN ĐỐI: trái = KÍCH THƯỚC hình học, phải = SỨC CHỊU TẢI.
        # Mỗi nhãn 1 cột + ô nhập 1 cột co giãn (sticky=ew) nên ô [Po]/[Ct]/[M]
        # LUÔN hiện đủ, không bị cắt dù panel hẹp.
        geom_fields = [("L_X", "Rộng bệ Lx (m)"), ("L_Y", "Dài bệ Ly (m)"),
                       ("D_PILE", "Đ.kính cọc d (m)")]
        cap_fields = [("P_LIMIT", "Sức nén [Po] (T)"), ("P_TENSION", "Sức nhổ [Ct] (T)"),
                      ("M_LIMIT", "Sức uốn [M] (T.m)")]
        # Chú thích ngắn (tiếng Việt) gắn vào nhãn từng trường khi rê chuột.
        param_tips = {
            'D_PILE': "Đường kính cọc d (m). Quyết định k/c tối thiểu (×d) và sức "
                      "chịu tải thật của cọc.",
            'P_LIMIT': "[Po] — sức chịu nén thiết kế của 1 cọc (T). Nhập giá trị "
                       "THẬT theo đường kính, KHÔNG dùng mặc định 500 trong file.",
            'P_TENSION': "[Ct] — sức chịu nhổ thiết kế của 1 cọc (T). Để trống nếu "
                         "không kiểm tra điều kiện nhổ.",
            'M_LIMIT': "[M] — sức chịu uốn cho phép (T.m). Để trống/0 nếu không "
                       "kiểm tra điều kiện uốn.",
        }
        self._param_entries = {}
        for r, (k, text) in enumerate(geom_fields):
            lbl = ttk.Label(frame_geom, text=text)
            lbl.grid(row=r, column=0, sticky="w", padx=(2, 4), pady=2)
            if k in param_tips:
                Tooltip(lbl, param_tips[k])
            e = ttk.Entry(frame_geom, textvariable=self.params[k], width=9)
            e.grid(row=r, column=1, sticky="ew", padx=(0, 8), pady=2)
            self._param_entries[k] = e
        for r, (k, text) in enumerate(cap_fields):
            lbl = ttk.Label(frame_geom, text=text)
            lbl.grid(row=r, column=2, sticky="w", padx=(2, 4), pady=2)
            if k in param_tips:
                Tooltip(lbl, param_tips[k])
            e = ttk.Entry(frame_geom, textvariable=self.params[k], width=9)
            e.grid(row=r, column=3, sticky="ew", padx=(0, 2), pady=2)
            self._param_entries[k] = e
        # Cho 2 cột ô nhập co giãn theo bề rộng panel (chia đều), nhãn giữ cố định.
        frame_geom.columnconfigure(1, weight=1, minsize=60)
        frame_geom.columnconfigure(3, weight=1, minsize=60)

        # Ghi chú đơn vị — tránh nhầm giữa tải trọng (kN) và sức chịu tải (Tấn)
        ttk.Label(frame_geom,
                  text="Đơn vị (theo MCOC): lực = Tấn (T); momen = T.m. Áp dụng cho cả tải trọng và [Po]/[Ct]/[M].",
                  foreground="#888", wraplength=380, justify="left").grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))
        # Cảnh báo: [Po] trong file input MCOC chỉ là MẶC ĐỊNH (thường 500) — phải
        # nhập sức chịu tải THẬT theo đường kính (vd cọc d=2.0 m ~ 2000 T), nếu
        # không mọi phương án sẽ "trượt" và không tìm được lời giải.
        ttk.Label(frame_geom,
                  text="⚠ [Po]/[Ct]/[M] trong file input chỉ là MẶC ĐỊNH — hãy nhập sức chịu tải THẬT theo đường kính cọc.",
                  foreground="#b03a2e", wraplength=380, justify="left").grid(
            row=4, column=0, columnspan=4, sticky="w", pady=(2, 0))

        # --- Sức chịu tải theo TCVN 10304:2014 (tùy chọn) ---
        # Cho phép kỹ sư nhập Rc,k + hệ số tin cậy để chương trình TỰ TÍNH [Po]/[Ct]
        # theo Điều 7.1.11 (Rc,d = γ0/γn · Rc,k/γk). Khi bật, giá trị tính được sẽ
        # GHI ĐÈ [Po]/[Ct] (xem get_params_dict + core/tcvn.apply_design_capacities).
        frame_tcvn = tk.LabelFrame(
            inner, text="Sức chịu tải theo TCVN 10304:2014 (tùy chọn)",
            padx=10, pady=5)
        frame_tcvn.pack(fill=tk.X, pady=5)
        chk_tcvn = ttk.Checkbutton(
            frame_tcvn, text="Tự tính [Po]/[Ct] từ Rc,k",
            variable=self.var_tcvn_enable, command=self._toggle_tcvn)
        chk_tcvn.pack(anchor="w")
        Tooltip(chk_tcvn, "Bật để chương trình suy ra sức chịu tải THIẾT KẾ "
                          "Rc,d/Rt,d từ sức chịu tải tiêu chuẩn Rc,k và các hệ số "
                          "tin cậy theo TCVN 10304:2014 Điều 7.1.11. Khi bật, "
                          "[Po]/[Ct] sẽ được tính tự động (ô nhập tay bị khóa).")

        self.frame_tcvn_body = tk.Frame(frame_tcvn)
        self.frame_tcvn_body.pack(fill=tk.X, pady=(4, 0))
        tcvn_fields = [
            ("Rc,k — nén tiêu chuẩn (T)", self.var_rck,
             "Rc,k — sức chịu tải NÉN tiêu chuẩn của 1 cọc (T). Nếu xác định bằng "
             "tính toán thì lấy bằng sức chịu tải cực hạn Rc,u."),
            ("Rt,k — kéo tiêu chuẩn (T, tùy chọn)", self.var_rtk,
             "Rt,k — sức chịu tải KÉO tiêu chuẩn (T). Để trống nếu không kiểm tra "
             "điều kiện nhổ."),
            ("γ0 — điều kiện làm việc", self.var_g0,
             "γ0 — hệ số điều kiện làm việc (mặc định 1.15)."),
            ("γk — theo đất", self.var_gk,
             "γk — hệ số tin cậy theo đất (mặc định 1.40)."),
            ("γk,t — theo đất khi kéo (tùy chọn)", self.var_gk_t,
             "γk,t — hệ số tin cậy theo đất khi KÉO. Để trống = dùng chung γk."),
        ]
        for r, (text, var, tip) in enumerate(tcvn_fields):
            lbl = ttk.Label(self.frame_tcvn_body, text=text)
            lbl.grid(row=r, column=0, sticky="w", padx=(2, 4), pady=2)
            Tooltip(lbl, tip)
            e = ttk.Entry(self.frame_tcvn_body, textvariable=var, width=10)
            e.grid(row=r, column=1, sticky="ew", padx=(0, 2), pady=2)
        lbl_lv = ttk.Label(self.frame_tcvn_body, text="Cấp công trình (γn)")
        lbl_lv.grid(row=len(tcvn_fields), column=0, sticky="w", padx=(2, 4), pady=2)
        Tooltip(lbl_lv, "Cấp công trình → hệ số tin cậy tầm quan trọng γn: "
                        "I=1.20, II=1.15, III=1.10.")
        cb_lv = ttk.Combobox(self.frame_tcvn_body, textvariable=self.var_imp_level,
                             values=['I', 'II', 'III'], width=7, state="readonly")
        cb_lv.grid(row=len(tcvn_fields), column=1, sticky="w", padx=(0, 2), pady=2)
        self.frame_tcvn_body.columnconfigure(1, weight=1, minsize=60)

        # Xem trước kết quả tính (cập nhật tức thời khi đổi tham số)
        self.lbl_tcvn_preview = ttk.Label(
            self.frame_tcvn_body, text="→ nhập Rc,k để tính",
            foreground="#1a6", wraplength=360, justify="left")
        self.lbl_tcvn_preview.grid(
            row=len(tcvn_fields) + 1, column=0, columnspan=2, sticky="w",
            pady=(4, 0))

        # Gắn trace cập nhật xem trước cho mọi biến TCVN (null-safe khi dựng UI)
        for _v in (self.var_rck, self.var_rtk, self.var_g0, self.var_gk,
                   self.var_gk_t, self.var_imp_level):
            _v.trace_add("write", self._update_tcvn_preview)
        self._toggle_tcvn()          # đặt trạng thái ban đầu (ẩn/mờ body)
        self._update_tcvn_preview()  # tính xem trước lần đầu

        # Loads
        frame_loads = tk.LabelFrame(inner, text="Tổ hợp Tải trọng", padx=10, pady=5)
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
        frame_load_btns = tk.Frame(inner)
        frame_load_btns.pack(fill=tk.X, pady=(0, 3))
        ttk.Button(frame_load_btns, text="Thêm tổ hợp",   command=self.add_load_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="Sửa dòng chọn", command=self.edit_load).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="Xóa dòng chọn", command=self.delete_load).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="Dán nhiều dòng (CSV)", command=self.paste_loads_csv).pack(side=tk.RIGHT, padx=2)

        # --- ĐIỀU KHIỂN & KẾT QUẢ TỐI ƯU ---
        frame_run = tk.LabelFrame(inner, text="Điều Khiển Tối Ưu", padx=10, pady=5)
        frame_run.pack(fill=tk.X, pady=5)

        self.output_option = tk.StringVar(value="BEST")
        row_out = tk.Frame(frame_run); row_out.pack(fill=tk.X)
        ttk.Radiobutton(row_out, text="Chỉ phương án tối ưu", variable=self.output_option, value="BEST").pack(side=tk.LEFT)
        ttk.Radiobutton(row_out, text="Hiện tất cả phương án", variable=self.output_option, value="ALL").pack(side=tk.LEFT, padx=10)

        # Mục tiêu phụ (sau khi đủ số cọc + đạt Pmax<=Po)
        self.var_secondary = tk.StringVar(value="compact")
        row_sec = tk.Frame(frame_run); row_sec.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(row_sec, text="Ưu tiên:").pack(side=tk.LEFT)
        rb_compact = ttk.Radiobutton(row_sec, text="Tiết kiệm (bệ gọn)", variable=self.var_secondary,
                        value="compact")
        rb_compact.pack(side=tk.LEFT, padx=4)
        Tooltip(rb_compact, "Sau khi đủ cọc & đạt Pmax≤[Po], ưu tiên bố trí GỌN "
                            "(bệ nhỏ, ít tốn vật liệu).")
        rb_pmax = ttk.Radiobutton(row_sec, text="An toàn (giảm Pmax)", variable=self.var_secondary,
                        value="pmax")
        rb_pmax.pack(side=tk.LEFT, padx=10)
        Tooltip(rb_pmax, "Sau khi đủ cọc, ưu tiên GIẢM lực nén lớn nhất Pmax "
                         "(tăng dự trữ an toàn).")

        # Xử lý bệ chật (tùy chọn): k/c tối thiểu + đề xuất nới bệ. Mặc định 3d và
        # BẬT gợi ý — không đổi thuật toán, chỉ là lựa chọn người dùng kiểm soát.
        row_sp = tk.Frame(frame_run); row_sp.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(row_sp, text="K/c tối thiểu:").pack(side=tk.LEFT)
        cb_minsp = ttk.Combobox(row_sp, textvariable=self.var_min_spacing,
                     values=['3.0', '2.75', '2.5'], width=5, state="readonly")
        cb_minsp.pack(side=tk.LEFT, padx=2)
        Tooltip(cb_minsp, "Hệ số khoảng cách tim cọc tối thiểu (×d). TCVN khuyến "
                          "nghị 3.0d; giảm xuống 2.75d/2.5d chỉ khi bệ quá chật.")
        ttk.Label(row_sp, text="×d", foreground="#888").pack(side=tk.LEFT)
        chk_suggest = ttk.Checkbutton(row_sp, text="Đề xuất nới bệ khi bệ chật",
                        variable=self.var_suggest_cap)
        chk_suggest.pack(side=tk.LEFT, padx=(12, 0))
        Tooltip(chk_suggest, "Khi không xếp đủ cọc trong bệ hiện tại, gợi ý kích "
                             "thước bệ tối thiểu cần nới rộng.")

        # --- TỐI ƯU MỞ RỘNG: gộp chung vào "Điều Khiển Tối Ưu" (ngăn bằng đường kẻ) ---
        ttk.Separator(frame_run, orient="horizontal").pack(fill=tk.X, pady=(8, 4))
        ttk.Checkbutton(frame_run,
                        text="Bật tối ưu mở rộng (đổi đường kính cọc + thu bệ)",
                        variable=self.var_ext_enable,
                        command=self._toggle_ext).pack(anchor="w")
        self.frame_ext_body = tk.Frame(frame_run)

        row_chk = tk.Frame(self.frame_ext_body); row_chk.pack(fill=tk.X, pady=(2, 0))
        chk_r7 = ttk.Checkbutton(row_chk, text="R7 lực ngang [H]",
                        variable=self.var_ext_r7)
        chk_r7.pack(side=tk.LEFT)
        Tooltip(chk_r7, "R7: kiểm tra sức chịu LỰC NGANG [H] của cọc (cần khai báo "
                        "[H] trong bảng đường kính).")
        chk_r8 = ttk.Checkbutton(row_chk, text="R8 tương tác P–M",
                        variable=self.var_ext_r8)
        chk_r8.pack(side=tk.LEFT, padx=10)
        Tooltip(chk_r8, "R8: kiểm tra TƯƠNG TÁC nén–uốn (P–M) trên tiết diện cọc.")

        row_cap = tk.Frame(self.frame_ext_body); row_cap.pack(fill=tk.X, pady=(2, 0))
        chk_resize = ttk.Checkbutton(row_cap, text="Tự thu bệ",
                        variable=self.var_ext_capresize)
        chk_resize.pack(side=tk.LEFT)
        Tooltip(chk_resize, "Tự động THU NHỎ kích thước bệ về mức tối thiểu vừa đủ "
                            "bố trí cọc (làm tròn theo bội số đã chọn).")
        ttk.Label(row_cap, text="Làm tròn (m):").pack(side=tk.LEFT, padx=(8, 2))
        ttk.Combobox(row_cap, textvariable=self.var_ext_round,
                     values=['0.05', '0.1', '0.25', '0.5', '1.0'], width=5,
                     state="readonly").pack(side=tk.LEFT)

        row_dia = tk.Frame(self.frame_ext_body); row_dia.pack(fill=tk.X, pady=(2, 0))
        ttk.Button(row_dia, text="Bảng đường kính...",
                   command=self.open_diameter_dialog).pack(side=tk.LEFT)
        self.lbl_ext_dia = ttk.Label(row_dia, text="(chưa có — sẽ dùng d hiện tại)",
                                     foreground="#888")
        self.lbl_ext_dia.pack(side=tk.LEFT, padx=6)
        self._toggle_ext()   # ẩn body khi chưa bật

        # --- Cấu hình MCOC (bắt buộc — mọi phương án được chấm bằng MCOC chính xác) ---
        frame_mcoc = tk.LabelFrame(inner, text="Cấu hình MCOC (bắt buộc)", padx=10, pady=5)
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

        # ── Pane dưới: ô KẾT QUẢ ĐÁNH GIÁ (tách riêng, kéo sash để đổi cỡ) ──
        res_pane = tk.LabelFrame(left_paned, text="Kết quả Đánh giá", padx=8, pady=4)
        left_paned.add(res_pane, weight=2)

        self.txt_result = tk.Text(res_pane, height=12, width=40, font=("Consolas", 10))
        # Thẻ màu để dễ quét kết quả: ĐẠT xanh, KHÔNG ĐẠT đỏ, tiêu đề xanh đậm.
        self.txt_result.tag_config("ok", foreground="#1e8449")
        self.txt_result.tag_config("bad", foreground="#b03a2e")
        self.txt_result.tag_config("head", foreground="#1a3c5e", font=("Consolas", 10, "bold"))
        self.txt_result.tag_config("muted", foreground="#888")
        res_vsb = ttk.Scrollbar(res_pane, orient="vertical", command=self.txt_result.yview)
        self.txt_result.configure(yscrollcommand=res_vsb.set)
        res_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_result.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

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

        # Chế độ hiển thị: Mặt bằng bố trí ⇄ Bảng kiểm tra điều kiện R1–R8 (chuẩn tư vấn)
        self.view_mode = tk.StringVar(value="layout")
        ttk.Radiobutton(frame_sim, text="Mặt bằng", variable=self.view_mode,
                        value="layout", command=self.update_simulation).pack(side=tk.LEFT, padx=(12, 2))
        ttk.Radiobutton(frame_sim, text="Kiểm tra điều kiện (R1–R8)", variable=self.view_mode,
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
        # Auto-scale: ghi chú phạm vi tự xuống dòng theo bề rộng panel phải,
        # tránh chữ bị cắt/đổi bố cục khi người dùng kéo chỉnh layout.
        right_frame.bind(
            "<Configure>",
            lambda e: self.lbl_scope.config(wraplength=max(e.width - 16, 200)))

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
        # Hệ số k/c tối thiểu do người dùng chọn (mặc định 3.0 = giữ nguyên TCVN).
        try:
            d['SPACING_MIN_FACTOR'] = float(self.var_min_spacing.get())
        except (ValueError, AttributeError):
            d['SPACING_MIN_FACTOR'] = 3.0
        # Nếu người dùng bật panel TCVN trên GUI: nạp Rc,k + hệ số tin cậy vào d
        # để apply_design_capacities() suy ra Rc,d/Rt,d (Điều 7.1.11). Chỉ áp khi
        # Rc,k hợp lệ (>0); ô trống → giữ mặc định của core.
        try:
            if self.var_tcvn_enable.get():
                rck = (self.var_rck.get() or '').strip()
                rck_val = float(rck) if rck else 0.0
                if rck_val > 0:
                    d['R_C_K'] = rck_val
                    rtk = (self.var_rtk.get() or '').strip()
                    if rtk:
                        d['R_T_K'] = float(rtk)
                    g0 = (self.var_g0.get() or '').strip()
                    d['GAMMA_0'] = float(g0) if g0 else 1.15
                    gk = (self.var_gk.get() or '').strip()
                    d['GAMMA_K'] = float(gk) if gk else 1.40
                    gk_t = (self.var_gk_t.get() or '').strip()
                    if gk_t:
                        d['GAMMA_K_T'] = float(gk_t)
                    d['IMPORTANCE_LEVEL'] = self.var_imp_level.get()
        except (ValueError, AttributeError):
            pass
        # Chuẩn hóa [Po]/[Ct] -> Rc,d/Rt,d theo TCVN 10304:2014 Điều 7.1.11 nếu
        # người dùng đã khai báo Rc,k + hệ số tin cậy (qua file/CSV/GUI). Idempotent.
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

                # Cập nhật thông số HÌNH HỌC từ file (Lx/Ly/d là số liệu THẬT).
                for k in ('L_X', 'L_Y', 'D_PILE'):
                    if k in params and params[k] is not None and params[k] > 0:
                        # StringVar: hiển thị gọn (bỏ ".0" thừa)
                        self.params[k].set(f"{params[k]:g}")

                # Giới hạn SỨC CHỊU TẢI ([Po]/[Ct]/[M]) trong file MCOC chỉ là GIÁ
                # TRỊ MẶC ĐỊNH (thường 500) — MCOC không dùng để chấm. Vì vậy CHỈ
                # điền khi ô đang TRỐNG, KHÔNG ghi đè giá trị người dùng đã nhập
                # (tránh bẫy: nạp file làm [Po] bị về 500 -> mọi phương án "trượt").
                for k in ('P_LIMIT', 'P_TENSION', 'M_LIMIT'):
                    cur = self.params[k].get().strip()
                    if (not cur) and k in params and params[k] is not None and params[k] > 0:
                        self.params[k].set(f"{params[k]:g}")

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

            self._set_status(
                "Đã nạp %d file (%d tổ hợp tải)." % (success_count, total_new_loads))
            self._validate_inputs()

    def clear_loads(self):
        """Làm mới: xóa tải trọng, THÔNG SỐ BÀI TOÁN, file gốc và kết quả.

        Đưa Tab Tương tác về trạng thái trắng như lúc vừa mở app (trừ cấu hình
        MCOC Batch — là tùy chọn công cụ, giữ lại cho tiện)."""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn LÀM MỚI toàn bộ (tải trọng, thông số bài toán, file gốc và kết quả) không?"):
            self.loads = []
            self.refresh_loads_ui()

            # 1) Xóa trắng các ô THÔNG SỐ BÀI TOÁN (L_X, L_Y, d, [Po], [Ct], [M])
            for k in self.NUMERIC_PARAMS:
                if k in self.params:
                    self.params[k].set('')
            # Mở khóa lại L_X / L_Y (có thể đã bị khóa sau khi nạp file)
            for k in ('L_X', 'L_Y'):
                if k in self._param_entries:
                    self._param_entries[k].config(state='normal')

            # 2) Reset trạng thái FILE GỐC (template MCOC) + nhãn hiển thị
            self.input_filepath = ''
            self.original_coords = []
            self.project_name = "Du An Toi Uu Coc"
            if hasattr(self, 'lbl_template'):
                self.lbl_template.config(text="File input gốc: (chưa có)", foreground="gray")

            # 3) Xóa các giá trị "gốc" nội bộ đọc từ file (để không lẫn sang lần sau)
            for attr in ('original_d', 'original_p', 'orig_pmax', 'orig_pmin',
                         'orig_mxmax', 'orig_mymax', 'result_filepath'):
                if hasattr(self, attr):
                    delattr(self, attr)

            # 4) Reset trạng thái TỐI ƯU MỞ RỘNG (bảng đường kính + cờ audit)
            self.ext_diameters = []
            self._ext_active = False
            self._ext_hlimit = 0.0
            self._last_ext_out = None
            if hasattr(self, 'lbl_ext_dia'):
                self._update_ext_dia_label()

            # 5) Reset UI kết quả như lúc mới mở
            self.current_config = None
            self.txt_result.delete(1.0, tk.END)
            self.cb_config.set('')
            self.cb_config['values'] = []
            # Xóa luôn ô Tổ hợp + dải KPI (số cọc/hệ số sử dụng/trạng thái) — nếu
            # không, chúng giữ giá trị phương án cũ dù đã làm mới.
            self.cb_load_case.set('')
            self.cb_load_case['values'] = []
            self.lbl_kpi.config(text="", fg="#1a3c5e")
            self.view_mode.set('layout')
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

            # Tham số + tùy chọn báo cáo. Nếu là phiên TỐI ƯU MỞ RỘNG: thêm [H],
            # bật R7/R8 và đính kèm mục 3b (quét đường kính + thu bệ).
            report_params = self.get_params_dict()
            report_kwargs = {}
            if getattr(self, '_ext_active', False) and getattr(self, '_last_ext_out', None):
                report_params['H_LIMIT'] = getattr(self, '_ext_hlimit', 0.0)
                out = self._last_ext_out
                cfg_ext = getattr(self, '_last_ext_cfg', None)
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
                    report_path, self.current_config, report_params,
                    self.loads, getattr(self, 'project_name', 'Du An Toi Uu Coc'),
                    **report_kwargs)
            except Exception:
                report_path = None

            # 1c. Xuất BÁO CÁO KỸ THUẬT dạng PDF (cùng nội dung, có bảng R1-R8, font Việt)
            pdf_report_path = os.path.join(base_dir, f"{base_name}_baocao_kythuat.pdf")
            try:
                export_technical_report_pdf(
                    pdf_report_path, self.current_config, report_params,
                    self.loads, getattr(self, 'project_name', 'Du An Toi Uu Coc'),
                    **report_kwargs)
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
    def _validate_mcoc_setup(self):
        """Kiểm tra cấu hình MCOC bắt buộc (exe + file input gốc + tọa độ cọc gốc).

        Trả về True nếu hợp lệ; nếu thiếu thì hiện cảnh báo phù hợp và trả về False.
        Dùng chung cho run_optimize / run_optimize_ext / run_refine_real.
        """
        exe = self.params['exe_path'].get().strip()
        if not exe or not os.path.exists(exe):
            messagebox.showwarning(
                "Cần cấu hình MCOC",
                "Mọi phương án được chấm bằng MCOC (chính xác).\n"
                "Hãy chọn đường dẫn MCOC Batch ở mục \"Cấu hình MCOC (bắt buộc)\".")
            return False
        if (not self.input_filepath or not os.path.exists(self.input_filepath)
                or not getattr(self, 'original_coords', None)):
            messagebox.showwarning(
                "Thiếu file MCOC gốc",
                "Cần mở FILE INPUT MCOC gốc (.txt, có tọa độ cọc gốc) làm template.\n"
                "Dùng \"Mở file đầu vào\" để nạp file input MCOC — không phải file _result hay CSV.")
            return False
        return True

    # ========================================================================
    # TAB 1 - VÒNG ĐỜI 1 LẦN CHẠY: khóa nút Chạy, tiến trình trực tiếp, Dừng
    # ========================================================================
    def _set_running(self, running: bool):
        """Bật/tắt trạng thái "đang chạy": khóa nút Chạy, mở nút Dừng, chạy
        thanh tiến trình; và ngược lại khi kết thúc."""
        if running:
            self._is_running = True
            self._run_cancel.clear()
            self._set_status("Đang chạy tối ưu...")
            self.btn_run_opt.config(state="disabled")
            self.btn_stop_opt.config(state="normal")
            try:
                self.progress_run.start(12)
            except Exception:
                pass
        else:
            self._is_running = False
            self._set_status("Đã xong." if not self._run_cancel.is_set() else "Đã dừng.")
            self.btn_run_opt.config(state="normal")
            self.btn_stop_opt.config(state="disabled")
            try:
                self.progress_run.stop()
            except Exception:
                pass

    def _poll_run_progress(self, evaluator=None):
        """Cập nhật nhãn "Đã gọi MCOC: N lần" mỗi 250 ms khi còn đang chạy.

        evaluator chỉ là gợi ý ban đầu; thực tế ưu tiên evaluator hiện hành
        (self._active_evaluator) vì luồng mở rộng đổi runner theo từng đường kính."""
        if not self._is_running:
            return
        ev = self._active_evaluator or evaluator
        runner = getattr(ev, 'runner', None)
        if runner is not None and not self._run_cancel.is_set():
            self.lbl_run_status.config(
                text="Đã gọi MCOC: %d lần" % getattr(runner, 'n_calls', 0))
        self.root.after(250, lambda: self._poll_run_progress(evaluator))

    def _request_stop_opt(self):
        """Yêu cầu DỪNG: đặt cờ hợp tác; evaluator bọc sẽ ngắt ở lần chấm kế tiếp."""
        self._run_cancel.set()
        self.lbl_run_status.config(text="Đang dừng...")

    def _wrap_cancellable(self, evaluator):
        """Bọc evaluator thực để hỗ trợ DỪNG hợp tác mà KHÔNG sửa core.

        Trước mỗi lần chấm, nếu cờ dừng đã đặt thì ném MCOCError để vòng tối ưu
        thoát ở lần đánh giá kế tiếp. Sao chép .runner/.workdir để phần đếm tiến
        trình và xử lý kết quả vẫn hoạt động."""
        from core.mcoc_runner import MCOCError

        def wrapped(coords):
            if self._run_cancel.is_set():
                raise MCOCError("Đã dừng theo yêu cầu")
            return evaluator(coords)

        wrapped.runner = getattr(evaluator, 'runner', None)
        wrapped.workdir = getattr(evaluator, 'workdir', None)
        if hasattr(evaluator, 'dia'):
            wrapped.dia = evaluator.dia
        # evaluator hiện hành để _poll_run_progress đếm đúng runner đang chạy
        self._active_evaluator = wrapped
        return wrapped

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

    def _validate_inputs(self, *_args):
        """Kiểm tra tức thời 4 thông số BẮT BUỘC (L_X, L_Y, D_PILE, P_LIMIT).

        Trả về True khi cả 4 đều là số > 0; ngược lại False. Đồng thời:
          - tô đỏ ô không hợp lệ bằng style ttk "Invalid.TEntry" (fieldbackground);
          - cập nhật thanh trạng thái với tóm tắt trường thiếu/sai.
        KHÔNG hiển thị popup và KHÔNG khóa nút Chạy (giữ cổng kiểm tra ở run_optimize).
        """
        required = {'L_X': "Lx", 'L_Y': "Ly", 'D_PILE': "d", 'P_LIMIT': "[Po]"}
        bad = []
        for k, short in required.items():
            raw = self.params[k].get().strip()
            ok = False
            if raw != '':
                try:
                    ok = float(raw) > 0
                except ValueError:
                    ok = False
            entry = self._param_entries.get(k)
            if entry is not None:
                try:
                    entry.config(style=("TEntry" if ok else "Invalid.TEntry"))
                except Exception:
                    pass
            if not ok:
                bad.append(short)

        if bad:
            self._set_status("Thiếu/không hợp lệ: " + ", ".join(bad))
            return False
        self._set_status("Thông số hợp lệ.")
        return True

    def run_optimize(self):
        """Chạy tối ưu — mặc định ĐÁNH GIÁ CHÍNH XÁC bằng MCOC (NSGA-II).

        Nếu bật "Tối ưu mở rộng" thì chuyển sang luồng quét đường kính + R7/R8 +
        thu bệ (run_optimize_ext)."""
        if self.var_ext_enable.get():
            return self.run_optimize_ext()
        if self._is_running:   # chống bấm Chạy lần 2 khi đang chạy
            return
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
        if not self._validate_mcoc_setup():
            return

        params = self.get_params_dict()
        params['input_filepath'] = self.input_filepath
        params['mock_mode'] = False
        loads = list(self.loads)

        self.txt_result.delete(1.0, tk.END)
        self._log_refine("=== TỐI ƯU BẰNG MCOC (NSGA-II — đánh giá chính xác) ===")
        self._log_refine("Đang chạy MCOC, vui lòng đợi...")
        self._set_running(True)

        def worker():
            from core.mcoc_runner import MCOCError
            try:
                from io_handlers.mcoc_writer import self_check
                from core.nsga2_optimizer import run_nsga2
                ok, msg = self_check(self.input_filepath, params['original_coords'])
                if not ok:
                    self._log_refine("LỖI TEMPLATE: " + msg)
                    return
                # Tải trọng lấy TỪ UI (ghi đè tải trong file MCOC gốc) — UI là nguồn duy nhất
                evaluator = MCOCBlackbox.make_real_evaluator(params, loads=loads, log=self._log_refine)
                ev = self._wrap_cancellable(evaluator)
                self.root.after(0, lambda: self._poll_run_progress(ev))
                # Chấm phương án gốc (để so sánh) — cùng bộ tải UI
                orig_res = ev(np.array(params['original_coords'], dtype=float))
                results = run_nsga2(params, loads, evaluator=ev,
                                    pop_size=20, n_gen=10, max_evals=140,
                                    secondary=self.var_secondary.get(),
                                    log=self._log_refine)
                results['_orig_eval'] = (len(params['original_coords']), orig_res)
                self.root.after(0, lambda: self._show_nsga2_results(results))
            except MCOCError as e:
                if "Đã dừng" in str(e):
                    self._log_refine("Đã dừng.")
                else:
                    self._log_refine("LỖI: %s" % e)
            except Exception as e:
                import traceback
                self._log_refine("LỖI: %s" % e)
                self._log_refine(traceback.format_exc()[-300:])
            finally:
                self.root.after(0, lambda: self._set_running(False))

        threading.Thread(target=worker, daemon=True).start()

    def _show_nsga2_results(self, results):
        """Hiển thị kết quả NSGA-II + MCOC: chuyển về cấu trúc dùng chung."""
        self._ext_active = False   # luồng chuẩn: audit R1–R8 nhưng R7 = "không kiểm" ([H]=0)
        P_LIMIT = self._pget('P_LIMIT')
        orig_cfg = None
        oe = results.get('_orig_eval')
        if oe:
            n0, r0 = oe
            # Trạng thái phương án gốc xét ĐẦY ĐỦ (lực + hình học) để KHỚP bảng audit
            # R1–R8, tránh mâu thuẫn "DAT (chỉ lực) vs KHÔNG ĐẠT (R3/R4)".
            orig_cfg = {
                'type': 'Goc', 'nx': 0, 'ny': 0, 'sx': 0, 'sy': 0, 'n': n0,
                'coords': self.original_coords,
                'pmax': r0.get('pmax', 0), 'pmin': r0.get('pmin', 0),
                'mxmax': r0.get('mxmax', 0), 'mymax': r0.get('mymax', 0),
                'msg': 'Phuong an goc (MCOC)',
            }
            # Bệ gốc đủ chứa cọc gốc (kể cả khi ô L_X/L_Y bị thu nhỏ hơn) — tránh
            # cọc tràn ra ngoài bệ khi vẽ. Để trống thì update_simulation dùng ô UI.
            pco = np.asarray(self.original_coords, float)
            if pco.ndim == 2 and len(pco):
                sd = self._pget('D_PILE') or 1.2
                from core.ext.cap_resize import recommend_cap_size
                flx, fly = recommend_cap_size(self.original_coords, sd, 0.1)
                orig_cfg['cap_lx'] = max(self._pget('L_X') or 0.0, flx)
                orig_cfg['cap_ly'] = max(self._pget('L_Y') or 0.0, fly)
            orig_cfg['ok'] = self._config_fully_ok(orig_cfg)
        # LUÔN giữ TẤT CẢ phương án chấp nhận được (không chỉ Pareto) để người
        # dùng so sánh "tiến hóa" + tự chọn theo điều kiện. Radio BEST/ALL chỉ
        # chi phối khâu XUẤT FILE (save_file), không cắt danh sách trên màn hình.
        valid = results.get('all_valid_configs', [])
        self.current_config = {
            'recommended': results.get('recommended'),
            'original_config': orig_cfg,
            'all_valid_configs': valid,
            'pareto_front': results.get('pareto_front', []),
            'all_candidates': [],
            'best_A': results.get('best_A'), 'best_B': results.get('best_B'),
            'reason': results.get('reason', ''),
        }
        self.txt_result.delete(1.0, tk.END)
        self._render_results(self.current_config, results.get('n_evals'))
        self._maybe_suggest_cap(self.current_config)
        self.populate_comboboxes(self.current_config)

    def _maybe_suggest_cap(self, results):
        """Khi KHÔNG có phương án (bệ chật) và người dùng bật 'Đề xuất nới bệ',
        in gợi ý: bệ hiện chứa tối đa bao nhiêu cọc + bệ tối thiểu khả thi.

        TÙY CHỌN, do người dùng kiểm soát — chỉ trình bày số liệu, KHÔNG tự áp
        dụng và KHÔNG đổi thuật toán tối ưu. Dùng mô hình bệ cứng (không gọi MCOC).
        """
        if results.get('recommended'):
            return
        if not getattr(self, 'var_suggest_cap', None) or not self.var_suggest_cap.get():
            return
        if not self.loads:
            return
        try:
            from core.cap_suggest import cap_max_piles, suggest_min_cap
            params = self.get_params_dict()
            cm = cap_max_piles(params)
            sug = suggest_min_cap(params, self.loads)
        except Exception:
            return
        ins = lambda s="": self.txt_result.insert(tk.END, s + "\n")
        ins("")
        ins("-" * 60)
        ins("  GOI Y XU LY BE CHAT (tham khao — chua ap dung)")
        ins("-" * 60)
        if cm['n']:
            ins("  Be hien tai %g x %g m chua TOI DA %d coc (luoi %dx%d @ k/c >= %.2f m)."
                % (params.get('L_X', 0), params.get('L_Y', 0), cm['n'],
                   cm['nx'], cm['ny'], cm['s_min']))
        if sug:
            ins("  De dat o k/c toi thieu, NOI be toi thieu ~ %.1f x %.1f m"
                % (sug['cap_lx'], sug['cap_ly']))
            ins("     (luoi %dx%d = %d coc, Pmax ~ %.0f T <= [Po])."
                % (sug['nx'], sug['ny'], sug['n'], sug['pmax']))
            ins("  Hoac: tang duong kinh coc (luong mo rong), hoac giam k/c toi")
            ins("  thieu neu loai coc cho phep (o 'K/c toi thieu ×d').")
        else:
            ins("  Chua tim duoc be kha thi trong gioi han quet — xem lai [Po]/tai.")

    def _render_results(self, results, n_evals=None):
        """In kết quả ra ô 'Kết quả Đánh giá' theo bố cục gọn, kèm bảng tọa độ."""
        P_LIMIT = self._pget('P_LIMIT')
        M_LIMIT = self._pget('M_LIMIT')
        P_TENSION = self._pget('P_TENSION')
        W = 60
        def ins(s="", tag=None):
            start = self.txt_result.index(tk.END)
            self.txt_result.insert(tk.END, s + "\n")
            if tag:
                self.txt_result.tag_add(tag, start, self.txt_result.index(tk.END))
        rec = results.get('recommended')
        orig = results.get('original_config')

        ins("=" * W, "head")
        ins("  PHUONG AN KIEN NGHI", "head")
        ins("=" * W, "head")
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
            if rec.get('cap_lx') and rec.get('cap_ly'):
                ins(f"  Kich thuoc be: {rec['cap_lx']:g} x {rec['cap_ly']:g} m")
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
            ins("  Khong tim thay phuong an thoa man.", "bad")
            ins(f"  Ly do: {results.get('reason', '')}")
        ins("")

        if orig:
            status = "DAT" if orig['ok'] else "KHONG DAT"
            ins("-" * W, "head")
            ins(f"  PHUONG AN GOC : {status}", "ok" if orig['ok'] else "bad")
            ins("-" * W, "head")
            ins(f"  So coc = {orig['n']}    Pmax = {orig['pmax']:.2f} T   (Po = {P_LIMIT:.0f} T)")
            ins(f"  Pmin = {orig['pmin']:.2f} T")
            if orig.get('cap_lx') and orig.get('cap_ly'):
                ins(f"  Kich thuoc be goc: {orig['cap_lx']:g} x {orig['cap_ly']:g} m")
            ins("")

        show = results.get('all_valid_configs', [])
        ins("-" * W, "head")
        ins(f"  CAC PHUONG AN DAT (MCOC)  -  {len(show)} phuong an", "head")
        ins("-" * W, "head")
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
            ins(f"  (Gioi han: {', '.join(notes)})", "muted")
        else:
            ins("  Khong co phuong an nao DAT trong kich thuoc be nay.", "bad")
        if n_evals is not None:
            ins(f"\n  So lan goi MCOC: {n_evals}")

    # ========================================================================
    # TAB 1 - TƯƠNG TÁC: TỐI ƯU MỞ RỘNG (R7/R8 + đổi đường kính + thu bệ)
    # ========================================================================
    def _toggle_ext(self):
        """LUÔN hiện phần thân cấu hình mở rộng để người dùng THẤY chức năng
        (đổi đường kính, R7/R8, thu bệ) — tránh ẩn khiến không biết chương trình
        có gì. Công tắc chính chỉ quyết định luồng chạy có dùng mở rộng hay không;
        khi tắt thì làm mờ các điều khiển con để báo trạng thái rõ ràng."""
        self.frame_ext_body.pack(fill=tk.X)   # luôn hiện -> dễ khám phá
        on = self.var_ext_enable.get()
        self._set_state_recursive(self.frame_ext_body, on)

    def _toggle_tcvn(self):
        """Bật/tắt panel TCVN: hiện thân, mờ/sáng các ô con và KHÓA [Po]/[Ct].

        Khi bật tự tính: [Po]/[Ct] do chương trình suy ra nên khóa 2 ô nhập tay
        (state='readonly'); khi tắt thì mở lại ('normal'). Giữ vững khi thiếu key.
        """
        # Luôn hiện thân để người dùng THẤY chức năng; chỉ làm mờ khi tắt.
        try:
            self.frame_tcvn_body.pack(fill=tk.X, pady=(4, 0))
        except Exception:
            pass
        on = self.var_tcvn_enable.get()
        self._set_state_recursive(self.frame_tcvn_body, on)
        # Nhãn xem trước nên luôn đọc được (không làm mờ) — bật lại nếu vừa bị mờ.
        try:
            self.lbl_tcvn_preview.state(['!disabled'])
        except Exception:
            pass
        # Khóa/mở 2 ô [Po]/[Ct] theo trạng thái bật của panel.
        for key in ('P_LIMIT', 'P_TENSION'):
            e = getattr(self, '_param_entries', {}).get(key)
            if e is None:
                continue
            try:
                e.config(state=('readonly' if on else 'normal'))
            except Exception:
                pass

    def _update_tcvn_preview(self, *_args):
        """Cập nhật nhãn xem trước Rc,d (+Rt,d) từ các tham số TCVN đang nhập.

        Null-safe trong lúc dựng UI (nhãn có thể chưa tồn tại). Ô trống/không hợp
        lệ → hiển thị gợi ý nhập Rc,k.
        """
        lbl = getattr(self, 'lbl_tcvn_preview', None)
        if lbl is None:
            return
        from core import tcvn

        def _f(var, default=None):
            raw = (var.get() or '').strip()
            if raw == '':
                return default
            try:
                return float(raw)
            except (ValueError, TypeError):
                return default

        rck = _f(self.var_rck)
        if not rck or rck <= 0:
            lbl.config(text="→ nhập Rc,k để tính")
            return
        g0 = _f(self.var_g0, 1.15)
        gk = _f(self.var_gk, 1.40)
        level = (self.var_imp_level.get() or 'II').strip().upper()
        gn = tcvn.GAMMA_N_BY_LEVEL.get(level, 1.15)
        po = tcvn.design_axial_capacity(rck, g0, gn, gk)
        text = f"→ Rc,d = {po:.1f} T"
        rtk = _f(self.var_rtk)
        if rtk and rtk > 0:
            gk_t = _f(self.var_gk_t, gk)
            ct = tcvn.design_axial_capacity(rtk, g0, gn, gk_t)
            text += f"; Rt,d = {ct:.1f} T"
        lbl.config(text=text)

    def _set_state_recursive(self, widget, enabled):
        """Bật/mờ đệ quy mọi widget con (ttk dùng state(), tk dùng config)."""
        for w in widget.winfo_children():
            try:
                if isinstance(w, ttk.Widget):
                    w.state(['!disabled'] if enabled else ['disabled'])
                else:
                    w.config(state=('normal' if enabled else 'disabled'))
            except Exception:
                pass
            self._set_state_recursive(w, enabled)

    def _diameter_row_dialog(self, title, init=None):
        """Hộp thoại nhập/sửa 1 dòng bảng đường kính. Trả về dict hoặc None.

        Trường: d (m), [Po] (T), [Ct] (T), [M] (T.m), [H] (T). d>0 và [Po]>0
        bắt buộc; [Ct]/[M]/[H] = 0 nghĩa là không kiểm ràng buộc tương ứng.
        """
        dlg = tk.Toplevel(self.root)
        dlg.title(title); dlg.resizable(False, False)
        dlg.grab_set(); dlg.transient(self.root)
        fields = [
            ("Đường kính d (m)",        "d",  1.2),
            ("Sức nén [Po] (T)",        "Po", 0.0),
            ("Sức nhổ [Ct] (T)",        "Ct", 0.0),
            ("Sức uốn [M] (T.m)",       "M",  0.0),
            ("Sức ngang [H] (T) — R7",  "H",  0.0),
        ]
        vars_ = {}
        for i, (label, key, default) in enumerate(fields):
            ttk.Label(dlg, text=label, width=24, anchor="w").grid(
                row=i, column=0, padx=10, pady=4, sticky="w")
            v = tk.StringVar(value=str(init.get(key, default)) if init else str(default))
            vars_[key] = v
            ttk.Entry(dlg, textvariable=v, width=12).grid(row=i, column=1, padx=10, pady=4)
        result = [None]

        def on_ok():
            try:
                row = {k: float(v.get()) for k, v in vars_.items()}
            except ValueError:
                messagebox.showerror("Lỗi", "Nhập số hợp lệ cho mọi trường.", parent=dlg)
                return
            if row['d'] <= 0 or row['Po'] <= 0:
                messagebox.showerror("Lỗi", "d và [Po] phải > 0.", parent=dlg)
                return
            result[0] = row
            dlg.destroy()

        bf = tk.Frame(dlg); bf.grid(row=len(fields), column=0, columnspan=2, pady=8)
        ttk.Button(bf, text="  OK  ", command=on_ok).pack(side=tk.LEFT, padx=6)
        ttk.Button(bf, text="Hủy", command=dlg.destroy).pack(side=tk.LEFT, padx=6)
        dlg.wait_window()
        return result[0]

    def open_diameter_dialog(self):
        """Hộp thoại quản lý BẢNG ĐƯỜNG KÍNH ứng viên cho tối ưu mở rộng."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Bảng đường kính ứng viên")
        dlg.geometry("520x340"); dlg.grab_set(); dlg.transient(self.root)

        tk.Label(dlg, justify="left", anchor="w",
                 text="Mỗi dòng = một đường kính ứng viên kèm sức chịu tải (TCVN 10304:2014).\n"
                      "Chương trình quét mọi đường kính, chấm bằng MCOC, chọn phương án rẻ nhất.").pack(
            fill=tk.X, padx=10, pady=(8, 2))

        cols = ("d", "Po", "Ct", "M", "H")
        tree = ttk.Treeview(dlg, columns=cols, show="headings", height=8)
        for c, hdr in zip(cols, ("d (m)", "[Po] (T)", "[Ct] (T)", "[M] (T.m)", "[H] (T)")):
            tree.heading(c, text=hdr); tree.column(c, width=90, anchor="e")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        def refresh():
            for it in tree.get_children():
                tree.delete(it)
            for r in self.ext_diameters:
                tree.insert("", tk.END, values=(f"{r['d']:g}", f"{r['Po']:g}",
                            f"{r['Ct']:g}", f"{r['M']:g}", f"{r['H']:g}"))

        def add_row():
            r = self._diameter_row_dialog("Thêm đường kính")
            if r:
                self.ext_diameters.append(r); refresh()

        def edit_row():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Thông báo", "Chọn một dòng để sửa.", parent=dlg); return
            idx = tree.index(sel[0])
            r = self._diameter_row_dialog("Sửa đường kính", init=self.ext_diameters[idx])
            if r:
                self.ext_diameters[idx] = r; refresh()

        def del_row():
            sel = tree.selection()
            if not sel:
                return
            for i in sorted([tree.index(s) for s in sel], reverse=True):
                self.ext_diameters.pop(i)
            refresh()

        def seed_current():
            """Thêm 1 dòng từ thông số bài toán hiện tại trên UI."""
            d = self._pget('D_PILE')
            if d <= 0:
                messagebox.showinfo("Thông báo", "Chưa có đường kính d trên UI.", parent=dlg); return
            self.ext_diameters.append({'d': d, 'Po': self._pget('P_LIMIT'),
                                       'Ct': self._pget('P_TENSION'),
                                       'M': self._pget('M_LIMIT'), 'H': 0.0})
            refresh()

        bf = tk.Frame(dlg); bf.pack(fill=tk.X, padx=10, pady=6)
        ttk.Button(bf, text="Thêm", command=add_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(bf, text="Sửa", command=edit_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(bf, text="Xóa", command=del_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(bf, text="Lấy d hiện tại", command=seed_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(bf, text="Đóng",
                   command=lambda: (self._update_ext_dia_label(), dlg.destroy())).pack(side=tk.RIGHT, padx=2)

        refresh()
        dlg.wait_window()
        self._update_ext_dia_label()

    def _update_ext_dia_label(self):
        """Cập nhật nhãn tóm tắt bảng đường kính cạnh nút mở dialog."""
        if not self.ext_diameters:
            self.lbl_ext_dia.config(text="(chưa có — sẽ dùng d hiện tại)", foreground="#888")
        else:
            ds = ", ".join(f"{r['d']:g}" for r in sorted(self.ext_diameters, key=lambda r: r['d']))
            self.lbl_ext_dia.config(text=f"{len(self.ext_diameters)} đ.kính: {ds} m",
                                    foreground="black")

    def run_optimize_ext(self):
        """Chạy TỐI ƯU MỞ RỘNG: quét đường kính (MCOC) + R7/R8 + thu bệ."""
        if self._is_running:   # chống bấm Chạy lần 2 khi đang chạy
            return
        # Validation giống luồng chuẩn
        required = {'L_X': "Rộng bệ Lx", 'L_Y': "Dài bệ Ly",
                    'D_PILE': "Đ.kính cọc d (gốc)", 'P_LIMIT': "Sức nén [Po]"}
        missing = [name for k, name in required.items() if self._pget(k) <= 0]
        if missing:
            messagebox.showwarning("Chưa nhập đủ thông số",
                                   "Vui lòng nhập (>0) cho: " + ", ".join(missing) + ".")
            return
        if not self.loads:
            messagebox.showwarning("Chưa có tải trọng", "Vui lòng thêm ít nhất một tổ hợp tải trọng.")
            return
        if not self._validate_mcoc_setup():
            return

        params = self.get_params_dict()
        params['input_filepath'] = self.input_filepath
        params['mock_mode'] = False
        loads = list(self.loads)
        d_orig = getattr(self, 'original_d', None) or self._pget('D_PILE')
        # [Po] trong file MCOC chỉ là mặc định (500) — ƯU TIÊN giá trị người dùng
        # nhập trên UI làm sức chịu nén GỐC; chỉ lùi về giá trị file nếu UI trống.
        Po_orig = self._pget('P_LIMIT') or getattr(self, 'original_p', None) or 500.0

        # Bảng đường kính: dùng bảng người dùng, hoặc 1 dòng từ thông số hiện tại
        from core.ext.pile_section import DiameterTable
        from core.ext.config_ext import ExtConfig
        if self.ext_diameters:
            table = DiameterTable(self.ext_diameters)
        else:
            table = DiameterTable([{'d': self._pget('D_PILE'), 'Po': self._pget('P_LIMIT'),
                                    'Ct': self._pget('P_TENSION'), 'M': self._pget('M_LIMIT'),
                                    'H': 0.0}])
        cfg = ExtConfig(enable_R7=self.var_ext_r7.get(), enable_R8=self.var_ext_r8.get(),
                        cap_round_to=float(self.var_ext_round.get()),
                        cap_resize=self.var_ext_capresize.get())

        self.txt_result.delete(1.0, tk.END)
        self._log_refine("=== TỐI ƯU MỞ RỘNG (quét %d đường kính, R7=%s, R8=%s) ==="
                         % (len(table), cfg.enable_R7, cfg.enable_R8))
        self._log_refine("Đang chạy MCOC cho từng đường kính, vui lòng đợi...")
        self._set_running(True)
        self.root.after(0, lambda: self._poll_run_progress(None))

        def worker():
            from core.mcoc_runner import MCOCError
            try:
                from io_handlers.mcoc_writer import self_check
                from core.ext.orchestrator import run_extended_optimization
                ok, msg = self_check(self.input_filepath, params['original_coords'])
                if not ok:
                    self._log_refine("LỖI TEMPLATE: " + msg)
                    return
                # Factory bọc evaluator thực mỗi đường kính để hỗ trợ DỪNG hợp tác.
                def _cancellable_factory(params_d, dia, lds):
                    from core.ext.blackbox_ext import make_diameter_evaluator
                    base_ev = make_diameter_evaluator(params, dia, loads=lds,
                                                      d_orig=d_orig, Po_orig=Po_orig,
                                                      log=self._log_refine)
                    return self._wrap_cancellable(base_ev)
                out = run_extended_optimization(
                    params, loads, table, cfg=cfg,
                    evaluator_factory=_cancellable_factory,
                    d_orig=d_orig, Po_orig=Po_orig,
                    pop_size=16, n_gen=8, max_evals=140,
                    secondary=self.var_secondary.get(), log=self._log_refine)
                self.root.after(0, lambda: self._show_ext_results(out, cfg))
            except MCOCError as e:
                if "Đã dừng" in str(e):
                    self._log_refine("Đã dừng.")
                else:
                    self._log_refine("LỖI: %s" % e)
            except Exception as e:
                import traceback
                self._log_refine("LỖI: %s" % e)
                self._log_refine(traceback.format_exc()[-400:])
            finally:
                self.root.after(0, lambda: self._set_running(False))

        threading.Thread(target=worker, daemon=True).start()

    def _show_ext_results(self, out, cfg):
        """Hiển thị kết quả tối ưu mở rộng + cập nhật UI theo đường kính thắng."""
        ins = lambda s="": self.txt_result.insert(tk.END, s + "\n")
        self.txt_result.delete(1.0, tk.END)

        per = out.get('per_diameter', [])
        rec = out.get('recommended')
        dwin = out.get('winner_diameter')
        ins("=" * 60)
        ins("  TOI UU MO RONG  —  SO SANH CAC PHUONG AN THEO DUONG KINH")
        ins("=" * 60)
        ins(f"   {'d(m)':>6}{'so coc':>8}{'Pmax(T)':>10}{'chi phi':>10}   trang thai")
        ins("  " + "-" * 56)
        for r in per:
            dia = r['dia']
            is_win = (dwin is not None and abs(dia.d - dwin) < 1e-9)
            mark = "* " if is_win else "  "
            if r['best']:
                ins(f"{mark}{dia.d:>6g}{r['best']['n']:>8}{r['best']['pmax']:>10.1f}"
                    f"{r['cost']:>10.3f}   " + ("THANG" if is_win else "DAT"))
            else:
                ins(f"{mark}{dia.d:>6g}{'-':>8}{'-':>10}{'-':>10}   khong kha thi (R1-R8)")
        ins("  " + "-" * 56)
        ins("  (* = phuong an THANG; cac phuong an khac van duoc luu de so sanh)")
        ins("")

        if not rec:
            ins("  KHONG co duong kinh nao cho phuong an thoa man R1-R8.")
            # Vẫn HIỆN phương án gốc để người dùng so sánh / tự điều chỉnh.
            orig_cfg = out.get('original_config')
            if orig_cfg is not None:
                st = "DAT" if orig_cfg.get('ok') else "KHONG DAT"
                ins("")
                ins("  PHUONG AN GOC (d=%.3g m): %s | %d coc | Pmax=%.1f T"
                    % (orig_cfg.get('d_orig', 0), st, orig_cfg['n'], orig_cfg['pmax']))
            self._ext_active = False
            self.current_config = {
                'recommended': None, 'original_config': orig_cfg,
                'all_valid_configs': [], 'all_candidates': [],
                'reason': 'Khong co phuong an moi thoa R1-R8.',
            }
            self._render_results(self.current_config)
            self._maybe_suggest_cap(self.current_config)
            self.populate_comboboxes(self.current_config)
            return

        winner = out['winner']
        dia_win = winner['dia']
        cap = out['cap_report']
        ins("-" * 60)
        ins(f"  THANG: d = {dwin:g} m | {rec['n']} coc | Pmax = {rec['pmax']:.1f} T"
            f" | chi phi = {winner['cost']:.3f}")
        ins(f"  Suc chiu: [Po]={dia_win.Po:g}  [Ct]={dia_win.Ct:g}  [M]={dia_win.M:g}"
            f"  [H]={dia_win.H:g} (T, T.m)")
        # Báo cáo đổi kích thước bệ
        act = "da ap dung" if cap['applied'] else "chi de xuat"
        ins(f"  BE: {cap['old_LX']:g} x {cap['old_LY']:g}  ->  "
            f"{cap['new_LX']:g} x {cap['new_LY']:g} m ({act}, "
            f"mep cach tim >= {cap['safe_d']:g}, lam tron {cap['round_to']:g})")
        if cap['saved_area'] > 1e-9:
            ins(f"       Tiet kiem dien tich be: {cap['saved_area']:.2f} m2 ({cap['saved_pct']:.1f}%)")
        ins("")

        # Cập nhật THÔNG SỐ BÀI TOÁN trên UI theo đường kính thắng để bảng audit /
        # mặt bằng phản ánh đúng phương án (d, sức chịu, kích thước bệ mới).
        self.params['D_PILE'].set(f"{dwin:g}")
        self.params['P_LIMIT'].set(f"{dia_win.Po:g}")
        self.params['P_TENSION'].set(f"{dia_win.Ct:g}")
        self.params['M_LIMIT'].set(f"{dia_win.M:g}" if dia_win.M > 0 else "")
        if cap['applied']:
            self.params['L_X'].set(f"{cap['new_LX']:g}")
            self.params['L_Y'].set(f"{cap['new_LY']:g}")

        # Bật cờ audit mở rộng + lưu [H] để bảng R1–R8 hiển thị R7
        self._ext_active = True
        self._ext_hlimit = dia_win.H
        self._last_ext_out = out         # phục vụ xuất báo cáo (mục 3b + R7/R8)
        self._last_ext_cfg = cfg

        # LUÔN giữ TẤT CẢ phương án chấp nhận được (không chỉ Pareto) để so sánh
        # "tiến hóa". Phương án GỐC (đường kính gốc) đã được orchestrator chấm.
        res = winner['result']
        # Mỗi phương án thay thế cũng mang bệ RIÊNG của nó (thu vừa khít nếu
        # đang bật resize, ngược lại giữ bệ gốc) để so sánh tiến hóa kích thước.
        from core.ext.cap_resize import recommend_cap_size
        for vc in res.get('all_valid_configs', []):
            if vc.get('cap_lx') and vc.get('cap_ly'):
                continue
            vc_coords = vc.get('coords')
            has_coords = vc_coords is not None and len(np.asarray(vc_coords)) > 0
            if cap['applied'] and has_coords:
                lx, ly = recommend_cap_size(vc_coords, cap['safe_d'], cap['round_to'])
                vc['cap_lx'], vc['cap_ly'] = lx, ly
            else:
                vc['cap_lx'], vc['cap_ly'] = cap['old_LX'], cap['old_LY']
        # 'ok' của phương án gốc do orchestrator chấm theo đường kính/[Po] GỐC
        # (không dùng _config_fully_ok vì params UI đã đổi sang đường kính thắng).
        orig_cfg = out.get('original_config')
        self.current_config = {
            'recommended': rec,
            'original_config': orig_cfg,
            'all_valid_configs': res.get('all_valid_configs', []),
            'all_candidates': [],
            'best_A': res.get('best_A'), 'best_B': res.get('best_B'),
            'reason': res.get('reason', ''),
        }
        n_evals = sum(r['result'].get('n_evals', 0) for r in per)
        self._render_results(self.current_config, n_evals)
        self.populate_comboboxes(self.current_config)

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
        if self._is_running:   # chống bấm Chạy lần 2 khi đang chạy
            return
        if not self._validate_mcoc_setup():
            return

        self.txt_result.delete(1.0, tk.END)
        self.txt_result.insert(tk.END, "=== HOP DEN MCOC THUC - TINH CHINH TUNG BUOC ===\n")

        params = self.get_params_dict()
        params['input_filepath'] = self.input_filepath
        params['mock_mode'] = False
        params['refine_mode'] = self.var_refine_mode.get()
        loads = list(self.loads)
        self._set_running(True)

        def worker():
            from core.mcoc_runner import MCOCError
            try:
                # Kiểm tra template trước khi chạy
                from io_handlers.mcoc_writer import self_check
                ok, msg = self_check(self.input_filepath, params['original_coords'])
                if not ok:
                    self._log_refine("LOI TEMPLATE: " + msg)
                    return
                self._log_refine("Template: " + msg)

                evaluator = MCOCBlackbox.make_real_evaluator(params, log=self._log_refine)
                ev = self._wrap_cancellable(evaluator)
                self.root.after(0, lambda: self._poll_run_progress(ev))
                results = run_pareto_refinement(params, loads, ev, log=self._log_refine)
                self.root.after(0, lambda: self._show_refine_results(results))
            except MCOCError as e:
                if "Đã dừng" in str(e):
                    self._log_refine("Đã dừng.")
                else:
                    self._log_refine("LOI: %s" % e)
            except Exception as e:
                self._log_refine("LOI: %s" % e)
            finally:
                self.root.after(0, lambda: self._set_running(False))

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

        # Bệ của phương án nào PHẢI đi theo phương án đó: nếu config mang theo
        # kích thước bệ riêng (vd phương án gốc giữ bệ gốc, phương án đề xuất
        # mang bệ đã thu), ưu tiên dùng nó thay cho L_X/L_Y trên UI — nhờ vậy
        # mặt bằng + bảng audit R4 phản ánh đúng tiến hóa kích thước bệ.
        cap_lx = selected_cfg.get('cap_lx'); cap_ly = selected_cfg.get('cap_ly')
        if cap_lx and cap_ly:
            params_dict['L_X'] = float(cap_lx)
            params_dict['L_Y'] = float(cap_ly)
        # ...và ĐƯỜNG KÍNH / sức chịu cũng đi theo phương án: phương án gốc audit
        # R3 (3d–6d), R4 (mép ≥ d), R5/R6 theo d/[Po]/[Ct]/[M] GỐC — không theo
        # đường kính thắng (tránh báo KHÔNG ĐẠT oan khi UI đã đổi sang d thắng).
        if selected_cfg.get('d_orig'):
            params_dict['D_PILE'] = float(selected_cfg['d_orig'])
            params_dict['SAFE_D'] = float(selected_cfg.get('safe_d_orig')
                                          or selected_cfg['d_orig'])
            if selected_cfg.get('Po_orig'):
                params_dict['P_LIMIT'] = float(selected_cfg['Po_orig'])
            if selected_cfg.get('ct_orig') is not None:
                params_dict['P_TENSION'] = float(selected_cfg['ct_orig'])
            if selected_cfg.get('m_orig') is not None:
                params_dict['M_LIMIT'] = float(selected_cfg['m_orig'])

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

        # Số liệu kiểm tra điều kiện R1–R8 theo từng tổ hợp (chuẩn tư vấn) + cập nhật KPI.
        # Tính luôn cho cả 2 chế độ để dải KPI nhất quán dù đang xem mặt bằng.
        cdata = self._build_constraint_data(selected_cfg, coords, params_dict, calibration_factor)
        self._update_kpi(cdata)

        if self.view_mode.get() == "audit":
            self.plot_canvas.draw_constraint_view(cdata)
        else:
            # Khung nhìn CHUNG cho mọi phương án -> cùng tỉ lệ khi chuyển phương án.
            view_extent = self._global_view_extent(params_dict)
            self.plot_canvas.draw_simulation(coords, params_dict, forces,
                                             m_forces=(mxmax, mymax), view_extent=view_extent)

    def _global_view_extent(self, params, margin=1.0):
        """Nửa bề rộng/cao KHUNG NHÌN CHUNG (đối xứng quanh tâm) bao mọi phương án.

        Lấy max bao của BỆ + CỌC qua tất cả phương án (gốc, đề xuất, các phương án
        đạt) để khi chuyển phương án, tỉ lệ pixel/mét KHÔNG đổi — cọc giữ nguyên
        cỡ, kỹ thuật viên dễ quan sát thay đổi. Trả về (hx, hy) đã cộng lề."""
        cc = self.current_config or {}
        cfgs = []
        if cc.get('original_config'): cfgs.append(cc['original_config'])
        if cc.get('recommended'): cfgs.append(cc['recommended'])
        cfgs += cc.get('all_valid_configs', []) or []
        d = params.get('D_PILE', 1.2) or 1.2
        hx = hy = 0.0
        for cfg in cfgs:
            lx = cfg.get('cap_lx') or params.get('L_X', 0) or 0
            ly = cfg.get('cap_ly') or params.get('L_Y', 0) or 0
            hx = max(hx, float(lx) / 2.0); hy = max(hy, float(ly) / 2.0)
            co = np.asarray(cfg.get('coords', []), float)
            if co.ndim == 2 and len(co):
                hx = max(hx, float(np.max(np.abs(co[:, 0]))) + d / 2.0)
                hy = max(hy, float(np.max(np.abs(co[:, 1]))) + d / 2.0)
        if hx <= 0 or hy <= 0:   # phòng khi thiếu dữ liệu: lùi về bệ hiện tại
            hx = (params.get('L_X', 6.0) or 6.0) / 2.0
            hy = (params.get('L_Y', 9.0) or 9.0) / 2.0
        return hx + margin, hy + margin

    def _config_fully_ok(self, cfg):
        """Phương án ĐẠT ĐẦY ĐỦ (R3/R4 hình học + R5/R5b/R6/R8 lực) — trả 1 boolean
        để TRẠNG THÁI nhất quán với bảng audit R1–R8 (tránh 'DAT chỉ xét lực').

        Lực lấy trực tiếp từ cfg (pmax/pmin/mx/my đã do MCOC chấm); hình học dùng
        chung rigid_cap.spacing_values + mép bệ như _build_constraint_data."""
        params = self.get_params_dict()
        Po = params.get('P_LIMIT', 0) or 0
        Ct = params.get('P_TENSION', 0) or 0
        Mlim = params.get('M_LIMIT', 0) or 0
        d = params.get('D_PILE', 1.0) or 1.0
        c_min = params.get('SAFE_D', d)
        coords = np.asarray(cfg.get('coords', []), float)
        if coords.ndim != 2 or len(coords) == 0:
            return False
        pmax = cfg.get('pmax', 0) or 0; pmin = cfg.get('pmin', 0) or 0
        mxmax = cfg.get('mxmax', 0) or 0; mymax = cfg.get('mymax', 0) or 0
        ok = (pmax <= Po) if Po > 0 else True               # R5 nén
        if Ct > 0:
            ok = ok and (pmin >= -Ct)                       # R5b nhổ
        if Mlim > 0:
            ok = ok and (max(mxmax, mymax) <= Mlim)         # R6 uốn
            if Po > 0:                                      # R8 tương tác P–M
                ok = ok and (pmax / Po + max(mxmax, mymax) / Mlim <= 1.0 + 1e-6)
        # R3 khoảng cách (cùng nguồn) + R4 mép bệ
        s_min_req = effective_min_spacing(params); s_max_req = 6 * d
        for _nm, _v, _chk_up in rigid_cap.spacing_values(
                cfg.get('type'), cfg.get('nx', 0), cfg.get('ny', 0),
                cfg.get('sx', 0), cfg.get('sy', 0), coords):
            if _v < s_min_req - 1e-3 or (_chk_up and _v > s_max_req + 1e-3):
                ok = False
        # R4 mép bệ: dùng bệ RIÊNG của phương án (cap_lx/cap_ly) nếu có — khớp với
        # mặt bằng + header; tránh báo R4 oan khi ô L_X/L_Y trên UI đã bị thu nhỏ.
        Lx = cfg.get('cap_lx') or params.get('L_X', 0) or 0
        Ly = cfg.get('cap_ly') or params.get('L_Y', 0) or 0
        if Lx and Ly:
            if (float(np.max(np.abs(coords[:, 0]))) + c_min > Lx / 2 + 1e-3 or
                    float(np.max(np.abs(coords[:, 1]))) + c_min > Ly / 2 + 1e-3):
                ok = False                                  # R4 mép bệ
        return bool(ok)

    # ── Kiểm tra điều kiện R1–R8 (chuẩn tư vấn) ──────────────────────────
    def _build_constraint_data(self, cfg, coords, params, calib):
        """Tổng hợp số liệu kiểm tra điều kiện R1–R8 theo từng tổ hợp cho phương án đang xem.

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

        # R3 (3d ≤ k/c ≤ 6d): dùng NGUỒN DUY NHẤT rigid_cap.spacing_values để KHỚP
        # với lõi (mechanics/nsga2) và báo cáo. Kiểu B (hoa mai) xét ĐƯỜNG CHÉO
        # √((sx/2)²+sy²) — min_spacing bỏ sót cận TRÊN. Cận dưới = effective_min_spacing
        # (max(3d, d+thông thủy)) đồng nhất với báo cáo.
        s_min_req = effective_min_spacing(params)
        s_max_req = 6 * d
        spac = rigid_cap.spacing_values(cfg.get('type'), cfg.get('nx', 0), cfg.get('ny', 0),
                                        cfg.get('sx', 0), cfg.get('sy', 0), coords)
        r3_ok = True
        for _nm, _v, _chk_up in spac:
            if _v < s_min_req - 1e-3:
                r3_ok = False
            if _chk_up and _v > s_max_req + 1e-3:
                r3_ok = False
        s_show = ", ".join(f"{nm}={v:.2f}" for nm, v, _ in spac) or "—"

        # R4 (tim cọc → mép ≥ d) — thuần hình học, không đổi theo tổ hợp
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
            f"R3 k/c: {s_show} m ∈ [{s_min_req:.2f}, {s_max_req:.2f}] "
            + ('✓' if r3_ok else '✗'),
            f"R4 tim→mép: {max(r4x, r4y) * 100:.0f}% " + ('✓' if r4_ok else '✗'),
            (f"R5/R6 uốn M: max({mxmax:.1f}, {mymax:.1f}) ≤ {Mlim:.1f} T·m "
             + ('✓' if m_ok else '✗')) if Mlim > 0 else "R5/R6 uốn M: không kiểm ([M]=0)",
        ]

        all_ok = bool(rows) and all(r['ok'] for r in rows) and r3_ok and r4_ok and m_ok

        # R7 (lực ngang) & R8 (tương tác P–M) — LUÔN trình bày khung R1–R8.
        # R7 cần [H] (chỉ có ở luồng MỞ RỘNG) → luồng chuẩn hiện "không kiểm".
        # R8 (P–M) tính được ở mọi luồng khi đã khai báo [M] và [Po].
        Hlim = (getattr(self, '_ext_hlimit', 0.0) or 0.0) if getattr(self, '_ext_active', False) else 0.0
        if Hlim > 0:
            hmax = float(rigid_cap.hmax(np.asarray(coords, float), self.loads)) \
                if self.loads else 0.0
            r7_ok = hmax <= Hlim + 1e-6
            geom_summary.append(
                f"R7 Hmax: {hmax:.1f} ≤ {Hlim:.1f} T " + ('✓' if r7_ok else '✗'))
            all_ok = all_ok and r7_ok
        else:
            geom_summary.append("R7 lực ngang: không kiểm ([H]=0)")
        if Mlim > 0 and Po > 0:
            it = gov_nmax / Po + max(mxmax, mymax) / Mlim
            r8_ok = it <= 1.0 + 1e-6
            geom_summary.append(
                f"R8 P–M: {it:.2f} ≤ 1.0 " + ('✓' if r8_ok else '✗'))
            all_ok = all_ok and r8_ok
        else:
            geom_summary.append("R8 P–M: không kiểm ([M]=0)")

        return {
            'n_piles': len(coords), 'rows': rows, 'governing': gov_i,
            'util_max': util_max, 'status': 'ĐẠT' if all_ok else 'KHÔNG ĐẠT',
            'geom_summary': geom_summary, 'Po': Po, 'Ct': Ct,
            'cons_label': 'R1–R8',
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
