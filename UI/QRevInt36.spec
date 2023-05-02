# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['QRev.py'],
             pathex=['C:\\Users\\dave\\Documents\\QRevInt_Project\\QRevInt\\UI\\', 'C:\\Users\\dave\\Documents\\QRevInt_Project\\QRevInt\\UI'],
             binaries=[('C:\\Users\\dave\\Documents\\QRevInt_Project\\QRevInt\\venv_qrevint39\\Lib\\site-packages\\sklearn\.libs\\vcomp140.dll', '.\\sklearn\\.libs'),
             ('C:\\Users\\dave\\Documents\\QRevInt_Project\\QRevInt\\venv_qrevint39\\Lib\\site-packages\\sklearn\.libs\\vcruntime140_1.dll', '.\\sklearn\\.libs')],
             datas=[],
             hiddenimports=['sklearn', 'sklearn.neighbors.typedefs', 'sklearn.utils._cython_blas', 'sklearn.utils._weight_vector'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[('C:\\Users\\dave\\Documents\\QRevInt_Project\\QRevInt\\venv_qrevint39\\Lib\\site-packages\\numpy\\distutils\\ccompiler')],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='QRevInt',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False ,
          version='file_version_info.txt',
          icon='QRevInt.ico')
