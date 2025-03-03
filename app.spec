# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs
block_cipher = None
from qrev import __app__
# Initialize hiddenimports list
hiddenimports = [
    'numba',
    'numba.core',
    'numba.core.types',
    'numba.core.typing',
    'numba.core.dispatcher',
    'numba.npyufunc',
    'numba.core.errors',
    'numba.pycc',
    'numba.pycc.cc',
    'numba.cext',
    'numba.misc.special',
    'numba.typed',
    'numba.typed.typedlist',
    'numba.core.registry',
    'qrev.Classes.QComp',
    'qrev.Classes.TransectData',
    'qrev.Classes.DepthStructure',
    'qrev.Classes.DepthData',
    'qrev.MiscLibs.robust_loess_compiled',
    'qrev.UI.QRev',
    'qrev.Classes.Measurement',
    'qrev.Classes.ComputeExtrap',
    'qrev.Classes.ExtrapQSensitivity',
    'qrev.DischargeFunctions.top_discharge_extrapolation'
]

# Collect all submodules and extend hiddenimports
all_submodules = collect_submodules('numba')
hiddenimports.extend(all_submodules)

# Collect all necessary files
datas = (collect_data_files('numba') + 
         collect_data_files('numpy'))



icon = "docs\\source\\assets\\files\\" + __app__ + '.ico'

added_files = [('docs\\_build\\html', 'qrev_documentation'),
               ("docs\\source\\assets\\files\\*", "qrev_files")]
# Add binaries
binaries = collect_dynamic_libs('numba') + collect_dynamic_libs('numpy')
a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['.'],
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

hiddenimports = [
    'numba',
    'numba.core',
    'numba.core.types',
    'numba.core.typing',
    'numba.core.dispatcher',
    'numba.npyufunc',
    'numba.core.errors',
    'numba.pycc',
    'numba.pycc.cc',
    'numba.cext',
    'numba.misc.special',
    'numba.typed',
    'numba.typed.typedlist',
    'numba.core.registry',
    'qrev.Classes.QComp',
    'qrev.Classes.TransectData',
    'qrev.Classes.DepthStructure',
    'qrev.Classes.DepthData',
    'qrev.MiscLibs.robust_loess_compiled',
    'qrev.UI.QRev',
    'qrev.Classes.Measurement',
    'qrev.Classes.ComputeExtrap',
    'qrev.Classes.ExtrapQSensitivity',
    'qrev.DischargeFunctions.top_discharge_extrapolation'
]
datas = collect_data_files('numba')+ collect_data_files('numpy')

# Include MSVC runtime files
msvc_runtime = collect_data_files('msvcrt')


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