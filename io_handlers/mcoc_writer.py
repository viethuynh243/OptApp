"""
mcoc_writer.py - Sinh file input MCOC cho phương án cọc mới (dựa trên template).

Dùng CHÍNH file input gốc làm khuôn: giữ nguyên header/footer, thay số cọc Nc,
khối tọa độ từng cọc; và (tùy chọn) GHI ĐÈ khối tổ hợp tải trọng bằng tải lấy
từ UI (UI là nguồn duy nhất) + cập nhật Np.

Template được phân tích thành 3 phần: header (đầu file, có thể chứa khối tải) /
khối cọc (lặp lại cho từng cọc) / footer (cuối file). Tọa độ cọc trong file có
thể nằm CÙNG DÒNG (inline: "x y ...") hoặc TÁCH DÒNG (split: x ở một dòng, y ở
dòng kế). Đơn vị giữ nguyên theo file gốc; chỉ thay con số, không đổi định dạng.
"""

import os
import re
import numpy as np

# Mẫu nhận diện một token số (kể cả dạng mũ 1.2e-3)
_NUM = re.compile(r'^-?\d+\.?\d*(?:[eE][+-]?\d+)?$')


class MCOCWriterError(Exception):
    """Lỗi khi phân tích template hoặc sinh file input MCOC."""
    pass


# ============================================================================
# Tiện ích nhận diện / định dạng số
# ============================================================================
def _single_float(line):
    """
    Trả về số float nếu dòng chỉ chứa ĐÚNG MỘT token số, ngược lại None.

    Dùng để nhận diện tọa độ kiểu tách dòng (x và y ở 2 dòng riêng).
    """
    parts = line.split()
    if len(parts) == 1 and _NUM.match(parts[0]):
        try:
            return float(parts[0])
        except ValueError:
            return None
    return None


def _is_inline_coord(line, x, y, tol=1e-3):
    """
    Kiểm tra dòng có phải tọa độ inline khớp (x, y) trong sai số tol.

    Dòng hợp lệ gồm 2 hoặc 5 token số; so 2 token đầu với (x, y).
    Trả về True/False.
    """
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
    """
    Kiểm tra tọa độ kiểu tách dòng: lines[i]=x và lines[i+1]=y khớp (x, y).

    Tham số:
        lines : toàn bộ dòng của file; i : chỉ số dòng nghi là x.
    Trả về True nếu cả hai dòng là số đơn và khớp trong sai số tol.
    """
    if i + 1 >= len(lines):
        return False
    vx = _single_float(lines[i])
    vy = _single_float(lines[i + 1])
    return vx is not None and vy is not None \
        and abs(vx - x) < tol and abs(vy - y) < tol


def _replace_inline_coord(line, x, y):
    """
    Thay 2 token đầu (x, y) của dòng inline, GIỮ NGUYÊN phần token còn lại.

    Trả về chuỗi dòng mới với x, y định dạng "%.3f", ngăn cách bằng 3 dấu cách.
    """
    parts = line.split()
    rest = parts[2:]
    return "   ".join(["%.3f" % x, "%.3f" % y] + rest)


def _fmt(v):
    """
    Định dạng số về dạng gọn: bỏ số 0 thừa ở đuôi nhưng giữ tối thiểu 1 chữ số
    thập phân (vd 2.500 -> '2.5', 3.000 -> '3.0'). Trả về chuỗi.
    """
    s = ("%.3f" % v).rstrip('0')
    if s.endswith('.'):
        s += '0'
    return s


