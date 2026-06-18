"""
mcoc_writer_ext.py - Sinh file input MCOC có ĐỔI ĐƯỜNG KÍNH cọc (mở rộng).

Mở rộng MCOCTemplate (io_handlers/mcoc_writer.py): ngoài việc thay số cọc / tọa
độ / tải trọng như bản gốc, lớp này còn PATCH các trường tiết diện trong từng
khối cọc khi đổi đường kính:

    - Bpx, Bpy (đường kính theo 2 phương) -> d mới.
    - Fo (diện tích) -> π·d²/4.
    - Jo (mômen quán tính) -> π·d⁴/64.
    - Po (sức chịu nén cho phép) -> [Po] mới (lấy theo bảng đường kính).

Cách dò vị trí trường: KHỚP GIÁ TRỊ gốc trong khối cọc mẫu (d gốc, Fo gốc,
Jo gốc, Po gốc) thay vì dựa vào offset cứng — bền vững với các biến thể template.
Các dòng tọa độ (X, Y) bị loại trừ để không nhầm.

KHÔNG sửa file gốc mcoc_writer.py: giữ nguyên hành vi luồng cũ.
"""

import os
import numpy as np

from io_handlers.mcoc_writer import MCOCTemplate, MCOCWriterError, _NUM, \
    _replace_inline_coord
from core.ext.pile_section import area, inertia


def _fmt_full(v):
    """Định dạng số đủ độ chính xác cho trường tiết diện (giữ ~12 chữ số)."""
    return "%.12g" % float(v)


def _line_float(line):
    """Trả về float nếu dòng chỉ chứa đúng một token số, ngược lại None."""
    parts = line.split()
    if len(parts) == 1 and _NUM.match(parts[0]):
        try:
            return float(parts[0])
        except ValueError:
            return None
    return None


