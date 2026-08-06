"""Defining fields on models."""

from __future__ import annotations as _annotations

import dataclasses
import inspect
import re
import sys
from collections.abc import Callable, Mapping
from copy import copy
from dataclasses import Field as DataclassField
from functools import cached_property
from types import EllipsisType
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Literal, TypeAlias, TypeVar, final, overload
from warnings import warn

import annotated_types
import typing_extensions
from pydantic_core import MISSING, PydanticUndefined
from typing_extensions import Self, TypedDict, Unpack, deprecated
from typing_inspection import typing_objects
from typing_inspection.introspection import UNKNOWN, AnnotationSource, ForbiddenQualifier, Qualifier, inspect_annotation

from . import types
from ._internal import _decorators, _fields, _generics, _repr, _typing_extra, _utils
from ._internal._namespace_utils import GlobalsNamespace, MappingNamespace
from .aliases import AliasChoices, AliasGenerator, AliasPath
from .config import JsonDict
from .errors import PydanticForbiddenQualifier, PydanticUserError
from .warnings import PydanticDeprecatedSince20

if TYPE_CHECKING:
    from ._internal._config import ConfigWrapper
    from ._internal._repr import ReprArgs


__all__ = 'Field', 'FieldInfo', 'FieldSpec', 'PrivateAttr', 'computed_field'


_Unset: Any = PydanticUndefined

if sys.version_info >= (3, 13):
    import warnings

    Deprecated: TypeAlias = warnings.deprecated | deprecated
else:
    Deprecated: TypeAlias = deprecated


class _FromFieldInfoInputs(TypedDict, total=False):
    """This class exists solely to add type checking for the `**kwargs` in `FieldInfo.from_field`."""

    # TODO PEP 747: use TypeForm:
    annotation: type[Any] | None
    default_factory: Callable[[], Any] | Callable[[dict[str, Any]], Any] | None
    alias: str | None
    alias_priority: int | None
    validation_alias: str | AliasPath | AliasChoices | None
    serialization_alias: str | None
    title: str | None
    field_title_generator: Callable[[str, FieldInfo], str] | None
    description: str | None
    examples: list[Any] | None
    exclude: bool | None
    exclude_if: Callable[[Any], bool] | None
    gt: annotated_types.SupportsGt | None
    ge: annotated_types.SupportsGe | None
    lt: annotated_types.SupportsLt | None
    le: annotated_types.SupportsLe | None
    multiple_of: float | None
    strict: bool | None
    min_length: int | None
    max_length: int | None
    pattern: str | re.Pattern[str] | None
    allow_inf_nan: bool | None
    max_digits: int | None
    decimal_places: int | None
    union_mode: Literal['smart', 'left_to_right'] | None
    discriminator: str | types.Discriminator | None
    deprecated: Deprecated | str | bool | None
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None
    frozen: bool | None
    validate_default: bool | None
    repr: bool
    init: bool | None
    init_var: bool | None
    kw_only: bool | None
    coerce_numbers_to_str: bool | None
    fail_fast: bool | None


class _FieldInfoInputs(_FromFieldInfoInputs, total=False):
    """This class exists solely to add type checking for the `**kwargs` in `FieldInfo.__init__`."""

    default: Any


class _FieldInfoAsDict(TypedDict, closed=True):
    # TODO PEP 747: use TypeForm:
    annotation: Any
    metadata: list[Any]
    attributes: dict[str, Any]


@final
class FieldSpec(_repr.Representation):
    """The return value of the [`Field()`][pydantic.fields.Field] function.

    A `FieldSpec` is a lightweight, unprocessed container for the arguments provided to the `Field()`
    function. When a Pydantic model, dataclass or similar construct is built, the field specifications
    (either used as `Annotated` metadata or as an assignment) are merged together with the rest of the
    annotation's metadata into a final [`FieldInfo`][pydantic.fields.FieldInfo] instance.
    """

    __slots__ = ('kwargs',)

    kwargs: dict[str, Any]
    """The keyword arguments provided to the `Field()` function, minus any unset values."""

    def __init__(self, kwargs: dict[str, Any], /) -> None:
        self.kwargs = kwargs

    def __repr_args__(self) -> ReprArgs:
        yield from self.kwargs.items()


