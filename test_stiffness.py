from io_handlers.file_io import parse_input_file
from core.stiffness import solve_pile_forces

params, loads, name = parse_input_file('Mcoc_test/T1_EXT.txt')

coords = params['original_coords']

results = solve_pile_forces(coords, loads, params)

for i, r in enumerate(results):
    if loads[i]['N'] == 0: continue
    print(f"Load Case {i+1}: P={loads[i]['N']}, Mx={loads[i]['Mx']}, My={loads[i]['My']}")
    for j, pile_N in enumerate(r['N_piles']):
        print(f"  Pile {j+1}: x={coords[j][0]}, y={coords[j][1]} -> N = {pile_N:.2f}")
