"""
orchestrator.py - Điều phối luồng tối ưu MỞ RỘNG đầu-cuối.

Gộp ba tính năng mở rộng thành một luồng:

    1) QUÉT ĐƯỜNG KÍNH: với mỗi đường kính trong bảng (mỗi đường kính có [Po]/
       [Ct]/[M]/[H] riêng), chạy NSGA-II (R7+R8 BẬT) đánh giá bằng MCOC THỰC
       đã patch tiết diện theo đường kính đó.
    2) CHỌN TOÀN CỤC: so sánh phương án tốt nhất của từng đường kính theo một
       hàm chi phí vật liệu (mặc định: số cọc × diện tích tiết diện = thể tích
       bê tông cọc trên 1 m dài), ưu tiên rẻ hơn, đồng hạng thì ít cọc hơn.
    3) ĐỔI KÍCH THƯỚC BỆ: thu bệ vừa khít phương án thắng theo TCVN 10304:2014.

Phụ thuộc: core.ext.{pile_section, config_ext, nsga2_ext, blackbox_ext,
cap_resize}. Có thể tiêm evaluator_factory để chạy không cần MCOC (kiểm thử).
"""

import numpy as np

from core.ext.pile_section import DiameterTable, DiameterOption, area
from core.ext.config_ext import DEFAULT_EXT_CONFIG
from core.ext.nsga2_ext import run_nsga2_one_diameter
from core.ext.cap_resize import resize_cap


# ===========================================================================
# Đánh giá PHƯƠNG ÁN GỐC (đường kính gốc) để so sánh "tiến hóa"
# ===========================================================================
def _evaluate_original(params, loads, table, d_orig, Po_orig,
                       evaluator_factory, log):
    """Chấm phương án GỐC của kỹ sư ở ĐƯỜNG KÍNH GỐC (MCOC) -> dict config.

    Trả về None nếu thiếu toạ độ gốc hoặc MCOC lỗi (không làm hỏng cả luồng).
    Dùng để hiển thị + so sánh với phương án tối ưu (yêu cầu: in phương án gốc).
    """
    orig_coords = params.get('original_coords')
    if not orig_coords:
        return None
    dia_o = table.get(d_orig) or DiameterOption(
        d_orig, Po_orig, params.get('P_TENSION', 0.0) or 0.0,
        params.get('M_LIMIT', 0.0) or 0.0, params.get('H_LIMIT', 0.0) or 0.0)
    params_o = dia_o.as_params(params)
    try:
        if evaluator_factory is None:
            from core.ext.blackbox_ext import make_diameter_evaluator
            ev_o = make_diameter_evaluator(params, dia_o, loads=loads,
                                           d_orig=d_orig, Po_orig=Po_orig, log=log)
        else:
            ev_o = evaluator_factory(params_o, dia_o, loads)
        r0 = ev_o(np.asarray(orig_coords, dtype=float))
    except Exception as e:
        log("  CANH BAO: khong cham duoc phuong an goc bang MCOC: %s" % e)
        return None
    # Bệ gốc = max(ô L_X/L_Y hiện tại, bệ vừa khít cọc gốc) để cọc gốc LUÔN nằm
    # trong bệ (kể cả khi ô đã bị thu ở lần chạy trước).
    from core.ext.cap_resize import recommend_cap_size
    _safe_d_o = float(params.get('SAFE_D', d_orig) or d_orig)
    _fit_lx, _fit_ly = recommend_cap_size(orig_coords, _safe_d_o, 0.1)
    _orig_cap_lx = max(float(params.get('L_X', 0.0) or 0.0), _fit_lx)
    _orig_cap_ly = max(float(params.get('L_Y', 0.0) or 0.0), _fit_ly)
    return {'type': 'Goc', 'nx': 0, 'ny': 0, 'sx': 0, 'sy': 0,
            'n': len(orig_coords), 'coords': [list(c) for c in orig_coords],
            'pmax': r0.get('pmax', 0.0), 'pmin': r0.get('pmin', 0.0),
            'mxmax': r0.get('mxmax', 0.0), 'mymax': r0.get('mymax', 0.0),
            'd_orig': d_orig, 'Po_orig': Po_orig,
            # Bệ + ĐƯỜNG KÍNH + sức chịu của phương án gốc PHẢI đi theo phương án
            # gốc (không lấy bệ đã thu / đường kính thắng) để audit R3/R4/R5… và
            # mặt bằng phản ánh ĐÚNG phương án gốc, so sánh được tiến hóa.
            # Bệ gốc phải ĐỦ CHỨA cọc gốc: nếu ô L_X/L_Y hiện tại nhỏ hơn mức cần
            # (vd đã bị "thu bệ" ở lần chạy trước) thì lấy bệ vừa khít cọc gốc —
            # tránh cọc tràn ra ngoài bệ + báo R4 KHÔNG ĐẠT oan.
            'cap_lx': _orig_cap_lx, 'cap_ly': _orig_cap_ly,
            'safe_d_orig': _safe_d_o,
            'ct_orig': float(dia_o.Ct or 0.0),
            'm_orig': float(dia_o.M or 0.0),
            'h_orig': float(dia_o.H or 0.0),
            'ok': r0.get('pmax', 1e9) <= Po_orig,
            'msg': 'Phuong an goc (MCOC, d=%.3g m)' % d_orig}


