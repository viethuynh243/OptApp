"""
pile_section.py - Tiết diện cọc tròn (TCVN) và BẢNG ĐƯỜNG KÍNH có sức chịu tải.

Hai nhóm chức năng:
    1. Đặc trưng tiết diện cọc tròn đặc theo đường kính d:
           Fo = π·d²/4   (diện tích tiết diện, m²)
           Jo = π·d⁴/64  (mômen quán tính, m⁴)
       Hai công thức này KHỚP đúng giá trị mà file input MCOC nhúng cho mỗi
       cọc (kiểm chứng: d=1.2 -> Fo=1.13097, Jo=0.101788). Nhờ vậy khi đổi
       đường kính ta có thể patch lại đúng Fo/Jo để MCOC chấm chính xác.

    2. Bảng đường kính ứng viên: mỗi dòng gồm (d, [Po], [Ct], [M]) — sức chịu
       NÉN, NHỔ, UỐN cho phép tương ứng đường kính đó, do người dùng nhập theo
       TCVN 10304:2014 (đường kính lớn hơn -> sức chịu tải lớn hơn). Tập đường
       kính cần quét chính là tập các dòng trong bảng này.

Quy ước đơn vị: d (m), Fo (m²), Jo (m⁴), [Po]/[Ct] (T), [M] (T.m).
"""

import math


# ===========================================================================
# Đặc trưng tiết diện cọc tròn đặc
# ===========================================================================
def area(d):
    """Diện tích tiết diện cọc tròn Fo = π·d²/4 (m²)."""
    return math.pi * d * d / 4.0


def inertia(d):
    """Mômen quán tính tiết diện cọc tròn Jo = π·d⁴/64 (m⁴)."""
    return math.pi * (d ** 4) / 64.0


def section_props(d):
    """Trả về (Fo, Jo) của cọc tròn đường kính d — xem area()/inertia()."""
    return area(d), inertia(d)


# ===========================================================================
# Một đường kính ứng viên kèm sức chịu tải cho phép
# ===========================================================================
class DiameterOption:
    """Một dòng trong bảng đường kính: d kèm sức chịu [Po], [Ct], [M].

    Thuộc tính:
        d   : đường kính cọc (m).
        Po  : sức chịu NÉN cho phép [Po] (T).
        Ct  : sức chịu NHỔ cho phép [Ct] (T); 0 nghĩa là không kiểm R5b.
        M   : sức chịu UỐN cho phép [M] (T.m); 0 nghĩa là không kiểm R6.
        H   : sức chịu lực NGANG cho phép [H] (T); 0 nghĩa là không kiểm R7.
    """

    def __init__(self, d, Po, Ct=0.0, M=0.0, H=0.0):
        """Khởi tạo và kiểm tra hợp lệ một dòng đường kính của bảng."""
        self.d = float(d)
        self.Po = float(Po)
        self.Ct = float(Ct or 0.0)
        self.M = float(M or 0.0)
        self.H = float(H or 0.0)
        if self.d <= 0:
            raise ValueError("Duong kinh coc phai > 0: %r" % d)
        if self.Po <= 0:
            raise ValueError("Suc chiu nen [Po] phai > 0 cho d=%.3f" % self.d)

    @property
    def Fo(self):
        """Diện tích tiết diện Fo (m²) suy từ đường kính d."""
        return area(self.d)

    @property
    def Jo(self):
        """Mômen quán tính tiết diện Jo (m⁴) suy từ đường kính d."""
        return inertia(self.d)

    def as_params(self, base_params):
        """Tạo bản sao params với d và các giới hạn lấy theo đường kính này.

        Dùng để chạy đánh giá/tối ưu cho riêng một đường kính: ghi đè D_PILE,
        SAFE_D, P_LIMIT, P_TENSION, M_LIMIT, H_LIMIT theo dòng bảng hiện tại,
        giữ nguyên các tham số còn lại của bài toán.
        """
        p = dict(base_params)
        p['D_PILE'] = self.d
        p['SAFE_D'] = self.d            # R4: tim cọc cách mép ≥ d (TCVN 10304)
        p['P_LIMIT'] = self.Po
        p['P_TENSION'] = self.Ct
        p['M_LIMIT'] = self.M
        p['H_LIMIT'] = self.H
        return p

    def __repr__(self):
        return ("DiameterOption(d=%.3f, Po=%.1f, Ct=%.1f, M=%.1f, H=%.1f)"
                % (self.d, self.Po, self.Ct, self.M, self.H))


# ===========================================================================
# Bảng đường kính ứng viên
# ===========================================================================
class DiameterTable:
    """Bảng các đường kính ứng viên (đã sắp xếp tăng dần theo d)."""

    def __init__(self, options):
        """Nhận danh sách DiameterOption (hoặc dict/tuple) và chuẩn hóa.

        Mỗi phần tử có thể là DiameterOption, hoặc dict
        {'d','Po','Ct','M','H'}, hoặc tuple (d, Po[, Ct[, M[, H]]]).
        Ném ValueError nếu bảng rỗng hoặc có đường kính trùng.
        """
        opts = [self._coerce(o) for o in options]
        if not opts:
            raise ValueError("Bang duong kinh rong.")
        ds = [round(o.d, 6) for o in opts]
        if len(set(ds)) != len(ds):
            raise ValueError("Bang duong kinh co duong kinh trung lap.")
        self.options = sorted(opts, key=lambda o: o.d)

    @staticmethod
    def _coerce(o):
        """Chuyển một phần tử bất kỳ về DiameterOption."""
        if isinstance(o, DiameterOption):
            return o
        if isinstance(o, dict):
            return DiameterOption(o['d'], o.get('Po', o.get('P_LIMIT')),
                                  o.get('Ct', o.get('P_TENSION', 0.0)),
                                  o.get('M', o.get('M_LIMIT', 0.0)),
                                  o.get('H', o.get('H_LIMIT', 0.0)))
        # tuple/list: (d, Po[, Ct[, M[, H]]])
        o = list(o)
        return DiameterOption(*o)

    def diameters(self):
        """Danh sách đường kính (m) theo thứ tự tăng dần."""
        return [o.d for o in self.options]

    def get(self, d, tol=1e-6):
        """Tra dòng bảng theo đường kính d (sai số tol); None nếu không có."""
        for o in self.options:
            if abs(o.d - d) <= tol:
                return o
        return None

    def __len__(self):
        return len(self.options)

    def __iter__(self):
        return iter(self.options)

    @classmethod
    def from_single(cls, params):
        """Dựng bảng 1 dòng từ params bài toán (khi không quét đường kính).

        Lấy D_PILE/P_LIMIT/P_TENSION/M_LIMIT/H_LIMIT hiện có làm dòng duy nhất.
        """
        return cls([DiameterOption(
            params['D_PILE'], params.get('P_LIMIT', 500.0),
            params.get('P_TENSION', 0.0), params.get('M_LIMIT', 0.0),
            params.get('H_LIMIT', 0.0))])
