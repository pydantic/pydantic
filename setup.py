import os
import re
from pathlib import Path

from setuptools import setup

description = 'TODO'
THIS_DIR = Path(__file__).resolve().parent
try:
    long_description = (THIS_DIR / 'README.md').read_text()
except FileNotFoundError:
    long_description = description

# VERSION is set in Cargo.toml
cargo = Path(THIS_DIR / 'Cargo.toml').read_text()
VERSION = re.search('version *= *"(.*?)"', cargo).group(1)

extra = {}
if not os.getenv('SKIP_RUST_EXTENSION'):
    from setuptools_rust import Binding, RustExtension

    extra['rust_extensions'] = [RustExtension('pydantic_core._pydantic_core', binding=Binding.PyO3)]

setup(
    name='pydantic_core',
    version=VERSION,
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
        'Environment :: MacOS X',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    author='Samuel Colvin',
    author_email='s@muelcolvin.com',
    url='https://github.com/samuelcolvin/pydantic_core',
    license='MIT',
    packages=['pydantic_core'],
    package_data={'pydantic_core': ['py.typed', '*.pyi']},
    install_requires=['typing_extensions; python_version < "3.11.0"'],
    python_requires='>=3.7',
    zip_safe=False,
    project_urls={
        'Funding': 'https://github.com/sponsors/samuelcolvin',
        'Source': 'https://github.com/samuelcolvin/pydantic_core',
    },
    **extra,
)
