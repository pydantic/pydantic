__all__ = 'VERSION', 'version_info'

VERSION = '1.8.2'


def version_info() -> str:
    import platform
    import sys
    from importlib import import_module
    from pathlib import Path

    from .main import compiled

    optional_deps = []
    for p in ('devtools', 'dotenv', 'email-validator', 'typing-extensions'):
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
