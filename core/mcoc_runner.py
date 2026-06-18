"""
mcoc_runner.py - Gọi chương trình MCOC Batch (Command Line) như một API HỘP ĐEN.

Quy trình 1 lần gọi:
    1. Ghi file input phương án (do mcoc_writer sinh ra).
    2. Chạy: MCOC_Batch.exe <file_input> --out-dir <thư_mục> (CLI dạng argparse).
    3. Chờ MCOC kết thúc, tìm file *_result.txt vừa sinh.
    4. Parse Nmax/Nmin/Mxmax/Mymax bằng parse_mcoc_result_file().

Hỗ trợ exe_path là đường dẫn .exe, .bat, .py hoặc shortcut .lnk
(tự động resolve .lnk bằng PowerShell trên Windows).
"""

import os
import sys
import time
import subprocess

from io_handlers.file_io import parse_mcoc_result_file


# ============================================================================
# Lỗi và tiện ích phân giải đường dẫn
# ============================================================================
class MCOCError(Exception):
    """Lỗi khi gọi/đọc kết quả MCOC Batch."""
    pass


def _no_window_kwargs():
    """Trả về kwargs cho subprocess để KHÔNG bật cửa sổ cmd/console (Windows).

    Khi app đóng gói dạng GUI (PyInstaller --windowed) gọi tiến trình con là
    .bat/.exe/.py thì Windows mặc định bật một cửa sổ console. Dùng đồng thời:
        - CREATE_NO_WINDOW : không cấp console mới cho tiến trình con.
        - STARTUPINFO + SW_HIDE : ẩn cửa sổ nếu tiến trình vẫn cố hiện.
    Ngoài Windows trả về dict rỗng (không ảnh hưởng).
    """
    if os.name != 'nt':
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startupinfo,
    }


def resolve_shortcut(path):
    """Resolve file .lnk về target thật (Windows). Trả về (target, arguments).

    Nếu path không phải .lnk thì trả về nguyên path và arguments rỗng.
    Trên Windows dùng WScript.Shell qua PowerShell để đọc TargetPath/Arguments
    của shortcut; ngoài Windows hoặc resolve thất bại thì raise MCOCError.
    """
    if not path.lower().endswith('.lnk'):
        return path, ''
    if os.name != 'nt':
        raise MCOCError("Khong the resolve .lnk ngoai Windows: " + path)
    # Script PowerShell: in ra TargetPath (dòng 1) và Arguments (dòng 2) của shortcut
    ps = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut(%s);"
        "Write-Output $s.TargetPath; Write-Output $s.Arguments"
        % ("'" + path.replace("'", "''") + "'")
    )
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True, text=True, timeout=30,
        **_no_window_kwargs()
    )
    # Lọc các dòng không rỗng: dòng đầu là target, dòng sau (nếu có) là arguments
    lines = [l.strip() for l in out.stdout.splitlines() if l.strip()]
    if not lines or not os.path.exists(lines[0]):
        raise MCOCError("Khong resolve duoc shortcut: " + path)
    target = lines[0]
    args = lines[1] if len(lines) > 1 else ''
    return target, args


