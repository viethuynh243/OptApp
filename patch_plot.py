import re

filepath = 'ui/main_window.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace redundant draw_simulation
old_draw_logic_1 = """            if self.loads:
                self.populate_comboboxes(results)
            self.plot_canvas.draw_simulation(rec['coords'], self.get_params_dict())"""
new_draw_logic_1 = """            self.populate_comboboxes(results)"""

old_draw_logic_2 = """            if self.loads:
                self.populate_comboboxes(results)
            if orig:
                self.plot_canvas.draw_simulation(orig['coords'], self.get_params_dict())
            else:
                self.plot_canvas.draw_simulation([], self.get_params_dict())"""
new_draw_logic_2 = """            self.populate_comboboxes(results)
            if not orig:
                self.plot_canvas.draw_simulation([], self.get_params_dict())"""

content = content.replace(old_draw_logic_1, new_draw_logic_1)
content = content.replace(old_draw_logic_2, new_draw_logic_2)

# Also fix the `if self.loads:` check inside populate_comboboxes if there is any issue.
# Wait, populate_comboboxes just does: cases = [f"Tổ hợp {i+1}" for i in range(len(self.loads))]
# It's perfectly safe to call unconditionally.

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Plot bug patched.")
