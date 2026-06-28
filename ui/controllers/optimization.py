"""optimization.py - OptimizationController: chạy tối ưu (NSGA-II / mở rộng / tinh chỉnh).

Tách từ ui/main_window.py (Plan 023, Pha 3f) — giữ NGUYÊN hành vi. Chạy trên
thread nền, cập nhật app.txt_result / nút Chạy-Dừng / tiến trình.
"""
import os
import threading
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from core.blackbox import MCOCBlackbox
from core.refine_optimizer import run_pareto_refinement
from ui import constants as uiconst
from ui.widgets.widget_utils import set_state_recursive


class OptimizationController:
    """Điều phối CHẠY tối ưu: kiểm tra cấu hình MCOC, vòng đời 1 lần chạy (khóa nút/tiến trình/Dừng hợp tác), luồng NSGA-II chuẩn, luồng mở rộng (quét đường kính), tinh chỉnh MCOC, và quản lý bảng đường kính ứng viên."""

    def __init__(self, app):
        self.app = app

    def _validate_mcoc_setup(self):
        """Kiểm tra cấu hình MCOC bắt buộc (exe + file input gốc + tọa độ cọc gốc).

        Trả về True nếu hợp lệ; nếu thiếu thì hiện cảnh báo phù hợp và trả về False.
        Dùng chung cho run_optimize / run_optimize_ext / run_refine_real.
        """
        exe = self.app.params['exe_path'].get().strip()
        if not exe or not os.path.exists(exe):
            messagebox.showwarning(
                "Cần cấu hình MCOC",
                "Mọi phương án được chấm bằng MCOC (chính xác).\n"
                "Hãy chọn đường dẫn MCOC Batch ở mục \"Cấu hình MCOC (bắt buộc)\".")
            return False
        if (not self.app.input_filepath or not os.path.exists(self.app.input_filepath)
                or not getattr(self.app, 'original_coords', None)):
            messagebox.showwarning(
                "Thiếu file MCOC gốc",
                "Cần mở FILE INPUT MCOC gốc (.txt, có tọa độ cọc gốc) làm template.\n"
                "Dùng \"Mở file đầu vào\" để nạp file input MCOC — không phải file _result hay CSV.")
            return False
        return True


    def _set_running(self, running: bool):
        """Bật/tắt trạng thái "đang chạy": khóa nút Chạy, mở nút Dừng, chạy
        thanh tiến trình; và ngược lại khi kết thúc."""
        if running:
            self.app._is_running = True
            self.app._run_cancel.clear()
            self.app._set_status("Đang chạy tối ưu...")
            self.app.btn_run_opt.config(state="disabled")
            self.app.btn_stop_opt.config(state="normal")
            try:
                self.app.progress_run.start(12)
            except Exception:
                pass
        else:
            self.app._is_running = False
            self.app._set_status("Đã xong." if not self.app._run_cancel.is_set() else "Đã dừng.")
            self.app.btn_run_opt.config(state="normal")
            self.app.btn_stop_opt.config(state="disabled")
            try:
                self.app.progress_run.stop()
            except Exception:
                pass


    def _poll_run_progress(self, evaluator=None):
        """Cập nhật nhãn "Đã gọi MCOC: N lần" mỗi 250 ms khi còn đang chạy.

        evaluator chỉ là gợi ý ban đầu; thực tế ưu tiên evaluator hiện hành
        (self.app._active_evaluator) vì luồng mở rộng đổi runner theo từng đường kính."""
        if not self.app._is_running:
            return
        ev = self.app._active_evaluator or evaluator
        runner = getattr(ev, 'runner', None)
        if runner is not None and not self.app._run_cancel.is_set():
            self.app.lbl_run_status.config(
                text="Đã gọi MCOC: %d lần" % getattr(runner, 'n_calls', 0))
        self.app.root.after(250, lambda: self._poll_run_progress(evaluator))


    def _request_stop_opt(self):
        """Yêu cầu DỪNG: đặt cờ hợp tác; evaluator bọc sẽ ngắt ở lần chấm kế tiếp."""
        self.app._run_cancel.set()
        self.app.lbl_run_status.config(text="Đang dừng...")


    def _wrap_cancellable(self, evaluator):
        """Bọc evaluator thực để hỗ trợ DỪNG hợp tác mà KHÔNG sửa core.

        Trước mỗi lần chấm, nếu cờ dừng đã đặt thì ném MCOCError để vòng tối ưu
        thoát ở lần đánh giá kế tiếp. Sao chép .runner/.workdir để phần đếm tiến
        trình và xử lý kết quả vẫn hoạt động."""
        from core.mcoc_runner import MCOCError

        def wrapped(coords):
            if self.app._run_cancel.is_set():
                raise MCOCError("Đã dừng theo yêu cầu")
            return evaluator(coords)

        wrapped.runner = getattr(evaluator, 'runner', None)
        wrapped.workdir = getattr(evaluator, 'workdir', None)
        if hasattr(evaluator, 'dia'):
            wrapped.dia = evaluator.dia
        # evaluator hiện hành để _poll_run_progress đếm đúng runner đang chạy
        self.app._active_evaluator = wrapped
        return wrapped


    def run_optimize(self):
        """Chạy tối ưu — mặc định ĐÁNH GIÁ CHÍNH XÁC bằng MCOC (NSGA-II).

        Nếu bật "Tối ưu mở rộng" thì chuyển sang luồng quét đường kính + R7/R8 +
        thu bệ (run_optimize_ext)."""
        if self.app.var_ext_enable.get():
            return self.run_optimize_ext()
        if self.app._is_running:   # chống bấm Chạy lần 2 khi đang chạy
            return
        # 0) Phải nhập đủ thông số bài toán bắt buộc (> 0)
        required = {'L_X': "Rộng bệ Lx", 'L_Y': "Dài bệ Ly",
                    'D_PILE': "Đ.kính cọc d", 'P_LIMIT': "Sức nén [Po]"}
        missing = [name for k, name in required.items() if self.app._pget(k) <= 0]
        if missing:
            messagebox.showwarning(
                "Chưa nhập đủ thông số",
                "Vui lòng nhập (giá trị > 0) cho: " + ", ".join(missing) + ".")
            return

        # 1) Phải có tải trọng
        if not self.app.loads:
            messagebox.showwarning(
                "Chưa có tải trọng",
                "Vui lòng thêm ít nhất một tổ hợp tải trọng "
                "(nút \"Thêm tổ hợp\", \"Dán nhiều dòng (CSV)\" hoặc mở file đầu vào).")
            return

        # 2) BẮT BUỘC MCOC — không chấp nhận phương án xấp xỉ
        if not self._validate_mcoc_setup():
            return

        params = self.app.get_params_dict()
        params['input_filepath'] = self.app.input_filepath
        params['mock_mode'] = False
        loads = list(self.app.loads)

        self.app.txt_result.delete(1.0, tk.END)
        self.app._log_refine("=== TỐI ƯU BẰNG MCOC (NSGA-II — đánh giá chính xác) ===")
        self.app._log_refine("Đang chạy MCOC, vui lòng đợi...")
        self._set_running(True)

        def worker():
            from core.mcoc_runner import MCOCError
            try:
                from io_handlers.mcoc_writer import self_check
                from core.nsga2_optimizer import run_nsga2
                ok, msg = self_check(self.app.input_filepath, params['original_coords'])
                if not ok:
                    self.app._log_refine("LỖI TEMPLATE: " + msg)
                    return
                # Tải trọng lấy TỪ UI (ghi đè tải trong file MCOC gốc) — UI là nguồn duy nhất
                evaluator = MCOCBlackbox.make_real_evaluator(params, loads=loads, log=self.app._log_refine)
                ev = self._wrap_cancellable(evaluator)
                self.app.root.after(0, lambda: self._poll_run_progress(ev))
                # Chấm phương án gốc (để so sánh) — cùng bộ tải UI
                orig_res = ev(np.array(params['original_coords'], dtype=float))
                results = run_nsga2(params, loads, evaluator=ev,
                                    **uiconst.NSGA2_INTERACTIVE,
                                    secondary=self.app.var_secondary.get(),
                                    log=self.app._log_refine)
                results['_orig_eval'] = (len(params['original_coords']), orig_res)
                self.app.root.after(0, lambda: self.app._show_nsga2_results(results))
            except MCOCError as e:
                if "Đã dừng" in str(e):
                    self.app._log_refine("Đã dừng.")
                else:
                    self.app._log_refine("LỖI: %s" % e)
            except Exception as e:
                import traceback
                self.app._log_refine("LỖI: %s" % e)
                self.app._log_refine(traceback.format_exc()[-300:])
            finally:
                self.app.root.after(0, lambda: self._set_running(False))

        threading.Thread(target=worker, daemon=True).start()

    # --- Delegators -> ResultsView (Plan 023) ---


    def _toggle_ext(self):
        """LUÔN hiện phần thân cấu hình mở rộng để người dùng THẤY chức năng
        (đổi đường kính, R7/R8, thu bệ) — tránh ẩn khiến không biết chương trình
        có gì. Công tắc chính chỉ quyết định luồng chạy có dùng mở rộng hay không;
        khi tắt thì làm mờ các điều khiển con để báo trạng thái rõ ràng."""
        self.app.frame_ext_body.pack(fill=tk.X)   # luôn hiện -> dễ khám phá
        on = self.app.var_ext_enable.get()
        set_state_recursive(self.app.frame_ext_body, on)


    def _diameter_row_dialog(self, title, init=None):
        """Hộp thoại nhập/sửa 1 dòng bảng đường kính. Trả về dict hoặc None.

        Trường: d (m), [Po] (T), [Ct] (T), [M] (T.m), [H] (T). d>0 và [Po]>0
        bắt buộc; [Ct]/[M]/[H] = 0 nghĩa là không kiểm ràng buộc tương ứng.
        """
        dlg = tk.Toplevel(self.app.root)
        dlg.title(title); dlg.resizable(False, False)
        dlg.grab_set(); dlg.transient(self.app.root)
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
        dlg = tk.Toplevel(self.app.root)
        dlg.title("Bảng đường kính ứng viên")
        dlg.geometry("520x340"); dlg.grab_set(); dlg.transient(self.app.root)

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
            for r in self.app.ext_diameters:
                tree.insert("", tk.END, values=(f"{r['d']:g}", f"{r['Po']:g}",
                            f"{r['Ct']:g}", f"{r['M']:g}", f"{r['H']:g}"))

        def add_row():
            r = self._diameter_row_dialog("Thêm đường kính")
            if r:
                self.app.ext_diameters.append(r); refresh()

        def edit_row():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Thông báo", "Chọn một dòng để sửa.", parent=dlg); return
            idx = tree.index(sel[0])
            r = self._diameter_row_dialog("Sửa đường kính", init=self.app.ext_diameters[idx])
            if r:
                self.app.ext_diameters[idx] = r; refresh()

        def del_row():
            sel = tree.selection()
            if not sel:
                return
            for i in sorted([tree.index(s) for s in sel], reverse=True):
                self.app.ext_diameters.pop(i)
            refresh()

        def seed_current():
            """Thêm 1 dòng từ thông số bài toán hiện tại trên UI."""
            d = self.app._pget('D_PILE')
            if d <= 0:
                messagebox.showinfo("Thông báo", "Chưa có đường kính d trên UI.", parent=dlg); return
            self.app.ext_diameters.append({'d': d, 'Po': self.app._pget('P_LIMIT'),
                                       'Ct': self.app._pget('P_TENSION'),
                                       'M': self.app._pget('M_LIMIT'), 'H': 0.0})
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
        if not self.app.ext_diameters:
            self.app.lbl_ext_dia.config(text="(chưa có — sẽ dùng d hiện tại)", foreground="#888")
        else:
            ds = ", ".join(f"{r['d']:g}" for r in sorted(self.app.ext_diameters, key=lambda r: r['d']))
            self.app.lbl_ext_dia.config(text=f"{len(self.app.ext_diameters)} đ.kính: {ds} m",
                                    foreground="black")


    def run_optimize_ext(self):
        """Chạy TỐI ƯU MỞ RỘNG: quét đường kính (MCOC) + R7/R8 + thu bệ."""
        if self.app._is_running:   # chống bấm Chạy lần 2 khi đang chạy
            return
        # Validation giống luồng chuẩn
        required = {'L_X': "Rộng bệ Lx", 'L_Y': "Dài bệ Ly",
                    'D_PILE': "Đ.kính cọc d (gốc)", 'P_LIMIT': "Sức nén [Po]"}
        missing = [name for k, name in required.items() if self.app._pget(k) <= 0]
        if missing:
            messagebox.showwarning("Chưa nhập đủ thông số",
                                   "Vui lòng nhập (>0) cho: " + ", ".join(missing) + ".")
            return
        if not self.app.loads:
            messagebox.showwarning("Chưa có tải trọng", "Vui lòng thêm ít nhất một tổ hợp tải trọng.")
            return
        if not self._validate_mcoc_setup():
            return

        params = self.app.get_params_dict()
        params['input_filepath'] = self.app.input_filepath
        params['mock_mode'] = False
        loads = list(self.app.loads)
        d_orig = getattr(self.app, 'original_d', None) or self.app._pget('D_PILE')
        # [Po] trong file MCOC chỉ là mặc định (500) — ƯU TIÊN giá trị người dùng
        # nhập trên UI làm sức chịu nén GỐC; chỉ lùi về giá trị file nếu UI trống.
        Po_orig = self.app._pget('P_LIMIT') or getattr(self.app, 'original_p', None) or 500.0

        # Bảng đường kính: dùng bảng người dùng, hoặc 1 dòng từ thông số hiện tại
        from core.ext.pile_section import DiameterTable
        from core.ext.config_ext import ExtConfig
        if self.app.ext_diameters:
            table = DiameterTable(self.app.ext_diameters)
        else:
            table = DiameterTable([{'d': self.app._pget('D_PILE'), 'Po': self.app._pget('P_LIMIT'),
                                    'Ct': self.app._pget('P_TENSION'), 'M': self.app._pget('M_LIMIT'),
                                    'H': 0.0}])
        cfg = ExtConfig(enable_R7=self.app.var_ext_r7.get(), enable_R8=self.app.var_ext_r8.get(),
                        cap_round_to=float(self.app.var_ext_round.get()),
                        cap_resize=self.app.var_ext_capresize.get())

        self.app.txt_result.delete(1.0, tk.END)
        self.app._log_refine("=== TỐI ƯU MỞ RỘNG (quét %d đường kính, R7=%s, R8=%s) ==="
                         % (len(table), cfg.enable_R7, cfg.enable_R8))
        self.app._log_refine("Đang chạy MCOC cho từng đường kính, vui lòng đợi...")
        self._set_running(True)
        self.app.root.after(0, lambda: self._poll_run_progress(None))

        def worker():
            from core.mcoc_runner import MCOCError
            try:
                from io_handlers.mcoc_writer import self_check
                from core.ext.orchestrator import run_extended_optimization
                ok, msg = self_check(self.app.input_filepath, params['original_coords'])
                if not ok:
                    self.app._log_refine("LỖI TEMPLATE: " + msg)
                    return
                # Factory bọc evaluator thực mỗi đường kính để hỗ trợ DỪNG hợp tác.
                def _cancellable_factory(params_d, dia, lds):
                    from core.ext.blackbox_ext import make_diameter_evaluator
                    base_ev = make_diameter_evaluator(params, dia, loads=lds,
                                                      d_orig=d_orig, Po_orig=Po_orig,
                                                      log=self.app._log_refine)
                    return self._wrap_cancellable(base_ev)
                out = run_extended_optimization(
                    params, loads, table, cfg=cfg,
                    evaluator_factory=_cancellable_factory,
                    d_orig=d_orig, Po_orig=Po_orig,
                    **uiconst.NSGA2_EXTENDED,
                    secondary=self.app.var_secondary.get(), log=self.app._log_refine)
                self.app.root.after(0, lambda: self.app._show_ext_results(out, cfg))
            except MCOCError as e:
                if "Đã dừng" in str(e):
                    self.app._log_refine("Đã dừng.")
                else:
                    self.app._log_refine("LỖI: %s" % e)
            except Exception as e:
                import traceback
                self.app._log_refine("LỖI: %s" % e)
                self.app._log_refine(traceback.format_exc()[-400:])
            finally:
                self.app.root.after(0, lambda: self._set_running(False))

        threading.Thread(target=worker, daemon=True).start()


    def run_refine_real(self):
        """Chạy chế độ MCOC thực: tinh chỉnh Pareto từng bước trên thread nền,
        dùng file input MCOC gốc làm template."""
        if self.app._is_running:   # chống bấm Chạy lần 2 khi đang chạy
            return
        if not self._validate_mcoc_setup():
            return

        self.app.txt_result.delete(1.0, tk.END)
        self.app.txt_result.insert(tk.END, "=== HOP DEN MCOC THUC - TINH CHINH TUNG BUOC ===\n")

        params = self.app.get_params_dict()
        params['input_filepath'] = self.app.input_filepath
        params['mock_mode'] = False
        params['refine_mode'] = self.app.var_refine_mode.get()
        loads = list(self.app.loads)
        self._set_running(True)

        def worker():
            from core.mcoc_runner import MCOCError
            try:
                # Kiểm tra template trước khi chạy
                from io_handlers.mcoc_writer import self_check
                ok, msg = self_check(self.app.input_filepath, params['original_coords'])
                if not ok:
                    self.app._log_refine("LOI TEMPLATE: " + msg)
                    return
                self.app._log_refine("Template: " + msg)

                evaluator = MCOCBlackbox.make_real_evaluator(params, log=self.app._log_refine)
                ev = self._wrap_cancellable(evaluator)
                self.app.root.after(0, lambda: self._poll_run_progress(ev))
                results = run_pareto_refinement(params, loads, ev, log=self.app._log_refine)
                self.app.root.after(0, lambda: self.app._show_refine_results(results))
            except MCOCError as e:
                if "Đã dừng" in str(e):
                    self.app._log_refine("Đã dừng.")
                else:
                    self.app._log_refine("LOI: %s" % e)
            except Exception as e:
                self.app._log_refine("LOI: %s" % e)
            finally:
                self.app.root.after(0, lambda: self._set_running(False))

        threading.Thread(target=worker, daemon=True).start()
