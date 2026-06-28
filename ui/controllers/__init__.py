"""ui.controllers — các controller tách từ MainWindow (Plan 023, Pha 3).

Mỗi controller nhận tham chiếu `app` (MainWindow) làm "shared context": state
chia sẻ (params, loads, current_config) và widget chia sẻ vẫn nằm trên `app`;
controller thao tác qua `self.app.<...>`. MainWindow để lại delegator mỏng cho
các method được test/harness hoặc UI gọi (giữ API ngoài bất biến).
"""
