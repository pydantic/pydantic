from typing import Any

MYPY = 1

if MYPY:
    from typing_extensions import TypeAlias

    def _anything() -> Any:
        pass

    CoreSchema: TypeAlias = _anything()  # type: ignore[valid-type]
    CoreSchemaType: TypeAlias = _anything()  # type: ignore[valid-type]
    TypedDictField: TypeAlias = _anything()  # type: ignore[valid-type]

    def __getattr__(name: str) -> Any:
        raise RuntimeError('this should never be called')

else:
    from pydantic_core.core_schema import *  # noqa: F403
