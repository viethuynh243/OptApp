"""
nsga2_ext.py - Chạy NSGA-II với R7/R8 BẬT, cho một đường kính cọc cố định.

Lõi cũ (core/nsga2_optimizer.py) đã có sẵn 2 cờ ENABLE_LATERAL_CHECK (R7) và
ENABLE_PM_INTERACTION (R8) nhưng để TẮT ("tạm tắt theo yêu cầu"). Luồng mở rộng
BẬT chúng đúng theo cơ chế lõi đã thiết kế, KHÔNG sửa mã nguồn lõi: dùng một
context manager tạm gán cờ ở cấp module rồi khôi phục nguyên trạng sau khi chạy.

Nhờ tái dùng 100% thuật toán đã kiểm thử của lõi, ở đây chỉ thêm lớp mỏng:
    - bật/khôi phục cờ R7/R8 an toàn (try/finally);
    - gọi core.run_nsga2 cho một đường kính (params + evaluator đã gắn đường kính).

Việc quét NHIỀU đường kính và gộp kết quả do orchestrator đảm nhiệm.
"""

from contextlib import contextmanager

from core import nsga2_optimizer as _core
from core import mechanics as _mech
from core.nsga2_optimizer import run_nsga2 as _run_nsga2
from core.ext.config_ext import DEFAULT_EXT_CONFIG


# ===========================================================================
# Bật/khôi phục ràng buộc R7, R8 an toàn (không sửa file lõi)
# ===========================================================================
@contextmanager
def constraints_enabled(cfg):
    """Tạm BẬT cờ R7/R8 ở core.nsga2_optimizer và core.mechanics theo cfg.

    Lưu giá trị cũ rồi khôi phục trong finally — đảm bảo không rò trạng thái
    sang phần còn lại của chương trình (luồng cũ vẫn thấy R7/R8 tắt như cũ).
    """
    saved = {
        ('n', 'R7'): _core.ENABLE_LATERAL_CHECK,
        ('n', 'R8'): _core.ENABLE_PM_INTERACTION,
        ('m', 'R7'): _mech.ENABLE_LATERAL_CHECK,
        ('m', 'R8'): _mech.ENABLE_PM_INTERACTION,
    }
    try:
        _core.ENABLE_LATERAL_CHECK = cfg.enable_R7
        _core.ENABLE_PM_INTERACTION = cfg.enable_R8
        _mech.ENABLE_LATERAL_CHECK = cfg.enable_R7
        _mech.ENABLE_PM_INTERACTION = cfg.enable_R8
        yield
    finally:
        _core.ENABLE_LATERAL_CHECK = saved[('n', 'R7')]
        _core.ENABLE_PM_INTERACTION = saved[('n', 'R8')]
        _mech.ENABLE_LATERAL_CHECK = saved[('m', 'R7')]
        _mech.ENABLE_PM_INTERACTION = saved[('m', 'R8')]


# ===========================================================================
# Chạy NSGA-II cho một đường kính (R7/R8 theo cấu hình)
# ===========================================================================
def run_nsga2_one_diameter(params, loads, evaluator, cfg=None, **kwargs):
    """Chạy NSGA-II cho params (đã gắn 1 đường kính) với R7/R8 bật theo cfg.

    Đầu vào:
        params    : tham số bài toán đã gắn đường kính (D_PILE, P_LIMIT,
                    P_TENSION, M_LIMIT, H_LIMIT...). Xem DiameterOption.as_params.
        loads     : danh sách tổ hợp tải.
        evaluator : hàm coords->dict (MCOC theo đường kính, hoặc mock).
        cfg       : ExtConfig (mặc định DEFAULT_EXT_CONFIG — bật R7+R8).
        **kwargs  : chuyển thẳng cho core.run_nsga2 (pop_size, n_gen, seed,
                    max_evals, secondary, log).

    Trả về: dict kết quả y như core.run_nsga2 nhưng các phương án ĐÃ được
    sàng lọc theo cả R7/R8 (nhờ cờ bật trong lúc chạy).
    """
    cfg = cfg or DEFAULT_EXT_CONFIG
    with constraints_enabled(cfg):
        return _run_nsga2(params, loads, evaluator=evaluator, **kwargs)
