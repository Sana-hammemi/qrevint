import os
import sys
import subprocess
import qrev.DischargeFunctions as QFunc
import qrev.MiscLibs as QLibs
from qrev import __sphinx_path__


def compile_numba_functions():
    """Compile Numba functions in the qrev package."""

    python_path = sys.executable

    # discharge functions
    q_func_path = os.path.join(os.path.dirname(QFunc.__file__))

    subprocess.run([python_path,
                    os.path.join(q_func_path,
                                 'bottom_discharge_extrapolation.py')],
                   cwd=q_func_path, check=True)
    subprocess.run([python_path,
                    os.path.join(q_func_path,
                                 'top_discharge_extrapolation.py')],
                   cwd=q_func_path, check=True)
    # misc libs
    misc_libs_path = os.path.join(os.path.dirname(QLibs.__file__))

    subprocess.run([python_path, os.path.join(misc_libs_path, 'run_iqr.py')],
                   cwd=misc_libs_path, check=True)
    subprocess.run([python_path,
                    os.path.join(misc_libs_path, 'robust_loess_compiled.py')],
                   cwd=misc_libs_path, check=True)
    subprocess.run(
        [python_path, os.path.join(misc_libs_path, 'bayes_cov_compiled.py')],
        cwd=misc_libs_path, check=True)

def build_docs():
    """Build Sphinx documentation for the qrev package."""

    make_cmd = os.path.join(__sphinx_path__, "make.bat")

    static_path = os.path.join(__sphinx_path__, "_static")
    build_path = os.path.join(__sphinx_path__, "_build")

    if not os.path.exists(static_path):
        os.makedirs(static_path)
    if not os.path.exists(build_path):
        os.makedirs(build_path)

    subprocess.run([make_cmd, "html"], cwd=__sphinx_path__, check=True)
    print("Sphinx documentation built successfully.")

def run_all():
    compile_numba_functions()
    build_docs()


if __name__ == "__main__":
    run_all()
    print("Setup complete.")
