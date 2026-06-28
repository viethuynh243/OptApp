"""loads.py - LoadsController: quản lý danh sách tổ hợp tải trọng (Tab 1).

Tách từ ui/main_window.py (Plan 023, Pha 3a) — giữ NGUYÊN hành vi. Thao tác trên
state chia sẻ `app.loads` và widget `app.tree_loads`.
"""
import tkinter as tk
from tkinter import ttk, messagebox


class LoadsController:
    """CRUD tổ hợp tải trọng: thêm/sửa/xóa qua hộp thoại, dán nhiều dòng CSV,
    và vẽ lại Treeview tải trọng."""

    def __init__(self, app):
        self.app = app

    def add_default_loads(self):
        """Khởi đầu bằng danh sách tải trọng TRỐNG (người dùng tự thêm/nhập)."""
        # Khởi đầu bằng TẢI TRỌNG TRỐNG (sạch) — người dùng tự thêm/nhập.
        self.app.loads = []
        self.refresh_loads_ui()

    def refresh_loads_ui(self):
        """Vẽ lại bảng tải trọng (Treeview) từ danh sách app.loads hiện hành."""
        for item in self.app.tree_loads.get_children():
            self.app.tree_loads.delete(item)
        for i, load in enumerate(self.app.loads):
            self.app.tree_loads.insert("", tk.END, values=(
                i + 1,
                load.get('Hx', 0.0), load.get('Hy', 0.0), load.get('N', 0.0),
                load.get('Mx', 0.0), load.get('My', 0.0), load.get('Mz', 0.0)
            ))

    # ── Nhập liệu tải trọng thủ công ──────────────────────────────────────

    def _load_dialog(self, title, init=None):
        """Hộp thoại nhập / sửa 1 tổ hợp tải trọng.
        Trả về dict hoặc None nếu hủy.
        """
        dlg = tk.Toplevel(self.app.root)
        dlg.title(title)
        dlg.resizable(False, False)
        dlg.grab_set()          # Modal
        dlg.transient(self.app.root)

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
            self.app.loads.append(d)
            self.refresh_loads_ui()

    def edit_load(self):
        """Sửa tổ hợp tải trọng đang chọn."""
        sel = self.app.tree_loads.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một tổ hợp để sửa.")
            return
        idx = self.app.tree_loads.index(sel[0])
        d = self._load_dialog(f"Sửa tổ hợp {idx + 1}", init=self.app.loads[idx])
        if d is not None:
            self.app.loads[idx] = d
            self.refresh_loads_ui()

    def delete_load(self):
        """Xóa các tổ hợp tải trọng đang chọn."""
        sel = self.app.tree_loads.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Vui lòng chọn tổ hợp cần xóa.")
            return
        if not messagebox.askyesno("Xác nhận", f"Xóa {len(sel)} tổ hợp đã chọn?"):
            return
        idxs = sorted([self.app.tree_loads.index(s) for s in sel], reverse=True)
        for i in idxs:
            self.app.loads.pop(i)
        self.refresh_loads_ui()

    def paste_loads_csv(self):
        """Nhập nhiều tổ hợp từ văn bản CSV dán vào (clipboard hoặc text area)."""
        dlg = tk.Toplevel(self.app.root)
        dlg.title("Nhập tải trọng từ văn bản CSV")
        dlg.geometry("560x360")
        dlg.grab_set()
        dlg.transient(self.app.root)

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
                self.app.loads = new_loads
            else:
                self.app.loads.extend(new_loads)
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
