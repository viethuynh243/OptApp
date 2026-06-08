import re

filepath = 'ui/main_window.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to remove the Blackbox Config UI frame
pattern = re.compile(r'\s*# Blackbox Config\s*frame_bb = tk\.LabelFrame\(tab_params, text="Liên kết Phần mềm Tính Lực \(MCOC\)".*?ttk\.Checkbutton\(frame_bb, text="Bật chế độ Giả Lập \(Mock Mode\)", variable=self\.params\[\'mock_mode\'\]\)\.grid\(row=1, column=0, columnspan=2, sticky="w", pady=2\)', re.DOTALL)

new_content = pattern.sub('', content)

if content == new_content:
    print("Warning: regex didn't match anything!")
else:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Removed MCOC frame successfully.")
