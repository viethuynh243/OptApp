# -*- mode: python ; coding: utf-8 -*-
"""
OptApp.spec - Cấu hình PyInstaller đóng gói GUI OptApp (onedir, windowed).

Gói main.py + toàn bộ thư viện (numpy, matplotlib, openpyxl, reportlab, PyPDF2)
và đặc biệt gom đầy đủ tkinterdnd2 (kèm thư viện nhị phân tkdnd) để tính năng
kéo - thả file hoạt động sau khi cài. Kết quả: dist/OptApp/OptApp.exe.

Build:  pyinstaller packaging/OptApp.spec --noconfirm \
            --distpath packaging/dist --workpath packaging/build
"""

import os
from PyInstaller.utils.hooks import collect_all

# SPECPATH = thư mục chứa file .spec (packaging/); ROOT = gốc dự án (cha của nó)
ROOT = os.path.dirname(SPECPATH)
ICON = os.path.join(SPECPATH, "optapp.ico")

# Gom trọn tkinterdnd2: data (thư viện tkdnd), binaries, hidden imports
tkdnd_datas, tkdnd_binaries, tkdnd_hidden = collect_all("tkinterdnd2")

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=tkdnd_binaries,
    datas=tkdnd_datas,
    hiddenimports=tkdnd_hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "tests"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OptApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,            # GUI app: ẩn cửa sổ console
    icon=ICON,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="OptApp",
)