# ============================================================================
# Runner: gọi MCOC Batch như API hộp đen
# ============================================================================
class MCOCRunner:
    """Gọi MCOC Batch như API: input file -> kết quả nội lực."""

    def __init__(self, exe_path, timeout=180, log=None):
        """Khởi tạo runner và phân giải đường dẫn chương trình.

        Đầu vào:
            exe_path : đường dẫn tới MCOC Batch (.exe/.bat/.py/.lnk).
            timeout  : thời gian chờ tối đa mỗi lần chạy (giây).
            log      : callable(str) để ghi log (mặc định print).
        """
        self.raw_path = exe_path
        self.timeout = timeout
        self.log = log or (lambda m: print("[MCOC]", m))
        # Nếu là shortcut .lnk thì lấy target thật + arguments kèm theo
        self.exe, self.exe_args = resolve_shortcut(exe_path)
        self.n_calls = 0

    def _build_cmd(self):
        """Dựng danh sách lệnh chạy theo loại file thực thi.

        - .py        -> chạy bằng trình Python hiện tại.
        - .bat/.cmd  -> chạy qua 'cmd /c'.
        - còn lại    -> gọi trực tiếp (vd .exe).
        Kèm thêm arguments của shortcut (nếu có).
        """
        ext = os.path.splitext(self.exe)[1].lower()
        cmd = []
        if ext == '.py':
            cmd = [sys.executable, self.exe]
        elif ext in ('.bat', '.cmd'):
            cmd = ['cmd', '/c', self.exe]
        else:
            cmd = [self.exe]
        if self.exe_args:
            cmd += self.exe_args.split()
        return cmd

    def run(self, input_filepath):
        """Chạy MCOC với 1 file input.

        Trả về dict kết quả:
            {'pmax','pmin','mxmax','mymax'} và đường dẫn file result.
        Raise MCOCError nếu chạy lỗi / không tìm thấy kết quả.
        """
        input_filepath = os.path.abspath(input_filepath)
        if not os.path.exists(input_filepath):
            raise MCOCError("File input khong ton tai: " + input_filepath)

        # Kết quả mặc định nằm cùng thư mục input, tên <base>_result.txt
        workdir = os.path.dirname(input_filepath)
        base = os.path.splitext(os.path.basename(input_filepath))[0]
        result_path = os.path.join(workdir, base + "_result.txt")

        # Xóa kết quả cũ để phát hiện kết quả mới chính xác
        if os.path.exists(result_path):
            try:
                os.remove(result_path)
            except OSError:
                pass

        t0 = time.time()
        # MCOC_Batch.exe [-h] [--out-dir OUT_DIR] [--pdf] [--excel] ... paths [paths ...]
        # -> truyền file input qua THAM SỐ dòng lệnh, ép kết quả về cùng thư mục.
        cmd = self._build_cmd() + [input_filepath, "--out-dir", workdir]
        self.n_calls += 1
        self.log("Goi MCOC lan %d: %s" % (self.n_calls, os.path.basename(input_filepath)))

        # Chạy tiến trình con, bắt stdout/stderr, giới hạn thời gian bằng timeout
        try:
            proc = subprocess.run(
                cmd,
                input="",
                capture_output=True,
                text=True,
                cwd=workdir,
                timeout=self.timeout,
                **_no_window_kwargs()
            )
        except subprocess.TimeoutExpired:
            raise MCOCError("MCOC chay qua %ds, da dung." % self.timeout)
        except OSError as e:
            raise MCOCError("Khong chay duoc MCOC (%s): %s" % (self.exe, e))

        # Tìm file kết quả: ưu tiên <base>_result.txt, nếu không có thì tìm
        # file *_result.txt mới nhất sinh ra sau t0 trong workdir.
        if not os.path.exists(result_path):
            cands = []
            for fn in os.listdir(workdir):
                if fn.lower().endswith("_result.txt"):
                    fp = os.path.join(workdir, fn)
                    # Chỉ nhận file mới sinh sau khi bắt đầu chạy (trừ 1s sai số)
                    if os.path.getmtime(fp) >= t0 - 1:
                        cands.append(fp)
            if cands:
                # Nhiều ứng viên -> lấy file mới nhất theo thời gian sửa đổi
                result_path = max(cands, key=os.path.getmtime)
            else:
                # Không có kết quả -> đính kèm phần cuối stdout/stderr để chẩn đoán
                tail = (proc.stdout or "")[-400:] + (proc.stderr or "")[-400:]
                raise MCOCError(
                    "MCOC khong sinh file ket qua cho %s.\nOutput cuoi:\n%s"
                    % (base, tail)
                )

        # Đọc bảng tổng kết nội lực từ file result
        res = parse_mcoc_result_file(result_path)
        if not res:
            raise MCOCError("Khong doc duoc bang tong ket noi luc tu " + result_path)

        res['result_path'] = result_path
        self.log("  -> Nmax=%.2f T, Nmin=%.2f T (%.1fs)"
                 % (res['pmax'], res['pmin'], time.time() - t0))
        return res
