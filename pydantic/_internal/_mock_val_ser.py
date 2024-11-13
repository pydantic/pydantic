from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Generic, Iterator, Mapping, TypeVar, Union

from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator
from typing_extensions import Literal, TypedDict

from ..errors import PydanticErrorCodes, PydanticUserError
from ..plugin._schema_validator import PluggableSchemaValidator

if TYPE_CHECKING:
    from ..dataclasses import PydanticDataclass
    from ..main import BaseModel
    from ..type_adapter import TypeAdapter


ValSer = TypeVar('ValSer', bound=Union[SchemaValidator, PluggableSchemaValidator, SchemaSerializer])
T = TypeVar('T')
R = TypeVar('R')


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


def _attempt_rebuild_fn(
    cls_: T, attr_fn: Callable[[T], R], rebuild_fn: Callable[[T], Callable[..., bool | None]]
) -> Callable[[], R | None]:
    def handler() -> R | None:
        if rebuild_fn(cls_)(raise_errors=False, _parent_namespace_depth=5) is not False:
            return attr_fn(cls_)
        return None

    return handler


class CoreAttrLookup(TypedDict):
    core_schema: str
    validator: str
    serializer: str


def _set_mocks(
    cls_: T, rebuild_fn: Callable[[T], Callable[..., bool | None]], core_attr_lookup: CoreAttrLookup, error_message: str
) -> None:
    core_schema_attr = core_attr_lookup['core_schema']
    core_schema = MockCoreSchema(
        error_message,
        code='class-not-fully-defined',
        attempt_rebuild=_attempt_rebuild_fn(
            cls_=cls_, attr_fn=lambda x: getattr(x, core_schema_attr), rebuild_fn=rebuild_fn
        ),
    )
    setattr(cls_, core_schema_attr, core_schema)

    validator_attr = core_attr_lookup['validator']
    validator = MockValSer(
        error_message,
        code='class-not-fully-defined',
        val_or_ser='validator',
        attempt_rebuild=_attempt_rebuild_fn(
            cls_=cls_, attr_fn=lambda x: getattr(x, validator_attr), rebuild_fn=rebuild_fn
        ),
    )
    setattr(cls_, validator_attr, validator)

    serializer_attr = core_attr_lookup['serializer']
    serializer = MockValSer(
        error_message,
        code='class-not-fully-defined',
        val_or_ser='serializer',
        attempt_rebuild=_attempt_rebuild_fn(
            cls_=cls_, attr_fn=lambda x: getattr(x, serializer_attr), rebuild_fn=rebuild_fn
        ),
    )
    setattr(cls_, serializer_attr, serializer)


def set_type_adapter_mocks(adapter: TypeAdapter, type_repr: str) -> None:
    """Set `core_schema`, `validator` and `serializer` to mock core types on a type adapter instance.

    Args:
        adapter: The type adapter instance to set the mocks on
        type_repr: Name of the type used in the adapter, used in error messages
    """
    _set_mocks(
        cls_=adapter,
        rebuild_fn=lambda ta: ta.rebuild,
        core_attr_lookup={'core_schema': 'core_schema', 'validator': 'validator', 'serializer': 'serializer'},
        error_message=(
            f'`TypeAdapter[{type_repr}]` is not fully defined; you should define `{type_repr}` and all referenced types,'
            f' then call `.rebuild()` on the instance.'
        ),
    )


def set_model_mocks(cls: type[BaseModel], cls_name: str, undefined_name: str = 'all referenced types') -> None:
    """Set `__pydantic_core_schema__`, `__pydantic_validator__` and `__pydantic_serializer__` to mock core types on a model.

    Args:
        cls: The model class to set the mocks on
        cls_name: Name of the model class, used in error messages
        undefined_name: Name of the undefined thing, used in error messages
    """
    _set_mocks(
        cls_=cls,
        rebuild_fn=lambda bm: bm.model_rebuild,
        core_attr_lookup={
            'core_schema': '__pydantic_core_schema__',
            'validator': '__pydantic_validator__',
            'serializer': '__pydantic_serializer__',
        },
        error_message=(
            f'`{cls_name}` is not fully defined; you should define {undefined_name},'
            f' then call `{cls_name}.model_rebuild()`.'
        ),
    )


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

    _set_mocks(
        cls_=cls,
        rebuild_fn=lambda d: partial(rebuild_dataclass, cls=d),
        core_attr_lookup={
            'core_schema': '__pydantic_core_schema__',
            'validator': '__pydantic_validator__',
            'serializer': '__pydantic_serializer__',
        },
        error_message=(
            f'`{cls_name}` is not fully defined; you should define {undefined_name},'
            f' then call `pydantic.dataclasses.rebuild_dataclass({cls_name})`.'
        ),
    )
