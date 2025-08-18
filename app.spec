# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
import os
from qrev import __app__, __doc_path__, __icon_path__, __translation_files__


icon = os.path.join(__icon_path__, '..', __app__ + '.ico')
translation_files = os.path.join(__translation_files__, '*.qm')

added_files = [(__doc_path__, 'qrev_documentation'),
               (__icon_path__, "qrev_files"),
               (__translation_files__, "translation_files")]


a = Analysis(['app.py'],
             binaries=[],
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

splash = Splash(
    icon,
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=False,)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    splash,
    exclude_binaries=True,
    name=__app__,
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
    version='file_version_info.txt',
    icon=icon
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    splash.binaries,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=__app__,
    version='file_version_info.txt',
    icon=icon
)