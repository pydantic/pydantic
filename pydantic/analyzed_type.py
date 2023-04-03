from __future__ import annotations as _annotations

import sys
from typing import TYPE_CHECKING, Any, Dict, Generic, Iterable, Set, TypeVar, Union, overload

from pydantic_core import CoreConfig, CoreSchema, SchemaSerializer, SchemaValidator, core_schema
from typing_extensions import Literal

from pydantic.config import ConfigDict
from pydantic.json_schema import DEFAULT_REF_TEMPLATE, GenerateJsonSchema

from ._internal import _generate_schema, _typing_extra

T = TypeVar('T')

if TYPE_CHECKING:
    # should be `set[int] | set[str] | dict[int, IncEx] | dict[str, IncEx] | None`, but mypy can't cope
    IncEx = Union[Set[int], Set[str], Dict[int, Any], Dict[str, Any]]


def _get_schema(type_: Any, config: CoreConfig | None, parent_depth: int) -> CoreSchema:
    """
      BaseModel uses it's own __module__ to find out where it was defined
    and then look for symbols to resolve forward references in those globals
    On the other hand this function can be called with arbitrary objects,
    including type aliases where __module__ (always `typing.py`) is not useful
    So instead we look at the globals in our parent stack frame
    This works for the case where this function is called in a module that
    has the target of forward references in its scope but
    does not work for more complex cases
    for example, take the following:

    a.py
    ```python
    from typing import List, Dict
    IntList = List[int]
    OuterDict = Dict[str, 'IntList']
    ```

    b.py
    ```python
    from pydantic import AnalyzedType
    from a import OuterDict
    IntList = int  # replaces the symbol the forward reference is looking for
    v = AnalyzedType(OuterDict)
    v({"x": 1})  # should fail but doesn't
    ```

    If OuterDict were a BaseModel this would work because it would resolve
    the forward reference within the `a.py` namespace.
    But `AnalyzedType(OuterDict)`
    can't know what module OuterDict came from.
    In other words, the assumption that _all_ forward references exist in the
    module we are being called from is not technically always true
    Although most of the time it is and it works fine for recursive models and such/
    BaseModel's behavior isn't perfect either and _can_ break in similar ways,
    so there is no right or wrong between the two.
    But at the very least this behavior is _subtly_ different from BaseModel's.
    """
    arbitrary_types = bool((config or {}).get('arbitrary_types_allowed', False))
    local_ns = _typing_extra.parent_frame_namespace(parent_depth=parent_depth)
    global_ns = sys._getframe(max(parent_depth - 1, 1)).f_globals.copy()
    global_ns.update(local_ns or {})
    gen = _generate_schema.GenerateSchema(arbitrary_types=arbitrary_types, types_namespace=global_ns, typevars_map={})
    return gen.generate_schema(type_)


# TODO: merge / replace this with _internal/_generate_schema.py::generate_config
# once we change the config logic to make ConfigDict not be a partial
def _translate_config(config: ConfigDict) -> core_schema.CoreConfig:
    """
    Create a pydantic-core config from a pydantic config.
    """
    unset: Any = object()
    core_config: dict[str, Any] = dict(
        title=config['title'] if 'title' in config and config['title'] is not None else unset,
        typed_dict_extra_behavior=config['extra'].value if 'extra' in config and config['extra'] is not None else unset,
        allow_inf_nan=config['allow_inf_nan'] if 'allow_inf_nan' in config else unset,
        populate_by_name=config['populate_by_name'] if 'populate_by_name' in config else unset,
        str_strip_whitespace=config['str_strip_whitespace'] if 'str_strip_whitespace' in config else unset,
        str_to_lower=config['str_to_lower'] if 'str_to_lower' in config else unset,
        str_to_upper=config['str_to_upper'] if 'str_to_upper' in config else unset,
        strict=config['strict'] if 'strict' in config else unset,
        ser_json_timedelta=config['ser_json_timedelta'] if 'ser_json_timedelta' in config else unset,
        ser_json_bytes=config['ser_json_bytes'] if 'ser_json_bytes' in config else unset,
        from_attributes=config['from_attributes'] if 'from_attributes' in config else unset,
        loc_by_alias=config['loc_by_alias'] if 'loc_by_alias' in config else unset,
        revalidate_instances=config['revalidate_instances'] if 'revalidate_instances' in config else unset,
        validate_default=config['validate_default'] if 'validate_default' in config else unset,
        str_max_length=(
            config['str_max_length'] if 'str_max_length' in config and config['str_max_length'] is not None else unset
        ),
        str_min_length=config['str_min_length'] if 'str_min_length' in config else unset,
    )
    for k in [k for k in core_config if core_config[k] is unset]:
        core_config.pop(k)
    return CoreConfig(**core_config)  # type: ignore[misc]


class AnalyzedType(Generic[T]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, __type: type[T], *, config: ConfigDict | None = ...) -> AnalyzedType[T]:
            ...

        # this overload is for non-type things like Union[int, str]
        # Pyright currently handles this "correctly", but MyPy understands this as AnalyzedType[object]
        # so an explicit type cast is needed
        @overload
        def __new__(cls, __type: T, *, config: ConfigDict | None = ...) -> AnalyzedType[T]:
            ...

        def __new__(cls, __type: Any, *, config: ConfigDict | None = ...) -> AnalyzedType[T]:
            raise NotImplementedError

    def __init__(self, __type: Any, *, config: ConfigDict | None = None, _parent_depth: int = 2) -> None:
        core_config: CoreConfig
        if config is not None:
            core_config = _translate_config(config)
        else:
            core_config = CoreConfig()
        try:
            core_config.update(__type.__pydantic_core_config__)
        except AttributeError:
            pass

        core_schema: CoreSchema
        try:
            core_schema = __type.__pydantic_core_schema__
        except AttributeError:
            core_schema = _get_schema(__type, core_config, parent_depth=_parent_depth + 1)

        validator: SchemaValidator
        if hasattr(__type, '__pydantic_validator__') and config is None:
            validator = __type.__pydantic_validator__
        else:
            validator = SchemaValidator(core_schema, core_config)

        serializer: SchemaSerializer
        if hasattr(__type, '__pydantic_serializer__') and config is None:
            serializer = __type.__pydantic_serializer__
        else:
            serializer = SchemaSerializer(core_schema, core_config)

        self.core_schema = core_schema
        self.validator = validator
        self.serializer = serializer

    def validate_python(self, __object: Any, *, strict: bool | None = None, context: dict[str, Any] | None = None) -> T:
        return self.validator.validate_python(__object, strict=strict, context=context)

    def validate_json(
        self, __data: str | bytes, *, strict: bool | None = None, context: dict[str, Any] | None = None
    ) -> T:
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
        schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)
        return schema_generator_instance.generate(self.core_schema)

    @staticmethod
    def json_schemas(
        __analyzed_types: Iterable[AnalyzedType[Any]],
        *,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        title: str | None = None,
        description: str | None = None,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    ) -> dict[str, Any]:
        # TODO: can we use model.__schema_cache__?
        schema_generator_instance = schema_generator(by_alias=by_alias, ref_template=ref_template)

        core_schemas = [at.core_schema for at in __analyzed_types]

        definitions = schema_generator_instance.generate_definitions(core_schemas)

        json_schema: dict[str, Any] = {}
        if definitions:
            json_schema['$defs'] = definitions
        if title:
            json_schema['title'] = title
        if description:
            json_schema['description'] = description

        return json_schema
