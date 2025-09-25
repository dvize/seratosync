# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# Data files and hidden imports
datas = [('seratosync', 'seratosync')]
binaries = []
hiddenimports = [
    'customtkinter', 
    'PIL', 
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'json',
    'pathlib',
    'subprocess',
    'threading',
    'shutil',
    'datetime',
]

# Collect CustomTkinter and tkinter files
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('tkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['seratosync_gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SeratoSync_GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SeratoSync_GUI',
)

app = BUNDLE(
    coll,
    name='SeratoSync GUI.app',
    icon=None,  # Add .icns file path here if you have an icon
    bundle_identifier='com.seratosync.gui',
    version='2.0.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'JSON Configuration',
                'CFBundleTypeIconFile': 'config.icns',
                'LSItemContentTypes': ['public.json'],
                'LSHandlerRank': 'Alternate'
            }
        ],
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 dvize. All rights reserved.',
        'CFBundleGetInfoString': 'Serato Sync GUI - Modern Serato database management tool',
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    },
)
