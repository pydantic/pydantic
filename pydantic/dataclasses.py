"""Provide an enhanced dataclass that performs validation."""
from __future__ import annotations as _annotations

import dataclasses
import sys
import types
from typing import TYPE_CHECKING, Any, Callable, Generic, NoReturn, TypeVar

from typing_extensions import Literal, TypeGuard, dataclass_transform

from ._internal import _config, _decorators, _typing_extra
from ._internal import _dataclasses as _pydantic_dataclasses
from ._migration import getattr_migration
from .config import ConfigDict
from .errors import PydanticUserError
from .fields import Field, FieldInfo, PrivateAttr

if TYPE_CHECKING:
    from ._internal._dataclasses import PydanticDataclass

__all__ = 'dataclass', 'rebuild_dataclass'

_T = TypeVar('_T')

if sys.version_info >= (3, 10):

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    def dataclass(
        _cls: type[_T] | None = None,
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
        kw_only: bool = False,
        slots: bool = False,
    ) -> Callable[[type[_T]], type[PydanticDataclass]] | type[PydanticDataclass]:
        """Usage docs: https://docs.pydantic.dev/2.8/concepts/dataclasses/

        A decorator used to create a Pydantic-enhanced dataclass, similar to the standard Python `dataclass`,
        but with added validation.

        This function should be used similarly to `dataclasses.dataclass`.

        Args:
        _cls: The target `dataclass`.
        init: Included for signature compatibility with `dataclasses.dataclass`, and is passed through to
            `dataclasses.dataclass` when appropriate. If specified, must be set to `False`, as pydantic inserts its
            own  `__init__` function.
        repr: A boolean indicating whether to include the field in the `__repr__` output.
        eq: Determines if a `__eq__` method should be generated for the class.
        order: Determines if comparison magic methods should be generated, such as `__lt__`, but not `__eq__`.
        unsafe_hash: Determines if a `__hash__` method should be included in the class, as in `dataclasses.dataclass`.
        frozen: Determines if the generated class should be a 'frozen' `dataclass`, which does not allow its
            attributes to be modified after it has been initialized.
        config: The Pydantic config to use for the `dataclass`.
        validate_on_init: A deprecated parameter included for backwards compatibility; in V2, all Pydantic dataclasses
            are validated on init.
        kw_only: Determines if `__init__` method parameters must be specified by keyword only. Defaults to `False`.
        slots: Determines if the generated class should be a 'slots' `dataclass`, which does not allow the addition of
            new attributes after instantiation.

        Returns:
        A decorator that accepts a class as its argument and returns a Pydantic `dataclass`.

        Raises:
        AssertionError: Raised if `init` is not `False` or `validate_on_init` is `False`.
        """
        assert init is False, 'pydantic.dataclasses.dataclass only supports init=False'
        assert validate_on_init is not False, 'validate_on_init=False is no longer supported'

        kwargs = {'kw_only': kw_only, 'slots': slots} if sys.version_info >= (3, 10) else {}

        def make_pydantic_fields_compatible(cls: type[Any]) -> None:
            """Make sure that stdlib `dataclasses` understands `Field` kwargs like `kw_only`
            To do that, we simply change
            `x: int = pydantic.Field(..., kw_only=True)`
            into
            `x: int = dataclasses.field(default=pydantic.Field(..., kw_only=True), kw_only=True)`
            """
            for annotation_cls in cls.__mro__:
                annotations = getattr(annotation_cls, '__annotations__', [])
                for field_name in annotations:
                    field_value = getattr(cls, field_name, None)
                    if isinstance(field_value, FieldInfo):
                        field_args = {'default': field_value}
                        if sys.version_info >= (3, 10) and field_value.kw_only:
                            field_args['kw_only'] = True
                        if field_value.repr is not True:
                            field_args['repr'] = field_value.repr
                        setattr(cls, field_name, dataclasses.field(**field_args))
                        if cls.__dict__.get('__annotations__') is None:
                            cls.__annotations__ = {}
                        cls.__annotations__[field_name] = annotations[field_name]

        def create_dataclass(cls: type[Any]) -> type[PydanticDataclass]:
            """Create a Pydantic dataclass from a regular dataclass.

            Args:
            cls: The class to create the Pydantic dataclass from.

            Returns:
            A Pydantic dataclass.
            """
            from ._internal._utils import is_model_class

            if is_model_class(cls):
                raise PydanticUserError(
                    f'Cannot create a Pydantic dataclass from {cls.__name__} as it is already a Pydantic model',
                    code='dataclass-on-model',
                )

            original_cls = cls

            config_dict = config or getattr(cls, '__pydantic_config__', None)
            config_wrapper = _config.ConfigWrapper(config_dict)
            decorators = _decorators.DecoratorInfos.build(cls)
            original_doc = cls.__doc__ if not _pydantic_dataclasses.is_builtin_dataclass(cls) else None

            if _pydantic_dataclasses.is_builtin_dataclass(cls):
                bases = (cls,) + ((Generic[cls.__parameters__],) if issubclass(cls, Generic) else ())
                cls = types.new_class(cls.__name__, bases)

            make_pydantic_fields_compatible(cls)

            cls = dataclasses.dataclass(
                cls,
                init=True,
                repr=repr,
                eq=eq,
                order=order,
                unsafe_hash=unsafe_hash,
                frozen=frozen,
                **kwargs,
            )

            cls.__pydantic_decorators__ = decorators
            cls.__doc__ = original_doc
            cls.__module__ = original_cls.__module__
            cls.__qualname__ = original_cls.__qualname__
            pydantic_complete = _pydantic_dataclasses.complete_dataclass(
                cls, config_wrapper, raise_errors=False, types_namespace=None
            )
            cls.__pydantic_complete__ = pydantic_complete
            return cls

        return create_dataclass if _cls is None else create_dataclass(_cls)

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    def dataclass(
        _cls: type[_T] | None = None,
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
        kw_only: bool = False,
        slots: bool = False,
    ) -> Callable[[type[_T]], type[PydanticDataclass]] | type[PydanticDataclass]:
        """Usage docs: https://docs.pydantic.dev/2.8/concepts/dataclasses/

        A decorator used to create a Pydantic-enhanced dataclass, similar to the standard Python `dataclass`,
        but with added validation.

        This function should be used similarly to `dataclasses.dataclass`.

        Args:
        _cls: The target `dataclass`.
        init: Included for signature compatibility with `dataclasses.dataclass`, and is passed through to
            `dataclasses.dataclass` when appropriate. If specified, must be set to `False`, as pydantic inserts its
            own  `__init__` function.
        repr: A boolean indicating whether to include the field in the `__repr__` output.
        eq: Determines if a `__eq__` method should be generated for the class.
        order: Determines if comparison magic methods should be generated, such as `__lt__`, but not `__eq__`.
        unsafe_hash: Determines if a `__hash__` method should be included in the class, as in `dataclasses.dataclass`.
        frozen: Determines if the generated class should be a 'frozen' `dataclass`, which does not allow its
            attributes to be modified after it has been initialized.
        config: The Pydantic config to use for the `dataclass`.
        validate_on_init: A deprecated parameter included for backwards compatibility; in V2, all Pydantic dataclasses
            are validated on init.
        kw_only: Determines if `__init__` method parameters must be specified by keyword only. Defaults to `False`.
        slots: Determines if the generated class should be a 'slots' `dataclass`, which does not allow the addition of
            new attributes after instantiation.

        Returns:
        A decorator that accepts a class as its argument and returns a Pydantic `dataclass`.

        Raises:
        AssertionError: Raised if `init` is not `False` or `validate_on_init` is `False`.
        """
        assert init is False, 'pydantic.dataclasses.dataclass only supports init=False'
        assert validate_on_init is not False, 'validate_on_init=False is no longer supported'

        kwargs = {'kw_only': kw_only, 'slots': slots} if sys.version_info >= (3, 10) else {}

        def make_pydantic_fields_compatible(cls: type[Any]) -> None:
            """Make sure that stdlib `dataclasses` understands `Field` kwargs like `kw_only`
            To do that, we simply change
            `x: int = pydantic.Field(..., kw_only=True)`
            into
            `x: int = dataclasses.field(default=pydantic.Field(..., kw_only=True), kw_only=True)`
            """
            for annotation_cls in cls.__mro__:
                annotations = getattr(annotation_cls, '__annotations__', [])
                for field_name in annotations:
                    field_value = getattr(cls, field_name, None)
                    if isinstance(field_value, FieldInfo):
                        field_args = {'default': field_value}
                        if sys.version_info >= (3, 10) and field_value.kw_only:
                            field_args['kw_only'] = True
                        if field_value.repr is not True:
                            field_args['repr'] = field_value.repr
                        setattr(cls, field_name, dataclasses.field(**field_args))
                        if cls.__dict__.get('__annotations__') is None:
                            cls.__annotations__ = {}
                        cls.__annotations__[field_name] = annotations[field_name]

        def create_dataclass(cls: type[Any]) -> type[PydanticDataclass]:
            """Create a Pydantic dataclass from a regular dataclass.

            Args:
            cls: The class to create the Pydantic dataclass from.

            Returns:
            A Pydantic dataclass.
            """
            from ._internal._utils import is_model_class

            if is_model_class(cls):
                raise PydanticUserError(
                    f'Cannot create a Pydantic dataclass from {cls.__name__} as it is already a Pydantic model',
                    code='dataclass-on-model',
                )

            original_cls = cls

            config_dict = config or getattr(cls, '__pydantic_config__', None)
            config_wrapper = _config.ConfigWrapper(config_dict)
            decorators = _decorators.DecoratorInfos.build(cls)
            original_doc = cls.__doc__ if not _pydantic_dataclasses.is_builtin_dataclass(cls) else None

            if _pydantic_dataclasses.is_builtin_dataclass(cls):
                bases = (cls,) + ((Generic[cls.__parameters__],) if issubclass(cls, Generic) else ())
                cls = types.new_class(cls.__name__, bases)

            make_pydantic_fields_compatible(cls)

            cls = dataclasses.dataclass(
                cls,
                init=True,
                repr=repr,
                eq=eq,
                order=order,
                unsafe_hash=unsafe_hash,
                frozen=frozen,
                **kwargs,
            )

            cls.__pydantic_decorators__ = decorators
            cls.__doc__ = original_doc
            cls.__module__ = original_cls.__module__
            cls.__qualname__ = original_cls.__qualname__
            pydantic_complete = _pydantic_dataclasses.complete_dataclass(
                cls, config_wrapper, raise_errors=False, types_namespace=None
            )
            cls.__pydantic_complete__ = pydantic_complete
            return cls

        return create_dataclass if _cls is None else create_dataclass(_cls)

