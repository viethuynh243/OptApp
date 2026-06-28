; OptApp.iss - Script Inno Setup tạo bộ cài OptApp_Setup_x.y.z.exe
; Đóng gói bản build PyInstaller (packaging\dist\OptApp) thành installer Windows,
; tạo shortcut Start Menu + Desktop, có trình gỡ cài đặt. Tương tự bộ cài MCOC.
;
; Build:  "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" packaging\OptApp.iss
; (file phải lưu UTF-8 có BOM để hiển thị đúng tiếng Việt)

#define AppName "OptApp - Toi uu bo tri coc mong cau"
#define AppNameVi "OptApp - Tối ưu bố trí cọc móng cầu"
; AppVersion lấy từ core/version.py (nguồn duy nhất) qua build_installer.bat (/DAppVersion=...).
; Giá trị dưới đây chỉ là mặc định dự phòng khi biên dịch .iss trực tiếp không truyền /D.
#ifndef AppVersion
#define AppVersion "1.3.0"
#endif
#define AppPublisher "TEDI - Tong Cong ty Tu van Thiet ke GTVT"
#define AppExe "OptApp.exe"

[Setup]
; AppId định danh duy nhất chương trình (giữ cố định qua các phiên bản để nâng cấp đúng)
AppId={{B3F1C2A4-7E5D-4A91-9C6B-0A1D2E3F4A50}
AppName={#AppNameVi}
AppVersion={#AppVersion}
AppVerName={#AppNameVi} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\OptApp
DefaultGroupName=OptApp
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=OptApp_Setup_{#AppVersion}
SetupIconFile=optapp.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppNameVi}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
; Cho phép cài không cần quyền admin (per-user) hoặc admin (toàn máy) tùy chọn
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tao bieu tuong ngoai Desktop"; GroupDescription: "Shortcut:"

[Files]
; Toàn bộ thư mục dist của PyInstaller (OptApp.exe + _internal)
Source: "dist\OptApp\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\OptApp"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"
Name: "{group}\Go cai dat OptApp"; Filename: "{uninstallexe}"
Name: "{autodesktop}\OptApp"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
; Mở chương trình ngay sau khi cài (tùy người dùng tick)
Filename: "{app}\{#AppExe}"; Description: "Chay OptApp ngay bay gio"; Flags: nowait postinstall skipifsilent
