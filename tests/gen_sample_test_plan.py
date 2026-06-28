# -*- coding: utf-8 -*-
"""gen_sample_test_plan.py - Sinh BỘ ĐIỀU KIỆN TEST (thủ công) cho các file mẫu
trong mcoc_input_sample/.

Đọc từng file bằng CHÍNH bộ parser của ứng dụng (io_handlers.file_io.parse_input_file)
nên số liệu kỳ vọng không bao giờ lệch với dữ liệu thật. Với mỗi file tính sẵn:
  - Thông số được parse: L_X, L_Y, d, [Po], số tổ hợp, số cọc gốc.
  - Hình học (TIÊU CHUẨN, tất định, KHÔNG cần MCOC): R3 k/c tim-tim nhỏ nhất so 3d,
    R4 mép bệ (max|x|+d ≤ Lx/2). Đây là phần audit tính tất định.
  - Dự báo nội lực BỆ CỨNG (rigid_cap): Pmax/Pmin và TỔ HỢP CHI PHỐI (chỉ tham
    chiếu — MCOC sẽ hiệu chỉnh trị tuyệt đối, nhưng tổ hợp chi phối thường khớp).

Xuất ra docs/KE_HOACH_TEST_MCOC.md. Chạy: python tests/gen_sample_test_plan.py
"""
import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from io_handlers.file_io import parse_input_file
from core import rigid_cap
from core.constants import effective_min_spacing

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'mcoc_input_sample')
OUT_MD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'docs', 'KE_HOACH_TEST_MCOC.md')


def analyze(path):
    """Parse 1 file + tính số liệu kỳ vọng tất định. Trả về dict hoặc None."""
    params, loads, name = parse_input_file(path)
    coords = params.get('original_coords')
    if not coords or not loads:
        return None
    coords = np.asarray(coords, float)
    d = float(params.get('D_PILE', 0) or 0)
    Po = float(params.get('P_LIMIT', 0) or 0)
    Lx = float(params.get('L_X', 0) or 0)
    Ly = float(params.get('L_Y', 0) or 0)
    n_piles = len(coords)

    # R3 (gốc = bố trí tùy biến) — chỉ xác định được cận DƯỚI qua k/c nhỏ nhất
    s_min_req = effective_min_spacing(params)         # = 3d (thông thủy=0)
    s_act = float(rigid_cap.min_spacing(coords)) if n_piles > 1 else float('inf')
    r3_ok = s_act >= s_min_req - 1e-3

    # R4 mép bệ (SAFE_D = d)
    max_x = float(np.max(np.abs(coords[:, 0])))
    max_y = float(np.max(np.abs(coords[:, 1])))
    r4_ok = (max_x + d <= Lx / 2 + 1e-3) and (max_y + d <= Ly / 2 + 1e-3)

    # Dự báo bệ cứng: Pmax/Pmin từng tổ hợp + tổ hợp chi phối (max nén)
    P = rigid_cap.forces_all_loads(coords, loads)     # (n_load, n_pile), đơn vị file
    nmax_per = P.max(axis=1)
    nmin_per = P.min(axis=1)
    gov = int(np.argmax(nmax_per))                    # tổ hợp Pmax lớn nhất
    pmax = float(nmax_per[gov]); pmin = float(P.min())

    return dict(name=name, file=os.path.basename(path), d=d, Po=Po, Lx=Lx, Ly=Ly,
                n_piles=n_piles, n_loads=len(loads), coords=coords, loads=loads,
                s_act=s_act, s_min_req=s_min_req, r3_ok=r3_ok,
                max_x=max_x, max_y=max_y, r4_ok=r4_ok,
                gov=gov + 1, pmax=pmax, pmin=pmin,
                nmax_per=nmax_per, nmin_per=nmin_per)


def fmt(v, n=2):
    return f"{v:.{n}f}"