else:

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    def dataclass(
        _cls: type[_T] | None = None,
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
        kw_only: bool = False,
        slots: bool = False,
    ) -> Callable[[type[_T]], type[PydanticDataclass]] | type[PydanticDataclass]:
        """Usage docs: https://docs.pydantic.dev/2.8/concepts/dataclasses/

        A decorator used to create a Pydantic-enhanced dataclass, similar to the standard Python `dataclass`,
        but with added validation.

        This function should be used similarly to `dataclasses.dataclass`.

        Args:
        _cls: The target `dataclass`.
        init: Included for signature compatibility with `dataclasses.dataclass`, and is passed through to
            `dataclasses.dataclass` when appropriate. If specified, must be set to `False`, as pydantic inserts its
            own  `__init__` function.
        repr: A boolean indicating whether to include the field in the `__repr__` output.
        eq: Determines if a `__eq__` method should be generated for the class.
        order: Determines if comparison magic methods should be generated, such as `__lt__`, but not `__eq__`.
        unsafe_hash: Determines if a `__hash__` method should be included in the class, as in `dataclasses.dataclass`.
        frozen: Determines if the generated class should be a 'frozen' `dataclass`, which does not allow its
            attributes to be modified after it has been initialized.
        config: The Pydantic config to use for the `dataclass`.
        validate_on_init: A deprecated parameter included for backwards compatibility; in V2, all Pydantic dataclasses
            are validated on init.
        kw_only: Determines if `__init__` method parameters must be specified by keyword only. Defaults to `False`.
        slots: Determines if the generated class should be a 'slots' `dataclass`, which does not allow the addition of
            new attributes after instantiation.

        Returns:
        A decorator that accepts a class as its argument and returns a Pydantic `dataclass`.

        Raises:
        AssertionError: Raised if `init` is not `False` or `validate_on_init` is `False`.
        """
        assert init is False, 'pydantic.dataclasses.dataclass only supports init=False'
        assert validate_on_init is not False, 'validate_on_init=False is no longer supported'

        kwargs = {'kw_only': kw_only, 'slots': slots} if sys.version_info >= (3, 10) else {}

        def make_pydantic_fields_compatible(cls: type[Any]) -> None:
            """Make sure that stdlib `dataclasses` understands `Field` kwargs like `kw_only`
            To do that, we simply change
            `x: int = pydantic.Field(..., kw_only=True)`
            into
            `x: int = dataclasses.field(default=pydantic.Field(..., kw_only=True), kw_only=True)`
            """
            for annotation_cls in cls.__mro__:
                annotations = getattr(annotation_cls, '__annotations__', [])
                for field_name in annotations:
                    field_value = getattr(cls, field_name, None)
                    if isinstance(field_value, FieldInfo):
                        field_args = {'default': field_value}
                        if sys.version_info >= (3, 10) and field_value.kw_only:
                            field_args['kw_only'] = True
                        if field_value.repr is not True:
                            field_args['repr'] = field_value.repr
                        setattr(cls, field_name, dataclasses.field(**field_args))
                        if cls.__dict__.get('__annotations__') is None:
                            cls.__annotations__ = {}
                        cls.__annotations__[field_name] = annotations[field_name]

        def create_dataclass(cls: type[Any]) -> type[PydanticDataclass]:
            """Create a Pydantic dataclass from a regular dataclass.

            Args:
            cls: The class to create the Pydantic dataclass from.

            Returns:
            A Pydantic dataclass.
            """
            from ._internal._utils import is_model_class

            if is_model_class(cls):
                raise PydanticUserError(
                    f'Cannot create a Pydantic dataclass from {cls.__name__} as it is already a Pydantic model',
                    code='dataclass-on-model',
                )

            original_cls = cls

            config_dict = config or getattr(cls, '__pydantic_config__', None)
            config_wrapper = _config.ConfigWrapper(config_dict)
            decorators = _decorators.DecoratorInfos.build(cls)
            original_doc = cls.__doc__ if not _pydantic_dataclasses.is_builtin_dataclass(cls) else None

            if _pydantic_dataclasses.is_builtin_dataclass(cls):
                bases = (cls,) + ((Generic[cls.__parameters__],) if issubclass(cls, Generic) else ())
                cls = types.new_class(cls.__name__, bases)

            make_pydantic_fields_compatible(cls)

            cls = dataclasses.dataclass(
                cls,
                init=True,
                repr=repr,
                eq=eq,
                order=order,
                unsafe_hash=unsafe_hash,
                frozen=frozen,
                **kwargs,
            )

            cls.__pydantic_decorators__ = decorators
            cls.__doc__ = original_doc
            cls.__module__ = original_cls.__module__
            cls.__qualname__ = original_cls.__qualname__
            pydantic_complete = _pydantic_dataclasses.complete_dataclass(
                cls, config_wrapper, raise_errors=False, types_namespace=None
            )
            cls.__pydantic_complete__ = pydantic_complete
            return cls

        return create_dataclass if _cls is None else create_dataclass(_cls)

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    def dataclass(
        _cls: type[_T] | None = None,
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict | type[object] | None = None,
        validate_on_init: bool | None = None,
        kw_only: bool = False,
        slots: bool = False,
    ) -> Callable[[type[_T]], type[PydanticDataclass]] | type[PydanticDataclass]:
        """Usage docs: https://docs.pydantic.dev/2.8/concepts/dataclasses/

        A decorator used to create a Pydantic-enhanced dataclass, similar to the standard Python `dataclass`,
        but with added validation.

        This function should be used similarly to `dataclasses.dataclass`.

        Args:
        _cls: The target `dataclass`.
        init: Included for signature compatibility with `dataclasses.dataclass`, and is passed through to
            `dataclasses.dataclass` when appropriate. If specified, must be set to `False`, as pydantic inserts its
            own  `__init__` function.
        repr: A boolean indicating whether to include the field in the `__repr__` output.
        eq: Determines if a `__eq__` method should be generated for the class.
        order: Determines if comparison magic methods should be generated, such as `__lt__`, but not `__eq__`.
        unsafe_hash: Determines if a `__hash__` method should be included in the class, as in `dataclasses.dataclass`.
        frozen: Determines if the generated class should be a 'frozen' `dataclass`, which does not allow its
            attributes to be modified after it has been initialized.
        config: The Pydantic config to use for the `dataclass`.
        validate_on_init: A deprecated parameter included for backwards compatibility; in V2, all Pydantic dataclasses
            are validated on init.
        kw_only: Determines if `__init__` method parameters must be specified by keyword only. Defaults to `False`.
        slots: Determines if the generated class should be a 'slots' `dataclass`, which does not allow the addition of
            new attributes after instantiation.

        Returns:
        A decorator that accepts a class as its argument and returns a Pydantic `dataclass`.

        Raises:
        AssertionError: Raised if `init` is not `False` or `validate_on_init` is `False`.
        """
        assert init is False, 'pydantic.dataclasses.dataclass only supports init=False'
        assert validate_on_init is not False, 'validate_on_init=False is no longer supported'

        kwargs = {'kw_only': kw_only, 'slots': slots} if sys.version_info >= (3, 10) else {}

        def make_pydantic_fields_compatible(cls: type[Any]) -> None:
            """Make sure that stdlib `dataclasses` understands `Field` kwargs like `kw_only`
            To do that, we simply change
            `x: int = pydantic.Field(..., kw_only=True)`
            into
            `x: int = dataclasses.field(default=pydantic.Field(..., kw_only=True), kw_only=True)`
            """
            for annotation_cls in cls.__mro__:
                annotations = getattr(annotation_cls, '__annotations__', [])
                for field_name in annotations:
                    field_value = getattr(cls, field_name, None)
                    if isinstance(field_value, FieldInfo):
                        field_args = {'default': field_value}
                        if sys.version_info >= (3, 10) and field_value.kw_only:
                            field_args['kw_only'] = True
                        if field_value.repr is not True:
                            field_args['repr'] = field_value.repr
                        setattr(cls, field_name, dataclasses.field(**field_args))
                        if cls.__dict__.get('__annotations__') is None:
                            cls.__annotations__ = {}
                        cls.__annotations__[field_name] = annotations[field_name]

        def create_dataclass(cls: type[Any]) -> type[PydanticDataclass]:
            """Create a Pydantic dataclass from a regular dataclass.

            Args:
            cls: The class to create the Pydantic dataclass from.

            Returns:
            A Pydantic dataclass.
            """
            from ._internal._utils import is_model_class

            if is_model_class(cls):
                raise PydanticUserError(
                    f'Cannot create a Pydantic dataclass from {cls.__name__} as it is already a Pydantic model',
                    code='dataclass-on-model',
                )

            original_cls = cls

            config_dict = config or getattr(cls, '__pydantic_config__', None)
            config_wrapper = _config.ConfigWrapper(config_dict)
            decorators = _decorators.DecoratorInfos.build(cls)
            original_doc = cls.__doc__ if not _pydantic_dataclasses.is_builtin_dataclass(cls) else None

            if _pydantic_dataclasses.is_builtin_dataclass(cls):
                bases = (cls,) + ((Generic[cls.__parameters__],) if issubclass(cls, Generic) else ())
                cls = types.new_class(cls.__name__, bases)

            make_pydantic_fields_compatible(cls)

            cls = dataclasses.dataclass(
                cls,
                init=True,
                repr=repr,
                eq=eq,
                order=order,
                unsafe_hash=unsafe_hash,
                frozen=frozen,
                **kwargs,
            )

            cls.__pydantic_decorators__ = decorators
            cls.__doc__ = original_doc
            cls.__module__ = original_cls.__module__
            cls.__qualname__ = original_cls.__qualname__
            pydantic_complete = _pydantic_dataclasses.complete_dataclass(
                cls, config_wrapper, raise_errors=False, types_namespace=None
            )
            cls.__pydantic_complete__ = pydantic_complete
            return cls

        return create_dataclass if _cls is None else create_dataclass(_cls)


@dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
def dataclass(
    _cls: type[_T] | None = None,
    *,
    init: Literal[False] = False,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    config: ConfigDict | type[object] | None = None,
    validate_on_init: bool | None = None,
    kw_only: bool = False,
    slots: bool = False,
) -> Callable[[type[_T]], type[PydanticDataclass]] | type[PydanticDataclass]:
    """Usage docs: https://docs.pydantic.dev/2.8/concepts/dataclasses/

    A decorator used to create a Pydantic-enhanced dataclass, similar to the standard Python `dataclass`,
    but with added validation.

    This function should be used similarly to `dataclasses.dataclass`.

    Args:
        _cls: The target `dataclass`.
        init: Included for signature compatibility with `dataclasses.dataclass`, and is passed through to
            `dataclasses.dataclass` when appropriate. If specified, must be set to `False`, as pydantic inserts its
            own  `__init__` function.
        repr: A boolean indicating whether to include the field in the `__repr__` output.
        eq: Determines if a `__eq__` method should be generated for the class.
        order: Determines if comparison magic methods should be generated, such as `__lt__`, but not `__eq__`.
        unsafe_hash: Determines if a `__hash__` method should be included in the class, as in `dataclasses.dataclass`.
        frozen: Determines if the generated class should be a 'frozen' `dataclass`, which does not allow its
            attributes to be modified after it has been initialized.
        config: The Pydantic config to use for the `dataclass`.
        validate_on_init: A deprecated parameter included for backwards compatibility; in V2, all Pydantic dataclasses
            are validated on init.
        kw_only: Determines if `__init__` method parameters must be specified by keyword only. Defaults to `False`.
        slots: Determines if the generated class should be a 'slots' `dataclass`, which does not allow the addition of
            new attributes after instantiation.

    Returns:
        A decorator that accepts a class as its argument and returns a Pydantic `dataclass`.

    Raises:
        AssertionError: Raised if `init` is not `False` or `validate_on_init` is `False`.
    """
    assert init is False, 'pydantic.dataclasses.dataclass only supports init=False'
    assert validate_on_init is not False, 'validate_on_init=False is no longer supported'

    kwargs = {'kw_only': kw_only, 'slots': slots} if sys.version_info >= (3, 10) else {}

    def make_pydantic_fields_compatible(cls: type[Any]) -> None:
        """Make sure that stdlib `dataclasses` understands `Field` kwargs like `kw_only`
        To do that, we simply change
          `x: int = pydantic.Field(..., kw_only=True)`
        into
          `x: int = dataclasses.field(default=pydantic.Field(..., kw_only=True), kw_only=True)`
        """
        for annotation_cls in cls.__mro__:
            annotations = getattr(annotation_cls, '__annotations__', [])
            for field_name in annotations:
                field_value = getattr(cls, field_name, None)
                if isinstance(field_value, FieldInfo):
                    field_args = {'default': field_value}
                    if sys.version_info >= (3, 10) and field_value.kw_only:
                        field_args['kw_only'] = True
                    if field_value.repr is not True:
                        field_args['repr'] = field_value.repr
                    setattr(cls, field_name, dataclasses.field(**field_args))
                    if cls.__dict__.get('__annotations__') is None:
                        cls.__annotations__ = {}
                    cls.__annotations__[field_name] = annotations[field_name]

    def create_dataclass(cls: type[Any]) -> type[PydanticDataclass]:
        """Create a Pydantic dataclass from a regular dataclass.

        Args:
            cls: The class to create the Pydantic dataclass from.

        Returns:
            A Pydantic dataclass.
        """
        from ._internal._utils import is_model_class

        if is_model_class(cls):
            raise PydanticUserError(
                f'Cannot create a Pydantic dataclass from {cls.__name__} as it is already a Pydantic model',
                code='dataclass-on-model',
            )

        original_cls = cls

        config_dict = config or getattr(cls, '__pydantic_config__', None)
        config_wrapper = _config.ConfigWrapper(config_dict)
        decorators = _decorators.DecoratorInfos.build(cls)
        original_doc = cls.__doc__ if not _pydantic_dataclasses.is_builtin_dataclass(cls) else None

        if _pydantic_dataclasses.is_builtin_dataclass(cls):
            bases = (cls,) + ((Generic[cls.__parameters__],) if issubclass(cls, Generic) else ())
            cls = types.new_class(cls.__name__, bases)

        make_pydantic_fields_compatible(cls)

        cls = dataclasses.dataclass(
            cls,
            init=True,
            repr=repr,
            eq=eq,
            order=order,
            unsafe_hash=unsafe_hash,
            frozen=frozen,
            **kwargs,
        )

        cls.__pydantic_decorators__ = decorators
        cls.__doc__ = original_doc
        cls.__module__ = original_cls.__module__
        cls.__qualname__ = original_cls.__qualname__
        pydantic_complete = _pydantic_dataclasses.complete_dataclass(
            cls, config_wrapper, raise_errors=False, types_namespace=None
        )
        cls.__pydantic_complete__ = pydantic_complete
        return cls

    return create_dataclass if _cls is None else create_dataclass(_cls)