@final
class FieldInfo(_repr.Representation):
    """This class holds information about a field.

    `FieldInfo` is used for any field definition regardless of whether the [`Field()`][pydantic.fields.Field]
    function is explicitly used.

    !!! warning
        The `FieldInfo` class is meant to expose information about a field in a Pydantic model or dataclass.
        `FieldInfo` instances shouldn't be instantiated directly, nor mutated.

        If you need to derive a new model from another one and are willing to alter `FieldInfo` instances,
        refer to this [dynamic model example](../examples/dynamic_models.md).

    Attributes:
        annotation: The type annotation of the field.
        default: The default value of the field.
        default_factory: A callable to generate the default value. The callable can either take 0 arguments
            (in which case it is called as is) or a single argument containing the already validated data.
        alias: The alias name of the field.
        alias_priority: The priority of the field's alias.
        validation_alias: The validation alias of the field.
        serialization_alias: The serialization alias of the field.
        title: The title of the field.
        field_title_generator: A callable that takes a field's name and info and returns title for it.
        description: The description of the field.
        examples: List of examples of the field.
        exclude: Whether to exclude the field from the model serialization.
        exclude_if: A callable that determines whether to exclude a field during serialization based on its value.
        discriminator: Field name or Discriminator for discriminating the type in a tagged union.
        deprecated: A deprecation message, an instance of `warnings.deprecated` or the `typing_extensions.deprecated` backport,
            or a boolean. If `True`, a default deprecation message will be emitted when accessing the field.
        json_schema_extra: A dict or callable to provide extra JSON schema properties.
        frozen: Whether the field is frozen.
        validate_default: Whether to validate the default value of the field.
        repr: Whether to include the field in representation of the model.
        init: Whether the field should be included in the constructor of the dataclass.
        init_var: Whether the field should _only_ be included in the constructor of the dataclass, and not stored.
        kw_only: Whether the field should be a keyword-only argument in the constructor of the dataclass.
        metadata: The metadata list. Contains all the data that isn't expressed as direct `FieldInfo` attributes, including:

            * Type-specific constraints, such as `gt` or `min_length` (these are converted to metadata classes such as `annotated_types.Gt`).
            * Any other arbitrary object used within [`Annotated`][typing.Annotated] metadata
              (e.g. [custom types handlers](../concepts/types.md#as-an-annotation) or any object not recognized by Pydantic).
    """

    # TODO PEP 747: use TypeForm:
    annotation: type[Any] | None
    default: Any
    default_factory: Callable[[], Any] | Callable[[dict[str, Any]], Any] | None
    alias: str | None
    alias_priority: int | None
    validation_alias: str | AliasPath | AliasChoices | None
    serialization_alias: str | None
    title: str | None
    field_title_generator: Callable[[str, FieldInfo], str] | None
    description: str | None
    examples: list[Any] | None
    exclude: bool | None
    exclude_if: Callable[[Any], bool] | None
    discriminator: str | types.Discriminator | None
    deprecated: Deprecated | str | bool | None
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None
    frozen: bool | None
    validate_default: bool | None
    repr: bool
    init: bool | None
    init_var: bool | None
    kw_only: bool | None
    metadata: list[Any]

    __slots__ = (
        'annotation',
        'default',
        'default_factory',
        'alias',
        'alias_priority',
        'validation_alias',
        'serialization_alias',
        'title',
        'field_title_generator',
        'description',
        'examples',
        'exclude',
        'exclude_if',
        'discriminator',
        'deprecated',
        'json_schema_extra',
        'frozen',
        'validate_default',
        'repr',
        'init',
        'init_var',
        'kw_only',
        'metadata',
        '_qualifiers',
        '_complete',
        '_original_assignment',
        '_original_annotation',
    )

    # used to convert kwargs to metadata/constraints,
    # None has a special meaning - these items are collected into a `PydanticGeneralMetadata`
    metadata_lookup: ClassVar[dict[str, Callable[[Any], Any] | None]] = {
        'strict': types.Strict,
        'gt': annotated_types.Gt,
        'ge': annotated_types.Ge,
        'lt': annotated_types.Lt,
        'le': annotated_types.Le,
        'multiple_of': annotated_types.MultipleOf,
        'min_length': annotated_types.MinLen,
        'max_length': annotated_types.MaxLen,
        'pattern': None,
        'allow_inf_nan': types.AllowInfNan,
        'max_digits': None,
        'decimal_places': None,
        'union_mode': None,
        'coerce_numbers_to_str': None,
        'fail_fast': types.FailFast,
    }

    def __init__(self, **kwargs: Unpack[_FieldInfoInputs]) -> None:
        """This class should generally not be initialized directly; `FieldInfo` instances are created
        by Pydantic when collecting the fields of a model-like class.

        See the signature of `pydantic.fields.Field` for more details about the expected arguments.
        """
        kwargs_: dict[str, Any] = {k: v for k, v in kwargs.items() if v is not _Unset}
        self.metadata = self._collect_constraints(kwargs_)
        self._apply_attrs(kwargs_)

    def _apply_attrs(self, kwargs: dict[str, Any]) -> None:
        """Set every `FieldInfo` attribute (except `metadata`) from the provided keyword arguments.

        Keys of `kwargs` that are not `FieldInfo` attributes (e.g. constraints such as `gt`) are ignored,
        and are expected to be processed separately (see `_collect_constraints()`).
        """
        get = kwargs.get
        self.annotation = get('annotation')
        default = get('default', PydanticUndefined)
        if default is Ellipsis:
            default = PydanticUndefined
        self.default = default
        self.default_factory = default_factory = get('default_factory')
        if default is not PydanticUndefined and default_factory is not None:
            raise TypeError('cannot specify both default and default_factory')
        self.alias = alias = get('alias')
        validation_alias = get('validation_alias')
        if validation_alias is None:
            validation_alias = alias
        elif not isinstance(validation_alias, (str, AliasChoices, AliasPath)):
            raise TypeError('Invalid `validation_alias` type. it should be `str`, `AliasChoices`, or `AliasPath`')
        self.validation_alias = validation_alias
        serialization_alias = get('serialization_alias')
        if serialization_alias is None and isinstance(alias, str):
            serialization_alias = alias
        self.serialization_alias = serialization_alias
        if alias is not None or validation_alias is not None or serialization_alias is not None:
            self.alias_priority = get('alias_priority') or 2
        else:
            self.alias_priority = None
        self.title = get('title')
        self.field_title_generator = get('field_title_generator')
        self.description = get('description')
        self.examples = get('examples')
        self.exclude = get('exclude')
        self.exclude_if = get('exclude_if')
        self.discriminator = get('discriminator')
        self.deprecated = get('deprecated')
        self.json_schema_extra = get('json_schema_extra')
        self.frozen = get('frozen')
        self.validate_default = get('validate_default')
        self.repr = get('repr', True)
        # currently only used on dataclasses:
        self.init = get('init')
        self.init_var = get('init_var')
        self.kw_only = get('kw_only')

        # Private attributes:
        self._qualifiers: set[Qualifier] = set()
        # Used to rebuild FieldInfo instances:
        self._complete = True
        self._original_annotation: Any = PydanticUndefined
        self._original_assignment: Any = PydanticUndefined

    def _apply_default_attrs(self, annotation: Any, default: Any) -> None:
        """Set every `FieldInfo` attribute (except `metadata`) to its default value.

        This is a performance fast path for the most common case, where only the annotation
        (and possibly a plain default value) is provided.
        """
        self.annotation = annotation
        self.default = PydanticUndefined if default is Ellipsis else default
        self.default_factory = None
        self.alias = None
        self.validation_alias = None
        self.serialization_alias = None
        self.alias_priority = None
        self.title = None
        self.field_title_generator = None
        self.description = None
        self.examples = None
        self.exclude = None
        self.exclude_if = None
        self.discriminator = None
        self.deprecated = None
        self.json_schema_extra = None
        self.frozen = None
        self.validate_default = None
        self.repr = True
        self.init = None
        self.init_var = None
        self.kw_only = None

        self._qualifiers = set()
        self._complete = True
        self._original_annotation = PydanticUndefined
        self._original_assignment = PydanticUndefined

    @staticmethod
    def from_field(default: Any = PydanticUndefined, **kwargs: Unpack[_FromFieldInfoInputs]) -> FieldInfo:
        """Create a final `FieldInfo` object from the arguments accepted by the `Field()` function.

        Args:
            default: The default value for the field. Defaults to Undefined.
            **kwargs: Additional arguments dictionary.

        Raises:
            TypeError: If 'annotation' is passed as a keyword argument.

        Returns:
            A new FieldInfo object with the given parameters.
        """
        if 'annotation' in kwargs:
            raise TypeError('"annotation" is not permitted as a Field keyword argument')
        kwargs_: dict[str, Any] = {k: v for k, v in kwargs.items() if v is not _Unset}
        if default is not PydanticUndefined and default is not Ellipsis:
            kwargs_['default'] = default
        return FieldInfo._construct([FieldSpec(kwargs_)], None)

    @staticmethod
    def from_annotation(annotation: type[Any], *, _source: AnnotationSource = AnnotationSource.ANY) -> FieldInfo:
        """Creates a `FieldInfo` instance from a bare annotation.

        This function is used internally to create a `FieldInfo` from a bare annotation like this:

        ```python
        import pydantic

        class MyModel(pydantic.BaseModel):
            foo: int  # <-- like this
        ```

        We also account for the case where the annotation can be an instance of `Annotated` and where
        one of the (not first) arguments in `Annotated` is an instance of `FieldInfo`, e.g.:

        ```python
        from typing import Annotated

        import annotated_types

        import pydantic

        class MyModel(pydantic.BaseModel):
            foo: Annotated[int, annotated_types.Gt(42)]
            bar: Annotated[int, pydantic.Field(gt=42)]
        ```

        Args:
            annotation: An annotation object.

        Returns:
            An instance of the field metadata.
        """
        if isinstance(annotation, type) and annotation is not dataclasses.InitVar:
            # Fast path for plain classes (the most common case), where no qualifier and no
            # metadata can be present (a bare `InitVar` — which is a class — is a qualifier):
            field_info = object.__new__(FieldInfo)
            field_info._apply_default_attrs(annotation, PydanticUndefined)
            field_info.metadata = []
            return field_info

        try:
            inspected_ann = inspect_annotation(
                annotation,
                annotation_source=_source,
                unpack_type_aliases='skip',
            )
        except ForbiddenQualifier as e:
            raise PydanticForbiddenQualifier(e.qualifier, annotation)

        # TODO check for classvar and error?

        # No assigned value, this happens when using a bare `Final` qualifier (also for other
        # qualifiers, but they shouldn't appear here). In this case we infer the type as `Any`
        # because we don't have any assigned value.
        type_expr: Any = Any if inspected_ann.type is UNKNOWN else inspected_ann.type
        metadata = inspected_ann.metadata

        attr_overrides: dict[str, Any] = {'annotation': type_expr}
        if 'final' in inspected_ann.qualifiers:
            attr_overrides['frozen'] = True
        field_info = FieldInfo._construct(metadata, attr_overrides)
        field_info._qualifiers = inspected_ann.qualifiers
        return field_info

    @staticmethod
    def from_annotated_attribute(
        annotation: type[Any], default: Any, *, _source: AnnotationSource = AnnotationSource.ANY
    ) -> FieldInfo:
        """Create `FieldInfo` from an annotation with a default value.

        This is used in cases like the following:

        ```python
        from typing import Annotated

        import annotated_types

        import pydantic

        class MyModel(pydantic.BaseModel):
            foo: int = 4  # <-- like this
            bar: Annotated[int, annotated_types.Gt(4)] = 4  # <-- or this
            spam: Annotated[int, pydantic.Field(gt=4)] = 4  # <-- or this
        ```

        Args:
            annotation: The type annotation of the field.
            default: The default value of the field.

        Returns:
            A field object with the passed values.
        """
        if annotation is not MISSING and annotation is default:
            raise PydanticUserError(
                'Error when building FieldInfo from annotated attribute. '
                "Make sure you don't have any field name clashing with a type annotation.",
                code='unevaluable-type-annotation',
            )

        metadata: list[Any]
        qualifiers: set[Qualifier] | None
        if isinstance(annotation, type) and annotation is not dataclasses.InitVar:
            # Fast path for plain classes (the most common case), where no qualifier and no
            # metadata can be present (a bare `InitVar` — which is a class — is a qualifier):
            type_expr: Any = annotation
            metadata = []
            qualifiers = None
        else:
            try:
                inspected_ann = inspect_annotation(
                    annotation,
                    annotation_source=_source,
                    unpack_type_aliases='skip',
                )
            except ForbiddenQualifier as e:
                raise PydanticForbiddenQualifier(e.qualifier, annotation)

            # TODO check for classvar and error?

            # TODO infer from the default, this can be done in v3 once we treat final fields with
            # a default as proper fields and not class variables:
            type_expr = Any if inspected_ann.type is UNKNOWN else inspected_ann.type
            metadata = inspected_ann.metadata
            qualifiers = inspected_ann.qualifiers

        attr_overrides: dict[str, Any] = {'annotation': type_expr}
        if qualifiers and 'final' in qualifiers:
            attr_overrides['frozen'] = True

        if type(default) is FieldSpec or isinstance(default, FieldInfo):
            # Either a `Field()` assignment, or a (final) `FieldInfo` instance (e.g. coming from
            # `model_fields` of another model). The assignment is merged as the last metadata element:
            metadata = metadata + [default]
            if qualifiers and 'init_var' in qualifiers:
                # Only relevant for dataclasses, when `f: InitVar[<type>] = Field(...)`
                # is used:
                attr_overrides['init_var'] = True
        elif isinstance(default, dataclasses.Field):
            metadata = metadata + [FieldInfo._from_dataclass_field(default)]
            if qualifiers and 'init_var' in qualifiers:
                attr_overrides['init_var'] = True
            if (init := getattr(default, 'init', None)) is not None:
                attr_overrides['init'] = init
            if (kw_only := getattr(default, 'kw_only', None)) is not None:
                attr_overrides['kw_only'] = kw_only
        else:
            # `default` is the actual default value
            attr_overrides['default'] = default

        field_info = FieldInfo._construct(metadata, attr_overrides)
        if qualifiers is not None:
            field_info._qualifiers = qualifiers
        return field_info

    @classmethod
    def _construct(cls, metadata: list[Any], attr_overrides: dict[str, Any] | None) -> Self:
        """Construct the final `FieldInfo` instance, by merging the field specifications from the metadata.

        With the following example:

        ```python {test="skip" lint="skip"}
        class Model(BaseModel):
            f: Annotated[int, Gt(1), Field(description='desc', lt=2)]
        ```

        `metadata` refers to the metadata elements of the `Annotated` form. This metadata is iterated over from left to right:

        - If the element is a `FieldSpec` (i.e. the result of a `Field()` call), the field attributes (such as
          `description`) are saved to be set on the final `FieldInfo` instance, and the constraint arguments
          (such as `lt`) are converted to their metadata class counterpart (such as `annotated_types.Lt`) and
          appended to the final metadata list, in order.
        - If the element is a (final) `FieldInfo` instance (e.g. an instance coming from `model_fields` of another
          model), *all* of its attributes are used, and its metadata list is appended to the final metadata list.
          This makes patterns such as "make partial model" utilities (mutating `FieldInfo` instances from
          `model_fields` and reusing them in new models) work as expected.
        - Else, the element is considered as a single metadata object, and is appended to the final metadata list.

        Args:
            metadata: The list of metadata elements to merge together. If the `FieldInfo` instance to be constructed is for
                a field with an assigned `Field()`, this `Field()` assignment should be added as the last element of the
                provided metadata.
            attr_overrides: Extra attributes that should be set on the final merged `FieldInfo` instance.

        Returns:
            The final merged `FieldInfo` instance.
        """
        merged_metadata: list[Any] = []
        merged_kwargs: dict[str, Any] = {}
        metadata_lookup = cls.metadata_lookup

        for meta in metadata:
            if type(meta) is FieldSpec:
                general_metadata: dict[str, Any] | None = None
                for key, value in meta.kwargs.items():
                    if key in metadata_lookup:
                        # A constraint keyword argument (e.g. `gt`), converted to its metadata
                        # class counterpart (`None` values are ignored, meaning constraints can't
                        # be unset by a later `Field()` specification):
                        if value is None:
                            continue
                        marker = metadata_lookup[key]
                        if marker is None:
                            if general_metadata is None:
                                general_metadata = {}
                            general_metadata[key] = value
                        else:
                            merged_metadata.append(marker(value))
                    elif key == 'json_schema_extra':
                        existing_js_extra = merged_kwargs.get('json_schema_extra')
                        if existing_js_extra is not None and value is not None:
                            value = _merge_json_schema_extra(existing_js_extra, value)
                        merged_kwargs[key] = value
                    else:
                        merged_kwargs[key] = value
                if general_metadata is not None:
                    merged_metadata.append(_fields.pydantic_general_metadata(**general_metadata))
            elif isinstance(meta, FieldInfo):
                # A (final) `FieldInfo` instance, e.g. coming from `model_fields` of another model.
                # All of its attributes are used, so that mutations of such instances are correctly
                # picked up (see the `_construct()` docstring for more details):
                merged_metadata.extend(meta.metadata)
                existing_js_extra = merged_kwargs.get('json_schema_extra')
                for attr in _Attrs:
                    merged_kwargs[attr] = getattr(meta, attr)
                current_js_extra = meta.json_schema_extra
                if existing_js_extra is not None and current_js_extra is not None:
                    merged_kwargs['json_schema_extra'] = _merge_json_schema_extra(existing_js_extra, current_js_extra)
            elif typing_objects.is_deprecated(meta):
                merged_kwargs['deprecated'] = meta
            else:
                merged_metadata.append(meta)

        if attr_overrides:
            merged_kwargs.update(attr_overrides)
        merged_field_info = object.__new__(cls)
        if merged_kwargs.keys() <= _FAST_PATH_ATTRS:
            # Fast path for the most common case, where only the annotation
            # (and possibly a plain default value) is provided:
            merged_field_info._apply_default_attrs(
                merged_kwargs.get('annotation'), merged_kwargs.get('default', PydanticUndefined)
            )
        else:
            merged_field_info._apply_attrs(merged_kwargs)
        merged_field_info.metadata = merged_metadata
        return merged_field_info

    @staticmethod
    @typing_extensions.deprecated(
        "The 'merge_field_infos()' method is deprecated and will be removed in a future version. "
        'If you relied on this method, please open an issue in the Pydantic issue tracker.',
        category=None,
    )
    def merge_field_infos(*field_infos: FieldInfo, **overrides: Any) -> FieldInfo:
        """Merge `FieldInfo` instances keeping only explicitly set attributes.

        Later `FieldInfo` instances override earlier ones.

        Returns:
            FieldInfo: A merged FieldInfo instance.
        """
        if len(field_infos) == 1:
            # No merging necessary, but we still need to make a copy and apply the overrides
            field_info = field_infos[0]._copy()

            default_override = overrides.pop('default', PydanticUndefined)
            if default_override is Ellipsis:
                default_override = PydanticUndefined
            if default_override is not PydanticUndefined:
                field_info.default = default_override

            for k, v in overrides.items():
                setattr(field_info, k, v)
            return field_info  # type: ignore

        merged_field_info_kwargs: dict[str, Any] = {}
        metadata = {}
        for field_info in field_infos:
            attributes = {attr: getattr(field_info, attr) for attr in _Attrs}

            json_schema_extra = attributes.pop('json_schema_extra')
            if json_schema_extra is not None:
                existing_json_schema_extra = merged_field_info_kwargs.get('json_schema_extra')
                if existing_json_schema_extra is not None:
                    merged_field_info_kwargs['json_schema_extra'] = _merge_json_schema_extra(
                        existing_json_schema_extra, json_schema_extra
                    )
                else:
                    merged_field_info_kwargs['json_schema_extra'] = json_schema_extra

            # later FieldInfo instances override everything except json_schema_extra from earlier FieldInfo instances
            merged_field_info_kwargs.update(attributes)

            for x in field_info.metadata:
                if not isinstance(x, FieldInfo):
                    metadata[type(x)] = x

        merged_field_info_kwargs.update(overrides)
        field_info = FieldInfo(**merged_field_info_kwargs)
        field_info.metadata = list(metadata.values())
        return field_info

    @staticmethod
    def _from_dataclass_field(dc_field: DataclassField[Any]) -> FieldSpec:
        """Return a new `FieldSpec` instance from a `dataclasses.Field` instance.

        Args:
            dc_field: The `dataclasses.Field` instance to convert.

        Returns:
            The corresponding `FieldSpec` instance.
        """
        kwargs: dict[str, Any] = {k: v for k, v in dc_field.metadata.items() if k in _KNOWN_FIELD_KWARGS}
        if dc_field.default is not dataclasses.MISSING:
            kwargs['default'] = dc_field.default
        if dc_field.default_factory is not dataclasses.MISSING:
            kwargs['default_factory'] = dc_field.default_factory
        kwargs['repr'] = dc_field.repr
        if sys.version_info >= (3, 14) and dc_field.doc is not None:
            kwargs['description'] = dc_field.doc
        return FieldSpec(kwargs)

    @staticmethod
    def _collect_constraints(kwargs: dict[str, Any]) -> list[Any]:
        """Collect the constraint keyword arguments (e.g. `gt`) as metadata objects.

        Args:
            kwargs: Keyword arguments passed to the function. Constraint-related keys are *not* removed
                from the mapping (they are ignored by `_apply_attrs()`).

        Returns:
            A list of metadata objects - a combination of `annotated_types.BaseMetadata` and
                `PydanticMetadata`.
        """
        metadata: list[Any] = []
        general_metadata = {}
        metadata_lookup = FieldInfo.metadata_lookup
        for key, value in kwargs.items():
            if key not in metadata_lookup or value is None:
                continue
            marker = metadata_lookup[key]
            if marker is None:
                general_metadata[key] = value
            else:
                metadata.append(marker(value))
        if general_metadata:
            metadata.append(_fields.pydantic_general_metadata(**general_metadata))
        return metadata

    @property
    def deprecation_message(self) -> str | None:
        """The deprecation message to be emitted, or `None` if not set."""
        if self.deprecated is None:
            return None
        if isinstance(self.deprecated, bool):
            return 'deprecated' if self.deprecated else None
        return self.deprecated if isinstance(self.deprecated, str) else self.deprecated.message

    @property
    def default_factory_takes_validated_data(self) -> bool | None:
        """Whether the provided default factory callable has a validated data parameter.

        Returns `None` if no default factory is set.
        """
        if self.default_factory is not None:
            return _fields.takes_validated_data_argument(self.default_factory)

    @overload
    def get_default(
        self, *, call_default_factory: Literal[True], validated_data: dict[str, Any] | None = None
    ) -> Any: ...

    @overload
    def get_default(self, *, call_default_factory: Literal[False] = ...) -> Any: ...

    def get_default(self, *, call_default_factory: bool = False, validated_data: dict[str, Any] | None = None) -> Any:
        """Get the default value.

        We expose an option for whether to call the default_factory (if present), as calling it may
        result in side effects that we want to avoid. However, there are times when it really should
        be called (namely, when instantiating a model via `model_construct`).

        Args:
            call_default_factory: Whether to call the default factory or not.
            validated_data: The already validated data to be passed to the default factory.

        Returns:
            The default value, calling the default factory if requested or `PydanticUndefined` if not set.
        """
        return _fields.resolve_default_value(
            default=self.default,
            default_factory=self.default_factory,
            default_factory_takes_validated_data_argument=self.default_factory_takes_validated_data,
            validated_data=validated_data,
            call_default_factory=call_default_factory,
        )

    def is_required(self) -> bool:
        """Check if the field is required (i.e., does not have a default value or factory).

        Returns:
            `True` if the field is required, `False` otherwise.
        """
        return self.default is PydanticUndefined and self.default_factory is None

    def rebuild_annotation(self) -> Any:
        """Attempts to rebuild the original annotation for use in function signatures.

        If metadata is present, it adds it to the original annotation using
        `Annotated`. Otherwise, it returns the original annotation as-is.

        Note that because the metadata has been flattened, the original annotation
        may not be reconstructed exactly as originally provided, e.g. if the original
        type had unrecognized annotations, or was annotated with a call to `pydantic.Field`.

        Returns:
            The rebuilt annotation.
        """
        if not self.metadata:
            return self.annotation
        else:
            # Annotated arguments must be a tuple
            return Annotated[(self.annotation, *self.metadata)]  # type: ignore

    def apply_typevars_map(
        self,
        typevars_map: Mapping[TypeVar, Any] | None,
        globalns: GlobalsNamespace | None = None,
        localns: MappingNamespace | None = None,
    ) -> None:
        """Apply a `typevars_map` to the annotation.

        This method is used when analyzing parametrized generic types to replace typevars with their concrete types.

        This method applies the `typevars_map` to the annotation in place.

        Args:
            typevars_map: A dictionary mapping type variables to their concrete types.
            globalns: The globals namespace to use during type annotation evaluation.
            localns: The locals namespace to use during type annotation evaluation.

        See Also:
            pydantic._internal._generics.replace_types is used for replacing the typevars with
                their concrete types.
        """
        annotation = _generics.replace_types(self.annotation, typevars_map)
        annotation, evaluated = _typing_extra.try_eval_type(annotation, globalns, localns)
        self.annotation = annotation
        if not evaluated:
            self._complete = False
            self._original_annotation = self.annotation

    def asdict(self) -> _FieldInfoAsDict:
        """Return a dictionary representation of the `FieldInfo` instance.

        The returned value is a dictionary with three items:

        * `annotation`: The type annotation of the field.
        * `metadata`: The metadata list.
        * `attributes`: A mapping of the remaining `FieldInfo` attributes to their values (e.g. `alias`, `title`).
        """
        return {
            'annotation': self.annotation,
            'metadata': self.metadata,
            'attributes': {attr: getattr(self, attr) for attr in _Attrs},
        }

    def _copy(self) -> Self:
        """Return a copy of the `FieldInfo` instance."""
        # Note: we can't define a custom `__copy__()`, as `FieldInfo` is being subclassed
        # by some third-party libraries with extra attributes defined (and as `FieldInfo`
        # is slotted, we can't make a copy of the `__dict__`).
        if type(self) is FieldInfo:
            # Fast-path if the instance isn't a subclass (`copy.copy()` relies on pickling which is slower):
            copied = FieldInfo.__new__(FieldInfo)
            for attr_name in FieldInfo.__slots__:
                setattr(copied, attr_name, getattr(self, attr_name))
        else:
            copied = copy(self)

        for attr_name in ('metadata', '_qualifiers'):
            # Apply "deep-copy" behavior on collections attributes:
            setattr(copied, attr_name, getattr(copied, attr_name).copy())

        return copied  # pyright: ignore[reportReturnType]

    def __repr_args__(self) -> ReprArgs:
        yield 'annotation', _repr.PlainRepr(_repr.display_as_type(self.annotation))
        yield 'required', self.is_required()

        for s in self.__slots__:
            # TODO: properly make use of the protocol (https://rich.readthedocs.io/en/stable/pretty.html#rich-repr-protocol)
            # By yielding a three-tuple:
            if s in (
                'annotation',
                '_qualifiers',
                '_complete',
                '_original_assignment',
                '_original_annotation',
            ):
                continue
            elif s == 'metadata' and not self.metadata:
                continue
            elif s == 'repr' and self.repr is True:
                continue
            if s == 'frozen' and self.frozen is False:
                continue
            if s == 'validation_alias' and self.validation_alias == self.alias:
                continue
            if s == 'serialization_alias' and self.serialization_alias == self.alias:
                continue
            if s == 'default' and self.default is not PydanticUndefined:
                yield 'default', self.default
            elif s == 'default_factory' and self.default_factory is not None:
                yield 'default_factory', _repr.PlainRepr(_repr.display_as_type(self.default_factory))
            else:
                value = getattr(self, s)
                if value is not None and value is not PydanticUndefined:
                    yield s, value


