import os
import re
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

from setuptools import setup

if os.name == 'nt':
    from distutils.command import build_ext

    def get_export_symbols(self, ext):
        """
        Slightly modified from:
        https://github.com/python/cpython/blob/8849e5962ba481d5d414b3467a256aba2134b4da\
        /Lib/distutils/command/build_ext.py#L686-L703
        """
        # Patch from: https://bugs.python.org/issue35893
        parts = ext.name.split('.')
        if parts[-1] == '__init__':
            suffix = parts[-2]
        else:
            suffix = parts[-1]

        # from here on unchanged
        try:
            # Unicode module name support as defined in PEP-489
            # https://www.python.org/dev/peps/pep-0489/#export-hook-name
            suffix.encode('ascii')
        except UnicodeEncodeError:
            suffix = 'U' + suffix.encode('punycode').replace(b'-', b'_').decode('ascii')

        initfunc_name = 'PyInit_' + suffix
        if initfunc_name not in ext.export_symbols:
            ext.export_symbols.append(initfunc_name)
        return ext.export_symbols

    build_ext.build_ext.get_export_symbols = get_export_symbols


class ReplaceLinks:
    def __init__(self):
        self.links = set()

    def replace_issues(self, m):
        id = m.group(1)
        self.links.add(f'.. _#{id}: https://github.com/samuelcolvin/pydantic/issues/{id}')
        return f'`#{id}`_'

    def replace_users(self, m):
        name = m.group(2)
        self.links.add(f'.. _@{name}: https://github.com/{name}')
        return f'{m.group(1)}`@{name}`_'

    def extra(self):
        return '\n\n' + '\n'.join(sorted(self.links)) + '\n'


description = 'Data validation and settings management using python 3.6 type hinting'
THIS_DIR = Path(__file__).resolve().parent
try:
    history = (THIS_DIR / 'HISTORY.md').read_text()
    history = re.sub(r'#(\d+)', r'[#\1](https://github.com/samuelcolvin/pydantic/issues/\1)', history)
    history = re.sub(r'( +)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.I)
    history = re.sub('@@', '@', history)

    long_description = (THIS_DIR / 'README.md').read_text() + '\n\n' + history
except FileNotFoundError:
    long_description = description + '.\n\nSee https://pydantic-docs.helpmanual.io/ for documentation.'

# avoid loading the package before requirements are installed:
version = SourceFileLoader('version', 'pydantic/version.py').load_module()

ext_modules = None
if not any(arg in sys.argv for arg in ['clean', 'check']) and 'SKIP_CYTHON' not in os.environ:
    try:
        from Cython.Build import cythonize
    except ImportError:
        pass
    else:
        # For cython test coverage install with `make build-cython-trace`
        compiler_directives = {}
        if 'CYTHON_TRACE' in sys.argv:
            compiler_directives['linetrace'] = True
        os.environ['CFLAGS'] = '-O3'
        ext_modules = cythonize(
            'pydantic/*.py',
            exclude=['pydantic/generics.py'],
            nthreads=int(os.getenv('CYTHON_NTHREADS', 0)),
            language_level=3,
            compiler_directives=compiler_directives,
        )

setup(
    name='pydantic',
    version=str(version.VERSION),
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
    ],
    author='Samuel Colvin',
    author_email='s@muelcolvin.com',
    url='https://github.com/samuelcolvin/pydantic',
    license='MIT',
    packages=['pydantic'],
    package_data={'pydantic': ['py.typed']},
    python_requires='>=3.6',
    zip_safe=False,  # https://mypy.readthedocs.io/en/latest/installed_packages.html
    install_requires=[
        'dataclasses>=0.6;python_version<"3.7"'
    ],
    extras_require={
        'email': ['email-validator>=1.0.3'],
        'typing_extensions': ['typing-extensions>=3.7.2'],
        'dotenv': ['python-dotenv>=0.10.4'],
    },
    ext_modules=ext_modules,
)