def card(a):
    """Sinh 1 thẻ test Markdown cho 1 file."""
    L = []
    L.append(f"### `{a['file']}` — {a['name']}")
    L.append("")
    L.append("**B1. Nạp file → kiểm thông số parse (ô bên trái):**")
    L.append("")
    L.append("| Thông số | Giá trị kỳ vọng |")
    L.append("|---|---:|")
    L.append(f"| Rộng bệ Lx (m) | {fmt(a['Lx'])} |")
    L.append(f"| Dài bệ Ly (m) | {fmt(a['Ly'])} |")
    L.append(f"| Đ.kính cọc d (m) | {fmt(a['d'])} |")
    L.append(f"| Sức nén [Po] (T) | {fmt(a['Po'],0)} |")
    L.append(f"| Số tổ hợp tải | {a['n_loads']} |")
    L.append(f"| Số cọc (gốc) | {a['n_piles']} |")
    L.append("")
    L.append("> Lưu ý: file KHÔNG mang `[Ct]` (sức nhổ) và `[M]` (sức uốn) → 2 ô này TRỐNG; "
             "audit sẽ ghi R2/R5b và R5/R6 = *không kiểm*. Nhập tay nếu muốn kiểm.")
    L.append("")
    # Bảng 3 tổ hợp đầu để đối chiếu nhanh bảng tải trọng
    L.append("**B2. Đối chiếu vài dòng tải trọng (Hx, Hy, P, Mx, My, Mz):**")
    L.append("")
    L.append("| TH | Hx | Hy | P | Mx | My | Mz |")
    L.append("|---:|---:|---:|---:|---:|---:|---:|")
    show = list(range(min(3, a['n_loads'])))
    if a['n_loads'] > 3:
        show.append(a['n_loads'] - 1)
    for i in show:
        ld = a['loads'][i]
        L.append(f"| {i+1} | {fmt(ld['Hx'],0)} | {fmt(ld['Hy'],0)} | {fmt(ld['N'],0)} | "
                 f"{fmt(ld['Mx'],0)} | {fmt(ld['My'],0)} | {fmt(ld['Mz'],0)} |")
    L.append("")
    # Hình học gốc (tất định)
    r3 = "ĐẠT ✓" if a['r3_ok'] else "**KHÔNG ĐẠT ✗**"
    r4 = "ĐẠT ✓" if a['r4_ok'] else "**KHÔNG ĐẠT ✗**"
    L.append("**B3. Hình học bố trí GỐC (tất định theo TCVN — không cần MCOC):**")
    L.append("")
    L.append(f"- **R3** k/c tim-tim nhỏ nhất = `{fmt(a['s_act'])}` m; yêu cầu ≥ 3d = "
             f"`{fmt(a['s_min_req'])}` m → {r3}")
    L.append(f"- **R4** mép bệ: max|x|+d = `{fmt(a['max_x']+a['d'])}` ≤ Lx/2 = `{fmt(a['Lx']/2)}`; "
             f"max|y|+d = `{fmt(a['max_y']+a['d'])}` ≤ Ly/2 = `{fmt(a['Ly']/2)}` → {r4}")
    L.append("")
    # Dự báo bệ cứng — CHỈ khẳng định điều bất biến theo đơn vị (tổ hợp chi phối, dấu kéo).
    L.append("**B4. Dự báo BỆ CỨNG (tham chiếu — MCOC quyết định trị tuyệt đối):**")
    L.append("")
    L.append(f"- **Tổ hợp CHI PHỐI dự kiến: TH{a['gov']}** (nội lực nén lớn nhất — bất biến "
             "theo đơn vị, dùng đối chiếu \"TH… chi phối\" trên KPI/bảng audit).")
    L.append(f"- Pmax/Pmin dự báo (theo ĐƠN VỊ TẢI trong file, chỉ để so SÁNH TƯƠNG ĐỐI giữa "
             f"các tổ hợp): `{fmt(a['pmax'],1)}` / `{fmt(a['pmin'],1)}`.")
    if a['pmin'] < 0:
        L.append("- ⚠ Có cọc bị **KÉO** (Pmin < 0) ở ít nhất một tổ hợp → nên khai **[Ct]** để kiểm R2/R5b.")
    L.append("")
    L.append("**B5. Sau khi bấm ▶ CHẠY TỐI ƯU HÓA, kiểm:**")
    L.append("")
    L.append(f"- Phương án kiến nghị có **số cọc ≤ {a['n_piles']}** (gốc) và **Pmax ≤ [Po]**.")
    L.append("- Chuyển radio **\"Kiểm tra điều kiện (R1–R8)\"**: tiêu đề bảng ghi *R1–R8*; "
             "mọi ô R1/R2 của phương án kiến nghị **xanh (ĐẠT)**; tổ hợp chi phối viền đỏ.")
    L.append("- Dòng tổng hợp dưới bảng: R3/R4 ✓; R5/R6, R7, R8 ghi *không kiểm* (vì chưa khai [M]/[H]).")
    L.append("- Trạng thái KPI = **ĐẠT**; **Phương án gốc** hiển thị đúng trạng thái "
             + ("(GỐC vốn vi phạm hình học → KHÔNG ĐẠT, khớp audit)." if not (a['r3_ok'] and a['r4_ok'])
                else "ĐẠT/ KHÔNG ĐẠT theo lực thực MCOC).")
             )
    L.append("")
    L.append("---")
    L.append("")
    return "\n".join(L)


