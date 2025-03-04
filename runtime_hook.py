import os
import sys
import numba

# Disable AOT compilation and enable JIT
os.environ['NUMBA_DISABLE_INTEL_SVML'] = '1'
os.environ['NUMBA_DISABLE_JIT'] = '0'