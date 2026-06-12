"""
mcoc_writer.py - Sinh file input MCOC cho phuong an coc moi (template-based).

Nguyen ly: KHONG tu dung lai format MCOC (de sai), ma dung CHINH file input
goc cua nguoi dung lam khuon:
    - Header (ten cong trinh, dong 'Nc Np ... Ax By H', he so nen,
      to hop tai trong): giu nguyen, chi cap nhat so coc Nc.
    - Khoi du lieu tung coc: nhan ban khoi cua coc #1, thay toa do X, Y.
    - Footer (neu co): giu nguyen.

Ho tro 2 dang ghi toa do trong file input MCOC:
    (a) 'X Y' hoac 'X Y a b c'   - X, Y tren CUNG 1 dong
    (b) X va Y tren 2 DONG RIENG (moi thong so 1 dong - dang pho bien,
        khoi 16 dong: Lo H Bpx Bpy a b cday Fo Jo Po Co Ct X Y ...)

Vi tri khoi va do dai khoi (stride) duoc TU DONG do tu file goc va xac thuc
tren TAT CA cac coc; giu nguyen ket thuc dong (CRLF/LF) cua file goc.
"""

import os
import re
import numpy as np

_NUM = re.compile(r'^-?\d+\.?\d*(?:[eE][+-]?\d+)?$')


class MCOCWriterError(Exception):
    pass


def _single_float(line):
    """Tra ve float neu dong chi co dung 1 so, nguoc lai None."""
    parts = line.split()
    if len(parts) == 1 and _NUM.match(parts[0]):
        try:
            return float(parts[0])
        except ValueError:
            return None
    return None


def _is_inline_coord(line, x, y, tol=1e-3):
    """Dong 'X Y' hoac 'X Y a b c' khop (x, y)."""
    parts = line.split()
    if len(parts) not in (2, 5):
        return False
    if not all(_NUM.match(p) for p in parts):
        return False
    try:
        return abs(float(parts[0]) - x) < tol and abs(float(parts[1]) - y) < tol
    except ValueError:
        return False


def _is_split_coord(lines, i, x, y, tol=1e-3):
    """Dong i = X, dong i+1 = Y (moi dong 1 so)."""
    if i + 1 >= len(lines):
        return False
    vx = _single_float(lines[i])
    vy = _single_float(lines[i + 1])
    return vx is not None and vy is not None \
        and abs(vx - x) < tol and abs(vy - y) < tol


def _replace_inline_coord(line, x, y):
    """Thay 2 so dau cua dong toa do, GIU NGUYEN cac cot phu phia sau."""
    parts = line.split()
    rest = parts[2:]
    return "   ".join(["%.3f" % x, "%.3f" % y] + rest)


def _fmt(v):
    """Format so thuc gon (1.800 -> 1.8, 0.000 -> 0.0)."""
    s = ("%.3f" % v).rstrip('0')
    if s.endswith('.'):
        s += '0'
    return s


