"""A class representing the type adapter."""
from __future__ import annotations as _annotations

import sys
from typing import TYPE_CHECKING, Any, Dict, Generic, Iterable, Set, TypeVar, Union, overload

from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator
from typing_extensions import Literal

from ._internal import _config, _generate_schema, _typing_extra
from ._internal._core_utils import flatten_schema_defs, inline_schema_defs
from .config import ConfigDict
from .json_schema import DEFAULT_REF_TEMPLATE, GenerateJsonSchema

T = TypeVar('T')

if TYPE_CHECKING:
    # should be `set[int] | set[str] | dict[int, IncEx] | dict[str, IncEx] | None`, but mypy can't cope
    IncEx = Union[Set[int], Set[str], Dict[int, Any], Dict[str, Any]]


def _get_schema(type_: Any, config_wrapper: _config.ConfigWrapper, parent_depth: int) -> CoreSchema:
    """
    `BaseModel` uses its own `__module__` to find out where it was defined
    and then look for symbols to resolve forward references in those globals.
    On the other hand this function can be called with arbitrary objects,
    including type aliases where `__module__` (always `typing.py`) is not useful.
    So instead we look at the globals in our parent stack frame.

    This works for the case where this function is called in a module that
    has the target of forward references in its scope, but
    does not work for more complex cases.

    For example, take the following:

    a.py
    ```python
    from typing import List, Dict
    IntList = List[int]
    OuterDict = Dict[str, 'IntList']
    ```

    b.py
    ```python
    from pydantic import TypeAdapter
    from a import OuterDict
    IntList = int  # replaces the symbol the forward reference is looking for
    v = TypeAdapter(OuterDict)
    v({"x": 1})  # should fail but doesn't
    ```

    If OuterDict were a `BaseModel`, this would work because it would resolve
    the forward reference within the `a.py` namespace.
    But `TypeAdapter(OuterDict)`
    can't know what module OuterDict came from.

    In other words, the assumption that _all_ forward references exist in the
    module we are being called from is not technically always true.
    Although most of the time it is and it works fine for recursive models and such,
    `BaseModel`'s behavior isn't perfect either and _can_ break in similar ways,
    so there is no right or wrong between the two.

    But at the very least this behavior is _subtly_ different from `BaseModel`'s.
    """
    local_ns = _typing_extra.parent_frame_namespace(parent_depth=parent_depth)
    global_ns = sys._getframe(max(parent_depth - 1, 1)).f_globals.copy()
    global_ns.update(local_ns or {})
    gen = _generate_schema.GenerateSchema(config_wrapper, types_namespace=global_ns, typevars_map={})
    return gen.generate_schema(type_)


