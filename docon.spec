# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller derleme betiği.

Yalnızca hafif arayüz+analiz katmanı paketlenir (PySide6, pypdf). Ağır motor
bağımlılıkları (torch, marker-pdf, surya modelleri) pakete GİRMEZ; program ilk
açılışta bunları kendi ortamına (%LOCALAPPDATA%\\Docon\\runtime) kurar
(bkz. app/core/installer.py).

Derleme: .venv\\Scripts\\pyinstaller docon.spec
Çıktı:   dist\\Docon\\Docon.exe  (onedir; PySide6 çevrimiçi güncelleme yapısı için
         onefile'dan daha hızlı açılır ve AV yanlış-pozitiflerine daha az takılır)
"""

block_cipher = None

a = Analysis(
    ["app/__main__.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("app/assets/icon.ico", "app/assets"),
    ],
    hiddenimports=[
        "PySide6.QtSvg",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Bu makinede ve requirements.txt'te olmayan ama torch/marker'ın kendi
        # ortamıyla karışmasın diye açıkça dışlanan ağır paketler:
        "torch", "torchvision", "marker", "surya",
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Docon",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="app/assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="Docon",
)
