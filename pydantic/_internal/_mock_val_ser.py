from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Generic, Iterator, Mapping, TypeAlias, TypeVar, Union

from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator
from typing_extensions import Literal, TypedDict

from ..errors import PydanticErrorCodes, PydanticUserError
from ..plugin._schema_validator import PluggableSchemaValidator

if TYPE_CHECKING:
    from ..dataclasses import PydanticDataclass
    from ..main import BaseModel
    from ..type_adapter import TypeAdapter

ValidatorOrSerializer: TypeAlias = Union[SchemaValidator, PluggableSchemaValidator, SchemaSerializer]
ValSer = TypeVar('ValSer', bound=ValidatorOrSerializer)


class MockCoreSchema(Mapping[str, Any]):
    """Mocker for `pydantic_core.CoreSchema` which optionally attempts to
    rebuild the thing it's mocking when one of its methods is accessed and raises an error if that fails.
    """

    __slots__ = '_error_message', '_code', '_attempt_rebuild', '_built_memo'

    def __init__(
        self,
        error_message: str,
        *,
        code: PydanticErrorCodes,
        attempt_rebuild: Callable[[], CoreSchema | None] | None = None,
    ) -> None:
        self._error_message = error_message
        self._code: PydanticErrorCodes = code
        self._attempt_rebuild = attempt_rebuild
        self._built_memo: CoreSchema | None = None

    def __getitem__(self, key: str) -> Any:
        return self._get_built().__getitem__(key)

    def __len__(self) -> int:
        return self._get_built().__len__()

    def __iter__(self) -> Iterator[str]:
        return self._get_built().__iter__()

    def _get_built(self) -> CoreSchema:
        if self._built_memo is not None:
            return self._built_memo

        if self._attempt_rebuild:
            schema = self._attempt_rebuild()
            if schema is not None:
                self._built_memo = schema
                return schema
        raise PydanticUserError(self._error_message, code=self._code)

    def rebuild(self) -> CoreSchema | None:
        self._built_memo = None
        if self._attempt_rebuild:
            schema = self._attempt_rebuild()
            if schema is not None:
                return schema
            else:
                raise PydanticUserError(self._error_message, code=self._code)
        return None


class MockValSer(Generic[ValSer]):
    """Mocker for `pydantic_core.SchemaValidator` or `pydantic_core.SchemaSerializer` which optionally attempts to
    rebuild the thing it's mocking when one of its methods is accessed and raises an error if that fails.
    """

    __slots__ = '_error_message', '_code', '_val_or_ser', '_attempt_rebuild'

    def __init__(
        self,
        error_message: str,
        *,
        code: PydanticErrorCodes,
        val_or_ser: Literal['validator', 'serializer'],
        attempt_rebuild: Callable[[], ValSer | None] | None = None,
    ) -> None:
        self._error_message = error_message
        self._val_or_ser = SchemaValidator if val_or_ser == 'validator' else SchemaSerializer
        self._code: PydanticErrorCodes = code
        self._attempt_rebuild = attempt_rebuild

    def __getattr__(self, item: str) -> None:
        __tracebackhide__ = True
        if self._attempt_rebuild:
            val_ser = self._attempt_rebuild()
            if val_ser is not None:
                return getattr(val_ser, item)

        # raise an AttributeError if `item` doesn't exist
        getattr(self._val_or_ser, item)
        raise PydanticUserError(self._error_message, code=self._code)

    def rebuild(self) -> ValSer | None:
        if self._attempt_rebuild:
            val_ser = self._attempt_rebuild()
            if val_ser is not None:
                return val_ser
            else:
                raise PydanticUserError(self._error_message, code=self._code)
        return None


MockContainer = TypeVar('MockContainer', bound=type[BaseModel] | TypeAdapter | type[PydanticDataclass])
RebuildReturnType = TypeVar('RebuildReturnType', bound=CoreSchema | ValidatorOrSerializer)


class CoreAttrLookup(TypedDict):
    core_schema: str
    validator: str
    serializer: str


