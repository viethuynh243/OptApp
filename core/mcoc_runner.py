"""
mcoc_runner.py - Goi chuong trinh MCOC Batch (Command Line) nhu mot API Hop Den.

Quy trinh 1 lan goi:
    1. Ghi file input phuong an (do mcoc_writer sinh ra).
    2. Chay: MCOC_Batch.exe <file_input> --out-dir <thu_muc> (CLI dang argparse).
    3. Cho MCOC ket thuc, tim file *_result.txt vua sinh.
    4. Parse Nmax/Nmin/Mxmax/Mymax bang parse_mcoc_result_file().

Ho tro exe_path la duong dan .exe, .bat, .py hoac shortcut .lnk
(tu dong resolve .lnk bang PowerShell tren Windows).
"""

import os
import sys
import time
import subprocess

from io_handlers.file_io import parse_mcoc_result_file


class MCOCError(Exception):
    pass


def resolve_shortcut(path):
    """Resolve file .lnk ve target that (Windows). Tra ve (target, arguments)."""
    if not path.lower().endswith('.lnk'):
        return path, ''
    if os.name != 'nt':
        raise MCOCError("Khong the resolve .lnk ngoai Windows: " + path)
    ps = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut(%s);"
        "Write-Output $s.TargetPath; Write-Output $s.Arguments"
        % ("'" + path.replace("'", "''") + "'")
    )
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True, text=True, timeout=30
    )
    lines = [l.strip() for l in out.stdout.splitlines() if l.strip()]
    if not lines or not os.path.exists(lines[0]):
        raise MCOCError("Khong resolve duoc shortcut: " + path)
    target = lines[0]
    args = lines[1] if len(lines) > 1 else ''
    return target, args


class MCOCRunner:
    """Goi MCOC Batch nhu API: input file -> ket qua noi luc."""

    def __init__(self, exe_path, timeout=180, log=None):
        """
        exe_path : duong dan toi MCOC Batch (.exe/.bat/.py/.lnk)
        timeout  : thoi gian cho toi da moi lan chay (giay)
        log      : callable(str) de ghi log (mac dinh print)
        """
        self.raw_path = exe_path
        self.timeout = timeout
        self.log = log or (lambda m: print("[MCOC]", m))
        self.exe, self.exe_args = resolve_shortcut(exe_path)
        self.n_calls = 0

    def _build_cmd(self):
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
        """
        Chay MCOC voi 1 file input. Tra ve dict ket qua:
            {'pmax','pmin','mxmax','mymax'} va duong dan file result.
        Raise MCOCError neu chay loi / khong tim thay ket qua.
        """
        input_filepath = os.path.abspath(input_filepath)
        if not os.path.exists(input_filepath):
            raise MCOCError("File input khong ton tai: " + input_filepath)

        workdir = os.path.dirname(input_filepath)
        base = os.path.splitext(os.path.basename(input_filepath))[0]
        result_path = os.path.join(workdir, base + "_result.txt")

        # Xoa ket qua cu de phat hien ket qua moi chinh xac
        if os.path.exists(result_path):
            try:
                os.remove(result_path)
            except OSError:
                pass

        t0 = time.time()
        # MCOC_Batch.exe [-h] [--out-dir OUT_DIR] [--pdf] [--excel] ... paths [paths ...]
        # -> truyen file input qua THAM SO dong lenh, ep ket qua ve cung thu muc.
        cmd = self._build_cmd() + [input_filepath, "--out-dir", workdir]
        self.n_calls += 1
        self.log("Goi MCOC lan %d: %s" % (self.n_calls, os.path.basename(input_filepath)))

        try:
            proc = subprocess.run(
                cmd,
                input="",
                capture_output=True,
                text=True,
                cwd=workdir,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            raise MCOCError("MCOC chay qua %ds, da dung." % self.timeout)
        except OSError as e:
            raise MCOCError("Khong chay duoc MCOC (%s): %s" % (self.exe, e))

        # Tim file ket qua: uu tien <base>_result.txt, neu khong co thi tim
        # file *_result.txt moi nhat sinh ra sau t0 trong workdir.
        if not os.path.exists(result_path):
            cands = []
            for fn in os.listdir(workdir):
                if fn.lower().endswith("_result.txt"):
                    fp = os.path.join(workdir, fn)
                    if os.path.getmtime(fp) >= t0 - 1:
                        cands.append(fp)
            if cands:
                result_path = max(cands, key=os.path.getmtime)
            else:
                tail = (proc.stdout or "")[-400:] + (proc.stderr or "")[-400:]
                raise MCOCError(
                    "MCOC khong sinh file ket qua cho %s.\nOutput cuoi:\n%s"
                    % (base, tail)
                )

        res = parse_mcoc_result_file(result_path)
        if not res:
            raise MCOCError("Khong doc duoc bang tong ket noi luc tu " + result_path)

        res['result_path'] = result_path
        self.log("  -> Nmax=%.2f T, Nmin=%.2f T (%.1fs)"
                 % (res['pmax'], res['pmin'], time.time() - t0))
        return res
