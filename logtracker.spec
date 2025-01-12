# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Ajout du dossier src au PYTHONPATH
src_path = os.path.abspath(os.path.join(os.getcwd(), 'src'))
sys.path.insert(0, src_path)

# Définition des ressources
resources_path = os.path.join('src', 'resources')
resources_files = [(os.path.join(os.getcwd(), resources_path), 'resources')]

hidden_imports = collect_submodules('PyQt6') + [
    'utils.database',
    'utils.jira_client',
    'ui.config_dialog',
    'ui.sync_dialog'
]

a = Analysis(
    ['src/qt_main.py'],
    pathex=[src_path],
    binaries=[],
    datas=resources_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LogTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
