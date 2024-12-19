import os
import re
import sys
from pathlib import Path
from typing import List

from setuptools import Extension, setup


THIS_DIR = Path(__file__).resolve().parent
try:
    history = (THIS_DIR / 'HISTORY.md').read_text(encoding='utf-8')
    history = re.sub(r'(\s)#(\d+)', r'\1[#\2](https://github.com/pydantic/pydantic/issues/\2)', history)
    history = re.sub(r'( +)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.I)
    history = re.sub('@@', '@', history)

    long_description = (THIS_DIR / 'README.md').read_text(encoding='utf-8') + '\n\n' + history
except FileNotFoundError:
    long_description = 'Data validation and settings management using python type hints. \n\nSee https://docs.pydantic.dev/1.10/ for documentation.'


ext_modules: List[Extension] = []

# Build options:
# Can be provided as specified by PEP 517 by supplying --config-settings="--build-option=--<opt>":
# - `--cythonize`: Whether to use Cython as an extension.
# - `--enable-trace`: Whether to enable tracing for Cython. Not available for 3.12+
#   (see https://cython.readthedocs.io/en/latest/src/tutorial/profiling_tutorial.html).

if '--cythonize' in sys.argv:
    print('Cython is enabled')
    # Remove the special argument, otherwise setuptools can raise an exception
    sys.argv.remove('--cythonize')

    from Cython.Build import cythonize

    compiler_directives = {'annotation_typing': False}

    if '--enable-trace' in sys.argv:
        sys.argv.remove('--enable-trace')
        if sys.version_info >= (3, 12):
            raise RuntimeError("Tracing isn't supported for Python 3.12+.")
        print('Tracing is enabled')
        compiler_directives['linetrace'] = True

    # Set CFLAG to all optimizations (-O3), add `-g0` to reduce size of binaries, see #2276
    # Any additional CFLAGS will be appended. Only the last optimization flag will have effect
    os.environ['CFLAGS'] = '-O3 -g0 ' + os.environ.get('CFLAGS', '')

    ext_modules = cythonize(
        'pydantic/*.py',
        exclude=['pydantic/generics.py'],
        nthreads=int(os.getenv('CYTHON_NTHREADS', 0)),
        language_level=3,
        compiler_directives=compiler_directives,
    )

setup(
    ext_modules=ext_modules,
    long_description=long_description,
    long_description_content_type='text/markdown',
)
