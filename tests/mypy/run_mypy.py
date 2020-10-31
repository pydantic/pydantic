import sys

from mypy import api as mypy_api

if __name__ == '__main__':
    stdout, stderr, exit_status = mypy_api.run(['tests/mypy/modules/plugin_success.py', '--config-file', 'tests/mypy/configs/mypy-plugin.ini', '--cache-dir', '.mypy_cache/test-mypy-plugin', '--show-error-codes'])
    print(stdout, end='')
    print(stderr, file=sys.stderr)
    exit(exit_status)
