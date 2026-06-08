import os

# --- 1. Fix optimizer.py: Missing 'ok' and 'msg' in fallback dict ---
opt_file = 'core/optimizer.py'
with open(opt_file, 'r', encoding='utf-8') as f:
    content = f.read()

old_fallback = """        if recommended is None and ok:
            recommended = {
                'type': 'Gốc',
                'nx': 0, 'ny': 0,
                'sx': 0, 'sy': 0,
                'n': len(orig_coords),
                'coords': orig_coords,
                'pmax': pmax,
                'pmin': pmin,
                'forces': forces
            }"""
new_fallback = """        if recommended is None and ok:
            recommended = {
                'type': 'Gốc',
                'nx': 0, 'ny': 0,
                'sx': 0, 'sy': 0,
                'n': len(orig_coords),
                'coords': orig_coords,
                'pmax': pmax,
                'pmin': pmin,
                'forces': forces,
                'ok': True,
                'msg': 'Sử dụng phương án gốc'
            }"""
if old_fallback in content:
    content = content.replace(old_fallback, new_fallback)
    with open(opt_file, 'w', encoding='utf-8') as f:
        f.write(content)


# --- 2. Fix main_window.py issues ---
main_file = 'ui/main_window.py'
with open(main_file, 'r', encoding='utf-8') as f:
    content = f.read()

# a. Fix default loads (remove 0.0 row)
old_default_loads = """    def add_default_loads(self):
        default_loads = [
            {'Hx': 0.0, 'Hy': 0.0, 'N': 0.0, 'Mx': 0.0, 'My': 0.0, 'Mz': 0.0},
            {'Hx': 41.0, 'Hy': 0.0, 'N': 2577.0, 'Mx': -204.0, 'My': 646.0, 'Mz': 0.0},"""
new_default_loads = """    def add_default_loads(self):
        default_loads = [
            {'Hx': 41.0, 'Hy': 0.0, 'N': 2577.0, 'Mx': -204.0, 'My': 646.0, 'Mz': 0.0},"""
content = content.replace(old_default_loads, new_default_loads)

# b. Fix conflict du lieu (extend -> = )
old_extend = "self.loads.extend(loads)"
new_extend = "self.loads = loads"
content = content.replace(old_extend, new_extend)

# c. Rename "Cấu hình Hộp Đen" -> "Liên kết Phần mềm Tính Lực"
old_bb_title = 'frame_bb = tk.LabelFrame(tab_params, text="Cấu hình Hộp Đen (Black-box)"'
new_bb_title = 'frame_bb = tk.LabelFrame(tab_params, text="Liên kết Phần mềm Tính Lực (MCOC)"'
content = content.replace(old_bb_title, new_bb_title)

# d. Increase result text box size
old_text_box = 'self.txt_result = tk.Text(frame_result, height=8'
new_text_box = 'self.txt_result = tk.Text(frame_result, height=15'
content = content.replace(old_text_box, new_text_box)

# e. Rename "TÍNH TOÁN BATCH" -> "TÍNH TOÁN"
old_btn_batch = 'text="TÍNH TOÁN BATCH"'
new_btn_batch = 'text="TÍNH TOÁN"'
content = content.replace(old_btn_batch, new_btn_batch)

with open(main_file, 'w', encoding='utf-8') as f:
    f.write(content)


# --- 3. Fix export_utils.py (UTF-8 issues in PDF "Gốc" -> "Goc") ---
export_file = 'io_handlers/export_utils.py'
with open(export_file, 'r', encoding='utf-8') as f:
    content = f.read()

old_type = "c.drawString(70, y, f\"Kieu bo tri: {config.get('type')}\")"
new_type = "config_type = config.get('type', '')\n    if config_type == 'Gốc': config_type = 'Goc'\n    c.drawString(70, y, f\"Kieu bo tri: {config_type}\")"
content = content.replace(old_type, new_type)

with open(export_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patching completed.")