# ===========================================================================
# Hàm chi phí vật liệu để so sánh giữa các đường kính
# ===========================================================================
def material_cost(n, d):
    """Chi phí vật liệu xấp xỉ = số cọc × diện tích tiết diện (m²/m dài).

    Phản ánh thể tích bê tông cọc trên một mét dài; cọc to (d lớn) tốn hơn
    nên cân bằng được "ít cọc to" với "nhiều cọc nhỏ".
    """
    return n * area(d)


# ===========================================================================
# Luồng tối ưu mở rộng đầu-cuối
# ===========================================================================
def run_extended_optimization(params, loads, table, cfg=None,
                              evaluator_factory=None, d_orig=None, Po_orig=None,
                              cost_fn=None, log=None, **nsga_kwargs):
    """Quét đường kính + tối ưu (R7/R8) + đổi kích thước bệ.

    Đầu vào:
        params  : tham số bài toán (input_filepath, original_coords, exe_path,
                  L_X, L_Y, D_PILE, P_LIMIT...). D_PILE/P_LIMIT là của FILE GỐC.
        loads   : danh sách tổ hợp tải.
        table   : DiameterTable hoặc danh sách (DiameterOption/dict/tuple). Nếu
                  None -> dùng đúng đường kính hiện tại (DiameterTable.from_single).
        cfg     : ExtConfig (mặc định bật R7+R8, resize bệ tròn 0.1 m).
        evaluator_factory : None -> dùng MCOC thực
                  (blackbox_ext.make_diameter_evaluator). Ngược lại là callable
                  (params_d, dia, loads) -> evaluator(coords) — phục vụ kiểm thử.
        d_orig, Po_orig   : đường kính / [Po] GỐC trong file MCOC (None -> lấy
                  từ params['D_PILE']/['P_LIMIT']).
        cost_fn : hàm (n, d) -> chi phí (mặc định material_cost).
        log     : callable(str) ghi log.
        **nsga_kwargs : chuyển cho core.run_nsga2 (pop_size, n_gen, seed,
                  max_evals, secondary).

    Trả về dict:
        {
          'per_diameter' : [ {dia, result, best, cost} ... ] theo từng đường kính,
          'winner'       : bản ghi đường kính thắng (hoặc None nếu không có),
          'recommended'  : config phương án tối ưu toàn cục (hoặc None),
          'cap_report'   : báo cáo đổi kích thước bệ (hoặc None),
          'params_final' : params đã cập nhật L_X/L_Y (nếu resize),
        }
    """
    cfg = cfg or DEFAULT_EXT_CONFIG
    cost_fn = cost_fn or material_cost
    log = log or (lambda m: None)

    if table is None:
        table = DiameterTable.from_single(params)
    elif not isinstance(table, DiameterTable):
        table = DiameterTable(table)

    d_orig = float(params['D_PILE']) if d_orig is None else float(d_orig)
    Po_orig = float(params['P_LIMIT']) if Po_orig is None else float(Po_orig)

    # Chấm phương án GỐC (đường kính gốc) để LUÔN có cái so sánh "tiến hóa",
    # kể cả khi không tìm được phương án mới khả thi.
    original_config = _evaluate_original(params, loads, table, d_orig, Po_orig,
                                         evaluator_factory, log)

    per_diameter = []
    for dia in table:
        log("=== Duong kinh d=%.3f m | [Po]=%.1f [Ct]=%.1f [M]=%.1f [H]=%.1f ==="
            % (dia.d, dia.Po, dia.Ct, dia.M, dia.H))
        params_d = dia.as_params(params)

        if evaluator_factory is None:
            from core.ext.blackbox_ext import make_diameter_evaluator
            evaluator = make_diameter_evaluator(params, dia, loads=loads,
                                                d_orig=d_orig, Po_orig=Po_orig,
                                                log=log)
        else:
            evaluator = evaluator_factory(params_d, dia, loads)

        result = run_nsga2_one_diameter(params_d, loads, evaluator, cfg=cfg,
                                        log=log, **nsga_kwargs)
        best = result.get('recommended')
        cost = cost_fn(best['n'], dia.d) if best else float('inf')
        per_diameter.append({'dia': dia, 'result': result, 'best': best,
                             'cost': cost, 'params_d': params_d})
        if best:
            log("  -> d=%.3f: %d coc, Pmax=%.1f T, chi phi=%.4f"
                % (dia.d, best['n'], best['pmax'], cost))
        else:
            log("  -> d=%.3f: KHONG co phuong an kha thi (R1-R8)." % dia.d)

    # ---- Chọn toàn cục: chi phí nhỏ nhất, đồng hạng thì ít cọc hơn ----------
    feasible = [r for r in per_diameter if r['best'] is not None]
    if not feasible:
        log("Khong co phuong an kha thi cho moi duong kinh.")
        return {'per_diameter': per_diameter, 'winner': None,
                'recommended': None, 'cap_report': None, 'params_final': params,
                'original_config': original_config}

    winner = min(feasible, key=lambda r: (r['cost'], r['best']['n']))
    rec = winner['best']
    dwin = winner['dia'].d
    log("THANG: d=%.3f m, %d coc, Pmax=%.1f T, chi phi=%.4f"
        % (dwin, rec['n'], rec['pmax'], winner['cost']))

    # ---- Đổi kích thước bệ cho phương án thắng -----------------------------
    params_final, cap_report = resize_cap(winner['params_d'],
                                          rec['coords'], dwin, cfg)
    log("BE: %.2f x %.2f -> %.2f x %.2f m (mep cach tim >= %.3f, lam tron %.2f)"
        % (cap_report['old_LX'], cap_report['old_LY'],
           cap_report['new_LX'], cap_report['new_LY'],
           cap_report['safe_d'], cap_report['round_to']))

    # Bệ của PHƯƠNG ÁN ĐỀ XUẤT đi theo chính nó: bệ đã thu nếu áp dụng resize,
    # ngược lại giữ bệ gốc (chỉ đề xuất). Để mỗi phương án vẽ trong bệ của mình.
    if cap_report['applied']:
        rec['cap_lx'] = cap_report['new_LX']
        rec['cap_ly'] = cap_report['new_LY']
    else:
        rec['cap_lx'] = cap_report['old_LX']
        rec['cap_ly'] = cap_report['old_LY']

    return {
        'per_diameter': per_diameter,
        'winner': winner,
        'recommended': rec,
        'winner_diameter': dwin,
        'cap_report': cap_report,
        'params_final': params_final,
        'original_config': original_config,
    }
