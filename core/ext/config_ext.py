"""
config_ext.py - Cấu hình cho luồng tối ưu MỞ RỘNG (tách biệt lõi cũ).

Mục đích: gom mọi công tắc/chính sách của tính năng mở rộng vào một chỗ, KHÔNG
đụng tới core/constants.py (giữ nguyên hành vi chương trình cũ). Gồm:

    - Bật R7 (lực ngang) và R8 (tương tác P-M) MẶC ĐỊNH cho luồng mở rộng.
    - Chính sách đổi kích thước bệ sau tối ưu (làm tròn theo bội số thi công).

Lưu ý: lõi cũ đọc cờ R7/R8 từ core.constants (đang False). Luồng mở rộng KHÔNG
phụ thuộc các cờ đó mà dùng ExtConfig.enable_R7/enable_R8 tại đây, nên việc bật
ở đây không ảnh hưởng tới chương trình cũ.
"""


# ===========================================================================
# Cấu hình ràng buộc mở rộng + chính sách bệ
# ===========================================================================
class ExtConfig:
    """Cấu hình luồng tối ưu mở rộng (ràng buộc + đổi kích thước bệ)."""

    def __init__(self, enable_R7=True, enable_R8=True,
                 cap_round_to=0.1, cap_resize=True):
        """Khởi tạo cấu hình mở rộng.

        Đầu vào:
            enable_R7   : bật kiểm tra lực ngang R7 (Hmax ≤ [H]).
            enable_R8   : bật kiểm tra tương tác P-M R8 (P/[Po]+M/[M] ≤ 1).
            cap_round_to: bội số làm tròn LÊN kích thước bệ (m). VD 0.1 hoặc 0.5.
            cap_resize  : True -> tự đổi L_X/L_Y; False -> chỉ đề xuất, không sửa.
        """
        self.enable_R7 = bool(enable_R7)
        self.enable_R8 = bool(enable_R8)
        self.cap_round_to = float(cap_round_to)
        self.cap_resize = bool(cap_resize)
        if self.cap_round_to <= 0:
            raise ValueError("cap_round_to phai > 0.")

    def __repr__(self):
        return ("ExtConfig(R7=%s, R8=%s, cap_round_to=%.3f, cap_resize=%s)"
                % (self.enable_R7, self.enable_R8, self.cap_round_to,
                   self.cap_resize))


# Cấu hình mặc định: BẬT R7+R8, làm tròn bệ lên bội số 0.1 m, có đổi kích thước.
DEFAULT_EXT_CONFIG = ExtConfig()
