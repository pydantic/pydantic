def test_explicit_reexports() -> None:
    from pydantic import __all__ as root_all
    from pydantic.deprecated.tools import __all__ as tools
    from pydantic.main import __all__ as main
    from pydantic.networks import __all__ as networks
    from pydantic.types import __all__ as types

    for name, export_all in [('main', main), ('networks', networks), ('deprecated.tools', tools), ('types', types)]:
        for export in export_all:
            assert export in root_all, f'{export} is in `pydantic.{name}.__all__` but missing in `pydantic.__all__`'


def test_explicit_reexports_exist() -> None:
    import pydantic

    for name in pydantic.__all__:
        assert hasattr(pydantic, name), f'{name} is in `pydantic.__all__` but `from pydantic import {name}` fails'
