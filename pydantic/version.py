__all__ = 'VERSION', 'version_info'

VERSION = '2.0b2'


def version_info() -> str:
    import platform
    import sys
    from importlib import import_module
    from pathlib import Path

    import pydantic_core._pydantic_core as pdc

    optional_deps = []
    for p in 'devtools', 'email-validator', 'typing-extensions':
        try:
            import_module(p.replace('-', '_'))
        except ImportError:  # pragma: no cover
            continue
        optional_deps.append(p)

    info = {
        'pydantic version': VERSION,
        'pydantic-core version': f'{pdc.__version__} {pdc.build_profile} build profile',
        'install path': Path(__file__).resolve().parent,
        'python version': sys.version,
        'platform': platform.platform(),
        'optional deps. installed': optional_deps,
    }
    return '\n'.join('{:>30} {}'.format(k + ':', str(v).replace('\n', ' ')) for k, v in info.items())
