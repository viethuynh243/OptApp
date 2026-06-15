# Đóng gói OptApp thành bộ cài (`OptApp_Setup_x.y.z.exe`)

Thư mục này chứa toàn bộ cấu hình để tạo bộ cài Windows cho OptApp, giống cách
MCOC được đóng gói (PyInstaller bundle + installer Inno Setup).

## Thành phần

| File | Vai trò |
|---|---|
| `make_icon.py` | Sinh `optapp.ico` (icon app + shortcut) bằng Pillow |
| `OptApp.spec` | Cấu hình PyInstaller: gói `main.py` + thư viện (gom đầy đủ tkinterdnd2) thành `dist/OptApp/OptApp.exe` (onedir, windowed) |
| `OptApp.iss` | Script Inno Setup: đóng `dist/OptApp` thành installer, tạo shortcut Start Menu + Desktop, có trình gỡ cài. Lưu **UTF-8 có BOM** |
| `build_installer.bat` | Chạy cả 3 bước trên một lần |
| `optapp.ico` | Icon đã sinh (commit để khỏi cần Pillow khi build lại) |

> `build/`, `dist/`, và `*.exe` **không** được commit (đã ghi trong `.gitignore`) — chúng tự sinh lại khi build.

## Yêu cầu một lần

```bat
pip install pyinstaller pillow
winget install JRSoftware.InnoSetup        REM cài Inno Setup 6 (per-user)
```

## Build

```bat
packaging\build_installer.bat
```

Kết quả: **`packaging\OptApp_Setup_1.0.0.exe`**.

Hoặc chạy thủ công từng bước (từ thư mục gốc dự án):

```bat
python packaging\make_icon.py
python -m PyInstaller packaging\OptApp.spec --noconfirm --clean ^
  --distpath packaging\dist --workpath packaging\build
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" packaging\OptApp.iss
```

## Đổi phiên bản / tên

Sửa `#define AppVersion` (và `AppNameVi` nếu cần) ở đầu `OptApp.iss`, rồi build lại.
Tên file output đi theo `AppVersion`. Giữ nguyên `AppId` để Windows nhận đúng là
bản nâng cấp của cùng một chương trình.

## Ghi chú kỹ thuật

- **onedir, windowed:** ứng dụng là GUI Tkinter nên ẩn console (`console=False`);
  bản onedir khởi động nhanh và dễ nén bằng Inno Setup.
- **tkinterdnd2:** `OptApp.spec` dùng `collect_all("tkinterdnd2")` để kèm thư viện
  nhị phân `tkdnd` (gồm `win-x64`), nếu thiếu thì tính năng kéo-thả file sẽ lỗi.
- **MCOC:** bộ cài này chỉ đóng gói OptApp; người dùng vẫn cấu hình đường dẫn tới
  `MCOC_Batch.exe` của riêng họ trong ứng dụng để chạy đánh giá MCOC chính xác.
