"""
test_mcoc_runner.py - Kiem thu ranh gioi tien trinh con MCOC trong MCOCRunner.run().

Bao gom:
    1. Duong thanh cong: tro runner vao tests/mcoc_stub.py, chay 1 file input hop le,
       kiem tra run() tra ve dict co 'pmax'.
    2. Exit code != 0: stub gia in ra stderr roi sys.exit(1) ma KHONG ghi file ket qua,
       kiem tra run() raise MCOCError chua ma loi.
    3. Khong sinh file ket qua: stub exit 0 nhung khong ghi gi,
       kiem tra run() raise MCOCError noi ve khong co file ket qua.

Chay:  python -m pytest -q tests/test_mcoc_runner.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pytest

from core.mcoc_runner import MCOCRunner, MCOCError

STUB = os.path.join(ROOT, "tests", "mcoc_stub.py")


# ============================================================================
# Dựng file input MCOC hợp lệ (rút gọn từ tests/test_refine.py::build_demo_input)
# ============================================================================
def write_demo_input(path):
    """Ghi 1 file input MCOC tổng hợp (8 cọc, 2 tổ hợp tải) để stub đọc được."""
    coords = [(-1.8, -5.4), (1.8, -5.4),
              (-1.8, -1.8), (1.8, -1.8),
              (-1.8,  1.8), (1.8,  1.8),
              (-1.8,  5.4), (1.8,  5.4)]
    lines = []
    lines.append("DEMO TOI UU COC")
    lines.append("8 2 0 0 0 0 0 0 7.2 13.2 1.8")
    lines.append("")
    lines.append("83.0 105.0 2025.0 -1499.0 951.0 0.0")
    lines.append("20.0 0.0 2577.0 -94.0 170.0 0.0")
    for i, (x, y) in enumerate(coords, 1):
        lines.append("0.0")
        lines.append(str(i))
        lines.append("3001028 3001028 3001028 3001028 100 0 400")
        lines.append("20.0")
        lines.append("1.2")
        lines.append("1.2")
        lines.append("0.0")
        lines.append("1.131")
        lines.append("0.1018")
        lines.append("500")
        lines.append("33333.3")
        lines.append("16666.7")
        lines.append("%.3f   %.3f" % (x, y))
        lines.append("0")
        lines.append("0")
        lines.append("0")
    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
    return coords


# ============================================================================
# 1. Đường thành công
# ============================================================================
def test_run_success_returns_pmax(tmp_path):
    """Stub chạy đúng (exit 0 + sinh file) -> run() trả về dict có 'pmax'."""
    in_path = str(tmp_path / "DEMO.txt")
    write_demo_input(in_path)

    runner = MCOCRunner(STUB)
    res = runner.run(in_path)

    assert isinstance(res, dict)
    assert 'pmax' in res
    assert os.path.exists(res['result_path'])


# ============================================================================
# 2. Exit code != 0 -> MCOCError (không đọc file cũ/dở)
# ============================================================================
def test_run_nonzero_exit_raises(tmp_path):
    """Stub thoát với mã != 0 và KHÔNG ghi file -> run() raise MCOCError có mã lỗi."""
    in_path = str(tmp_path / "DEMO.txt")
    write_demo_input(in_path)

    # Stub giả: in ra stderr rồi sys.exit(1), không ghi *_result.txt
    fail_stub = str(tmp_path / "fail_stub.py")
    with open(fail_stub, 'w', encoding='utf-8') as f:
        f.write("import sys\n")
        f.write("sys.stderr.write('MCOC gia lap that bai\\n')\n")
        f.write("sys.exit(1)\n")

    runner = MCOCRunner(fail_stub)
    with pytest.raises(MCOCError) as exc:
        runner.run(in_path)
    # Thông điệp phải nhắc tới mã lỗi (1)
    assert "1" in str(exc.value)
    assert "ma loi" in str(exc.value)


# ============================================================================
# 3. Exit 0 nhưng không sinh file kết quả -> MCOCError
# ============================================================================
def test_run_no_result_file_raises(tmp_path):
    """Stub thoát 0 nhưng không ghi file -> run() raise MCOCError về thiếu file kết quả."""
    in_path = str(tmp_path / "DEMO.txt")
    write_demo_input(in_path)

    # Stub giả: in ra stdout rồi thoát bình thường, không ghi *_result.txt
    noop_stub = str(tmp_path / "noop_stub.py")
    with open(noop_stub, 'w', encoding='utf-8') as f:
        f.write("import sys\n")
        f.write("sys.stdout.write('Khong lam gi\\n')\n")
        f.write("sys.exit(0)\n")

    runner = MCOCRunner(noop_stub)
    with pytest.raises(MCOCError) as exc:
        runner.run(in_path)
    assert "khong sinh file ket qua" in str(exc.value)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
