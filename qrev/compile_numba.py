import os
import sys
import subprocess
import qrev.DischargeFunctions as qdf
import qrev.MiscLibs as qml


def compile_numba_functions():
    """Compile Numba functions in the qrev package."""

    python_path = sys.executable

    # discharge functions
    q_func_path = os.path.join(os.path.dirname(qdf.__file__))

    subprocess.run([python_path,
                    os.path.join(q_func_path,
                                 'bottom_discharge_extrapolation.py')],
                   cwd=q_func_path, check=True)
    subprocess.run([python_path,
                    os.path.join(q_func_path,
                                 'top_discharge_extrapolation.py')],
                   cwd=q_func_path, check=True)
    # misc libs
    misc_libs_path = os.path.join(os.path.dirname(qml.__file__))

    subprocess.run([python_path, os.path.join(misc_libs_path, 'run_iqr.py')],
                   cwd=misc_libs_path, check=True)
    subprocess.run([python_path,
                    os.path.join(misc_libs_path, 'robust_loess_compiled.py')],
                   cwd=misc_libs_path, check=True)
    subprocess.run(
        [python_path, os.path.join(misc_libs_path, 'bayes_cov_compiled.py')],
        cwd=misc_libs_path, check=True)


if __name__ == "__main__":
    compile_numba_functions()
    print("Numba functions compiled successfully.")


