__all__ = 'VERSION', 'version_info'

VERSION = '1.6.1'


def version_info() -> str:
    import platform
    import sys
    from importlib import import_module
    from pathlib import Path

    from .main import compiled

    optional_deps = []
    for p in ('typing-extensions', 'email-validator', 'devtools'):
        try:
            import_module(p.replace('-', '_'))
        except ImportError:
            continue
        optional_deps.append(p)

    info = {
        'pydantic version': VERSION,
        'pydantic compiled': compiled,
        'install path': Path(__file__).resolve().parent,
        'python version': sys.version,
        'platform': platform.platform(),
        'optional deps. installed': optional_deps,
    }
    return '\n'.join('{:>30} {}'.format(k + ':', str(v).replace('\n', ' ')) for k, v in info.items())
