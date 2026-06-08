from io_handlers.file_io import parse_input_file
import sys

try:
    params, loads, name = parse_input_file('Mcoc_test/T1_EXT.txt')
    print("Project:", name)
    print("Params:")
    for k, v in params.items():
        if k != 'original_coords':
            print(f"  {k}: {v}")
    print("Loads:")
    for load in loads:
        print(f"  {load}")
except Exception as e:
    print("Error:", e)