class _EmptyKwargs(TypedDict):
    """This class exists solely to ensure that type checking warns about passing `**extra` in `Field`."""


_Attrs: tuple[str, ...] = (
    'default',
    'default_factory',
    'alias',
    'alias_priority',
    'validation_alias',
    'serialization_alias',
    'title',
    'field_title_generator',
    'description',
    'examples',
    'exclude',
    'exclude_if',
    'discriminator',
    'deprecated',
    'json_schema_extra',
    'frozen',
    'validate_default',
    'repr',
    'init',
    'init_var',
    'kw_only',
)
"""The `FieldInfo` attribute names (every attribute except `annotation` and `metadata`)."""

_KNOWN_FIELD_KWARGS = frozenset(_FieldInfoInputs.__annotations__) - {'annotation'}
"""The keyword arguments accepted by the `Field()` function."""

_FAST_PATH_ATTRS = frozenset({'annotation', 'default'})
"""The attributes that can be set by the `FieldInfo._apply_default_attrs()` fast path."""


def _merge_json_schema_extra(
    existing: JsonDict | Callable[[JsonDict], None], current: JsonDict | Callable[[JsonDict], None]
) -> JsonDict | Callable[[JsonDict], None]:
    """Merge two `json_schema_extra` values, warning if a `dict` and a `callable` are being composed."""
    if isinstance(existing, dict):
        if isinstance(current, dict):
            return {**existing, **current}
        elif callable(current):
            warn(
                'Composing `dict` and `callable` type `json_schema_extra` is not supported. '
                'The `callable` type is being ignored. '
                "If you'd like support for this behavior, please open an issue on pydantic.",
                UserWarning,
            )
            return existing
    elif callable(existing) and isinstance(current, dict):
        warn(
            'Composing `dict` and `callable` type `json_schema_extra` is not supported. '
            'The `callable` type is being ignored. '
            "If you'd like support for this behavior, please open an issue on pydantic.",
            UserWarning,
        )
    return current


