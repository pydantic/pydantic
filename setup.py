import sys

sys.stderr.write(
    """
===============================
Unsupported installation method
===============================
pydantic no longer supports installation with `python setup.py install`.
Please use `python -m pip install .` instead.
"""
)
sys.exit(1)


# The below code will never execute, however GitHub is particularly
# picky about where it finds Python packaging metadata.
# See: https://github.com/github/feedback/discussions/6456
#
# To be removed once GitHub catches up.

setup(
    name='pydantic',
    install_requires=[
        'typing-extensions>=4.1.0',
        'pydantic-core>=0.7.1',
        'annotated-types>=0.4.0'
    ],
)
