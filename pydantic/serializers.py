from __future__ import annotations

from functools import partialmethod
from typing import TYPE_CHECKING, Any, Callable, TypeVar, Union, overload

from pydantic_core import core_schema
from pydantic_core import core_schema as _core_schema
from typing_extensions import Literal, TypeAlias

from ._internal import _decorators
from ._internal._decorators import inspect_annotated_serializer
from ._internal._internal_dataclass import slots_dataclass
from .annotated import GetCoreSchemaHandler


@slots_dataclass(frozen=True)
class PlainSerializer:
    func: core_schema.SerializerFunction
    json_return_type: core_schema.JsonReturnTypes | None = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        schema['serialization'] = core_schema.plain_serializer_function_ser_schema(
            function=self.func,
            info_arg=inspect_annotated_serializer(self.func, 'plain'),
            json_return_type=self.json_return_type,
            when_used=self.when_used,
        )
        return schema


@slots_dataclass(frozen=True)
class WrapSerializer:
    func: core_schema.WrapSerializerFunction
    json_return_type: core_schema.JsonReturnTypes | None = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        schema['serialization'] = core_schema.wrap_serializer_function_ser_schema(
            function=self.func,
            info_arg=inspect_annotated_serializer(self.func, 'wrap'),
            json_return_type=self.json_return_type,
            when_used=self.when_used,
        )
        return schema


if TYPE_CHECKING:
    _PartialClsOrStaticMethod: TypeAlias = Union[classmethod[Any, Any, Any], staticmethod[Any, Any], partialmethod[Any]]
    _PlainSerializationFunction = Union[_core_schema.SerializerFunction, _PartialClsOrStaticMethod]
    _WrapSerializationFunction = Union[_core_schema.WrapSerializerFunction, _PartialClsOrStaticMethod]
    _PlainSerializeMethodType = TypeVar('_PlainSerializeMethodType', bound=_PlainSerializationFunction)
    _WrapSerializeMethodType = TypeVar('_WrapSerializeMethodType', bound=_WrapSerializationFunction)


@overload
def field_serializer(
    __field: str,
    *fields: str,
    json_return_type: _core_schema.JsonReturnTypes | None = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_PlainSerializeMethodType], _PlainSerializeMethodType]:
    ...


@overload
def field_serializer(
    __field: str,
    *fields: str,
    mode: Literal['plain'],
    json_return_type: _core_schema.JsonReturnTypes | None = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_PlainSerializeMethodType], _PlainSerializeMethodType]:
    ...


@overload
def field_serializer(
    __field: str,
    *fields: str,
    mode: Literal['wrap'],
    json_return_type: _core_schema.JsonReturnTypes | None = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_WrapSerializeMethodType], _WrapSerializeMethodType]:
    ...


def field_serializer(
    *fields: str,
    mode: Literal['plain', 'wrap'] = 'plain',
    json_return_type: _core_schema.JsonReturnTypes | None = None,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always',
    check_fields: bool | None = None,
) -> Callable[[Any], Any]:
    """
    Decorate methods on the class indicating that they should be used to serialize fields.

    Four signatures are supported:

    - `(self, value: Any, info: FieldSerializationInfo)`
    - `(self, value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo)`
    - `(value: Any, info: SerializationInfo)`
    - `(value: Any, nxt: SerializerFunctionWrapHandler, info: SerializationInfo)`

    Args:
        fields (str): Which field(s) the method should be called on.
        mode (str): `plain` means the function will be called instead of the default serialization logic,
            `wrap` means the function will be called with an argument to optionally call the
            default serialization logic.
        json_return_type (str): The type that the function returns if the serialization mode is JSON.
        when_used (str): When the function should be called.
        check_fields (bool): Whether to check that the fields actually exist on the model.

    Returns:
        Callable: A decorator that can be used to decorate a function to be used as a field serializer.
    """

    def dec(
        f: Callable[..., Any] | staticmethod[Any, Any] | classmethod[Any, Any, Any]
    ) -> _decorators.PydanticDescriptorProxy[Any]:
        dec_info = _decorators.FieldSerializerDecoratorInfo(
            fields=fields,
            mode=mode,
            json_return_type=json_return_type,
            when_used=when_used,
            check_fields=check_fields,
        )
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    return dec


def model_serializer(
    __f: Callable[..., Any] | None = None,
    *,
    mode: Literal['plain', 'wrap'] = 'plain',
    json_return_type: _core_schema.JsonReturnTypes | None = None,
) -> Callable[[Any], _decorators.PydanticDescriptorProxy[Any]] | _decorators.PydanticDescriptorProxy[Any]:
    """
    Decorate a function which will be called to serialize the model.

    (`when_used` is not permitted here since it makes no sense.)

    Args:
        __f (Callable[..., Any] | None): The function to be decorated.
        mode (Literal['plain', 'wrap']): The serialization mode. `'plain'` means the function will be called
            instead of the default serialization logic, `'wrap'` means the function will be called with an argument
            to optionally call the default serialization logic.
        json_return_type (_core_schema.JsonReturnTypes | None): The type that the function returns if the
            serialization mode is JSON.

    Returns:
        Callable: A decorator that can be used to decorate a function to be used as a model serializer.
    """

    def dec(f: Callable[..., Any]) -> _decorators.PydanticDescriptorProxy[Any]:
        dec_info = _decorators.ModelSerializerDecoratorInfo(mode=mode, json_return_type=json_return_type)
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    if __f is None:
        return dec
    else:
        return dec(__f)