_T = TypeVar('_T')


# NOTE: Actual return type is 'FieldInfo', but we want to help type checkers
# to understand the magic that happens at runtime with the following overloads:
@overload  # type hint the return value as `Any` to avoid type checking regressions when using `...`.
def Field(
    default: EllipsisType,
    *,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: str | AliasPath | AliasChoices | None = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: Callable[[str, FieldInfo], str] | None = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | types.Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = _Unset,
    frozen: bool | None = _Unset,
    validate_default: bool | None = _Unset,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | re.Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: annotated_types.SupportsGt | None = _Unset,
    ge: annotated_types.SupportsGe | None = _Unset,
    lt: annotated_types.SupportsLt | None = _Unset,
    le: annotated_types.SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal['smart', 'left_to_right'] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs],
) -> Any: ...
@overload  # `default` argument set, validate_default=True (no type checking on the default value)
def Field(
    default: Any,
    *,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: str | AliasPath | AliasChoices | None = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: Callable[[str, FieldInfo], str] | None = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | types.Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = _Unset,
    frozen: bool | None = _Unset,
    validate_default: Literal[True],
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | re.Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: annotated_types.SupportsGt | None = _Unset,
    ge: annotated_types.SupportsGe | None = _Unset,
    lt: annotated_types.SupportsLt | None = _Unset,
    le: annotated_types.SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal['smart', 'left_to_right'] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs],
) -> Any: ...
@overload  # `default` argument set, validate_default=False or unset
def Field(
    default: _T,
    *,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: str | AliasPath | AliasChoices | None = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: Callable[[str, FieldInfo], str] | None = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    # NOTE: to get proper type checking on `exclude_if`'s argument, we could use `_T` instead of `Any`. However,
    # this requires (at least for pyright) adding an additional overload where `exclude_if` is required (otherwise
    # `a: int = Field(default_factory=str)` results in a false negative).
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | types.Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = _Unset,
    frozen: bool | None = _Unset,
    validate_default: Literal[False] = ...,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | re.Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: annotated_types.SupportsGt | None = _Unset,
    ge: annotated_types.SupportsGe | None = _Unset,
    lt: annotated_types.SupportsLt | None = _Unset,
    le: annotated_types.SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal['smart', 'left_to_right'] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs],
) -> _T: ...
@overload  # `default_factory` argument set, validate_default=True  (no type checking on the default value)
def Field(  # pyright: ignore[reportOverlappingOverload]
    *,
    default_factory: Callable[[], Any] | Callable[[dict[str, Any]], Any],
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: str | AliasPath | AliasChoices | None = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: Callable[[str, FieldInfo], str] | None = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | types.Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = _Unset,
    frozen: bool | None = _Unset,
    validate_default: Literal[True],
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | re.Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: annotated_types.SupportsGt | None = _Unset,
    ge: annotated_types.SupportsGe | None = _Unset,
    lt: annotated_types.SupportsLt | None = _Unset,
    le: annotated_types.SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal['smart', 'left_to_right'] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs],
) -> Any: ...
@overload  # `default_factory` argument set, validate_default=False or unset
def Field(
    *,
    default_factory: Callable[[], _T] | Callable[[dict[str, Any]], _T],
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: str | AliasPath | AliasChoices | None = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: Callable[[str, FieldInfo], str] | None = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    # NOTE: to get proper type checking on `exclude_if`'s argument, we could use `_T` instead of `Any`. However,
    # this requires (at least for pyright) adding an additional overload where `exclude_if` is required (otherwise
    # `a: int = Field(default_factory=str)` results in a false negative).
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | types.Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = _Unset,
    frozen: bool | None = _Unset,
    validate_default: Literal[False] | None = _Unset,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | re.Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: annotated_types.SupportsGt | None = _Unset,
    ge: annotated_types.SupportsGe | None = _Unset,
    lt: annotated_types.SupportsLt | None = _Unset,
    le: annotated_types.SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal['smart', 'left_to_right'] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs],
) -> _T: ...
@overload
def Field(  # No default set
    *,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: str | AliasPath | AliasChoices | None = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: Callable[[str, FieldInfo], str] | None = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | types.Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = _Unset,
    frozen: bool | None = _Unset,
    validate_default: bool | None = _Unset,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | re.Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: annotated_types.SupportsGt | None = _Unset,
    ge: annotated_types.SupportsGe | None = _Unset,
    lt: annotated_types.SupportsLt | None = _Unset,
    le: annotated_types.SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal['smart', 'left_to_right'] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs],
) -> Any: ...
def Field(  # noqa: D417 (each keyword argument is documented individually)
    default: Any = PydanticUndefined,
    **kwargs: Any,
) -> Any:
    """!!! abstract "Usage Documentation"
        [Fields](../concepts/fields.md)

    Create a field for objects that can be configured.

    Used to provide extra information about a field, either for the model schema or complex validation. Some arguments
    apply only to number fields (`int`, `float`, `Decimal`) and some apply only to `str`.

    Args:
        default: Default value if the field is not set.
        default_factory: A callable to generate the default value. The callable can either take 0 arguments
            (in which case it is called as is) or a single argument containing the already validated data.
        alias: The name to use for the attribute when validating or serializing by alias.
            This is often used for things like converting between snake and camel case.
        alias_priority: Priority of the alias. This affects whether an alias generator is used.
        validation_alias: Like `alias`, but only affects validation, not serialization.
        serialization_alias: Like `alias`, but only affects serialization, not validation.
        title: Human-readable title.
        field_title_generator: A callable that takes a field's name and info and returns title for it.
        description: Human-readable description.
        examples: Example values for this field.
        exclude: Whether to exclude the field from the model serialization.
        exclude_if: A callable that determines whether to exclude a field during serialization based on its value.
        discriminator: Field name or Discriminator for discriminating the type in a tagged union.
        deprecated: A deprecation message, an instance of `warnings.deprecated` or the `typing_extensions.deprecated` backport,
            or a boolean. If `True`, a default deprecation message will be emitted when accessing the field.
        json_schema_extra: A dict or callable to provide extra JSON schema properties.
        frozen: Whether the field is frozen. If true, attempts to change the value on an instance will raise an error.
        validate_default: If `True`, apply validation to the default value every time you create an instance.
            Otherwise, for performance reasons, the default value of the field is trusted and not validated.
        repr: A boolean indicating whether to include the field in the `__repr__` output.
        init: Whether the field should be included in the constructor of the dataclass.
            (Only applies to dataclasses.)
        init_var: Whether the field should _only_ be included in the constructor of the dataclass.
            (Only applies to dataclasses.)
        kw_only: Whether the field should be a keyword-only argument in the constructor of the dataclass.
            (Only applies to dataclasses.)
        coerce_numbers_to_str: Whether to enable coercion of any `Number` type to `str` (not applicable in `strict` mode).
        strict: If `True`, strict validation is applied to the field.
            See [Strict Mode](../concepts/strict_mode.md) for details.
        gt: Greater than. If set, value must be greater than this. Only applicable to numbers.
        ge: Greater than or equal. If set, value must be greater than or equal to this. Only applicable to numbers.
        lt: Less than. If set, value must be less than this. Only applicable to numbers.
        le: Less than or equal. If set, value must be less than or equal to this. Only applicable to numbers.
        multiple_of: Value must be a multiple of this. Only applicable to numbers.
        min_length: Minimum length for iterables.
        max_length: Maximum length for iterables.
        pattern: Pattern for strings (a regular expression).
        allow_inf_nan: Allow `inf`, `-inf`, `nan`. Only applicable to float and [`Decimal`][decimal.Decimal] numbers.
        max_digits: Maximum number of allowed digits for [`Decimal`][decimal.Decimal] numbers.
        decimal_places: Maximum number of decimal places allowed for numbers.
        union_mode: The strategy to apply when validating a union. Can be `smart` (the default), or `left_to_right`.
            See [Union Mode](../concepts/unions.md#union-modes) for details.
        fail_fast: If `True`, validation will stop on the first error. If `False`, all validation errors will be collected.
            This option can be applied only to iterable types (list, tuple, set, and frozenset).
        extra: (Deprecated) Extra fields that will be included in the JSON schema.

            !!! warning Deprecated
                The `extra` kwargs is deprecated. Use `json_schema_extra` instead.

    Returns:
        A new [`FieldSpec`][pydantic.fields.FieldSpec] instance, storing the provided arguments. The return
            annotation is `Any` so `Field` can be used on type-annotated fields without causing a type error.
    """
    if not kwargs.keys() <= _KNOWN_FIELD_KWARGS:
        # Slow path, only entered when deprecated/removed/extra keyword arguments are used:
        _process_deprecated_field_kwargs(kwargs)
    if default is not PydanticUndefined and default is not Ellipsis:
        if kwargs.get('default_factory') is not None:
            raise TypeError('cannot specify both default and default_factory')
        kwargs['default'] = default
    return FieldSpec(kwargs)


