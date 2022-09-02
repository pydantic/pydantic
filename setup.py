import re
from importlib.machinery import SourceFileLoader
from pathlib import Path

from setuptools import setup


class ReplaceLinks:
    def __init__(self):
        self.links = set()

    def replace_issues(self, m):
        id = m.group(1)
        self.links.add(f'.. _#{id}: https://github.com/pydantic/pydantic/issues/{id}')
        return f'`#{id}`_'

    def replace_users(self, m):
        name = m.group(2)
        self.links.add(f'.. _@{name}: https://github.com/{name}')
        return f'{m.group(1)}`@{name}`_'

    def extra(self):
        return '\n\n' + '\n'.join(sorted(self.links)) + '\n'


description = 'Data validation and settings management using python type hints'
THIS_DIR = Path(__file__).resolve().parent
try:
    history = (THIS_DIR / 'HISTORY.md').read_text(encoding='utf-8')
    history = re.sub(r'#(\d+)', r'[#\1](https://github.com/pydantic/pydantic/issues/\1)', history)
    history = re.sub(r'( +)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.I)
    history = re.sub('@@', '@', history)

    long_description = (THIS_DIR / 'README.md').read_text(encoding='utf-8') + '\n\n' + history
except FileNotFoundError:
    long_description = description + '.\n\nSee https://pydantic-docs.helpmanual.io/ for documentation.'

# avoid loading the package before requirements are installed:
version = SourceFileLoader('version', 'pydantic/version.py').load_module()

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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Framework :: Hypothesis',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
    ],
    author='Samuel Colvin',
    author_email='s@muelcolvin.com',
    url='https://github.com/pydantic/pydantic',
    license='MIT',
    packages=['pydantic'],
    package_data={'pydantic': ['py.typed']},
    python_requires='>=3.7',
    zip_safe=False,  # https://mypy.readthedocs.io/en/latest/installed_packages.html
    install_requires=[
        'typing-extensions>=4.1.0'
    ],
    extras_require={
        'email': ['email-validator>=1.0.3'],
        'dotenv': ['python-dotenv>=0.10.4'],
    },
    entry_points={'hypothesis': ['_ = pydantic._hypothesis_plugin']},
)