# ============================================================================
# Template MCOC: phân tích và kết xuất
# ============================================================================
class MCOCTemplate:
    """Phân tích file input MCOC gốc thành header / khối cọc / footer."""

    def __init__(self, template_path, original_coords):
        """
        Đọc và phân tích file template theo bố cục cọc gốc.

        Tham số:
            template_path  : đường dẫn file input MCOC gốc.
            original_coords: tọa độ cọc gốc (dùng để dò vị trí khối cọc).
        Phát hiện: kiểu xuống dòng (eol), khối cọc (block), header, footer và
        khối tải trọng. Ném MCOCWriterError nếu thiếu file hoặc tọa độ rỗng.
        """
        if not os.path.exists(template_path):
            raise MCOCWriterError("Khong thay file input goc: " + template_path)
        with open(template_path, 'rb') as f:
            raw = f.read()
        # Giữ đúng kiểu xuống dòng của file gốc khi ghi lại
        self.eol = "\r\n" if b"\r\n" in raw else "\n"
        self.lines = raw.decode('utf-8', errors='replace').splitlines()
        self.path = template_path

        coords = [tuple(map(float, c)) for c in np.asarray(original_coords, dtype=float)]
        if not coords:
            raise MCOCWriterError("original_coords rong - khong dung template duoc.")
        self.n_orig = len(coords)

        # Dò bố cục khối cọc rồi tách header / khối mẫu / footer
        self._detect_layout(coords)
        self.header = self.lines[:self.block_start]
        b0 = self.block_start
        self.block_tpl = self.lines[b0: b0 + self.block_len]
        self.footer = self.lines[b0 + self.n_orig * self.block_len:]
        self._detect_load_block()

    def _detect_load_block(self):
        """
        Tìm khối tổ hợp tải (các dòng liên tiếp có đúng 6 số) trong header.

        Ghi nhận vị trí (load_start) và số dòng (load_len); để None/0 nếu
        không tìm thấy. Phục vụ việc ghi đè tải bằng dữ liệu từ UI.
        """
        self.load_start = None
        self.load_len = 0
        start = None
        cnt = 0
        for i, ln in enumerate(self.header):
            toks = ln.split()
            is_load = len(toks) == 6 and all(_NUM.match(t) for t in toks)
            if is_load:
                if start is None:
                    start = i
                cnt += 1
            elif start is not None:
                break
        if start is not None:
            self.load_start = start
            self.load_len = cnt

    @staticmethod
    def _fmt_load(ld):
        """
        Định dạng một tổ hợp tải thành dòng 6 số theo thứ tự Hx Hy N Mx My Mz.

        Trả về chuỗi các giá trị (định dạng _fmt) ngăn cách bằng 2 dấu cách.
        """
        return "  ".join(_fmt(ld.get(k, 0.0)) for k in ('Hx', 'Hy', 'N', 'Mx', 'My', 'Mz'))

    def _detect_layout(self, coords):
        """
        Dò bố cục khối cọc trong file: kiểu tọa độ (inline/split) và chiều dài
        khối lặp (block_len).

        Thử khớp tọa độ cọc đầu rồi kiểm tra các cọc tiếp theo cách đều nhau L
        dòng. Khi tìm được, gọi _set_layout. Ném MCOCWriterError nếu không thấy
        tọa độ cọc gốc trong file.
        """
        lines = self.lines
        n = self.n_orig
        x0, y0 = coords[0]
        # Thử kiểu inline trước
        cands_inline = [i for i in range(len(lines)) if _is_inline_coord(lines[i], x0, y0)]
        for c in cands_inline:
            if n == 1:
                self._set_layout('inline', c, 17, coords); return
            for L in range(4, 80):
                if all(c + k * L < len(lines) and
                       _is_inline_coord(lines[c + k * L], coords[k][0], coords[k][1])
                       for k in range(1, n)):
                    self._set_layout('inline', c, L, coords); return
        # Không khớp inline -> thử kiểu tách dòng (split)
        cands_split = [i for i in range(len(lines)) if _is_split_coord(lines, i, x0, y0)]
        for c in cands_split:
            if n == 1:
                self._set_layout('split', c, 16, coords); return
            for L in range(4, 80):
                if all(c + k * L + 1 < len(lines) and
                       _is_split_coord(lines, c + k * L, coords[k][0], coords[k][1])
                       for k in range(1, n)):
                    self._set_layout('split', c, L, coords); return
        raise MCOCWriterError(
            "Khong tim thay toa do coc (%.3f, %.3f) trong file template." % (x0, y0))

    def _set_layout(self, kind, c0, L, coords):
        """
        Ghi nhận bố cục đã dò: kiểu tọa độ, chiều dài khối, vị trí dòng tọa độ
        trong khối (coord_offset) và dòng bắt đầu khối cọc (block_start).

        Với từ 2 cọc trở lên, suy ra coord_offset bằng cách so các dòng phía
        trước với khối kế tiếp; với 1 cọc dùng giá trị mặc định.
        """
        self.coord_kind = kind
        self.block_len = L
        if self.n_orig >= 2:
            # Lùi dần để tìm điểm khối bắt đầu lặp lại giống nhau
            off = 0
            while off + 1 <= c0:
                if self.lines[c0 - off - 1] != self.lines[c0 + L - off - 1]:
                    break
                off += 1
            off = min(off, L - 1)
        else:
            off = 12
        self.coord_offset = off
        self.block_start = c0 - off

    def _patch_header(self, n_new, n_loads=None):
        """
        Cập nhật số cọc Nc (và tùy chọn số tổ hợp tải) ở dòng thứ 2 của header.

        Tham số:
            n_new   : số cọc mới; n_loads : số tổ hợp tải mới (nếu có).
        Trả về bản sao header đã sửa (không thay đổi self.header).
        """
        header = list(self.header)
        if len(header) >= 2:
            parts = header[1].split()
            if parts and _NUM.match(parts[0]):
                parts[0] = str(n_new)
                if n_loads is not None and len(parts) >= 2 and _NUM.match(parts[1]):
                    parts[1] = str(n_loads)
                header[1] = ' '.join(parts)
        return header

    def render(self, coords, name_suffix="", loads=None):
        """
        Dựng nội dung file input MCOC mới (chuỗi) cho bộ tọa độ cọc đã cho.

        Tham số:
            coords      : tọa độ cọc mới.
            name_suffix : (tùy chọn) hậu tố thêm vào tên ở dòng đầu.
            loads       : (tùy chọn) danh sách tổ hợp tải để ghi đè khối tải.
        Trả về chuỗi nội dung đầy đủ (header + các khối cọc + footer), kết
        thúc bằng đúng kiểu xuống dòng của file gốc.
        """
        coords = np.asarray(coords, dtype=float)
        n_loads = len(loads) if loads is not None else None
        # Header: cập nhật số cọc / số tổ hợp tải
        out = self._patch_header(len(coords), n_loads)
        # Ghi đè khối tải bằng dữ liệu từ UI (nếu có khối tải trong template)
        if loads is not None and self.load_start is not None:
            new_load_lines = [self._fmt_load(ld) for ld in loads]
            out = out[:self.load_start] + new_load_lines + out[self.load_start + self.load_len:]
        if name_suffix and out:
            out[0] = out[0].rstrip() + " " + name_suffix
        # Sinh một khối cọc cho mỗi tọa độ, thay đúng dòng tọa độ theo kiểu
        for (x, y) in coords:
            block = list(self.block_tpl)
            if self.coord_kind == 'inline':
                block[self.coord_offset] = _replace_inline_coord(block[self.coord_offset], x, y)
            else:
                block[self.coord_offset] = _fmt(x)
                block[self.coord_offset + 1] = _fmt(y)
            out.extend(block)
        out.extend(self.footer)
        return self.eol.join(out) + self.eol

    def write(self, coords, out_path, name_suffix="", loads=None):
        """
        Dựng nội dung (render) và ghi ra file out_path.

        Giữ nguyên kiểu xuống dòng của template (newline=''). Trả về out_path.
        """
        content = self.render(coords, name_suffix, loads=loads)
        with open(out_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        return out_path


# ============================================================================
# Tự kiểm tra template (round-trip)
# ============================================================================
def self_check(template_path, original_coords):
    """
    Kiểm tra round-trip của template: sinh file từ tọa độ gốc rồi đọc lại.

    Tham số:
        template_path  : đường dẫn file input MCOC gốc.
        original_coords: tọa độ cọc gốc dùng để đối chiếu.
    Trả về (ok, thông_điệp): ok=True kèm mô tả template nếu tọa độ đọc lại
    khớp tọa độ gốc; ngược lại ok=False kèm lý do/lỗi.
    """
    import tempfile
    from io_handlers.file_io import parse_input_file
    try:
        tpl = MCOCTemplate(template_path, original_coords)
        tmp = os.path.join(tempfile.gettempdir(), "_mcoc_selfcheck.txt")
        tpl.write(original_coords, tmp)
        # Đọc ngược file vừa sinh và so tọa độ với bản gốc
        params, loads, _ = parse_input_file(tmp)
        got = np.asarray(params.get('original_coords', []), dtype=float)
        want = np.asarray(original_coords, dtype=float)
        if got.shape != want.shape or not np.allclose(got, want, atol=1e-3):
            return False, "Doc nguoc file sinh ra cho toa do khac toa do goc."
        return True, "Template OK (%d coc, khoi %d dong, kieu %s)." % (
            tpl.n_orig, tpl.block_len, tpl.coord_kind)
    except Exception as e:
        return False, str(e)