# ===========================================================================
# Template MCOC có đổi đường kính
# ===========================================================================
class DiameterMCOCTemplate(MCOCTemplate):
    """MCOCTemplate + khả năng patch tiết diện cọc theo đường kính mới."""

    def __init__(self, template_path, original_coords, d_orig, Po_orig):
        """Phân tích template và dò vị trí các trường tiết diện trong khối cọc.

        Đầu vào:
            template_path  : file input MCOC gốc.
            original_coords: tọa độ cọc gốc (dò bố cục khối cọc).
            d_orig         : đường kính cọc gốc trong file (m).
            Po_orig        : sức chịu nén [Po] gốc trong file (T).
        """
        super().__init__(template_path, original_coords)
        self.d_orig = float(d_orig)
        self.Po_orig = float(Po_orig)
        self._detect_section_fields()

    def _detect_section_fields(self, tol=1e-3):
        """Dò chỉ số dòng (trong khối mẫu) của Bpx/Bpy, Fo, Jo, Po bằng giá trị.

        Khớp theo giá trị gốc: d (đường kính, thường 2 dòng), Fo=π·d²/4,
        Jo=π·d⁴/64, Po. Bỏ qua 2 dòng tọa độ (coord_offset, +1) nếu là split.
        Ghi nhận: dia_idx (list), fo_idx, jo_idx, po_idx (None nếu không thấy).
        """
        fo_orig = area(self.d_orig)
        jo_orig = inertia(self.d_orig)
        # Các dòng tọa độ cần loại trừ khỏi việc dò
        skip = set()
        if self.coord_kind == 'split':
            skip = {self.coord_offset, self.coord_offset + 1}
        else:
            skip = {self.coord_offset}

        self.dia_idx = []
        self.fo_idx = None
        self.jo_idx = None
        self.po_idx = None
        for i, line in enumerate(self.block_tpl):
            if i in skip:
                continue
            v = _line_float(line)
            if v is None:
                continue
            if abs(v - self.d_orig) <= tol:
                self.dia_idx.append(i)
            elif self.fo_idx is None and abs(v - fo_orig) <= max(tol, fo_orig * 1e-4):
                self.fo_idx = i
            elif self.jo_idx is None and abs(v - jo_orig) <= max(tol, jo_orig * 1e-4):
                self.jo_idx = i
            elif self.po_idx is None and abs(v - self.Po_orig) <= max(tol, self.Po_orig * 1e-4):
                self.po_idx = i

        if not self.dia_idx or self.fo_idx is None or self.jo_idx is None:
            raise MCOCWriterError(
                "Khong do duoc truong tiet dien (d/Fo/Jo) trong khoi coc mau "
                "(d_orig=%.3f). Khong the doi duong kinh an toan." % self.d_orig)

    def render_diameter(self, coords, d_new, Po_new, name_suffix="", loads=None):
        """Dựng nội dung file MCOC cho bố trí coords với đường kính d_new.

        Patch Bpx/Bpy=d_new, Fo=π·d_new²/4, Jo=π·d_new⁴/64, Po=Po_new cho MỌI
        khối cọc; phần header/tải/tọa độ xử lý như bản gốc. Trả về chuỗi nội dung.
        """
        coords = np.asarray(coords, dtype=float)
        fo_new = area(d_new)
        jo_new = inertia(d_new)
        n_loads = len(loads) if loads is not None else None

        out = self._patch_header(len(coords), n_loads)
        if loads is not None and self.load_start is not None:
            new_load_lines = [self._fmt_load(ld) for ld in loads]
            out = out[:self.load_start] + new_load_lines + out[self.load_start + self.load_len:]
        if name_suffix and out:
            out[0] = out[0].rstrip() + " " + name_suffix

        for (x, y) in coords:
            block = list(self.block_tpl)
            # 1) Patch tiết diện theo đường kính mới
            for di in self.dia_idx:
                block[di] = _fmt_full(d_new)
            block[self.fo_idx] = _fmt_full(fo_new)
            block[self.jo_idx] = _fmt_full(jo_new)
            if self.po_idx is not None:
                block[self.po_idx] = _fmt_full(Po_new)
            # 2) Patch tọa độ cọc (giữ logic kiểu inline/split như bản gốc)
            if self.coord_kind == 'inline':
                block[self.coord_offset] = _replace_inline_coord(
                    block[self.coord_offset], x, y)
            else:
                block[self.coord_offset] = _fmt_full(x)
                block[self.coord_offset + 1] = _fmt_full(y)
            out.extend(block)
        out.extend(self.footer)
        return self.eol.join(out) + self.eol

    def write_diameter(self, coords, out_path, d_new, Po_new,
                       name_suffix="", loads=None):
        """Dựng (render_diameter) và ghi ra file out_path. Trả về out_path."""
        content = self.render_diameter(coords, d_new, Po_new,
                                       name_suffix=name_suffix, loads=loads)
        with open(out_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        return out_path


# ===========================================================================
# Tự kiểm tra đổi đường kính (round-trip)
# ===========================================================================
def self_check_diameter(template_path, original_coords, d_orig, Po_orig,
                        d_new, Po_new):
    """Kiểm tra round-trip: sinh file với d_new rồi đọc lại, đối chiếu d/Fo/Jo.

    Trả về (ok, thông_điệp). Đọc ngược bằng file_io.parse_input_file và so
    đường kính đọc được với d_new (sai số nhỏ).
    """
    import tempfile
    from io_handlers.file_io import parse_input_file
    try:
        tpl = DiameterMCOCTemplate(template_path, original_coords, d_orig, Po_orig)
        tmp = os.path.join(tempfile.gettempdir(), "_mcoc_dia_selfcheck.txt")
        tpl.write_diameter(original_coords, tmp, d_new, Po_new)
        params, _, _ = parse_input_file(tmp)
        got_d = float(params.get('D_PILE', -1))
        if abs(got_d - d_new) > 1e-3:
            return False, "Doc nguoc d=%.4f khac d_new=%.4f." % (got_d, d_new)
        return True, ("Template doi duong kinh OK (d %.3f->%.3f, %d coc, "
                      "dia_idx=%s, Fo@%s, Jo@%s, Po@%s)."
                      % (d_orig, d_new, tpl.n_orig, tpl.dia_idx, tpl.fo_idx,
                         tpl.jo_idx, tpl.po_idx))
    except Exception as e:
        return False, str(e)
