from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs
datas = collect_data_files('numba')
hiddenimports = collect_submodules('numba')
binaries = collect_dynamic_libs('numba')