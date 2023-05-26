"""
Private logic for creating pydantic dataclasses.
"""
from __future__ import annotations as _annotations

import dataclasses
import typing
import warnings
from functools import partial, wraps
from typing import Any, Callable, ClassVar

from pydantic_core import ArgsKwargs, SchemaSerializer, SchemaValidator, core_schema
from typing_extensions import TypeGuard

from ..errors import PydanticUndefinedAnnotation
from ..fields import FieldInfo
from . import _config, _decorators, _typing_extra
from ._core_utils import flatten_schema_defs, inline_schema_defs
from ._fields import collect_dataclass_fields
from ._generate_schema import GenerateSchema
from ._generics import get_standard_typevars_map
from ._model_construction import MockValidator
from ._schema_generation_shared import CallbackGetCoreSchemaHandler

if typing.TYPE_CHECKING:
    from ..config import ConfigDict

    class StandardDataclass(typing.Protocol):
        __dataclass_fields__: ClassVar[dict[str, Any]]
        __dataclass_params__: ClassVar[Any]  # in reality `dataclasses._DataclassParams`
        __post_init__: ClassVar[Callable[..., None]]

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

    class PydanticDataclass(StandardDataclass, typing.Protocol):
        __pydantic_core_schema__: typing.ClassVar[core_schema.CoreSchema]
        __pydantic_validator__: typing.ClassVar[SchemaValidator]
        __pydantic_serializer__: typing.ClassVar[SchemaSerializer]
        __pydantic_decorators__: typing.ClassVar[_decorators.DecoratorInfos]
        """metadata for `@field_validator`, `@root_validator` and `@serializer` decorators"""
        __pydantic_fields__: typing.ClassVar[dict[str, FieldInfo]]
        __pydantic_config__: typing.ClassVar[ConfigDict]
        __pydantic_complete__: typing.ClassVar[bool]


def set_dataclass_fields(cls: type[StandardDataclass], types_namespace: dict[str, Any] | None = None) -> None:
    """
    Collect and set `cls.__pydantic_fields__`
    """
    typevars_map = get_standard_typevars_map(cls)
    fields = collect_dataclass_fields(cls, types_namespace, typevars_map=typevars_map)

    cls.__pydantic_fields__ = fields  # type: ignore


def complete_dataclass(
    cls: type[Any],
    config_wrapper: _config.ConfigWrapper,
    *,
    raise_errors: bool = True,
    types_namespace: dict[str, Any] | None,
) -> bool:
    """
    Finish building a pydantic dataclass.

    This logic is called on a class which is yet to be wrapped in `dataclasses.dataclass()`.

    This is somewhat analogous to `pydantic._internal._model_construction.complete_model_class`.
    """
    if hasattr(cls, '__post_init_post_parse__'):
        warnings.warn(
            'Support for `__post_init_post_parse__` has been dropped, the method will not be called', DeprecationWarning
        )

    if types_namespace is None:
        types_namespace = _typing_extra.get_cls_types_namespace(cls)

    set_dataclass_fields(cls, types_namespace)

    typevars_map = get_standard_typevars_map(cls)
    gen_schema = GenerateSchema(
        config_wrapper,
        types_namespace,
        typevars_map,
    )

    # dataclass.__init__ must be defined here so its `__qualname__` can be changed since functions can't be copied.

    def __init__(__dataclass_self__: PydanticDataclass, *args: Any, **kwargs: Any) -> None:
        __tracebackhide__ = True
        s = __dataclass_self__
        s.__pydantic_validator__.validate_python(ArgsKwargs(args, kwargs), self_instance=s)

    __init__.__qualname__ = f'{cls.__qualname__}.__init__'
    cls.__init__ = __init__  # type: ignore
    cls.__pydantic_config__ = config_wrapper.config_dict  # type: ignore

    get_core_schema = getattr(cls, '__get_pydantic_core_schema__', None)
    try:
        if get_core_schema:
            schema = get_core_schema(
                cls,
                CallbackGetCoreSchemaHandler(
                    partial(gen_schema.generate_schema, from_dunder_get_core_schema=False),
                    gen_schema.generate_schema,
                ),
            )
        else:
            schema = gen_schema.generate_schema(cls, from_dunder_get_core_schema=False)
    except PydanticUndefinedAnnotation as e:
        cls_name = cls.__name__
        if raise_errors:
            raise
        undefined_type_error_message = (
            f'`{cls_name}` is not fully defined; you should define `{e.name}`,'
            f' then call `pydantic.dataclasses.rebuild_dataclass({cls_name})`'
            f' before the first `{cls_name}` instance is created.'
        )

        def attempt_rebuild() -> SchemaValidator | None:
            from ..dataclasses import rebuild_dataclass

            if rebuild_dataclass(cls, raise_errors=False, _parent_namespace_depth=5):
                return cls.__pydantic_validator__  # type: ignore
            else:
                return None

        cls.__pydantic_validator__ = MockValidator(  # type: ignore[assignment]
            undefined_type_error_message, code='class-not-fully-defined', attempt_rebuild=attempt_rebuild
        )
        return False

    core_config = config_wrapper.core_config(cls)

    # We are about to set all the remaining required properties expected for this cast;
    # __pydantic_decorators__ and __pydantic_fields__ should already be set
    cls = typing.cast('type[PydanticDataclass]', cls)
    # debug(schema)
    cls.__pydantic_core_schema__ = schema
    simplified_core_schema = inline_schema_defs(flatten_schema_defs(schema))
    cls.__pydantic_validator__ = validator = SchemaValidator(simplified_core_schema, core_config)
    cls.__pydantic_serializer__ = SchemaSerializer(simplified_core_schema, core_config)

    if config_wrapper.validate_assignment:

        @wraps(cls.__setattr__)
        def validated_setattr(instance: Any, __field: str, __value: str) -> None:
            validator.validate_assignment(instance, __field, __value)

        cls.__setattr__ = validated_setattr.__get__(None, cls)  # type: ignore

    return True


def is_builtin_dataclass(_cls: type[Any]) -> TypeGuard[type[StandardDataclass]]:
    """
    Whether a class is a stdlib dataclass
    (useful to discriminated a pydantic dataclass that is actually a wrapper around a stdlib dataclass)

    we check that
    - `_cls` is a dataclass
    - `_cls` is not a processed pydantic dataclass (with a basemodel attached)
    - `_cls` is not a pydantic dataclass inheriting directly from a stdlib dataclass
    e.g.
    ```py
    @dataclasses.dataclass
    class A:
        x: int

    @pydantic.dataclasses.dataclass
    class B(A):
        y: int
    ```
    In this case, when we first check `B`, we make an extra check and look at the annotations ('y'),
    which won't be a superset of all the dataclass fields (only the stdlib fields i.e. 'x')
    """
    return (
        dataclasses.is_dataclass(_cls)
        and not hasattr(_cls, '__pydantic_validator__')
        and set(_cls.__dataclass_fields__).issuperset(set(getattr(_cls, '__annotations__', {})))
    )


def is_pydantic_dataclass(_cls: type[Any]) -> TypeGuard[type[PydanticDataclass]]:
    return dataclasses.is_dataclass(_cls) and '__pydantic_validator__' in _cls.__dict__
