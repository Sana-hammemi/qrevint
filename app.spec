# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
from Classes import __app__
icon = "docs\\source\\assets\\files\\" + __app__ + '.ico'

added_files = [('docs\\_build\\html', 'qrev_documentation'),
               ("docs\\source\\assets\\files\\*", "qrev_files")]

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
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          splash,
          splash.binaries,
          [],
          name=__app__,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          version='file_version_info.txt',
          icon=icon)