class MCOCTemplate:
    """Phan tich file input MCOC goc thanh header / khoi coc / footer."""

    def __init__(self, template_path, original_coords):
        if not os.path.exists(template_path):
            raise MCOCWriterError("Khong thay file input goc: " + template_path)
        with open(template_path, 'rb') as f:
            raw = f.read()
        self.eol = "\r\n" if b"\r\n" in raw else "\n"
        text = raw.decode('utf-8', errors='replace')
        self.lines = text.splitlines()
        self.path = template_path

        coords = [tuple(map(float, c)) for c in np.asarray(original_coords, dtype=float)]
        if not coords:
            raise MCOCWriterError("original_coords rong - khong dung template duoc.")
        self.n_orig = len(coords)

        self._detect_layout(coords)

        self.header = self.lines[:self.block_start]
        b0 = self.block_start
        self.block_tpl = self.lines[b0: b0 + self.block_len]
        self.footer = self.lines[b0 + self.n_orig * self.block_len:]

    # ------------------------------------------------------------------ #
    def _detect_layout(self, coords):
        """Tim kieu toa do (inline/split), vi tri khoi dau tien va stride."""
        lines = self.lines
        n = self.n_orig
        x0, y0 = coords[0]

        # ---- Kieu (a): 'X Y' tren 1 dong --------------------------------
        cands_inline = [i for i in range(len(lines))
                        if _is_inline_coord(lines[i], x0, y0)]
        for c in cands_inline:
            if n == 1:
                self._set_layout('inline', c, 17, coords)
                return
            for L in range(4, 80):
                if all(c + k * L < len(lines) and
                       _is_inline_coord(lines[c + k * L], coords[k][0], coords[k][1])
                       for k in range(1, n)):
                    self._set_layout('inline', c, L, coords)
                    return

        # ---- Kieu (b): X, Y tren 2 dong rieng ---------------------------
        cands_split = [i for i in range(len(lines))
                       if _is_split_coord(lines, i, x0, y0)]
        for c in cands_split:
            if n == 1:
                self._set_layout('split', c, 16, coords)
                return
            for L in range(4, 80):
                if all(c + k * L + 1 < len(lines) and
                       _is_split_coord(lines, c + k * L, coords[k][0], coords[k][1])
                       for k in range(1, n)):
                    self._set_layout('split', c, L, coords)
                    return

        raise MCOCWriterError(
            "Khong tim thay toa do coc (%.3f, %.3f) trong file template. "
            "Kiem tra file co dung la file INPUT MCOC khong (khong phai _result)."
            % (x0, y0))

    def _set_layout(self, kind, c0, L, coords):
        """Xac dinh offset dong toa do trong khoi bang cach lui tu dong toa do."""
        self.coord_kind = kind
        self.block_len = L

        if self.n_orig >= 2:
            # Lui dan tu dong toa do coc 1 va coc 2 cho den khi noi dung khac
            off = 0
            while off + 1 <= c0:
                a = self.lines[c0 - off - 1]
                b = self.lines[c0 + L - off - 1]
                if a != b:
                    break
                off += 1
            # Gioi han: offset khong vuot qua do dai khoi - 1
            off = min(off, L - 1)
        else:
            off = 12 if kind == 'split' else 12
        self.coord_offset = off
        self.block_start = c0 - off

    # ------------------------------------------------------------------ #
    def _patch_header(self, n_new):
        """Cap nhat so coc Nc (so dau tien tren dong 2: 'Nc Np ... Ax By H')."""
        header = list(self.header)
        if len(header) >= 2:
            parts = header[1].split()
            if parts and _NUM.match(parts[0]):
                parts[0] = str(n_new)
                header[1] = ' '.join(parts)
        return header

    def render(self, coords, name_suffix=""):
        """Sinh noi dung file input cho bo toa do moi."""
        coords = np.asarray(coords, dtype=float)
        out = self._patch_header(len(coords))
        if name_suffix and out:
            out[0] = out[0].rstrip() + " " + name_suffix
        for (x, y) in coords:
            block = list(self.block_tpl)
            if self.coord_kind == 'inline':
                block[self.coord_offset] = _replace_inline_coord(
                    block[self.coord_offset], x, y)
            else:  # split: X va Y tren 2 dong rieng
                block[self.coord_offset] = _fmt(x)
                block[self.coord_offset + 1] = _fmt(y)
            out.extend(block)
        out.extend(self.footer)
        return self.eol.join(out) + self.eol

    def write(self, coords, out_path, name_suffix=""):
        content = self.render(coords, name_suffix)
        with open(out_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        return out_path


def self_check(template_path, original_coords):
    """
    Kiem tra nhanh: sinh lai file voi CHINH toa do goc va doc nguoc bang
    parse_input_file - toa do phai khop. Tra ve (ok, message).
    """
    import tempfile
    from io_handlers.file_io import parse_input_file

    try:
        tpl = MCOCTemplate(template_path, original_coords)
        tmp = os.path.join(tempfile.gettempdir(), "_mcoc_selfcheck.txt")
        tpl.write(original_coords, tmp)
        params, loads, _ = parse_input_file(tmp)
        got = np.asarray(params.get('original_coords', []), dtype=float)
        want = np.asarray(original_coords, dtype=float)
        if got.shape != want.shape or not np.allclose(got, want, atol=1e-3):
            return False, ("Doc nguoc file sinh ra cho toa do khac toa do goc "
                           "(%s vs %s)." % (got.shape, want.shape))
        return True, "Template OK (%d coc, khoi %d dong, kieu %s)." % (
            tpl.n_orig, tpl.block_len, tpl.coord_kind)
    except Exception as e:
        return False, str(e)
