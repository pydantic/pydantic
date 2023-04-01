"""
Private logic for creating pydantic dataclasses.
"""
from __future__ import annotations as _annotations

import typing
import warnings
from functools import wraps
from typing import Any, Callable, ClassVar

from pydantic_core import ArgsKwargs, SchemaSerializer, SchemaValidator, core_schema

from ..config import ConfigDict
from ..errors import PydanticUndefinedAnnotation
from ..fields import FieldInfo
from . import _decorators
from ._core_utils import get_type_ref
from ._fields import collect_fields
from ._forward_ref import PydanticForwardRef
from ._generate_schema import dataclass_schema, generate_config
from ._model_construction import MockValidator

__all__ = 'StandardDataclass', 'PydanticDataclass', 'prepare_dataclass'

if typing.TYPE_CHECKING:

    class StandardDataclass(typing.Protocol):
        __dataclass_fields__: ClassVar[dict[str, Any]]
        __dataclass_params__: ClassVar[Any]  # in reality `dataclasses._DataclassParams`
        __post_init__: ClassVar[Callable[..., None]]

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

    class PydanticDataclass(StandardDataclass, typing.Protocol):
        __pydantic_validator__: typing.ClassVar[SchemaValidator]
        __pydantic_core_schema__: typing.ClassVar[core_schema.CoreSchema]
        __pydantic_serializer__: typing.ClassVar[SchemaSerializer]
        __pydantic_decorators__: typing.ClassVar[_decorators.DecoratorInfos]
        """metadata for `@validator`, `@root_validator` and `@serializer` decorators"""
        __pydantic_fields__: typing.ClassVar[dict[str, FieldInfo]]
        __pydantic_config__: typing.ClassVar[ConfigDict]


def prepare_dataclass(
    cls: type[Any],
    config: ConfigDict,
    kw_only: bool,
    *,
    raise_errors: bool = True,
    types_namespace: dict[str, Any] | None = None,
) -> bool:
    """
    Prepare a raw class to become a pydantic dataclass.

    Returns `True` if the validation construction is successfully completed, else `False`.

    This logic is called on a class which is yet to be wrapped in `dataclasses.dataclass()`.
    """
    if hasattr(cls, '__post_init_post_parse__'):
        warnings.warn(
            'Support for `__post_init_post_parse__` has been dropped, the method will not be called', DeprecationWarning
        )

    name = cls.__name__
    bases = cls.__bases__

    dataclass_ref = get_type_ref(cls)
    self_schema = core_schema.definition_reference_schema(dataclass_ref)
    types_namespace = {**(types_namespace or {}), name: PydanticForwardRef(self_schema, cls)}
    try:
        fields, _ = collect_fields(cls, bases, types_namespace, is_dataclass=True, dc_kw_only=kw_only)
    except PydanticUndefinedAnnotation as e:
        if raise_errors:
            raise
        warning_string = (
            f'`{name}` is not fully defined, you should define `{e}`, then call TODO! `methods.rebuild({name})`'
        )
        if config['undefined_types_warning']:
            raise UserWarning(warning_string)
        cls.__pydantic_validator__ = MockValidator(warning_string)
        return False

    decorators = cls.__pydantic_decorators__

    cls.__pydantic_core_schema__ = schema = dataclass_schema(
        cls,
        dataclass_ref,
        fields,
        decorators,
        config['arbitrary_types_allowed'],
        types_namespace,
    )

    core_config = generate_config(config, cls)
    cls.__pydantic_fields__ = fields
    cls.__pydantic_validator__ = validator = SchemaValidator(schema, core_config)
    # this works because cls has been transformed into a dataclass by the time "cls" is called
    cls.__pydantic_serializer__ = SchemaSerializer(schema, core_config)
    cls.__pydantic_config__ = config

    if config.get('validate_assignment'):

        @wraps(cls.__setattr__)
        def validated_setattr(instance: Any, __field: str, __value: str) -> None:
            validator.validate_assignment(instance, __field, __value)

        cls.__setattr__ = validated_setattr.__get__(None, cls)

    # dataclass.__init__ must be defined here so its `__qualname__` can be changed since functions can't copied.

    def __init__(__dataclass_self__: PydanticDataclass, *args: Any, **kwargs: Any) -> None:
        __tracebackhide__ = True
        s = __dataclass_self__
        s.__pydantic_validator__.validate_python(ArgsKwargs(args, kwargs), self_instance=s)

    __init__.__qualname__ = f'{cls.__qualname__}.__init__'
    cls.__init__ = __init__

    return True


def is_builtin_dataclass(_cls: type[Any]) -> bool:
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
    import dataclasses

    return (
        dataclasses.is_dataclass(_cls)
        and not hasattr(_cls, '__pydantic_validator__')
        and set(_cls.__dataclass_fields__).issuperset(set(getattr(_cls, '__annotations__', {})))
    )