def _process_deprecated_field_kwargs(kwargs: dict[str, Any]) -> None:
    """Process the deprecated and removed `Field()` keyword arguments from V1, mutating `kwargs` in place.

    This logic should eventually be removed.
    """
    if 'annotation' in kwargs:
        raise TypeError('"annotation" is not permitted as a Field keyword argument')

    if kwargs.pop('const', None) is not None:
        raise PydanticUserError('`const` is removed, use `Literal` instead', code='removed-kwargs')

    min_items = kwargs.pop('min_items', None)
    if min_items is not None:
        warn(
            '`min_items` is deprecated and will be removed, use `min_length` instead',
            PydanticDeprecatedSince20,
            stacklevel=3,
        )
        if kwargs.get('min_length') is None:
            kwargs['min_length'] = min_items

    max_items = kwargs.pop('max_items', None)
    if max_items is not None:
        warn(
            '`max_items` is deprecated and will be removed, use `max_length` instead',
            PydanticDeprecatedSince20,
            stacklevel=3,
        )
        if kwargs.get('max_length') is None:
            kwargs['max_length'] = max_items

    if kwargs.pop('unique_items', None) is not None:
        raise PydanticUserError(
            (
                '`unique_items` is removed, use `Set` instead'
                '(this feature is discussed in https://github.com/pydantic/pydantic-core/issues/296)'
            ),
            code='removed-kwargs',
        )

    allow_mutation = kwargs.pop('allow_mutation', None)
    if allow_mutation is not None:
        warn(
            '`allow_mutation` is deprecated and will be removed. use `frozen` instead',
            PydanticDeprecatedSince20,
            stacklevel=3,
        )
        if allow_mutation is False:
            kwargs['frozen'] = True

    if kwargs.pop('regex', None) is not None:
        raise PydanticUserError('`regex` is removed. use `pattern` instead', code='removed-kwargs')

    if kwargs.pop('include', None) is not None:
        warn(
            '`include` is deprecated and does nothing. It will be removed, use `exclude` instead',
            PydanticDeprecatedSince20,
            stacklevel=3,
        )

    extra = {k: kwargs.pop(k) for k in [k for k in kwargs if k not in _KNOWN_FIELD_KWARGS]}
    if extra:
        warn(
            'Using extra keyword arguments on `Field` is deprecated and will be removed.'
            ' Use `json_schema_extra` instead.'
            f' (Extra keys: {", ".join(k.__repr__() for k in extra.keys())})',
            PydanticDeprecatedSince20,
            stacklevel=3,
        )
        if not kwargs.get('json_schema_extra'):
            kwargs['json_schema_extra'] = extra


