## pydantic.__version__

```python
__version__ = VERSION

```

## pydantic.version.version_info

```python
version_info() -> str

```

Return complete version information for Pydantic and its dependencies.

Source code in `pydantic/version.py`

```python
def version_info() -> str:
    """Return complete version information for Pydantic and its dependencies."""
    import importlib.metadata
    import platform
    from pathlib import Path

    import pydantic_core._pydantic_core as pdc

    from ._internal import _git as git

    # get data about packages that are closely related to pydantic, use pydantic or often conflict with pydantic
    package_names = {
        'email-validator',
        'fastapi',
        'mypy',
        'pydantic-extra-types',
        'pydantic-settings',
        'pyright',
        'typing_extensions',
    }
    related_packages = []

    for dist in importlib.metadata.distributions():
        name = dist.metadata['Name']
        if name in package_names:
            related_packages.append(f'{name}-{dist.version}')

    pydantic_dir = Path(__file__).parents[1].resolve()
    most_recent_commit = (
        git.git_revision(pydantic_dir) if git.is_git_repo(pydantic_dir) and git.have_git() else 'unknown'
    )

    info = {
        'pydantic version': VERSION,
        'pydantic-core version': __pydantic_core_version__,
        'pydantic-core build': getattr(pdc, 'build_info', None) or pdc.build_profile,  # pyright: ignore[reportPrivateImportUsage]
        'python version': sys.version,
        'platform': platform.platform(),
        'related packages': ' '.join(related_packages),
        'commit': most_recent_commit,
    }
    return '\n'.join('{:>30} {}'.format(k + ':', str(v).replace('\n', ' ')) for k, v in info.items())

```
