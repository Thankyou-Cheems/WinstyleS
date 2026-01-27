# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for WinstyleS
Build command: pyinstaller winstyles.spec
"""

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Get the project root
project_root = os.path.dirname(os.path.abspath(SPEC))

# Collect all winstyles submodules
hiddenimports = collect_submodules('winstyles')

# Add additional hidden imports
hiddenimports += [
    'http.server',
    'socketserver',
    'webbrowser',
    'json',
    'subprocess',
    'threading',
    'tempfile',
    'winreg',
    'ctypes',
]

a = Analysis(
    [os.path.join(project_root, 'launcher.py')],
    pathex=[
        os.path.join(project_root, 'src'),
        project_root,
    ],
    binaries=[],
    datas=[
        # Include frontend files for Web UI
        (os.path.join(project_root, 'frontend'), 'frontend'),
        # Include start_web_ui.py
        (os.path.join(project_root, 'start_web_ui.py'), '.'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'tkinter',  # We use customtkinter, not tkinter directly... actually we need it
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove tkinter from excludes as customtkinter needs it
a.excludes = [e for e in a.excludes if e != 'tkinter']

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WinstyleS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window - pure GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: Add icon: 'assets/icon.ico'
    version=None,  # TODO: Add version info file
)