_FIELD_ARG_NAMES = _KNOWN_FIELD_KWARGS
"""Deprecated alias of `_KNOWN_FIELD_KWARGS` (kept as it was used by third-party code)."""


class ModelPrivateAttr(_repr.Representation):
    """A descriptor for private attributes in class models.

    !!! warning
        You generally shouldn't be creating `ModelPrivateAttr` instances directly, instead use
        the [`PrivateAttr()`][pydantic.fields.PrivateAttr] function.

    Attributes:
        default: The default value of the attribute if not provided.
        default_factory: A callable to generate the default value. The callable can either take 0 arguments
            (in which case it is called as is) or a single argument containing the validated data (the model's
            [`__dict__`][object.__dict__]) and the already initialized private attributes.
    """

    __slots__ = ('default', 'default_factory', '_default_factory_takes_validated_data')

    def __init__(
        self,
        default: Any = PydanticUndefined,
        *,
        default_factory: Callable[[], Any] | Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        if default is Ellipsis:
            self.default = PydanticUndefined
        else:
            self.default = default
        self.default_factory = default_factory
        self._default_factory_takes_validated_data: bool | None = _Unset

    if not TYPE_CHECKING:
        # We put `__getattr__` in a non-TYPE_CHECKING block because otherwise, mypy allows arbitrary attribute access

        def __getattr__(self, item: str) -> Any:
            """This function improves compatibility with custom descriptors by ensuring delegation happens
            as expected when the default value of a private attribute is a descriptor.
            """
            if item in {'__get__', '__set__', '__delete__'}:
                if hasattr(self.default, item):
                    return getattr(self.default, item)
            raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')

    def __set_name__(self, cls: type[Any], name: str) -> None:
        """Preserve `__set_name__` protocol defined in https://peps.python.org/pep-0487."""
        default = self.default
        if default is PydanticUndefined:
            return
        set_name = getattr(default, '__set_name__', None)
        if callable(set_name):
            set_name(cls, name)

    @property
    def default_factory_takes_validated_data(self) -> bool | None:
        """Whether the provided default factory callable has a validated data parameter.

        Returns `None` if no default factory is set.
        """
        if self._default_factory_takes_validated_data is not _Unset:
            return self._default_factory_takes_validated_data

        value: bool | None = None
        if self.default_factory is not None:
            value = _fields.takes_validated_data_argument(self.default_factory)

        self._default_factory_takes_validated_data = value
        return value

    @overload
    def get_default(
        self, *, call_default_factory: Literal[True], validated_data: dict[str, Any] | None = None
    ) -> Any: ...

    @overload
    def get_default(self, *, call_default_factory: Literal[False] = ...) -> Any: ...

    def get_default(self, *, call_default_factory: bool = False, validated_data: dict[str, Any] | None = None) -> Any:
        """Get the default value.

        We expose an option for whether to call the default_factory (if present), as calling it may
        result in side effects that we want to avoid. However, there are times when it really should
        be called (namely, when instantiating a model via `model_construct`).

        Args:
            call_default_factory: Whether to call the default factory or not.
            validated_data: The already validated data to be passed to the default factory.

        Returns:
            The default value, calling the default factory if requested or `None` if not set.
        """
        return _fields.resolve_default_value(
            default=self.default,
            default_factory=self.default_factory,
            default_factory_takes_validated_data_argument=self.default_factory_takes_validated_data,
            validated_data=validated_data,
            call_default_factory=call_default_factory,
        )

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and (self.default, self.default_factory) == (
            other.default,
            other.default_factory,
        )

    def __repr_args__(self) -> ReprArgs:
        if self.default is not PydanticUndefined:
            yield 'default', self.default
        if self.default_factory is not None:
            yield 'default_factory', self.default_factory


# NOTE: Actual return type is 'ModelPrivateAttr', but we want to help type checkers
# to understand the magic that happens at runtime.
@overload  # `default` argument set
def PrivateAttr(
    default: _T,
    *,
    init: Literal[False] = False,
) -> _T: ...
@overload  # `default_factory` argument set
def PrivateAttr(
    *,
    default_factory: Callable[[], _T] | Callable[[dict[str, Any]], _T],
    init: Literal[False] = False,
) -> _T: ...
@overload  # No default set
def PrivateAttr(
    *,
    init: Literal[False] = False,
) -> Any: ...
def PrivateAttr(
    default: Any = PydanticUndefined,
    *,
    default_factory: Callable[[], Any] | Callable[[dict[str, Any]], Any] | None = None,
    init: Literal[False] = False,
) -> Any:
    """!!! abstract "Usage Documentation"
        [Private Model Attributes](../concepts/models.md#private-model-attributes)

    Indicates that an attribute is intended for private use and not handled during normal validation/serialization.

    Private attributes are not validated by Pydantic, so it's up to you to ensure they are used in a type-safe manner.

    Private attributes are stored in `__private_attributes__` on the model.

    Args:
        default: The attribute's default value. Defaults to Undefined.
        default_factory: A callable to generate the default value. The callable can either take 0 arguments
            (in which case it is called as is) or a single argument containing the validated data (the model's
            [`__dict__`][object.__dict__]) and the already initialized private attributes.
            If both `default` and `default_factory` are set, an error will be raised.
        init: Whether the attribute should be included in the constructor of the dataclass. Always `False`.

    Returns:
        An instance of [`ModelPrivateAttr`][pydantic.fields.ModelPrivateAttr] class.

    Raises:
        TypeError: If both `default` and `default_factory` are set.
    """
    if default is not PydanticUndefined and default_factory is not None:
        raise TypeError('cannot specify both default and default_factory')

    return ModelPrivateAttr(
        default,
        default_factory=default_factory,
    )


@dataclasses.dataclass(slots=True)
class ComputedFieldInfo:
    """A container for data from `@computed_field` so that we can access it while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@computed_field'.
        wrapped_property: The wrapped computed field property.
        return_type: The type of the computed field property's return value.
        alias: The alias of the property to be used during serialization.
        alias_priority: The priority of the alias. This affects whether an alias generator is used.
        title: Title of the computed field to include in the serialization JSON schema.
        field_title_generator: A callable that takes a field's name and info and returns title for it.
        description: Description of the computed field to include in the serialization JSON schema.
        deprecated: A deprecation message, an instance of `warnings.deprecated` or the `typing_extensions.deprecated` backport,
            or a boolean. If `True`, a default deprecation message will be emitted when accessing the field.
        examples: Example values of the computed field to include in the serialization JSON schema.
        json_schema_extra: A dict or callable to provide extra JSON schema properties.
        repr: A boolean indicating whether to include the field in the __repr__ output.
    """

    decorator_repr: ClassVar[str] = '@computed_field'
    wrapped_property: property
    return_type: Any
    alias: str | None
    alias_priority: int | None
    exclude_if: Callable[[Any], bool] | None
    title: str | None
    field_title_generator: Callable[[str, ComputedFieldInfo], str] | None
    description: str | None
    deprecated: Deprecated | str | bool | None
    examples: list[Any] | None
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None
    repr: bool
    # NOTE: if you add a new field, add it to the `__copy__()` implementation.

    def __copy__(self) -> Self:
        return type(self)(
            wrapped_property=self.wrapped_property,
            return_type=self.return_type,
            alias=self.alias,
            alias_priority=self.alias_priority,
            exclude_if=self.exclude_if,
            title=self.title,
            field_title_generator=self.field_title_generator,
            description=self.description,
            deprecated=self.deprecated,
            examples=self.examples.copy() if isinstance(self.examples, list) else self.examples,
            json_schema_extra=self.json_schema_extra.copy()
            if isinstance(self.json_schema_extra, dict)
            else self.json_schema_extra,
            repr=self.repr,
        )

    @property
    def deprecation_message(self) -> str | None:
        """The deprecation message to be emitted, or `None` if not set."""
        if self.deprecated is None:
            return None
        if isinstance(self.deprecated, bool):
            return 'deprecated' if self.deprecated else None
        return self.deprecated if isinstance(self.deprecated, str) else self.deprecated.message

    def _update_from_config(self, config_wrapper: ConfigWrapper, name: str) -> None:
        """Update the instance from the configuration set on the class this computed field belongs to."""
        title_generator = self.field_title_generator or config_wrapper.field_title_generator
        if title_generator is not None and self.title is None:
            self.title = title_generator(name, self)
        if config_wrapper.alias_generator is not None:
            self._apply_alias_generator(config_wrapper.alias_generator, name)

    def _apply_alias_generator(self, alias_generator: Callable[[str], str] | AliasGenerator, name: str) -> None:
        """Apply an alias generator to aliases if appropriate.

        Args:
            alias_generator: A callable that takes a string and returns a string, or an `AliasGenerator` instance.
            name: The name of the computed field from which to generate the alias.
        """
        # Apply an alias_generator if
        # 1. An alias is not specified
        # 2. An alias is specified, but the priority is <= 1

        if self.alias_priority is None or self.alias_priority <= 1 or self.alias is None:
            alias, _, serialization_alias = None, None, None

            if isinstance(alias_generator, AliasGenerator):
                alias, _, serialization_alias = alias_generator.generate_aliases(name)
            elif callable(alias_generator):
                alias = alias_generator(name)

            # if priority is not set, we set to 1
            # which supports the case where the alias_generator from a child class is used
            # to generate an alias for a field in a parent class
            if self.alias_priority is None or self.alias_priority <= 1:
                self.alias_priority = 1

            # if the priority is 1, then we set the aliases to the generated alias
            # note that we use the serialization_alias with priority over alias, as computed_field
            # aliases are used for serialization only (not validation)
            if self.alias_priority == 1:
                self.alias = _utils.get_first_not_none(serialization_alias, alias)


def _wrapped_property_is_private(property_: cached_property | property) -> bool:  # type: ignore
    """Returns true if provided property is private, False otherwise."""
    wrapped_name: str = ''

    if isinstance(property_, property):
        wrapped_name = getattr(property_.fget, '__name__', '')
    elif isinstance(property_, cached_property):  # type: ignore
        wrapped_name = getattr(property_.func, '__name__', '')  # type: ignore

    return wrapped_name.startswith('_') and not wrapped_name.startswith('__')


# this should really be `property[T], cached_property[T]` but property is not generic unlike cached_property
# See https://github.com/python/typing/issues/985 and linked issues
PropertyT = TypeVar('PropertyT')


@overload
def computed_field(func: PropertyT, /) -> PropertyT: ...


@overload
def computed_field(
    *,
    alias: str | None = None,
    alias_priority: int | None = None,
    exclude_if: Callable[[Any], bool] | None = None,
    title: str | None = None,
    field_title_generator: Callable[[str, ComputedFieldInfo], str] | None = None,
    description: str | None = None,
    deprecated: Deprecated | str | bool | None = None,
    examples: list[Any] | None = None,
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = None,
    repr: bool = True,
    return_type: Any = PydanticUndefined,
) -> Callable[[PropertyT], PropertyT]: ...


def computed_field(
    func: PropertyT | None = None,
    /,
    *,
    alias: str | None = None,
    alias_priority: int | None = None,
    exclude_if: Callable[[Any], bool] | None = None,
    title: str | None = None,
    field_title_generator: Callable[[str, ComputedFieldInfo], str] | None = None,
    description: str | None = None,
    deprecated: Deprecated | str | bool | None = None,
    examples: list[Any] | None = None,
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = None,
    repr: bool | None = None,
    return_type: Any = PydanticUndefined,
) -> PropertyT | Callable[[PropertyT], PropertyT]:
    """!!! abstract "Usage Documentation"
        [The `computed_field` decorator](../concepts/fields.md#the-computed_field-decorator)

    Decorator to include `property` and `cached_property` when serializing models or dataclasses.

    This is useful for fields that are computed from other fields, or for fields that are expensive to compute and should be cached.

    ```python
    from pydantic import BaseModel, computed_field

    class Rectangle(BaseModel):
        width: int
        length: int

        @computed_field
        @property
        def area(self) -> int:
            return self.width * self.length

    print(Rectangle(width=3, length=2).model_dump())
    #> {'width': 3, 'length': 2, 'area': 6}
    ```

    If applied to functions not yet decorated with `@property` or `@cached_property`, the function is
    automatically wrapped with `property`. Although this is more concise, you will lose IntelliSense in your IDE,
    and confuse static type checkers, thus explicit use of `@property` is recommended.

    !!! warning "Mypy Warning"
        Even with the `@property` or `@cached_property` applied to your function before `@computed_field`,
        mypy may throw a `Decorated property not supported` error.
        See [mypy issue #1362](https://github.com/python/mypy/issues/1362), for more information.
        To avoid this error message, add `# type: ignore[prop-decorator]` to the `@computed_field` line.

        [pyright](https://github.com/microsoft/pyright) supports `@computed_field` without error.

    ```python
    import random

    from pydantic import BaseModel, computed_field

    class Square(BaseModel):
        width: float

        @computed_field
        def area(self) -> float:  # converted to a `property` by `computed_field`
            return round(self.width**2, 2)

        @area.setter
        def area(self, new_area: float) -> None:
            self.width = new_area**0.5

        @computed_field(alias='the magic number', repr=False)
        def random_number(self) -> int:
            return random.randint(0, 1_000)

    square = Square(width=1.3)

    # `random_number` does not appear in representation
    print(repr(square))
    #> Square(width=1.3, area=1.69)

    print(square.random_number)
    #> 3

    square.area = 4

    print(square.model_dump_json(by_alias=True))
    #> {"width":2.0,"area":4.0,"the magic number":3}
    ```

    !!! warning "Overriding with `computed_field`"
        You can't override a field from a parent class with a `computed_field` in the child class.
        `mypy` complains about this behavior if allowed, and `dataclasses` doesn't allow this pattern either.
        See the example below:

    ```python
    from pydantic import BaseModel, computed_field

    class Parent(BaseModel):
        a: str

    try:

        class Child(Parent):
            @computed_field
            @property
            def a(self) -> str:
                return 'new a'

    except TypeError as e:
        print(e)
        '''
        Field 'a' of class 'Child' overrides symbol of same name in a parent class. This override with a computed_field is incompatible.
        '''
    ```

    Private properties decorated with `@computed_field` have `repr=False` by default.

    ```python
    from functools import cached_property

    from pydantic import BaseModel, computed_field

    class Model(BaseModel):
        foo: int

        @computed_field
        @cached_property
        def _private_cached_property(self) -> int:
            return -self.foo

        @computed_field
        @property
        def _private_property(self) -> int:
            return -self.foo

    m = Model(foo=1)
    print(repr(m))
    #> Model(foo=1)
    ```

    Args:
        func: the function to wrap.
        alias: alias to use when serializing this computed field, only used when `by_alias=True`
        alias_priority: priority of the alias. This affects whether an alias generator is used
        exclude_if: A callable that determines whether to exclude this computed field during serialization based on its value.
        title: Title to use when including this computed field in JSON Schema
        field_title_generator: A callable that takes a field's name and info and returns title for it.
        description: Description to use when including this computed field in JSON Schema, defaults to the function's
            docstring
        deprecated: A deprecation message (or an instance of `warnings.deprecated` or the `typing_extensions.deprecated` backport).
            to be emitted when accessing the field. Or a boolean. This will automatically be set if the property is decorated with the
            `deprecated` decorator.
        examples: Example values to use when including this computed field in JSON Schema
        json_schema_extra: A dict or callable to provide extra JSON schema properties.
        repr: whether to include this computed field in model repr.
            Default is `False` for private properties and `True` for public properties.
        return_type: optional return for serialization logic to expect when serializing to JSON, if included
            this must be correct, otherwise a `TypeError` is raised.
            If you don't include a return type Any is used, which does runtime introspection to handle arbitrary
            objects.

    Returns:
        A proxy wrapper for the property.
    """

    def dec(f: Any) -> Any:
        nonlocal description, deprecated, return_type, alias_priority
        unwrapped = _decorators.unwrap_wrapped_function(f)

        if description is None and unwrapped.__doc__:
            description = inspect.cleandoc(unwrapped.__doc__)

        if deprecated is None and hasattr(unwrapped, '__deprecated__'):
            deprecated = unwrapped.__deprecated__

        # if the function isn't already decorated with `@property` (or another descriptor), then we wrap it now
        f = _decorators.ensure_property(f)
        alias_priority = (alias_priority or 2) if alias is not None else None

        if repr is None:
            repr_: bool = not _wrapped_property_is_private(property_=f)
        else:
            repr_ = repr

        dec_info = ComputedFieldInfo(
            f,
            return_type,
            alias,
            alias_priority,
            exclude_if,
            title,
            field_title_generator,
            description,
            deprecated,
            examples,
            json_schema_extra,
            repr_,
        )
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    if func is None:
        return dec
    else:
        return dec(func)