__getattr__ = getattr_migration(__name__)

if (3, 8) <= sys.version_info < (3, 11):
    # Monkeypatch dataclasses.InitVar so that typing doesn't error if it occurs as a type when evaluating type hints
    # Starting in 3.11, typing.get_type_hints will not raise an error if the retrieved type hints are not callable.

    def _call_initvar(*args: Any, **kwargs: Any) -> NoReturn:
        """This function does nothing but raise an error that is as similar as possible to what you'd get
        if you were to try calling `InitVar[int]()` without this monkeypatch. The whole purpose is just
        to ensure typing._type_check does not error if the type hint evaluates to `InitVar[<parameter>]`.
        """
        raise TypeError("'InitVar' object is not callable")

    dataclasses.InitVar.__call__ = _call_initvar


def rebuild_dataclass(
    cls: type[PydanticDataclass],
    *,
    force: bool = False,
    raise_errors: bool = True,
    _parent_namespace_depth: int = 2,
    _types_namespace: dict[str, Any] | None = None,
) -> bool | None:
    """Try to rebuild the pydantic-core schema for the dataclass.

    This may be necessary when one of the annotations is a ForwardRef which could not be resolved during
    the initial attempt to build the schema, and automatic rebuilding fails.

    This is analogous to `BaseModel.model_rebuild`.

    Args:
        cls: The class to rebuild the pydantic-core schema for.
        force: Whether to force the rebuilding of the schema, defaults to `False`.
        raise_errors: Whether to raise errors, defaults to `True`.
        _parent_namespace_depth: The depth level of the parent namespace, defaults to 2.
        _types_namespace: The types namespace, defaults to `None`.

    Returns:
        Returns `None` if the schema is already "complete" and rebuilding was not required.
        If rebuilding _was_ required, returns `True` if rebuilding was successful, otherwise `False`.
    """
    if not force and cls.__pydantic_complete__:
        return None
    else:
        if _types_namespace is not None:
            types_namespace: dict[str, Any] | None = _types_namespace.copy()
        else:
            if _parent_namespace_depth > 0:
                frame_parent_ns = _typing_extra.parent_frame_namespace(parent_depth=_parent_namespace_depth) or {}
                # Note: we may need to add something similar to cls.__pydantic_parent_namespace__ from BaseModel
                #   here when implementing handling of recursive generics. See BaseModel.model_rebuild for reference.
                types_namespace = frame_parent_ns
            else:
                types_namespace = {}

            types_namespace = _typing_extra.get_cls_types_namespace(cls, types_namespace)
        return _pydantic_dataclasses.complete_dataclass(
            cls,
            _config.ConfigWrapper(cls.__pydantic_config__, check=False),
            raise_errors=raise_errors,
            types_namespace=types_namespace,
        )


def is_pydantic_dataclass(class_: type[Any], /) -> TypeGuard[type[PydanticDataclass]]:
    """Whether a class is a pydantic dataclass.

    Args:
        class_: The class.

    Returns:
        `True` if the class is a pydantic dataclass, `False` otherwise.
    """
    try:
        return '__pydantic_validator__' in class_.__dict__ and dataclasses.is_dataclass(class_)
    except AttributeError:
        return False
