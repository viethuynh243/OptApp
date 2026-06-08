import sys
from io_handlers.file_io import parse_input_file
from core.optimizer import run_optimization

params, loads, name = parse_input_file('T1_EXT_result.txt')
params['D_PILE'] = 1.2
params['SAFE_D'] = 1.2
params['P_LIMIT'] = 600.0
params['P_TENSION'] = 200.0
params['M_LIMIT'] = 0.0
params['mock_mode'] = True
params['result_filepath'] = 'T1_EXT_result.txt'

res = run_optimization(params, loads)
orig = res.get('original_config')
print('Original:', orig['ok'] if orig else None)

all_configs = res.get('all_valid_configs', [])
print('All valid:', len(all_configs))
for c in all_configs:
    print(f"Type {c['type']} nx={c['nx']} ny={c['ny']} n={c['n']} Pmax={c['pmax']:.1f}")
