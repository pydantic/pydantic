"""
Private logic for creating pydantic datacalsses.
"""
from __future__ import annotations as _annotations

import typing
from copy import copy
from typing import Any, Callable, ClassVar

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema

from ..errors import PydanticUndefinedAnnotation
from ..fields import FieldInfo
from ._decorators import SerializationFunctions, ValidationFunctions
from ._fields import collect_fields
from ._generate_schema import dataclass_fields_schema, generate_config
from ._model_construction import MockValidator, object_setattr

__all__ = 'StandardDataclass', 'PydanticDataclass', 'prepare_dataclass'

if typing.TYPE_CHECKING:
    from ..config import BaseConfig

    class StandardDataclass(typing.Protocol):
        __dataclass_fields__: ClassVar[dict[str, Any]]
        __dataclass_params__: ClassVar[Any]  # in reality `dataclasses._DataclassParams`
        __post_init__: ClassVar[Callable[..., None]]

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

    class PydanticDataclass(StandardDataclass):
        __pydantic_validator__: typing.ClassVar[SchemaValidator]
        __pydantic_core_schema__: typing.ClassVar[core_schema.CoreSchema]
        __pydantic_serializer__: typing.ClassVar[SchemaSerializer]
        __pydantic_validator_functions__: typing.ClassVar[ValidationFunctions]
        __pydantic_serializer_functions__: typing.ClassVar[SerializationFunctions]
        __pydantic_fields__: typing.ClassVar[dict[str, FieldInfo]]
        # __pydantic_run_validation__: ClassVar[bool]
        # __post_init_post_parse__: ClassVar[Callable[..., None]]
        # __pydantic_initialised__: ClassVar[bool]
        # __pydantic_model__: ClassVar[type[BaseModel]]
        # __pydantic_validate_values__: ClassVar[Callable[['Dataclass'], None]]
        # __pydantic_has_field_info_default__: ClassVar[bool]  # whether a `pydantic.Field` is used as default value
        #
        #
        # @classmethod
        # def __get_validators__(cls: type['Dataclass']) -> 'CallableGenerator':
        #     pass
        #
        # @classmethod
        # def __validate__(cls: type['DataclassT'], v: Any) -> 'DataclassT':
        #     pass


def pydantic_dataclass_init(__dataclass_self__: PydanticDataclass, *args: Any, **kwargs: Any) -> None:
    v_args, v_kwargs = __dataclass_self__.__pydantic_validator__.validate_python(
        {'__args__': args, '__kwargs__': kwargs}
    )

    # TODO this is a slow workaround until get get https://github.com/pydantic/pydantic-core/issues/381
    if v_args:
        args_dict = {f: a for a, f in zip(v_args, __dataclass_self__.__pydantic_fields__.keys())}
        v_kwargs = {**args_dict, **kwargs}
    object_setattr(__dataclass_self__, '__dict__', v_kwargs)


def pydantic_dataclass_init_post(__dataclass_self__: PydanticDataclass, *args: Any, **kwargs: Any) -> None:
    pydantic_dataclass_init(__dataclass_self__, *args, **kwargs)
    # TODO support InitVar
    __dataclass_self__.__post_init__()


def prepare_dataclass(
    cls: type[Any],
    config: type[BaseConfig],
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
    name = cls.__name__
    bases = cls.__bases__
    try:
        fields, model_ref = collect_fields(cls, name, bases, types_namespace)
    except PydanticUndefinedAnnotation as e:
        if raise_errors:
            raise
        warning_string = f'`{name}` is not fully defined, you should define `{e}`, then call `{name}.model_rebuild()`'
        if config.undefined_types_warning:
            raise UserWarning(warning_string)
        cls.__pydantic_validator__ = MockValidator(warning_string)
        return False

    cls.__pydantic_validator_functions__ = validator_functions = ValidationFunctions(bases)
    cls.__pydantic_serializer_functions__ = serializer_functions = SerializationFunctions(bases)
    validator_functions.set_bound_functions(cls)
    serializer_functions.set_bound_functions(cls)

    inner_schema = dataclass_fields_schema(
        model_ref,
        fields,
        'keyword_only' if kw_only else 'positional_or_keyword',
        validator_functions,
        serializer_functions,
        config.arbitrary_types_allowed,
        types_namespace,
    )
    validator_functions.check_for_unused()
    serializer_functions.check_for_unused()

    core_config = generate_config(config, cls)
    cls.__pydantic_fields__ = fields
    cls.__pydantic_validator__ = SchemaValidator(inner_schema, core_config)

    dc_init = copy(pydantic_dataclass_init_post) if hasattr(cls, '__post_init__') else copy(pydantic_dataclass_init)
    dc_init.__name__ = '__init__'
    dc_init.__qualname__ = f'{cls.__qualname__}.__init__'
    setattr(cls, '__init__', dc_init)
    # cls.__pydantic_core_schema__ = outer_schema = core_schema.model_schema(
    #     cls, inner_schema,
    #     config=core_config,
    #     # call_after_init=model_post_init
    # )
    # cls.__pydantic_serializer__ = SchemaSerializer(outer_schema, core_config)

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