def main():
    files = sorted(glob.glob(os.path.join(SAMPLE_DIR, '*.txt')),
                   key=lambda p: os.path.basename(p))
    cards, warns = [], []
    summary = []
    for p in files:
        try:
            a = analyze(p)
        except Exception as e:
            warns.append(f"- `{os.path.basename(p)}`: parse lỗi — {e}")
            continue
        if a is None:
            warns.append(f"- `{os.path.basename(p)}`: thiếu tọa độ gốc / tải trọng — bỏ qua.")
            continue
        cards.append(card(a))
        summary.append(a)

    out = []
    out.append("# BỘ ĐIỀU KIỆN TEST THỦ CÔNG — mcoc_input_sample/")
    out.append("")
    out.append("> Sinh tự động bởi `tests/gen_sample_test_plan.py` (đọc bằng chính parser "
               "của app nên luôn khớp dữ liệu thật). Chạy lại để cập nhật khi đổi file mẫu.")
    out.append("")
    out.append("**Quy ước đơn vị:** lực = Tấn (T), momen = T.m. **[Po] đọc từ file = 500 T.** "
               "File mẫu KHÔNG có [Ct]/[M] nên R2/R5b/R6 mặc định *không kiểm* (nhập tay nếu cần). "
               "**R7** chỉ kiểm khi bật *Tối ưu mở rộng* + khai [H].")
    out.append("")
    out.append("**Cấu hình bắt buộc trước khi chạy:** MCOC Batch + đúng file input gốc "
               "(các trị Pmax/Pmin trị tuyệt đối do MCOC quyết định; mục B4 chỉ là dự báo bệ cứng).")
    out.append("")
    # Bảng tổng quan
    out.append("## Bảng tổng quan")
    out.append("")
    out.append("| File | Lx×Ly (m) | d (m) | #TH | #cọc gốc | k/c min (m) | R3 gốc | R4 gốc | TH chi phối | Pmax dự báo* |")
    out.append("|---|---|---:|---:|---:|---:|:--:|:--:|:--:|---:|")
    for a in summary:
        out.append(f"| {a['file']} | {fmt(a['Lx'],1)}×{fmt(a['Ly'],1)} | {fmt(a['d'],2)} | "
                   f"{a['n_loads']} | {a['n_piles']} | {fmt(a['s_act'],2)} | "
                   f"{'✓' if a['r3_ok'] else '✗'} | {'✓' if a['r4_ok'] else '✗'} | "
                   f"TH{a['gov']} | {fmt(a['pmax'],1)} |")
    out.append("")
    out.append("> `*` Pmax dự báo theo **đơn vị tải trong file** (bệ cứng, chưa hiệu chỉnh MCOC) — "
               "chỉ để so sánh tương đối; trị Tấn chính thức do MCOC tính. `R3/R4 gốc` là kiểm "
               "hình học TẤT ĐỊNH theo TCVN (đúng không cần MCOC).")
    out.append("")
    out.append("**Đọc nhanh:** các bố trí gốc có **R3 ✗** (vd T3–T6, T22: k/c 3.33 m < 3d=3.6 m) "
               "→ bảng audit PHẢI báo *KHÔNG ĐẠT* cho phương án gốc; phần tối ưu phải tìm bố trí "
               "đạt 3d–6d. `[Po]=500 T` lấy từ file — với trụ lớn (T10–T14) nếu tối ưu báo vô "
               "nghiệm thì chỉnh [Po]/đơn vị cho đúng thực tế.")
    if warns:
        out.append("### Ghi chú file bỏ qua")
        out.extend(warns)
        out.append("")
    out.append("## Thẻ test từng file")
    out.append("")
    out.extend(cards)

    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write("\n".join(out))
    print(f"Đã sinh {len(summary)} thẻ test -> {OUT_MD}")
    if warns:
        print(f"({len(warns)} file bỏ qua)")


if __name__ == '__main__':
    main()
