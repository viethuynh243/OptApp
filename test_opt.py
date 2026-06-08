from io_handlers.file_io import parse_input_file
from core.optimizer import run_optimization

# Test T3: Lx=8, Ly=9.6 - 8 coc
params, loads, name = parse_input_file('T3_EXT_result.txt')
params['SAFE_D'] = params['D_PILE']
params['P_TENSION'] = 200.0
params['M_LIMIT'] = 0.0
params['mock_mode'] = True
params['exe_path'] = ''
params['result_filepath'] = 'T3_EXT_result.txt'

print("=== T3 (Lx=8 Ly=9.6) ===")
print("Lx=%s Ly=%s d=%s P_LIMIT=%s" % (params['L_X'], params['L_Y'], params['D_PILE'], params['P_LIMIT']))
print("Loads count:", len(loads))
print("orig_pmax:", params.get('orig_pmax'))
print("orig_coords:", params.get('original_coords'))
print()

res = run_optimization(params, loads)
orig = res.get('original_config')
if orig:
    print("Original pmax: %.2f  OK: %s" % (orig.get('pmax', 0), orig.get('ok')))
rec = res.get('recommended')
if rec:
    print("RECOMMENDED: Type=%s nx=%d ny=%d n=%d  pmax=%.1f pmin=%.1f" % (
        rec['type'], rec['nx'], rec['ny'], rec['n'], rec['pmax'], rec['pmin']))
else:
    print("No recommended config found")
    
print()
print("All valid configs (%d):" % len(res.get('all_valid_configs', [])))
for cfg in res.get('all_valid_configs', [])[:8]:
    print("  n=%d type=%s nx=%d ny=%d  pmax=%.1f" % (
        cfg['n'], cfg['type'], cfg['nx'], cfg['ny'], cfg['pmax']))

# Also test T1 for reference
print()
print("=== T1 (Lx=6 Ly=9.6) ===")
p1, l1, _ = parse_input_file('T1_EXT_result.txt')
p1['SAFE_D'] = p1['D_PILE']
p1['P_TENSION'] = 200.0
p1['M_LIMIT'] = 0.0
p1['mock_mode'] = True
p1['exe_path'] = ''
print("orig_pmax:", p1.get('orig_pmax'))
res1 = run_optimization(p1, l1)
orig1 = res1.get('original_config')
if orig1:
    print("Original pmax: %.2f  OK: %s" % (orig1.get('pmax', 0), orig1.get('ok')))
print("All valid:", len(res1.get('all_valid_configs', [])))
rec1 = res1.get('recommended')
if rec1:
    print("RECOMMENDED:", rec1['type'], rec1['n'], "coc")
else:
    print("=> T1 khong co phuong an nao dat voi P_LIMIT=500T (dung theo thuc te)")
