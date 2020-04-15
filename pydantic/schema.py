import re
import warnings
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID

from .class_validators import ROOT_KEY
from .fields import (
    SHAPE_FROZENSET,
    SHAPE_ITERABLE,
    SHAPE_LIST,
    SHAPE_MAPPING,
    SHAPE_SEQUENCE,
    SHAPE_SET,
    SHAPE_SINGLETON,
    SHAPE_TUPLE,
    SHAPE_TUPLE_ELLIPSIS,
    FieldInfo,
    ModelField,
)
from .json import pydantic_encoder
from .networks import AnyUrl, EmailStr
from .types import (
    ConstrainedDecimal,
    ConstrainedFloat,
    ConstrainedInt,
    ConstrainedList,
    ConstrainedStr,
    conbytes,
    condecimal,
    confloat,
    conint,
    conlist,
    constr,
)
from .typing import ForwardRef, Literal, is_callable_type, is_literal_type, literal_values
from .utils import get_model, lenient_issubclass, sequence_like

if TYPE_CHECKING:
    from .main import BaseModel  # noqa: F401
    from .dataclasses import DataclassType  # noqa: F401

default_prefix = '#/definitions/'


def schema(
    models: Sequence[Union[Type['BaseModel'], Type['DataclassType']]],
    *,
    by_alias: bool = True,
    title: Optional[str] = None,
    description: Optional[str] = None,
    ref_prefix: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process a list of models and generate a single JSON Schema with all of them defined in the ``definitions``
    top-level JSON key, including their sub-models.

    :param models: a list of models to include in the generated JSON Schema
    :param by_alias: generate the schemas using the aliases defined, if any
    :param title: title for the generated schema that includes the definitions
    :param description: description for the generated schema
    :param ref_prefix: the JSON Pointer prefix for schema references with ``$ref``, if None, will be set to the
      default of ``#/definitions/``. Update it if you want the schemas to reference the definitions somewhere
      else, e.g. for OpenAPI use ``#/components/schemas/``. The resulting generated schemas will still be at the
      top-level key ``definitions``, so you can extract them from there. But all the references will have the set
      prefix.
    :return: dict with the JSON Schema with a ``definitions`` top-level key including the schema definitions for
      the models and sub-models passed in ``models``.
    """
    clean_models = [get_model(model) for model in models]
    ref_prefix = ref_prefix or default_prefix
    flat_models = get_flat_models_from_models(clean_models)
    model_name_map = get_model_name_map(flat_models)
    definitions = {}
    output_schema: Dict[str, Any] = {}
    if title:
        output_schema['title'] = title
    if description:
        output_schema['description'] = description
    for model in clean_models:
        m_schema, m_definitions, m_nested_models = model_process_schema(
            model, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(m_definitions)
        model_name = model_name_map[model]
        definitions[model_name] = m_schema
    if definitions:
        output_schema['definitions'] = definitions
    return output_schema


def model_schema(
    model: Union[Type['BaseModel'], Type['DataclassType']], by_alias: bool = True, ref_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a JSON Schema for one model. With all the sub-models defined in the ``definitions`` top-level
    JSON key.

    :param model: a Pydantic model (a class that inherits from BaseModel)
    :param by_alias: generate the schemas using the aliases defined, if any
    :param ref_prefix: the JSON Pointer prefix for schema references with ``$ref``, if None, will be set to the
      default of ``#/definitions/``. Update it if you want the schemas to reference the definitions somewhere
      else, e.g. for OpenAPI use ``#/components/schemas/``. The resulting generated schemas will still be at the
      top-level key ``definitions``, so you can extract them from there. But all the references will have the set
      prefix.
    :return: dict with the JSON Schema for the passed ``model``
    """
    model = get_model(model)
    ref_prefix = ref_prefix or default_prefix
    flat_models = get_flat_models_from_model(model)
    model_name_map = get_model_name_map(flat_models)
    model_name = model_name_map[model]
    m_schema, m_definitions, nested_models = model_process_schema(
        model, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
    )
    if model_name in nested_models:
        # model_name is in Nested models, it has circular references
        m_definitions[model_name] = m_schema
        m_schema = {'$ref': ref_prefix + model_name}
    if m_definitions:
        m_schema.update({'definitions': m_definitions})
    return m_schema


def field_schema(
    field: ModelField,
    *,
    by_alias: bool = True,
    model_name_map: Dict[Type['BaseModel'], str],
    ref_prefix: Optional[str] = None,
    known_models: Set[Type['BaseModel']] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Set[str]]:
    """
    Process a Pydantic field and return a tuple with a JSON Schema for it as the first item.
    Also return a dictionary of definitions with models as keys and their schemas as values. If the passed field
    is a model and has sub-models, and those sub-models don't have overrides (as ``title``, ``default``, etc), they
    will be included in the definitions and referenced in the schema instead of included recursively.

    :param field: a Pydantic ``ModelField``
    :param by_alias: use the defined alias (if any) in the returned schema
    :param model_name_map: used to generate the JSON Schema references to other models included in the definitions
    :param ref_prefix: the JSON Pointer prefix to use for references to other schemas, if None, the default of
      #/definitions/ will be used
    :param known_models: used to solve circular references
    :return: tuple of the schema for this field and additional definitions
    """
    ref_prefix = ref_prefix or default_prefix
    schema_overrides = False
    s = dict(title=field.field_info.title or field.alias.title().replace('_', ' '))
    if field.field_info.title:
        schema_overrides = True

    if field.field_info.description:
        s['description'] = field.field_info.description
        schema_overrides = True

    if not field.required and not field.field_info.const and field.default is not None:
        s['default'] = encode_default(field.default)
        schema_overrides = True

    validation_schema = get_field_schema_validations(field)
    if validation_schema:
        s.update(validation_schema)
        schema_overrides = True

    f_schema, f_definitions, f_nested_models = field_type_schema(
        field,
        by_alias=by_alias,
        model_name_map=model_name_map,
        schema_overrides=schema_overrides,
        ref_prefix=ref_prefix,
        known_models=known_models or set(),
    )
    # $ref will only be returned when there are no schema_overrides
    if '$ref' in f_schema:
        return f_schema, f_definitions, f_nested_models
    else:
        s.update(f_schema)
        return s, f_definitions, f_nested_models


numeric_types = (int, float, Decimal)
_str_types_attrs: Tuple[Tuple[str, Union[type, Tuple[type, ...]], str], ...] = (
    ('max_length', numeric_types, 'maxLength'),
    ('min_length', numeric_types, 'minLength'),
    ('regex', str, 'pattern'),
)

_numeric_types_attrs: Tuple[Tuple[str, Union[type, Tuple[type, ...]], str], ...] = (
    ('gt', numeric_types, 'exclusiveMinimum'),
    ('lt', numeric_types, 'exclusiveMaximum'),
    ('ge', numeric_types, 'minimum'),
    ('le', numeric_types, 'maximum'),
    ('multiple_of', numeric_types, 'multipleOf'),
)


def get_field_schema_validations(field: ModelField) -> Dict[str, Any]:
    """
    Get the JSON Schema validation keywords for a ``field`` with an annotation of
    a Pydantic ``FieldInfo`` with validation arguments.
    """
    f_schema: Dict[str, Any] = {}
    if lenient_issubclass(field.type_, (str, bytes)):
        for attr_name, t, keyword in _str_types_attrs:
            attr = getattr(field.field_info, attr_name, None)
            if isinstance(attr, t):
                f_schema[keyword] = attr
    if lenient_issubclass(field.type_, numeric_types) and not issubclass(field.type_, bool):
        for attr_name, t, keyword in _numeric_types_attrs:
            attr = getattr(field.field_info, attr_name, None)
            if isinstance(attr, t):
                f_schema[keyword] = attr
    if field.field_info is not None and field.field_info.const:
        f_schema['const'] = field.default
    if field.field_info.extra:
        f_schema.update(field.field_info.extra)
    return f_schema


def get_model_name_map(unique_models: Set[Type['BaseModel']]) -> Dict[Type['BaseModel'], str]:
    """
    Process a set of models and generate unique names for them to be used as keys in the JSON Schema
    definitions. By default the names are the same as the class name. But if two models in different Python
    modules have the same name (e.g. "users.Model" and "items.Model"), the generated names will be
    based on the Python module path for those conflicting models to prevent name collisions.

    :param unique_models: a Python set of models
    :return: dict mapping models to names
    """
    name_model_map = {}
    conflicting_names: Set[str] = set()
    for model in unique_models:
        model_name = model.__name__
        model_name = re.sub(r'[^a-zA-Z0-9.\-_]', '_', model_name)
        if model_name in conflicting_names:
            model_name = get_long_model_name(model)
            name_model_map[model_name] = model
        elif model_name in name_model_map:
            conflicting_names.add(model_name)
            conflicting_model = name_model_map.pop(model_name)
            name_model_map[get_long_model_name(conflicting_model)] = conflicting_model
            name_model_map[get_long_model_name(model)] = model
        else:
            name_model_map[model_name] = model
    return {v: k for k, v in name_model_map.items()}


def get_flat_models_from_model(
    model: Type['BaseModel'], known_models: Set[Type['BaseModel']] = None
) -> Set[Type['BaseModel']]:
    """
    Take a single ``model`` and generate a set with itself and all the sub-models in the tree. I.e. if you pass
    model ``Foo`` (subclass of Pydantic ``BaseModel``) as ``model``, and it has a field of type ``Bar`` (also
    subclass of ``BaseModel``) and that model ``Bar`` has a field of type ``Baz`` (also subclass of ``BaseModel``),
    the return value will be ``set([Foo, Bar, Baz])``.

    :param model: a Pydantic ``BaseModel`` subclass
    :param known_models: used to solve circular references
    :return: a set with the initial model and all its sub-models
    """
    known_models = known_models or set()
    flat_models: Set[Type['BaseModel']] = set()
    flat_models.add(model)
    known_models |= flat_models
    fields = cast(Sequence[ModelField], model.__fields__.values())
    flat_models |= get_flat_models_from_fields(fields, known_models=known_models)
    return flat_models


def get_flat_models_from_field(field: ModelField, known_models: Set[Type['BaseModel']]) -> Set[Type['BaseModel']]:
    """
    Take a single Pydantic ``ModelField`` (from a model) that could have been declared as a sublcass of BaseModel
    (so, it could be a submodel), and generate a set with its model and all the sub-models in the tree.
    I.e. if you pass a field that was declared to be of type ``Foo`` (subclass of BaseModel) as ``field``, and that
    model ``Foo`` has a field of type ``Bar`` (also subclass of ``BaseModel``) and that model ``Bar`` has a field of
    type ``Baz`` (also subclass of ``BaseModel``), the return value will be ``set([Foo, Bar, Baz])``.

    :param field: a Pydantic ``ModelField``
    :param known_models: used to solve circular references
    :return: a set with the model used in the declaration for this field, if any, and all its sub-models
    """
    from .main import BaseModel  # noqa: F811

    flat_models: Set[Type[BaseModel]] = set()
    # Handle dataclass-based models
    field_type = field.type_
    if lenient_issubclass(getattr(field_type, '__pydantic_model__', None), BaseModel):
        field_type = field_type.__pydantic_model__
    if field.sub_fields:
        flat_models |= get_flat_models_from_fields(field.sub_fields, known_models=known_models)
    elif lenient_issubclass(field_type, BaseModel) and field_type not in known_models:
        flat_models |= get_flat_models_from_model(field_type, known_models=known_models)
    return flat_models


def get_flat_models_from_fields(
    fields: Sequence[ModelField], known_models: Set[Type['BaseModel']]
) -> Set[Type['BaseModel']]:
    """
    Take a list of Pydantic  ``ModelField``s (from a model) that could have been declared as sublcasses of ``BaseModel``
    (so, any of them could be a submodel), and generate a set with their models and all the sub-models in the tree.
    I.e. if you pass a the fields of a model ``Foo`` (subclass of ``BaseModel``) as ``fields``, and on of them has a
    field of type ``Bar`` (also subclass of ``BaseModel``) and that model ``Bar`` has a field of type ``Baz`` (also
    subclass of ``BaseModel``), the return value will be ``set([Foo, Bar, Baz])``.

    :param fields: a list of Pydantic ``ModelField``s
    :param known_models: used to solve circular references
    :return: a set with any model declared in the fields, and all their sub-models
    """
    flat_models: Set[Type['BaseModel']] = set()
    for field in fields:
        flat_models |= get_flat_models_from_field(field, known_models=known_models)
    return flat_models


def get_flat_models_from_models(models: Sequence[Type['BaseModel']]) -> Set[Type['BaseModel']]:
    """
    Take a list of ``models`` and generate a set with them and all their sub-models in their trees. I.e. if you pass
    a list of two models, ``Foo`` and ``Bar``, both subclasses of Pydantic ``BaseModel`` as models, and ``Bar`` has
    a field of type ``Baz`` (also subclass of ``BaseModel``), the return value will be ``set([Foo, Bar, Baz])``.
    """
    flat_models: Set[Type['BaseModel']] = set()
    for model in models:
        flat_models |= get_flat_models_from_model(model)
    return flat_models


def get_long_model_name(model: Type['BaseModel']) -> str:
    return f'{model.__module__}__{model.__name__}'.replace('.', '__')


def field_type_schema(
    field: ModelField,
    *,
    by_alias: bool,
    model_name_map: Dict[Type['BaseModel'], str],
    schema_overrides: bool = False,
    ref_prefix: Optional[str] = None,
    known_models: Set[Type['BaseModel']],
) -> Tuple[Dict[str, Any], Dict[str, Any], Set[str]]:
    """
    Used by ``field_schema()``, you probably should be using that function.

    Take a single ``field`` and generate the schema for its type only, not including additional
    information as title, etc. Also return additional schema definitions, from sub-models.
    """
    definitions = {}
    nested_models: Set[str] = set()
    f_schema: Dict[str, Any]
    ref_prefix = ref_prefix or default_prefix
    if field.shape in {SHAPE_LIST, SHAPE_TUPLE_ELLIPSIS, SHAPE_SEQUENCE, SHAPE_SET, SHAPE_FROZENSET, SHAPE_ITERABLE}:
        items_schema, f_definitions, f_nested_models = field_singleton_schema(
            field, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix, known_models=known_models
        )
        definitions.update(f_definitions)
        nested_models.update(f_nested_models)
        f_schema = {'type': 'array', 'items': items_schema}
        if field.shape in {SHAPE_SET, SHAPE_FROZENSET}:
            f_schema['uniqueItems'] = True

    elif field.shape == SHAPE_MAPPING:
        f_schema = {'type': 'object'}
        key_field = cast(ModelField, field.key_field)
        regex = getattr(key_field.type_, 'regex', None)
        items_schema, f_definitions, f_nested_models = field_singleton_schema(
            field, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix, known_models=known_models
        )
        definitions.update(f_definitions)
        nested_models.update(f_nested_models)
        if regex:
            # Dict keys have a regex pattern
            # items_schema might be a schema or empty dict, add it either way
            f_schema['patternProperties'] = {regex.pattern: items_schema}
        elif items_schema:
            # The dict values are not simply Any, so they need a schema
            f_schema['additionalProperties'] = items_schema
    elif field.shape == SHAPE_TUPLE:
        sub_schema = []
        sub_fields = cast(List[ModelField], field.sub_fields)
        for sf in sub_fields:
            sf_schema, sf_definitions, sf_nested_models = field_type_schema(
                sf, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix, known_models=known_models
            )
            definitions.update(sf_definitions)
            nested_models.update(sf_nested_models)
            sub_schema.append(sf_schema)
        if len(sub_schema) == 1:
            sub_schema = sub_schema[0]  # type: ignore
        f_schema = {'type': 'array', 'items': sub_schema}
    else:
        assert field.shape == SHAPE_SINGLETON, field.shape
        f_schema, f_definitions, f_nested_models = field_singleton_schema(
            field,
            by_alias=by_alias,
            model_name_map=model_name_map,
            schema_overrides=schema_overrides,
            ref_prefix=ref_prefix,
            known_models=known_models,
        )
        definitions.update(f_definitions)
        nested_models.update(f_nested_models)

    # check field type to avoid repeated calls to the same __modify_schema__ method
    if field.type_ != field.outer_type_:
        modify_schema = getattr(field.outer_type_, '__modify_schema__', None)
        if modify_schema:
            modify_schema(f_schema)
    return f_schema, definitions, nested_models


def model_process_schema(
    model: Type['BaseModel'],
    *,
    by_alias: bool = True,
    model_name_map: Dict[Type['BaseModel'], str],
    ref_prefix: Optional[str] = None,
    known_models: Set[Type['BaseModel']] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Set[str]]:
    """
    Used by ``model_schema()``, you probably should be using that function.

    Take a single ``model`` and generate its schema. Also return additional schema definitions, from sub-models. The
    sub-models of the returned schema will be referenced, but their definitions will not be included in the schema. All
    the definitions are returned as the second value.
    """
    from inspect import getdoc, signature

    ref_prefix = ref_prefix or default_prefix
    known_models = known_models or set()
    s = {'title': model.__config__.title or model.__name__}
    doc = getdoc(model)
    if doc:
        s['description'] = doc
    known_models.add(model)
    m_schema, m_definitions, nested_models = model_type_schema(
        model, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix, known_models=known_models
    )
    s.update(m_schema)
    schema_extra = model.__config__.schema_extra
    if callable(schema_extra):
        if len(signature(schema_extra).parameters) == 1:
            schema_extra(s)
        else:
            schema_extra(s, model)
    else:
        s.update(schema_extra)
    return s, m_definitions, nested_models


def model_type_schema(
    model: Type['BaseModel'],
    *,
    by_alias: bool,
    model_name_map: Dict[Type['BaseModel'], str],
    ref_prefix: Optional[str] = None,
    known_models: Set[Type['BaseModel']],
) -> Tuple[Dict[str, Any], Dict[str, Any], Set[str]]:
    """
    You probably should be using ``model_schema()``, this function is indirectly used by that function.

    Take a single ``model`` and generate the schema for its type only, not including additional
    information as title, etc. Also return additional schema definitions, from sub-models.
    """
    ref_prefix = ref_prefix or default_prefix
    properties = {}
    required = []
    definitions: Dict[str, Any] = {}
    nested_models: Set[str] = set()
    for k, f in model.__fields__.items():
        try:
            f_schema, f_definitions, f_nested_models = field_schema(
                f, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix, known_models=known_models
            )
        except SkipField as skip:
            warnings.warn(skip.message, UserWarning)
            continue
        definitions.update(f_definitions)
        nested_models.update(f_nested_models)
        if by_alias:
            properties[f.alias] = f_schema
            if f.required:
                required.append(f.alias)
        else:
            properties[k] = f_schema
            if f.required:
                required.append(k)
    if ROOT_KEY in properties:
        out_schema = properties[ROOT_KEY]
        out_schema['title'] = model.__config__.title or model.__name__
    else:
        out_schema = {'type': 'object', 'properties': properties}
        if required:
            out_schema['required'] = required
    if model.__config__.extra == 'forbid':
        out_schema['additionalProperties'] = False
    return out_schema, definitions, nested_models


def field_singleton_sub_fields_schema(
    sub_fields: Sequence[ModelField],
    *,
    by_alias: bool,
    model_name_map: Dict[Type['BaseModel'], str],
    schema_overrides: bool = False,
    ref_prefix: Optional[str] = None,
    known_models: Set[Type['BaseModel']],
) -> Tuple[Dict[str, Any], Dict[str, Any], Set[str]]:
    """
    This function is indirectly used by ``field_schema()``, you probably should be using that function.

    Take a list of Pydantic ``ModelField`` from the declaration of a type with parameters, and generate their
    schema. I.e., fields used as "type parameters", like ``str`` and ``int`` in ``Tuple[str, int]``.
    """
    ref_prefix = ref_prefix or default_prefix
    definitions = {}
    nested_models: Set[str] = set()
    sub_fields = [sf for sf in sub_fields if sf.include_in_schema()]
    if len(sub_fields) == 1:
        return field_type_schema(
            sub_fields[0],
            by_alias=by_alias,
            model_name_map=model_name_map,
            schema_overrides=schema_overrides,
            ref_prefix=ref_prefix,
            known_models=known_models,
        )
    else:
        sub_field_schemas = []
        for sf in sub_fields:
            sub_schema, sub_definitions, sub_nested_models = field_type_schema(
                sf,
                by_alias=by_alias,
                model_name_map=model_name_map,
                schema_overrides=schema_overrides,
                ref_prefix=ref_prefix,
                known_models=known_models,
            )
            definitions.update(sub_definitions)
            sub_field_schemas.append(sub_schema)
            nested_models.update(sub_nested_models)
        return {'anyOf': sub_field_schemas}, definitions, nested_models


# Order is important, e.g. subclasses of str must go before str
# this is used only for standard library types, custom types should use __modify_schema__ instead
field_class_to_schema: Tuple[Tuple[Any, Dict[str, Any]], ...] = (
    (Path, {'type': 'string', 'format': 'path'}),
    (datetime, {'type': 'string', 'format': 'date-time'}),
    (date, {'type': 'string', 'format': 'date'}),
    (time, {'type': 'string', 'format': 'time'}),
    (timedelta, {'type': 'number', 'format': 'time-delta'}),
    (IPv4Network, {'type': 'string', 'format': 'ipv4network'}),
    (IPv6Network, {'type': 'string', 'format': 'ipv6network'}),
    (IPv4Interface, {'type': 'string', 'format': 'ipv4interface'}),
    (IPv6Interface, {'type': 'string', 'format': 'ipv6interface'}),
    (IPv4Address, {'type': 'string', 'format': 'ipv4'}),
    (IPv6Address, {'type': 'string', 'format': 'ipv6'}),
    (str, {'type': 'string'}),
    (bytes, {'type': 'string', 'format': 'binary'}),
    (bool, {'type': 'boolean'}),
    (int, {'type': 'integer'}),
    (float, {'type': 'number'}),
    (Decimal, {'type': 'number'}),
    (UUID, {'type': 'string', 'format': 'uuid'}),
    (dict, {'type': 'object'}),
    (list, {'type': 'array', 'items': {}}),
    (tuple, {'type': 'array', 'items': {}}),
    (set, {'type': 'array', 'items': {}, 'uniqueItems': True}),
)

json_scheme = {'type': 'string', 'format': 'json-string'}


def field_singleton_schema(  # noqa: C901 (ignore complexity)
    field: ModelField,
    *,
    by_alias: bool,
    model_name_map: Dict[Type['BaseModel'], str],
    schema_overrides: bool = False,
    ref_prefix: Optional[str] = None,
    known_models: Set[Type['BaseModel']],
) -> Tuple[Dict[str, Any], Dict[str, Any], Set[str]]:
    """
    This function is indirectly used by ``field_schema()``, you should probably be using that function.

    Take a single Pydantic ``ModelField``, and return its schema and any additional definitions from sub-models.
    """
    from .main import BaseModel  # noqa: F811

    ref_prefix = ref_prefix or default_prefix
    definitions: Dict[str, Any] = {}
    nested_models: Set[str] = set()
    if field.sub_fields:
        return field_singleton_sub_fields_schema(
            field.sub_fields,
            by_alias=by_alias,
            model_name_map=model_name_map,
            schema_overrides=schema_overrides,
            ref_prefix=ref_prefix,
            known_models=known_models,
        )
    if field.type_ is Any or field.type_.__class__ == TypeVar:
        return {}, definitions, nested_models  # no restrictions
    if is_callable_type(field.type_):
        raise SkipField(f'Callable {field.name} was excluded from schema since JSON schema has no equivalent type.')
    f_schema: Dict[str, Any] = {}
    if field.field_info is not None and field.field_info.const:
        f_schema['const'] = field.default
    field_type = field.type_
    if is_literal_type(field_type):
        values = literal_values(field_type)
        if len(values) > 1:
            return field_schema(
                multivalue_literal_field_for_schema(values, field),
                by_alias=by_alias,
                model_name_map=model_name_map,
                ref_prefix=ref_prefix,
                known_models=known_models,
            )
        literal_value = values[0]
        field_type = literal_value.__class__
        f_schema['const'] = literal_value

    if issubclass(field_type, Enum):
        f_schema.update({'enum': [item.value for item in field_type]})
        # Don't return immediately, to allow adding specific types

    for type_, t_schema in field_class_to_schema:
        if issubclass(field_type, type_):
            f_schema.update(t_schema)
            break

    modify_schema = getattr(field_type, '__modify_schema__', None)
    if modify_schema:
        modify_schema(f_schema)

    if f_schema:
        return f_schema, definitions, nested_models

    # Handle dataclass-based models
    if lenient_issubclass(getattr(field_type, '__pydantic_model__', None), BaseModel):
        field_type = field_type.__pydantic_model__

    if issubclass(field_type, BaseModel):
        model_name = model_name_map[field_type]
        if field_type not in known_models:
            sub_schema, sub_definitions, sub_nested_models = model_process_schema(
                field_type,
                by_alias=by_alias,
                model_name_map=model_name_map,
                ref_prefix=ref_prefix,
                known_models=known_models,
            )
            definitions.update(sub_definitions)
            definitions[model_name] = sub_schema
            nested_models.update(sub_nested_models)
        else:
            nested_models.add(model_name)
        schema_ref = {'$ref': ref_prefix + model_name}
        if not schema_overrides:
            return schema_ref, definitions, nested_models
        else:
            return {'allOf': [schema_ref]}, definitions, nested_models

    raise ValueError(f'Value not declarable with JSON Schema, field: {field}')


def multivalue_literal_field_for_schema(values: Tuple[Any, ...], field: ModelField) -> ModelField:
    return ModelField(
        name=field.name,
        type_=Union[tuple(Literal[value] for value in values)],
        class_validators=field.class_validators,
        model_config=field.model_config,
        default=field.default,
        required=field.required,
        alias=field.alias,
        field_info=field.field_info,
    )


def encode_default(dft: Any) -> Any:
    if isinstance(dft, (int, float, str)):
        return dft
    elif sequence_like(dft):
        t = dft.__class__
        return t(encode_default(v) for v in dft)
    elif isinstance(dft, dict):
        return {encode_default(k): encode_default(v) for k, v in dft.items()}
    elif dft is None:
        return None
    else:
        return pydantic_encoder(dft)


_map_types_constraint: Dict[Any, Callable[..., type]] = {int: conint, float: confloat, Decimal: condecimal}
_field_constraints = {
    'min_length',
    'max_length',
    'regex',
    'gt',
    'lt',
    'ge',
    'le',
    'multiple_of',
    'min_items',
    'max_items',
}


def get_annotation_from_field_info(annotation: Any, field_info: FieldInfo, field_name: str) -> Type[Any]:  # noqa: C901
    """
    Get an annotation with validation implemented for numbers and strings based on the field_info.

    :param annotation: an annotation from a field specification, as ``str``, ``ConstrainedStr``
    :param field_info: an instance of FieldInfo, possibly with declarations for validations and JSON Schema
    :param field_name: name of the field for use in error messages
    :return: the same ``annotation`` if unmodified or a new annotation with validation in place
    """
    constraints = {f for f in _field_constraints if getattr(field_info, f) is not None}
    if not constraints:
        return annotation
    used_constraints: Set[str] = set()

    def go(type_: Any) -> Type[Any]:
        if is_literal_type(annotation) or isinstance(type_, ForwardRef) or lenient_issubclass(type_, ConstrainedList):
            return type_
        origin = getattr(type_, '__origin__', None)
        if origin is not None:
            args: Tuple[Any, ...] = type_.__args__
            if any(isinstance(a, ForwardRef) for a in args):
                # forward refs cause infinite recursion below
                return type_

            if origin is Union:
                return Union[tuple(go(a) for a in args)]

            if issubclass(origin, List) and (field_info.min_items is not None or field_info.max_items is not None):
                used_constraints.update({'min_items', 'max_items'})
                return conlist(go(args[0]), min_items=field_info.min_items, max_items=field_info.max_items)

            for t in (Tuple, List, Set, FrozenSet, Sequence):
                if issubclass(origin, t):  # type: ignore
                    return t[tuple(go(a) for a in args)]  # type: ignore

            if issubclass(origin, Dict):
                return Dict[args[0], go(args[1])]  # type: ignore

        attrs: Optional[Tuple[str, ...]] = None
        constraint_func: Optional[Callable[..., type]] = None
        if isinstance(type_, type):
            if issubclass(type_, str) and not issubclass(type_, (EmailStr, AnyUrl, ConstrainedStr)):
                attrs = ('max_length', 'min_length', 'regex')
                constraint_func = constr
            elif issubclass(type_, bytes):
                attrs = ('max_length', 'min_length', 'regex')
                constraint_func = conbytes
            elif issubclass(type_, numeric_types) and not issubclass(
                type_, (ConstrainedInt, ConstrainedFloat, ConstrainedDecimal, ConstrainedList, bool)
            ):
                # Is numeric type
                attrs = ('gt', 'lt', 'ge', 'le', 'multiple_of')
                numeric_type = next(t for t in numeric_types if issubclass(type_, t))  # pragma: no branch
                constraint_func = _map_types_constraint[numeric_type]

        if attrs:
            used_constraints.update(set(attrs))
            kwargs = {
                attr_name: attr
                for attr_name, attr in ((attr_name, getattr(field_info, attr_name)) for attr_name in attrs)
                if attr is not None
            }
            if kwargs:
                constraint_func = cast(Callable[..., type], constraint_func)
                return constraint_func(**kwargs)
        return type_

    ans = go(annotation)

    unused_constraints = constraints - used_constraints
    if unused_constraints:
        raise ValueError(
            f'On field "{field_name}" the following field constraints are set but not enforced: '
            f'{", ".join(unused_constraints)}. '
            f'\nFor more details see https://pydantic-docs.helpmanual.io/usage/schema/#unenforced-field-constraints'
        )

    return ans


class SkipField(Exception):
    """
    Utility exception used to exclude fields from schema.
    """

    def __init__(self, message: str) -> None:
        self.message = message