class TypeAdapter(Generic[T]):
    """A class representing the type adapter.

    Attributes:
        core_schema (CoreSchema): The core schema for the type.
        validator (SchemaValidator): The schema validator for the type.
        serializer (SchemaSerializer): The schema serializer for the type.
    """

    if TYPE_CHECKING:

        @overload
        def __new__(cls, __type: type[T], *, config: ConfigDict | None = ...) -> TypeAdapter[T]:
            ...

        # this overload is for non-type things like Union[int, str]
        # Pyright currently handles this "correctly", but MyPy understands this as TypeAdapter[object]
        # so an explicit type cast is needed
        @overload
        def __new__(cls, __type: T, *, config: ConfigDict | None = ...) -> TypeAdapter[T]:
            ...

        def __new__(cls, __type: Any, *, config: ConfigDict | None = ...) -> TypeAdapter[T]:
            raise NotImplementedError

    def __init__(self, __type: Any, *, config: ConfigDict | None = None, _parent_depth: int = 2) -> None:
        """Initializes the TypeAdapter object."""
        config_wrapper = _config.ConfigWrapper(config)

        core_schema: CoreSchema
        try:
            core_schema = __type.__pydantic_core_schema__
        except AttributeError:
            core_schema = _get_schema(__type, config_wrapper, parent_depth=_parent_depth + 1)

        core_schema = flatten_schema_defs(core_schema)
        simplified_core_schema = inline_schema_defs(core_schema)

        core_config = config_wrapper.core_config()
        validator: SchemaValidator
        if hasattr(__type, '__pydantic_validator__') and config is None:
            validator = __type.__pydantic_validator__
        else:
            validator = SchemaValidator(simplified_core_schema, core_config)

        serializer: SchemaSerializer
        if hasattr(__type, '__pydantic_serializer__') and config is None:
            serializer = __type.__pydantic_serializer__
        else:
            serializer = SchemaSerializer(simplified_core_schema, core_config)

        self.core_schema = core_schema
        self.validator = validator
        self.serializer = serializer

    def validate_python(self, __object: Any, *, strict: bool | None = None, context: dict[str, Any] | None = None) -> T:
        """
        Validate a Python object against the model.

        Args:
            __object (Any): The Python object to validate against the model.
            strict (bool | None, optional): Whether to strictly check types. Defaults to None.
            context (dict[str, Any] | None, optional): Additional context to use during validation. Defaults to None.

        Returns:
            T: The validated object.

        """
        return self.validator.validate_python(__object, strict=strict, context=context)

    def validate_json(
        self, __data: str | bytes, *, strict: bool | None = None, context: dict[str, Any] | None = None
    ) -> T:
        """Validate a JSON string or bytes against the model.

        Args:
            __data (str | bytes): The JSON data to validate against the model.
            strict (bool | None, optional): Whether to strictly check types. Defaults to None.
            context (dict[str, Any] | None, optional): Additional context to use during validation. Defaults to None.

        Returns:
            T: The validated object.

        """
        return self.validator.validate_json(__data, strict=strict, context=context)

    def dump_python(
        self,
        __instance: T,
        *,
        mode: Literal['json', 'python'] = 'python',
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> Any:
        """Dump a Python object to a serialized format.

        Args:
            __instance (T): The Python object to serialize.
            mode (Literal['json', 'python'], optional): The output format. Defaults to 'python'.
            include (IncEx | None, optional): Fields to include in the output. Defaults to None.
            exclude (IncEx | None, optional): Fields to exclude from the output. Defaults to None.
            by_alias (bool, optional): Whether to use alias names for field names. Defaults to False.
            exclude_unset (bool, optional): Whether to exclude unset fields. Defaults to False.
            exclude_defaults (bool, optional): Whether to exclude fields with default values. Defaults to False.
            exclude_none (bool, optional): Whether to exclude fields with None values. Defaults to False.
            round_trip (bool, optional): Whether to output the serialized data in a way that is compatible with
                deserialization. Defaults to False.
            warnings (bool, optional): Whether to display serialization warnings. Defaults to True.

        Returns:
            Any: The serialized object.

        """
        return self.serializer.to_python(
            __instance,
            mode=mode,
            by_alias=by_alias,
            include=include,
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

    def dump_json(
        self,
        __instance: T,
        *,
        indent: int | None = None,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> bytes:
        """Serialize the given instance to JSON.

        Args:
            __instance (T): The instance to be serialized.
            indent (Optional[int]): Number of spaces for JSON indentation (default: None).
            include (Optional[IncEx]): Fields to include (default: None).
            exclude (Optional[IncEx]): Fields to exclude (default: None).
            by_alias (bool): Whether to use alias names (default: False).
            exclude_unset (bool): Whether to exclude unset fields (default: False).
            exclude_defaults (bool): Whether to exclude fields with default values (default: False).
            exclude_none (bool): Whether to exclude fields with a value of None (default: False).
            round_trip (bool): Whether to serialize and deserialize the instance to ensure
                round-tripping (default: False).
            warnings (bool): Whether to emit serialization warnings (default: True).

        Returns:
            bytes: The JSON representation of the given instance as bytes.
        """
        return self.serializer.to_json(
            __instance,
            indent=indent,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

    def json_schema(
        self,
        *,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    ) -> dict[str, Any]:
        """Generate a JSON schema for the model.

        Args:
            by_alias (bool): Whether to use alias names (default: True).
            ref_template (str): The format string used for generating $ref strings (default: DEFAULT_REF_TEMPLATE).
            schema_generator (Type[GenerateJsonSchema]): The generator class used for creating the schema
                (default: GenerateJsonSchema).

        Returns:
            Dict[str, Any]: The JSON schema for the model as a dictionary.
        """
        schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)
        return schema_generator_instance.generate(self.core_schema)

    @staticmethod
    def json_schemas(
        __types: Iterable[TypeAdapter[Any]],
        *,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        title: str | None = None,
        description: str | None = None,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    ) -> dict[str, Any]:
        """Generate JSON schemas for multiple models.

        Args:
            __types (Iterable[TypeAdapter[Any]]): The types to generate schemas for.
            by_alias (bool): Whether to use alias names (default: True).
            ref_template (str): The format string used for generating $ref strings (default: DEFAULT_REF_TEMPLATE).
            title (Optional[str]): The title for the schema (default: None).
            description (Optional[str]): The description for the schema (default: None).
            schema_generator (Type[GenerateJsonSchema]): The generator class used for creating the
                schema (default: GenerateJsonSchema).

        Returns:
            Dict[str, Any]: The JSON schema for the models as a dictionary.
        """
        # TODO: can we use model.__schema_cache__?
        schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)

        core_schemas = [at.core_schema for at in __types]

        definitions = schema_generator_instance.generate_definitions(core_schemas)

        json_schema: dict[str, Any] = {}
        if definitions:
            json_schema['$defs'] = definitions
        if title:
            json_schema['title'] = title
        if description:
            json_schema['description'] = description

        return json_schema
