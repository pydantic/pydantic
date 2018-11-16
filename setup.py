import re
from importlib.machinery import SourceFileLoader
from pathlib import Path
from setuptools import setup


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
        return '\n\n' + '\n'.join(self.links) + '\n'


description = 'Data validation and settings management using python 3.6 type hinting'
THIS_DIR = Path(__file__).resolve().parent
try:
    history = THIS_DIR.joinpath('HISTORY.rst').read_text()

    replacer = ReplaceLinks()
    history = re.sub(r'#(\d+)', replacer.replace_issues, history)
    history = re.sub(r'( +)@(\w+)', replacer.replace_users, history, flags=re.I)
    history = re.sub(r'@@', '@', history)
    history += replacer.extra()

    long_description = '\n\n'.join([THIS_DIR.joinpath('README.rst').read_text(), history])
except FileNotFoundError:
    long_description = description + '.\n\nSee https://pydantic-docs.helpmanual.io/ for documentation.'

# avoid loading the package before requirements are installed:
version = SourceFileLoader('version', 'pydantic/version.py').load_module()

setup(
    name='pydantic',
    version=str(version.VERSION),
    description=description,
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Environment :: MacOS X',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
    ],
    author='Samuel Colvin',
    author_email='s@muelcolvin.com',
    url='https://github.com/samuelcolvin/pydantic',
    license='MIT',
    packages=['pydantic'],
    python_requires='>=3.6',
    zip_safe=True,
    install_requires=[
        'dataclasses>=0.6;python_version<"3.7"'
    ],
    extras_require={
        'ujson': ['ujson>=1.35'],
        'email': ['email-validator>=1.0.3'],
    }
)