class MockFactory(Generic[MockContainer]):
    """Factory for creating `MockCoreSchema`, `MockValSer` and `MockValSer` instances for a given type."""

    __slots__ = '_obj', '_error_message', '_rebuild', '_core_attr_lookup'

    def __init__(
        self,
        obj: MockContainer,
        error_message: str,
        rebuild: Callable[[MockContainer], Callable[..., bool | None]],
        core_attr_lookup: CoreAttrLookup,
    ) -> None:
        self._obj = obj
        self._error_message = error_message
        self._rebuild = rebuild
        self._core_attr_lookup = core_attr_lookup

    def _attempt_rebuild_fn(
        self, attr_fn: Callable[[MockContainer], RebuildReturnType]
    ) -> Callable[[], RebuildReturnType | None]:
        def attempt_rebuild() -> RebuildReturnType | None:
            if self._rebuild(self._obj)(_parent_namespace_depth=5) is not False:
                return attr_fn(self._obj)
            return None

        return attempt_rebuild

    def mock_core_schema(self) -> MockCoreSchema:
        return MockCoreSchema(
            self._error_message,
            code='class-not-fully-defined',
            attempt_rebuild=self._attempt_rebuild_fn(lambda x: getattr(x, self._core_attr_lookup['core_schema'])),
        )

    def mock_schema_validator(self) -> MockValSer:
        return MockValSer(
            self._error_message,
            code='class-not-fully-defined',
            val_or_ser='validator',
            attempt_rebuild=self._attempt_rebuild_fn(lambda x: getattr(x, self._core_attr_lookup['validator'])),
        )

    def mock_schema_serializer(self) -> MockValSer:
        return MockValSer(
            self._error_message,
            code='class-not-fully-defined',
            val_or_ser='serializer',
            attempt_rebuild=self._attempt_rebuild_fn(lambda x: getattr(x, self._core_attr_lookup['serializer'])),
        )

    def set_mocks(self) -> None:
        setattr(self._obj, self._core_attr_lookup['core_schema'], self.mock_core_schema())
        setattr(self._obj, self._core_attr_lookup['validator'], self.mock_schema_validator())
        setattr(self._obj, self._core_attr_lookup['serializer'], self.mock_schema_serializer())


type_adapter_attr_lookup: CoreAttrLookup = {
    'core_schema': 'core_schema',
    'validator': 'validator',
    'serializer': 'serializer',
}
model_attr_lookup: CoreAttrLookup = {
    'core_schema': '__pydantic_core_schema__',
    'validator': '__pydantic_validator__',
    'serializer': '__pydantic_serializer__',
}
dataclass_attr_lookup: CoreAttrLookup = {
    'core_schema': '__pydantic_core_schema__',
    'validator': '__pydantic_validator__',
    'serializer': '__pydantic_serializer__',
}


def set_type_adapter_mocks(adapter: TypeAdapter, type_repr: str) -> None:
    """Set `core_schema`, `validator` and `serializer` to mock core types on a type adapter instance.

    Args:
        adapter: The type adapter instance to set the mocks on
        type_repr: Name of the type used in the adapter, used in error messages
    """
    mock_factory = MockFactory[TypeAdapter](
        obj=adapter,
        error_message=(
            f'`TypeAdapter[{type_repr}]` is not fully defined; you should define `{type_repr}` and all referenced types,'
            f' then call `.rebuild()` on the instance.'
        ),
        rebuild=lambda ta: partial(ta.rebuild, raise_errors=False),
        core_attr_lookup=type_adapter_attr_lookup,
    )
    mock_factory.set_mocks()


def set_model_mocks(cls: type[BaseModel], cls_name: str, undefined_name: str = 'all referenced types') -> None:
    """Set `__pydantic_core_schema__`, `__pydantic_validator__` and `__pydantic_serializer__` to mock core types on a model.

    Args:
        cls: The model class to set the mocks on
        cls_name: Name of the model class, used in error messages
        undefined_name: Name of the undefined thing, used in error messages
    """
    mock_factory = MockFactory[type[BaseModel]](
        obj=cls,
        error_message=(
            f'`{cls_name}` is not fully defined; you should define {undefined_name},'
            f' then call `{cls_name}.model_rebuild()`.'
        ),
        rebuild=lambda c: partial(c.model_rebuild, raise_errors=False),
        core_attr_lookup=model_attr_lookup,
    )
    mock_factory.set_mocks()


def set_dataclass_mocks(
    cls: type[PydanticDataclass], cls_name: str, undefined_name: str = 'all referenced types'
) -> None:
    """Set `__pydantic_validator__` and `__pydantic_serializer__` to `MockValSer`s on a dataclass.

    Args:
        cls: The model class to set the mocks on
        cls_name: Name of the model class, used in error messages
        undefined_name: Name of the undefined thing, used in error messages
    """
    from ..dataclasses import rebuild_dataclass

    mock_factory = MockFactory[type[PydanticDataclass]](
        obj=cls,
        error_message=(
            f'`{cls_name}` is not fully defined; you should define {undefined_name},'
            f' then call `pydantic.dataclasses.rebuild_dataclass({cls_name})`.'
        ),
        rebuild=lambda c: partial(rebuild_dataclass, cls=c, raise_errors=False),
        core_attr_lookup=dataclass_attr_lookup,
    )
    mock_factory.set_mocks()
