from __future__ import annotations

from functools import partialmethod
from typing import TYPE_CHECKING, Any, Callable, TypeVar, Union, overload

from pydantic_core import core_schema
from pydantic_core import core_schema as _core_schema
from typing_extensions import Literal, TypeAlias

from ._internal import _annotated_handlers, _decorators, _internal_dataclass


@_internal_dataclass.slots_dataclass(frozen=True)
class PlainSerializer:
    """
    Plain serializers use a function to modify the output of serialization.

    Attributes:
        func (core_schema.SerializerFunction): The serializer function.
        return_type: Optional return type for the function, if omitted it will be inferred from the type annotation.
        when_used (Literal['always', 'unless-none', 'json', 'json-unless-none'], optional): The serialization condition.
            Defaults to 'always'.
    """

    func: core_schema.SerializerFunction
    return_type: Any = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: _annotated_handlers.GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Gets the Pydantic core schema.

        Args:
            source_type: The source type.
            handler: The `GetCoreSchemaHandler` instance.

        Returns:
            The Pydantic core schema.
        """
        schema = handler(source_type)
        return_type = _decorators.get_function_return_type(self.func, self.return_type)
        return_schema = None if return_type is None else handler.generate_schema(return_type)
        schema['serialization'] = core_schema.plain_serializer_function_ser_schema(
            function=self.func,
            info_arg=_decorators.inspect_annotated_serializer(self.func, 'plain'),
            return_schema=return_schema,
            when_used=self.when_used,
        )
        return schema


@_internal_dataclass.slots_dataclass(frozen=True)
class WrapSerializer:
    """
    Wrap serializers receive the raw inputs along with a handler function that applies the standard serialization logic,
    and can modify the resulting value before returning it as the final output of serialization.

    Attributes:
        func (core_schema.WrapSerializerFunction): The function to be wrapped.
        return_type: Optional return type for the function, if omitted it will be inferred from the type annotation.
        when_used: Determines the serializer will be used for serialization.
    """

    func: core_schema.WrapSerializerFunction
    return_type: Any = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: _annotated_handlers.GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        This method is used to get the Pydantic core schema of the class.

        Args:
            source_type: Source type.
            handler: Core schema handler.

        Returns:
            The generated core schema of the class.
        """
        schema = handler(source_type)
        return_type = _decorators.get_function_return_type(self.func, self.return_type)
        return_schema = None if return_type is None else handler.generate_schema(return_type)
        schema['serialization'] = core_schema.wrap_serializer_function_ser_schema(
            function=self.func,
            info_arg=_decorators.inspect_annotated_serializer(self.func, 'wrap'),
            return_schema=return_schema,
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
    return_type: Any = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_PlainSerializeMethodType], _PlainSerializeMethodType]:
    ...


@overload
def field_serializer(
    __field: str,
    *fields: str,
    mode: Literal['plain'],
    return_type: Any = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_PlainSerializeMethodType], _PlainSerializeMethodType]:
    ...


@overload
def field_serializer(
    __field: str,
    *fields: str,
    mode: Literal['wrap'],
    return_type: Any = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_WrapSerializeMethodType], _WrapSerializeMethodType]:
    ...


def field_serializer(
    *fields: str,
    mode: Literal['plain', 'wrap'] = 'plain',
    return_type: Any = None,
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
        fields: Which field(s) the method should be called on.
        mode: `plain` means the function will be called instead of the default serialization logic,
            `wrap` means the function will be called with an argument to optionally call the
            default serialization logic.
        return_type: Optional return type for the function, if omitted it will be inferred from the type annotation.
        when_used: Determines the serializer will be used for serialization.
        check_fields (bool): Whether to check that the fields actually exist on the model.

    Returns:
        A decorator that can be used to decorate a function to be used as a field serializer.
    """

    def dec(
        f: Callable[..., Any] | staticmethod[Any, Any] | classmethod[Any, Any, Any]
    ) -> _decorators.PydanticDescriptorProxy[Any]:
        dec_info = _decorators.FieldSerializerDecoratorInfo(
            fields=fields,
            mode=mode,
            return_type=_decorators.get_function_return_type(f, return_type),
            when_used=when_used,
            check_fields=check_fields,
        )
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    return dec


FuncType = TypeVar('FuncType', bound=Callable[..., Any])


@overload
def model_serializer(__f: FuncType) -> FuncType:
    ...


@overload
def model_serializer(
    *,
    mode: Literal['plain', 'wrap'] = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always',
    return_type: Any = ...,
) -> Callable[[FuncType], FuncType]:
    ...


def model_serializer(
    __f: Callable[..., Any] | None = None,
    *,
    mode: Literal['plain', 'wrap'] = 'plain',
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always',
    return_type: Any = None,
) -> Callable[[Any], Any]:
    """
    Decorate a function which will be called to serialize the model.

    (`when_used` is not permitted here since it makes no sense.)

    Args:
        __f: The function to be decorated.
        mode: The serialization mode. `'plain'` means the function will be called
            instead of the default serialization logic, `'wrap'` means the function will be called with an argument
            to optionally call the default serialization logic.
        when_used: Determines the serializer will be be used for serialization.
        return_type: Optional return type for the function, if omitted it will be inferred from the type annotation.

    Returns:
        A decorator that can be used to decorate a function to be used as a model serializer.
    """

    def dec(f: Callable[..., Any]) -> _decorators.PydanticDescriptorProxy[Any]:
        dec_info = _decorators.ModelSerializerDecoratorInfo(
            mode=mode, return_type=_decorators.get_function_return_type(f, return_type), when_used=when_used
        )
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    if __f is None:
        return dec
    else:
        return dec(__f)  # type: ignore
