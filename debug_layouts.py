from io_handlers.file_io import parse_input_file
from core.generator import generate_coords
from core.blackbox import MCOCBlackbox
import numpy as np

params, loads, _ = parse_input_file('T1_EXT_result.txt')
params['SAFE_D'] = params['D_PILE']
params['P_TENSION'] = 200.0
params['M_LIMIT'] = 0.0
params['mock_mode'] = True
params['exe_path'] = ''

d = params['D_PILE']  # 1.2
L_X = params['L_X']  # 6.0
L_Y = params['L_Y']  # 9.6
SAFE_D = d
P_LIMIT = params['P_LIMIT']  # 500.0

print("d=%.1f  L_X=%.1f  L_Y=%.1f  P_LIMIT=%.1f" % (d, L_X, L_Y, P_LIMIT))
print("3d=%.2f  6d=%.2f" % (3*d, 6*d))
print("Max sx (nx=2): %.2f" % ((L_X - 2*SAFE_D)/(2-1)))
print("Max sy (ny=3): %.2f" % ((L_Y - 2*SAFE_D)/(3-1)))
print()

print("Testing candidate layouts:")
for nx in range(2, 8):
    for ny in range(2, 8):
        if nx == 1:
            sx_max = 0
        else:
            sx_max = min(6.0*d, (L_X - 2*SAFE_D)/(nx-1))
        if ny == 1:
            sy_max = 0
        else:
            sy_max = min(6.0*d, (L_Y - 2*SAFE_D)/(ny-1))
        
        if nx > 1 and sx_max < 3.0*d:
            continue
        if ny > 1 and sy_max < 3.0*d:
            continue
        
        coords = generate_coords(nx, ny, sx_max, sy_max, 'A')
        res, msg = MCOCBlackbox.evaluate_layout(coords, loads, params)
        if res:
            status = "PASS" if res['pmax'] <= P_LIMIT else "FAIL"
            print("  nx=%d ny=%d n=%d  sx=%.2f sy=%.2f  Pmax=%.1f [%s]" % (
                nx, ny, len(coords), sx_max, sy_max, res['pmax'], status))
