"""interactive_tab.py - InteractiveTab: dựng giao diện Tab 1.

Tách từ ui/main_window.py (Plan 023, Pha 4b) — giữ NGUYÊN hành vi. Tạo widget
và gắn vào app.<...>; lệnh nút trỏ tới delegator/controller trên app.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from core import tcvn
from ui import strings as S
from ui.widgets.tooltip import Tooltip
from ui.plot_canvas import PlotCanvas


class InteractiveTab:
    """Tab 1 (Tương tác): dựng toàn bộ giao diện nhập liệu (thông số, TCVN, SSI/đài, địa chất, tải trọng, điều khiển tối ưu, MCOC) + panel mô phỏng; gắn widget vào state chia sẻ trên app và nối lệnh tới các controller."""

    def __init__(self, app):
        self.app = app

    def setup_interactive_ui(self, parent_frame):
        """Dựng toàn bộ giao diện Tab 1: panel trái (nhập liệu/điều khiển) và
        panel phải (mô phỏng mặt bằng cọc)."""
        self.app.main_paned = main_paned = ttk.PanedWindow(parent_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left Panel — chia DỌC: (trên) nút IO + vùng nhập liệu CUỘN ĐƯỢC + nút Chạy;
        # (dưới) ô "Kết quả Đánh giá" tách riêng, kéo sash để đổi cỡ nên không bị bóp.
        left_frame = tk.Frame(main_paned, width=760)
        main_paned.add(left_frame, weight=0)

        left_paned = ttk.PanedWindow(left_frame, orient=tk.VERTICAL)
        left_paned.pack(fill=tk.BOTH, expand=True)

        # ── Pane trên: IO (ghim) + vùng cuộn nhập liệu + nút Chạy (ghim đáy) ──
        top_pane = tk.Frame(left_paned)
        left_paned.add(top_pane, weight=3)

        # Buttons IO — ghim trên cùng (không cuộn)
        frame_io = tk.Frame(top_pane, padx=10)
        frame_io.pack(side=tk.TOP, fill=tk.X, pady=(10, 2))
        ttk.Button(frame_io, text="Mở file đầu vào  (hoặc kéo-thả)", command=self.app.load_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(frame_io, text="Làm mới", command=self.app.clear_loads).pack(side=tk.LEFT, fill=tk.X, expand=False, padx=2)
        ttk.Button(frame_io, text="Xuất kết quả", command=self.app.save_file).pack(side=tk.RIGHT, fill=tk.X, expand=False, padx=2)

        # Nút CHẠY — ghim đáy pane trên (gọn), luôn thấy dù vùng nhập liệu đang cuộn
        # Cụm tiến trình + nút DỪNG — ghim đáy DƯỚI nút Chạy (pack BOTTOM xếp chồng
        # ngược nên cụm này được khai báo TRƯỚC để nằm dưới cùng).
        run_state_frame = tk.Frame(top_pane)
        run_state_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 8))
        self.app.progress_run = ttk.Progressbar(run_state_frame, mode="indeterminate")
        self.app.progress_run.pack(side=tk.TOP, fill=tk.X)
        bottom_row = tk.Frame(run_state_frame)
        bottom_row.pack(side=tk.TOP, fill=tk.X, pady=(2, 0))
        self.app.lbl_run_status = ttk.Label(bottom_row, text="")
        self.app.lbl_run_status.pack(side=tk.LEFT)
        self.app.btn_stop_opt = ttk.Button(bottom_row, text="■ Dừng", state="disabled",
                                       command=self.app._request_stop_opt)
        self.app.btn_stop_opt.pack(side=tk.RIGHT)

        # Nút CHẠY — gọn lại (font nhỏ hơn, bỏ ipady) để nhường diện tích cho nội dung.
        self.app.btn_run_opt = tk.Button(top_pane, text="▶ CHẠY TỐI ƯU HÓA",
                                     font=("Arial", 10, "bold"), bg="#27ae60", fg="white",
                                     command=self.app.run_optimize)
        self.app.btn_run_opt.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(2, 2))

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
            foreground="#666", wraplength=720, justify="left").pack(
            anchor="w", pady=(0, 4))

        # Bố cục 2 CỘT để thấy MỌI mục nhập liệu cùng lúc (giảm cuộn dọc):
        #   cột TRÁI = thông số/sức chịu tải/nền-đài; cột PHẢI = tải/điều khiển/MCOC.
        cols = tk.Frame(inner)
        cols.pack(fill=tk.BOTH, expand=True)
        col1 = tk.Frame(cols)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), anchor="n")
        col2 = tk.Frame(cols)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor="n")

        # Geometrics
        frame_geom = tk.LabelFrame(col1, text="Thông số Bài toán", padx=10, pady=5)
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
        self.app._param_entries = {}
        for r, (k, text) in enumerate(geom_fields):
            lbl = ttk.Label(frame_geom, text=text)
            lbl.grid(row=r, column=0, sticky="w", padx=(2, 4), pady=2)
            if k in param_tips:
                Tooltip(lbl, param_tips[k])
            e = ttk.Entry(frame_geom, textvariable=self.app.params[k], width=9)
            e.grid(row=r, column=1, sticky="ew", padx=(0, 8), pady=2)
            self.app._param_entries[k] = e
        for r, (k, text) in enumerate(cap_fields):
            lbl = ttk.Label(frame_geom, text=text)
            lbl.grid(row=r, column=2, sticky="w", padx=(2, 4), pady=2)
            if k in param_tips:
                Tooltip(lbl, param_tips[k])
            e = ttk.Entry(frame_geom, textvariable=self.app.params[k], width=9)
            e.grid(row=r, column=3, sticky="ew", padx=(0, 2), pady=2)
            self.app._param_entries[k] = e
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
            col1, text="Sức chịu tải theo TCVN 10304:2014 (tùy chọn)",
            padx=10, pady=5)
        frame_tcvn.pack(fill=tk.X, pady=5)
        chk_tcvn = ttk.Checkbutton(
            frame_tcvn, text="Tự tính [Po]/[Ct] từ Rc,k",
            variable=self.app.var_tcvn_enable, command=self.app._toggle_tcvn)
        chk_tcvn.pack(anchor="w")
        Tooltip(chk_tcvn, "Bật để chương trình suy ra sức chịu tải THIẾT KẾ "
                          "Rc,d/Rt,d từ sức chịu tải tiêu chuẩn Rc,k và các hệ số "
                          "tin cậy theo TCVN 10304:2014 Điều 7.1.11. Khi bật, "
                          "[Po]/[Ct] sẽ được tính tự động (ô nhập tay bị khóa).")

        self.app.frame_tcvn_body = tk.Frame(frame_tcvn)
        self.app.frame_tcvn_body.pack(fill=tk.X, pady=(4, 0))
        tcvn_fields = [
            ("Rc,k — nén tiêu chuẩn (T)", self.app.var_rck,
             "Rc,k — sức chịu tải NÉN tiêu chuẩn của 1 cọc (T). Nếu xác định bằng "
             "tính toán thì lấy bằng sức chịu tải cực hạn Rc,u."),
            ("Rt,k — kéo tiêu chuẩn (T, tùy chọn)", self.app.var_rtk,
             "Rt,k — sức chịu tải KÉO tiêu chuẩn (T). Để trống nếu không kiểm tra "
             "điều kiện nhổ."),
            ("γ0 — điều kiện làm việc", self.app.var_g0,
             "γ0 — hệ số điều kiện làm việc (mặc định 1.15)."),
            ("γk — theo đất", self.app.var_gk,
             "γk — hệ số tin cậy theo đất (mặc định 1.40)."),
            ("γk,t — theo đất khi kéo (tùy chọn)", self.app.var_gk_t,
             "γk,t — hệ số tin cậy theo đất khi KÉO. Để trống = dùng chung γk."),
        ]
        for r, (text, var, tip) in enumerate(tcvn_fields):
            lbl = ttk.Label(self.app.frame_tcvn_body, text=text)
            lbl.grid(row=r, column=0, sticky="w", padx=(2, 4), pady=2)
            Tooltip(lbl, tip)
            e = ttk.Entry(self.app.frame_tcvn_body, textvariable=var, width=10)
            e.grid(row=r, column=1, sticky="ew", padx=(0, 2), pady=2)
        lbl_lv = ttk.Label(self.app.frame_tcvn_body, text="Cấp công trình (γn)")
        lbl_lv.grid(row=len(tcvn_fields), column=0, sticky="w", padx=(2, 4), pady=2)
        Tooltip(lbl_lv, "Cấp công trình → hệ số tin cậy tầm quan trọng γn: "
                        "I=1.20, II=1.15, III=1.10.")
        cb_lv = ttk.Combobox(self.app.frame_tcvn_body, textvariable=self.app.var_imp_level,
                             values=['I', 'II', 'III'], width=7, state="readonly")
        cb_lv.grid(row=len(tcvn_fields), column=1, sticky="w", padx=(0, 2), pady=2)
        self.app.frame_tcvn_body.columnconfigure(1, weight=1, minsize=60)

        # Xem trước kết quả tính (cập nhật tức thời khi đổi tham số)
        self.app.lbl_tcvn_preview = ttk.Label(
            self.app.frame_tcvn_body, text="→ nhập Rc,k để tính",
            foreground="#1a6", wraplength=360, justify="left")
        self.app.lbl_tcvn_preview.grid(
            row=len(tcvn_fields) + 1, column=0, columnspan=2, sticky="w",
            pady=(4, 0))

        # Gắn trace cập nhật xem trước cho mọi biến TCVN (null-safe khi dựng UI)
        for _v in (self.app.var_rck, self.app.var_rtk, self.app.var_g0, self.app.var_gk,
                   self.app.var_gk_t, self.app.var_imp_level):
            _v.trace_add("write", self.app._update_tcvn_preview)
        self.app._toggle_tcvn()          # đặt trạng thái ban đầu (ẩn/mờ body)
        self.app._update_tcvn_preview()  # tính xem trước lần đầu

        # --- Thông số NỀN & ĐÀI (cho tab "SSI (đất–cọc)" và thiết kế kết cấu đài) ---
        frame_ssi = tk.LabelFrame(col1, text="Nền & đài cọc (cho SSI / thiết kế đài)",
                                  padx=10, pady=5)
        frame_ssi.pack(fill=tk.X, pady=5)
        ssi_fields = [
            (self.app.var_pile_length, "Chiều dài cọc Lc (m)",
             "Chiều dài cọc trong đất. Quyết định độ cứng dọc trục & vùng kháng "
             "ngang. Trống → engine vẽ minh hoạ."),
            (self.app.var_ks_soil, "Mô đun nền ks (T/m³)",
             "Hệ số nền ngang DỰ PHÒNG (lò xo Winkler hằng) khi nạp file MCOC KHÔNG "
             "có hệ số m. Nếu file có m, app TỰ dùng phương pháp “m” (TCVN 10304 "
             "Phụ lục A: k=m·z·d). Sét yếu ~300–800; cát chặt ~2000–5000 T/m³."),
            (self.app.var_cap_h, "Chiều cao đài H (m)",
             "Chiều cao (bề dày) đài cọc — dùng kiểm tra chọc thủng/uốn đài."),
            (self.app.var_cover, "Lớp bảo vệ a (m)",
             "Khoảng cách từ mép đài tới trọng tâm cốt thép (h0 = H − a)."),
            (self.app.var_col_b, "Bề rộng cột bx (m)",
             "Kích thước tiết diện trụ/cột theo phương x — cho chọc thủng & uốn."),
            (self.app.var_col_h, "Bề cao cột by (m)",
             "Kích thước tiết diện trụ/cột theo phương y."),
        ]
        for i, (var, text, tip) in enumerate(ssi_fields):
            r, c = divmod(i, 2)
            lbl = ttk.Label(frame_ssi, text=text)
            lbl.grid(row=r, column=c * 2, sticky="w", padx=(2, 4), pady=2)
            Tooltip(lbl, tip)
            ttk.Entry(frame_ssi, textvariable=var, width=9).grid(
                row=r, column=c * 2 + 1, sticky="ew", padx=(0, 8), pady=2)
        # Hàng combobox mác bê tông / nhóm thép
        rbase = (len(ssi_fields) + 1) // 2
        ttk.Label(frame_ssi, text="Mác bê tông đài").grid(row=rbase, column=0, sticky="w", padx=(2, 4), pady=2)
        ttk.Combobox(frame_ssi, textvariable=self.app.var_conc_grade, width=7, state="readonly",
                     values=['B15', 'B20', 'B25', 'B30', 'B35', 'B40']).grid(
            row=rbase, column=1, sticky="ew", padx=(0, 8), pady=2)
        ttk.Label(frame_ssi, text="Nhóm cốt thép").grid(row=rbase, column=2, sticky="w", padx=(2, 4), pady=2)
        ttk.Combobox(frame_ssi, textvariable=self.app.var_steel_grade, width=7, state="readonly",
                     values=['CB240-T', 'CB300-V', 'CB400-V', 'CB500-V']).grid(
            row=rbase, column=3, sticky="ew", padx=(0, 2), pady=2)
        # Checkbox hiệu ứng nhóm cọc
        tk.Checkbutton(frame_ssi, text="Xét hiệu ứng nhóm cọc (p-multiplier) khi phân tích ngang",
                       variable=self.app.var_group_effect).grid(
            row=rbase + 1, column=0, columnspan=4, sticky="w", pady=(4, 0))
        frame_ssi.columnconfigure(1, weight=1, minsize=60)
        frame_ssi.columnconfigure(3, weight=1, minsize=60)

        # --- Trụ địa chất & LÚN (TCVN 10304 Điều 7.4 — móng khối quy ước) ---
        frame_geo = tk.LabelFrame(col1, text="Trụ địa chất & lún (TCVN 10304 Đ.7.4)",
                                  padx=10, pady=5)
        frame_geo.pack(fill=tk.X, pady=5)
        geo_fields = [
            (self.app.var_phi_tb, "φ tb dọc cọc (°)",
             "Góc ma sát trong trung bình theo chiều dài cọc (trọng số bề dày lớp) "
             "— quyết định góc loe φ/4 của móng khối quy ước."),
            (self.app.var_cap_depth, "Độ sâu đáy đài (m)",
             "Từ mặt đất tới đáy đài. Đáy khối quy ước ở (độ sâu này + Lc)."),
            (self.app.var_gamma_avg, "γ' tb trên đáy khối (T/m³)",
             "Dung trọng đẩy nổi TB của đất trên đáy khối quy ước — để trừ ứng suất "
             "bản thân. Để TRỐNG = cộng lún HẾT các lớp (demo rõ hơn, thiên an toàn)."),
            (self.app.var_s_limit, "Lún giới hạn Sgh (m)",
             "Độ lún cho phép (cầu ~0.08 m) để kết luận ĐẠT/KHÔNG ĐẠT."),
        ]
        for i, (var, text, tip) in enumerate(geo_fields):
            r, c = divmod(i, 2)
            lbl = ttk.Label(frame_geo, text=text)
            lbl.grid(row=r, column=c * 2, sticky="w", padx=(2, 4), pady=2)
            Tooltip(lbl, tip)
            ttk.Entry(frame_geo, textvariable=var, width=9).grid(
                row=r, column=c * 2 + 1, sticky="ew", padx=(0, 8), pady=2)
        ttk.Label(frame_geo, text="Lớp đất DƯỚI mũi cọc — mỗi dòng: h, E, γ  (m, T/m², T/m³):",
                  foreground="#555").grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 1))
        self.app.txt_soil_layers = tk.Text(frame_geo, height=4, width=30, font=("Consolas", 9))
        self.app.txt_soil_layers.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(0, 2))
        chk_soft = ttk.Checkbutton(
            frame_geo, text="Đất dính yếu IL>0,6 dưới mũi (chặn a≤2d — TCVN 10304 Đ.7.4.4)",
            variable=self.app.var_soft_clay)
        chk_soft.grid(row=4, column=0, columnspan=4, sticky="w", pady=(0, 2))
        Tooltip(chk_soft, "Khi nền dưới mũi cọc là đất dính có chỉ số sệt IL>0,6, kích "
                          "thước móng khối quy ước mở rộng KHÔNG quá 2d mỗi bên (a≤2d). "
                          "Bật để tính lún theo đúng TCVN 10304:2014 Điều 7.4.4.")
        btnrow = tk.Frame(frame_geo)
        btnrow.grid(row=5, column=0, columnspan=4, sticky="w")
        ttk.Button(btnrow, text="⚡ Nạp DEMO đầy đủ",
                   command=self.app._load_demo_geotech).pack(side=tk.LEFT)
        ttk.Label(btnrow, text="(điền mọi ô TRỐNG: [Po]/[Ct], cột, mác, địa chất — cỡ theo tải file)",
                  foreground="#888").pack(side=tk.LEFT, padx=6)
        frame_geo.columnconfigure(1, weight=1, minsize=60)
        frame_geo.columnconfigure(3, weight=1, minsize=60)

        # Loads
        frame_loads = tk.LabelFrame(col2, text="Tổ hợp Tải trọng", padx=10, pady=5)
        frame_loads.pack(fill=tk.BOTH, expand=True, pady=5)

        cols = ("TH", "Hx", "Hy", "P", "Mx", "My", "Mz")
        self.app.tree_loads = ttk.Treeview(frame_loads, columns=cols, show="headings", height=5)
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
            self.app.tree_loads.heading(c, text=hdr)
            self.app.tree_loads.column(c, width=w, anchor="e")
        self.app.tree_loads.column("TH", anchor="center")

        # Scrollbar
        sb_loads = ttk.Scrollbar(frame_loads, orient="vertical", command=self.app.tree_loads.yview)
        self.app.tree_loads.configure(yscrollcommand=sb_loads.set)
        self.app.tree_loads.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_loads.pack(side=tk.RIGHT, fill=tk.Y)

        # Double-click để sửa
        self.app.tree_loads.bind("<Double-1>", lambda e: self.app.edit_load())

        # Nút CRUD tải trọng
        frame_load_btns = tk.Frame(inner)
        frame_load_btns.pack(fill=tk.X, pady=(0, 3))
        ttk.Button(frame_load_btns, text="Thêm tổ hợp",   command=self.app.add_load_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="Sửa dòng chọn", command=self.app.edit_load).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="Xóa dòng chọn", command=self.app.delete_load).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_load_btns, text="Dán nhiều dòng (CSV)", command=self.app.paste_loads_csv).pack(side=tk.RIGHT, padx=2)

        # --- ĐIỀU KHIỂN & KẾT QUẢ TỐI ƯU ---
        frame_run = tk.LabelFrame(col2, text="Điều Khiển Tối Ưu", padx=10, pady=5)
        frame_run.pack(fill=tk.X, pady=5)

        self.app.output_option = tk.StringVar(value="BEST")
        row_out = tk.Frame(frame_run); row_out.pack(fill=tk.X)
        ttk.Radiobutton(row_out, text="Chỉ phương án tối ưu", variable=self.app.output_option, value="BEST").pack(side=tk.LEFT)
        ttk.Radiobutton(row_out, text="Hiện tất cả phương án", variable=self.app.output_option, value="ALL").pack(side=tk.LEFT, padx=10)

        # Mục tiêu phụ (sau khi đủ số cọc + đạt Pmax<=Po)
        self.app.var_secondary = tk.StringVar(value="compact")
        row_sec = tk.Frame(frame_run); row_sec.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(row_sec, text="Ưu tiên:").pack(side=tk.LEFT)
        rb_compact = ttk.Radiobutton(row_sec, text="Tiết kiệm (bệ gọn)", variable=self.app.var_secondary,
                        value="compact")
        rb_compact.pack(side=tk.LEFT, padx=4)
        Tooltip(rb_compact, "Sau khi đủ cọc & đạt Pmax≤[Po], ưu tiên bố trí GỌN "
                            "(bệ nhỏ, ít tốn vật liệu).")
        rb_pmax = ttk.Radiobutton(row_sec, text="An toàn (giảm Pmax)", variable=self.app.var_secondary,
                        value="pmax")
        rb_pmax.pack(side=tk.LEFT, padx=10)
        Tooltip(rb_pmax, "Sau khi đủ cọc, ưu tiên GIẢM lực nén lớn nhất Pmax "
                         "(tăng dự trữ an toàn).")

        # Xử lý bệ chật (tùy chọn): k/c tối thiểu + đề xuất nới bệ. Mặc định 3d và
        # BẬT gợi ý — không đổi thuật toán, chỉ là lựa chọn người dùng kiểm soát.
        row_sp = tk.Frame(frame_run); row_sp.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(row_sp, text="K/c tối thiểu:").pack(side=tk.LEFT)
        cb_minsp = ttk.Combobox(row_sp, textvariable=self.app.var_min_spacing,
                     values=['3.0', '2.75', '2.5'], width=5, state="readonly")
        cb_minsp.pack(side=tk.LEFT, padx=2)
        Tooltip(cb_minsp, "Hệ số khoảng cách tim cọc tối thiểu (×d). TCVN khuyến "
                          "nghị 3.0d; giảm xuống 2.75d/2.5d chỉ khi bệ quá chật.")
        ttk.Label(row_sp, text="×d", foreground="#888").pack(side=tk.LEFT)
        chk_suggest = ttk.Checkbutton(row_sp, text="Đề xuất nới bệ khi bệ chật",
                        variable=self.app.var_suggest_cap)
        chk_suggest.pack(side=tk.LEFT, padx=(12, 0))
        Tooltip(chk_suggest, "Khi không xếp đủ cọc trong bệ hiện tại, gợi ý kích "
                             "thước bệ tối thiểu cần nới rộng.")

        # --- TỐI ƯU MỞ RỘNG: gộp chung vào "Điều Khiển Tối Ưu" (ngăn bằng đường kẻ) ---
        ttk.Separator(frame_run, orient="horizontal").pack(fill=tk.X, pady=(8, 4))
        ttk.Checkbutton(frame_run,
                        text="Bật tối ưu mở rộng (đổi đường kính cọc + thu bệ)",
                        variable=self.app.var_ext_enable,
                        command=self.app._toggle_ext).pack(anchor="w")
        self.app.frame_ext_body = tk.Frame(frame_run)

        row_chk = tk.Frame(self.app.frame_ext_body); row_chk.pack(fill=tk.X, pady=(2, 0))
        chk_r7 = ttk.Checkbutton(row_chk, text="R7 lực ngang [H]",
                        variable=self.app.var_ext_r7)
        chk_r7.pack(side=tk.LEFT)
        Tooltip(chk_r7, "R7: kiểm tra sức chịu LỰC NGANG [H] của cọc (cần khai báo "
                        "[H] trong bảng đường kính).")
        chk_r8 = ttk.Checkbutton(row_chk, text="R8 tương tác P–M",
                        variable=self.app.var_ext_r8)
        chk_r8.pack(side=tk.LEFT, padx=10)
        Tooltip(chk_r8, "R8: kiểm tra TƯƠNG TÁC nén–uốn (P–M) trên tiết diện cọc.")

        row_cap = tk.Frame(self.app.frame_ext_body); row_cap.pack(fill=tk.X, pady=(2, 0))
        chk_resize = ttk.Checkbutton(row_cap, text="Tự thu bệ",
                        variable=self.app.var_ext_capresize)
        chk_resize.pack(side=tk.LEFT)
        Tooltip(chk_resize, "Tự động THU NHỎ kích thước bệ về mức tối thiểu vừa đủ "
                            "bố trí cọc (làm tròn theo bội số đã chọn).")
        ttk.Label(row_cap, text="Làm tròn (m):").pack(side=tk.LEFT, padx=(8, 2))
        ttk.Combobox(row_cap, textvariable=self.app.var_ext_round,
                     values=['0.05', '0.1', '0.25', '0.5', '1.0'], width=5,
                     state="readonly").pack(side=tk.LEFT)

        row_dia = tk.Frame(self.app.frame_ext_body); row_dia.pack(fill=tk.X, pady=(2, 0))
        ttk.Button(row_dia, text="Bảng đường kính...",
                   command=self.app.open_diameter_dialog).pack(side=tk.LEFT)
        self.app.lbl_ext_dia = ttk.Label(row_dia, text="(chưa có — sẽ dùng d hiện tại)",
                                     foreground="#888")
        self.app.lbl_ext_dia.pack(side=tk.LEFT, padx=6)
        self.app._toggle_ext()   # ẩn body khi chưa bật

        # --- Cấu hình MCOC (bắt buộc — mọi phương án được chấm bằng MCOC chính xác) ---
        frame_mcoc = tk.LabelFrame(col2, text="Cấu hình MCOC (bắt buộc)", padx=10, pady=5)
        frame_mcoc.pack(fill=tk.X, pady=5)

        row_exe = tk.Frame(frame_mcoc)
        row_exe.pack(fill=tk.X, pady=2)
        ttk.Label(row_exe, text="MCOC Batch:").pack(side=tk.LEFT)
        self.app.txt_exe_path = ttk.Entry(row_exe, textvariable=self.app.params['exe_path'])
        self.app.txt_exe_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(row_exe, text="...", width=3, command=self.app.browse_exe).pack(side=tk.LEFT)

        self.app.lbl_template = ttk.Label(frame_mcoc, text="File input gốc: (chưa có)", foreground="gray")
        self.app.lbl_template.pack(anchor="w", pady=(2, 0))
        ttk.Label(frame_mcoc,
                  text="Mọi phương án đều được chấm bằng MCOC (chính xác) — cần MCOC Batch + file input MCOC gốc.",
                  foreground="#888").pack(anchor="w")
        # Giữ biến để tương thích (không dùng trong chế độ NSGA-II + MCOC)
        self.app.var_refine_mode = tk.StringVar(value="full")

        # ── Pane dưới: ô KẾT QUẢ ĐÁNH GIÁ — to hơn (2 cột nhập liệu đã gọn chiều cao) ──
        res_pane = tk.LabelFrame(left_paned, text="Kết quả Đánh giá", padx=8, pady=4)
        left_paned.add(res_pane, weight=3)

        self.app.txt_result = tk.Text(res_pane, height=18, width=72, font=("Consolas", 10), wrap="none")
        res_hsb = ttk.Scrollbar(res_pane, orient="horizontal", command=self.app.txt_result.xview)
        self.app.txt_result.configure(xscrollcommand=res_hsb.set)
        res_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        # Thẻ màu để dễ quét kết quả: ĐẠT xanh, KHÔNG ĐẠT đỏ, tiêu đề xanh đậm.
        self.app.txt_result.tag_config("ok", foreground="#1e8449")
        self.app.txt_result.tag_config("bad", foreground="#b03a2e")
        self.app.txt_result.tag_config("head", foreground="#1a3c5e", font=("Consolas", 10, "bold"))
        self.app.txt_result.tag_config("muted", foreground="#888")
        res_vsb = ttk.Scrollbar(res_pane, orient="vertical", command=self.app.txt_result.yview)
        self.app.txt_result.configure(yscrollcommand=res_vsb.set)
        res_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.app.txt_result.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right Panel
        right_frame = tk.Frame(main_paned, bg="white")
        main_paned.add(right_frame, weight=1)

        # Thêm Combobox để chọn Tổ hợp tải trọng mô phỏng
        frame_sim = tk.Frame(right_frame, bg="white")
        frame_sim.pack(side=tk.TOP, fill=tk.X, pady=5)

        tk.Label(frame_sim, text="Phương án:", bg="white").pack(side=tk.LEFT, padx=5)
        self.app.cb_config = ttk.Combobox(frame_sim, state="readonly", width=25)
        self.app.cb_config.pack(side=tk.LEFT, padx=5)
        self.app.cb_config.bind("<<ComboboxSelected>>", self.app.update_simulation)

        tk.Label(frame_sim, text="Tổ hợp:", bg="white").pack(side=tk.LEFT, padx=5)
        self.app.cb_load_case = ttk.Combobox(frame_sim, state="readonly", width=12)
        self.app.cb_load_case.pack(side=tk.LEFT, padx=5)
        self.app.cb_load_case.bind("<<ComboboxSelected>>", self.app.update_simulation)

        # Chế độ hiển thị — đặt trên HÀNG RIÊNG (5 chế độ, tránh tràn ngang).
        frame_view = tk.Frame(right_frame, bg="white")
        frame_view.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))
        tk.Label(frame_view, text="Xem:", bg="white").pack(side=tk.LEFT, padx=(6, 4))
        self.app.view_mode = tk.StringVar(value=S.VIEW_LAYOUT)
        for _txt, _val in (("Mặt bằng", S.VIEW_LAYOUT),
                           ("Điều kiện R1–R8", S.VIEW_AUDIT),
                           ("3D", S.VIEW_MODEL3D),
                           ("SSI đất–cọc", S.VIEW_SSI),
                           ("Thiết kế đài", S.VIEW_CAPDESIGN)):
            ttk.Radiobutton(frame_view, text=_txt, variable=self.app.view_mode,
                            value=_val, command=self.app.update_simulation).pack(side=tk.LEFT, padx=3)

        # Dải KPI: mục tiêu (số cọc) + hệ số sử dụng max + tổ hợp chi phối — luôn hiện
        self.app.lbl_kpi = tk.Label(right_frame, text="", bg="#eef3f8", fg="#1a3c5e",
                                font=("Arial", 10, "bold"), anchor="w", padx=8, pady=4)
        self.app.lbl_kpi.pack(side=tk.TOP, fill=tk.X, padx=2)

        # Ghi chú phạm vi & giới hạn mô hình (bắt buộc theo chuẩn tư vấn thiết kế)
        self.app.lbl_scope = tk.Label(
            right_frame,
            text=("Phạm vi: bố trí/tối ưu dùng mô hình bệ cứng. Tab “SSI (đất–cọc)” "
                  "thêm Hx/Hy/Mz (nền Winkler) + hiệu ứng nhóm cọc (p-mult) + độ lún; "
                  "tab “Thiết kế đài” kiểm toán uốn/chọc thủng/cắt theo TCVN 11823-5:2017 (bê tông cầu, LRFD). "
                  "Đều là THIẾT KẾ SƠ BỘ — hồ sơ chi tiết vẫn cần MCOC/FEM đầy đủ."),
            bg="white", fg="#888", font=("Arial", 8), anchor="w",
            justify="left", wraplength=720)
        self.app.lbl_scope.pack(side=tk.BOTTOM, fill=tk.X, padx=4, pady=(0, 2))
        # Auto-scale: ghi chú phạm vi tự xuống dòng theo bề rộng panel phải,
        # tránh chữ bị cắt/đổi bố cục khi người dùng kéo chỉnh layout.
        right_frame.bind(
            "<Configure>",
            lambda e: self.app.lbl_scope.config(wraplength=max(e.width - 16, 200)))

        self.app.plot_canvas = PlotCanvas(right_frame)
        self.app.plot_canvas.widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
