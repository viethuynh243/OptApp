import re
import os

# --- 1. Fix mechanics.py return signature ---
mech_file = 'core/mechanics.py'
with open(mech_file, 'r', encoding='utf-8') as f:
    mech_content = f.read()

old_mech_ret = "return ok, pmax, pmin, forces, final_msg"
new_mech_ret = "return ok, pmax, pmin, mxmax, mymax, forces, final_msg"
mech_content = mech_content.replace(old_mech_ret, new_mech_ret)

with open(mech_file, 'w', encoding='utf-8') as f:
    f.write(mech_content)


# --- 2. Fix optimizer.py (unpack and store mxmax, mymax) ---
opt_file = 'core/optimizer.py'
with open(opt_file, 'r', encoding='utf-8') as f:
    opt_content = f.read()

opt_content = opt_content.replace(
    "ok, pmax, pmin, forces, msg = check_layout",
    "ok, pmax, pmin, mxmax, mymax, forces, msg = check_layout"
)

old_cand = """                'pmax': pmax,
                'pmin': pmin,
                'forces': forces,"""
new_cand = """                'pmax': pmax,
                'pmin': pmin,
                'mxmax': mxmax,
                'mymax': mymax,
                'forces': forces,"""
opt_content = opt_content.replace(old_cand, new_cand)

old_orig_cand = """            'pmax': pmax,
            'pmin': pmin,
            'forces': forces,"""
new_orig_cand = """            'pmax': pmax,
            'pmin': pmin,
            'mxmax': mxmax,
            'mymax': mymax,
            'forces': forces,"""
opt_content = opt_content.replace(old_orig_cand, new_orig_cand)

with open(opt_file, 'w', encoding='utf-8') as f:
    f.write(opt_content)


# --- 3. Fix main_window.py ---
main_file = 'ui/main_window.py'
with open(main_file, 'r', encoding='utf-8') as f:
    main_content = f.read()

# a. Fix button text "Nhiều File" -> "1 File"
main_content = main_content.replace('Kéo thả File hoặc Chọn Input (Nhiều File)', 'Kéo thả File hoặc Chọn Input (1 File)')

# b. Remove .cti export logic entirely from save_file
# We will just remove lines from `# Sinh file .cti cho spColumn` up to the end of the `try` block.
# Let's use regex.
import re
# Find from # Sinh file .cti cho spColumn to the end of the try block
pattern_cti = re.compile(r'# Sinh file \.cti cho spColumn\s+if self\.var_export_cti\.get\(\):.*?messagebox\.showinfo\("Thành công", f"Đã xuất kết quả ra file:\\n{filepath}"\)', re.DOTALL)
main_content = pattern_cti.sub('messagebox.showinfo("Thành công", f"Đã xuất kết quả ra file:\\\\n{filepath}")', main_content)

# c. Print Mmax in run_optimize
old_print_orig = """            self.txt_result.insert(tk.END, f"  Pmin = {orig['pmin']:.2f} kN  (Gioi han chiu nho: -{P_TENSION:.0f} kN)\\n")"""
new_print_orig = """            self.txt_result.insert(tk.END, f"  Pmin = {orig['pmin']:.2f} kN  (Gioi han chiu nho: -{P_TENSION:.0f} kN)\\n")
            if self.params['M_LIMIT'].get() > 0:
                self.txt_result.insert(tk.END, f"  Mmax = {max(orig.get('mxmax',0), orig.get('mymax',0)):.2f} kNm (Gioi han uon: {self.params['M_LIMIT'].get():.0f} kNm)\\n")"""
main_content = main_content.replace(old_print_orig, new_print_orig)

old_print_rec = """            self.txt_result.insert(tk.END, f"     Pmin = {rec['pmin']:.2f} kN\\n")"""
new_print_rec = """            self.txt_result.insert(tk.END, f"     Pmin = {rec['pmin']:.2f} kN\\n")
            if self.params['M_LIMIT'].get() > 0:
                self.txt_result.insert(tk.END, f"     Mmax = {max(rec.get('mxmax',0), rec.get('mymax',0)):.2f} kNm\\n")"""
main_content = main_content.replace(old_print_rec, new_print_rec)

# d. Add Browse button for MCOC exe path
# Current UI:
#         tk.Label(frame_bb, text="Đường dẫn file .exe:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
#         self.txt_exe_path = tk.Entry(frame_bb, width=30)
#         self.txt_exe_path.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
old_bb_ui = """        self.txt_exe_path = tk.Entry(frame_bb, width=30)
        self.txt_exe_path.grid(row=0, column=1, padx=5, pady=5, sticky='ew')"""
new_bb_ui = """        self.txt_exe_path = tk.Entry(frame_bb, width=20)
        self.txt_exe_path.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(frame_bb, text="Chọn", command=self.browse_exe, width=5).grid(row=0, column=2, padx=5, pady=5)"""
main_content = main_content.replace(old_bb_ui, new_bb_ui)

# And add the browse_exe method right after save_file
browse_meth = """
    def browse_exe(self):
        filepath = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")])
        if filepath:
            self.txt_exe_path.delete(0, tk.END)
            self.txt_exe_path.insert(0, filepath)
"""
if "def browse_exe" not in main_content:
    main_content = main_content.replace("    def load_file(self):", browse_meth + "\n    def load_file(self):")

with open(main_file, 'w', encoding='utf-8') as f:
    f.write(main_content)


# --- 4. Fix export_utils.py (add Mmax) ---
export_file = 'io_handlers/export_utils.py'
with open(export_file, 'r', encoding='utf-8') as f:
    export_content = f.read()

old_pdf_pmin = "c.drawString(70, y, f\"Pmin = {config.get('pmin', 0):.2f} kN\"); y -= 15"
new_pdf_pmin = """c.drawString(70, y, f"Pmin = {config.get('pmin', 0):.2f} kN"); y -= 15
    if params.get('M_LIMIT', 0) > 0:
        c.drawString(70, y, f"Mmax = {max(config.get('mxmax', 0), config.get('mymax', 0)):.2f} kNm"); y -= 15"""
export_content = export_content.replace(old_pdf_pmin, new_pdf_pmin)

old_pdf_param = "c.drawString(70, y, f\"Suc chiu tai cho phep: Pmax = {params.get('P_LIMIT')} kN, Pnho = {params.get('P_TENSION')} kN\"); y -= 30"
new_pdf_param = """c.drawString(70, y, f"Suc chiu tai cho phep: Pmax = {params.get('P_LIMIT')} kN, Pnho = {params.get('P_TENSION')} kN"); y -= 15
    if params.get('M_LIMIT', 0) > 0:
        c.drawString(70, y, f"Suc uon cho phep: Mmax = {params.get('M_LIMIT')} kNm"); y -= 15
    else:
        y -= 15"""
export_content = export_content.replace(old_pdf_param, new_pdf_param)

with open(export_file, 'w', encoding='utf-8') as f:
    f.write(export_content)

print("Patch 2 completed.")
