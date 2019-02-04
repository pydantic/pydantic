import warnings
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Type, Union, cast
from uuid import UUID

from . import main
from .fields import Field, Shape
from .json import pydantic_encoder
from .types import (
    DSN,
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    ConstrainedDecimal,
    ConstrainedFloat,
    ConstrainedInt,
    ConstrainedStr,
    DirectoryPath,
    EmailStr,
    FilePath,
    Json,
    NameEmail,
    UrlStr,
    condecimal,
    confloat,
    conint,
    constr,
)
from .utils import clean_docstring, is_callable_type, lenient_issubclass

__all__ = [
    'Schema',
    'schema',
    'model_schema',
    'field_schema',
    'get_model_name_map',
    'get_flat_models_from_model',
    'get_flat_models_from_field',
    'get_flat_models_from_fields',
    'get_flat_models_from_models',
    'get_long_model_name',
    'field_type_schema',
    'model_process_schema',
    'model_type_schema',
    'field_singleton_sub_fields_schema',
    'field_singleton_schema',
    'get_annotation_from_schema',
]

default_prefix = '#/definitions/'


class Schema:
    """
    Used to provide extra information about a field in a model schema. The parameters will be
    converted to validations and will add annotations to the generated JSON Schema. Some arguments
    apply only to number fields (``int``, ``float``, ``Decimal``) and some apply only to ``str``

    :param default: since the Schema is replacing the field’s default, its first argument is used
      to set the default, use ellipsis (``...``) to indicate the field is required
    :param alias: the public name of the field
    :param title: can be any string, used in the schema
    :param description: can be any string, used in the schema
    :param gt: only applies to numbers, requires the field to be "greater than". The schema
      will have an ``exclusiveMinimum`` validation keyword
    :param ge: only applies to numbers, requires the field to be "greater than or equal to". The
      schema will have a ``minimum`` validation keyword
    :param lt: only applies to numbers, requires the field to be "less than". The schema
      will have an ``exclusiveMaximum`` validation keyword
    :param le: only applies to numbers, requires the field to be "less than or equal to". The
      schema will have a ``maximum`` validation keyword
    :param multiple_of: only applies to numbers, requires the field to be "a multiple of". The
      schema will have a ``multipleOf`` validation keyword
    :param min_length: only applies to strings, requires the field to have a minimum length. The
      schema will have a ``maximum`` validation keyword
    :param max_length: only applies to strings, requires the field to have a maximum length. The
      schema will have a ``maxLength`` validation keyword
    :param regex: only applies to strings, requires the field match agains a regular expression
      pattern string. The schema will have a ``pattern`` validation keyword
    :param **extra: any additional keyword arguments will be added as is to the schema
    """

    __slots__ = (
        'default',
        'alias',
        'title',
        'description',
        'gt',
        'ge',
        'lt',
        'le',
        'multiple_of',
        'min_length',
        'max_length',
        'regex',
        'extra',
    )

    def __init__(
        self,
        default: Any,
        *,
        alias: str = None,
        title: str = None,
        description: str = None,
        gt: float = None,
        ge: float = None,
        lt: float = None,
        le: float = None,
        multiple_of: float = None,
        min_length: int = None,
        max_length: int = None,
        regex: str = None,
        **extra: Any,
    ) -> None:
        self.default = default
        self.alias = alias
        self.title = title
        self.description = description
        self.extra = extra
        self.gt = gt
        self.ge = ge
        self.lt = lt
        self.le = le
        self.multiple_of = multiple_of
        self.min_length = min_length
        self.max_length = max_length
        self.regex = regex

    def __repr__(self) -> str:
        attrs = ((s, getattr(self, s)) for s in self.__slots__)
        return 'Schema({})'.format(', '.join(f'{a}: {v!r}' for a, v in attrs if v is not None))


def schema(
    models: Sequence[Type['main.BaseModel']],
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
    ref_prefix = ref_prefix or default_prefix
    flat_models = get_flat_models_from_models(models)
    model_name_map = get_model_name_map(flat_models)
    definitions = {}
    output_schema: Dict[str, Any] = {}
    if title:
        output_schema['title'] = title
    if description:
        output_schema['description'] = description
    for model in models:
        m_schema, m_definitions = model_process_schema(
            model, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(m_definitions)
        model_name = model_name_map[model]
        definitions[model_name] = m_schema
    if definitions:
        output_schema['definitions'] = definitions
    return output_schema


def model_schema(
    model: Type['main.BaseModel'], by_alias: bool = True, ref_prefix: Optional[str] = None
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
    ref_prefix = ref_prefix or default_prefix
    flat_models = get_flat_models_from_model(model)
    model_name_map = get_model_name_map(flat_models)
    m_schema, m_definitions = model_process_schema(
        model, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
    )
    if m_definitions:
        m_schema.update({'definitions': m_definitions})
    return m_schema


def field_schema(
    field: Field,
    *,
    by_alias: bool = True,
    model_name_map: Dict[Type['main.BaseModel'], str],
    ref_prefix: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Process a Pydantic field and return a tuple with a JSON Schema for it as the first item.
    Also return a dictionary of definitions with models as keys and their schemas as values. If the passed field
    is a model and has sub-models, and those sub-models don't have overrides (as ``title``, ``default``, etc), they
    will be included in the definitions and referenced in the schema instead of included recursively.

    :param field: a Pydantic ``Field``
    :param by_alias: use the defined alias (if any) in the returned schema
    :param model_name_map: used to generate the JSON Schema references to other models included in the definitions
    :param ref_prefix: the JSON Pointer prefix to use for references to other schemas, if None, the default of
      #/definitions/ will be used
    :return: tuple of the schema for this field and additional definitions
    """
    ref_prefix = ref_prefix or default_prefix
    schema_overrides = False
    schema = cast('Schema', field.schema)
    s = dict(title=schema.title or field.alias.title())
    if schema.title:
        schema_overrides = True

    if schema.description:
        s['description'] = schema.description
        schema_overrides = True

    if not field.required and field.default is not None:
        s['default'] = encode_default(field.default)
        schema_overrides = True

    validation_schema = get_field_schema_validations(field)
    if validation_schema:
        s.update(validation_schema)
        schema_overrides = True

    f_schema, f_definitions = field_type_schema(
        field,
        by_alias=by_alias,
        model_name_map=model_name_map,
        schema_overrides=schema_overrides,
        ref_prefix=ref_prefix,
    )
    # $ref will only be returned when there are no schema_overrides
    if '$ref' in f_schema:
        return f_schema, f_definitions
    else:
        s.update(f_schema)
        return s, f_definitions


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


def get_field_schema_validations(field: Field) -> Dict[str, Any]:
    """
    Get the JSON Schema validation keywords for a ``field`` with an annotation of
    a Pydantic ``Schema`` with validation arguments.
    """
    f_schema: Dict[str, Any] = {}
    if lenient_issubclass(field.type_, (str, bytes)):
        for attr_name, t, keyword in _str_types_attrs:
            attr = getattr(field.schema, attr_name, None)
            if isinstance(attr, t):
                f_schema[keyword] = attr
    if lenient_issubclass(field.type_, numeric_types) and not issubclass(field.type_, bool):
        for attr_name, t, keyword in _numeric_types_attrs:
            attr = getattr(field.schema, attr_name, None)
            if isinstance(attr, t):
                f_schema[keyword] = attr
    schema = cast('Schema', field.schema)
    if schema.extra:
        f_schema.update(schema.extra)
    return f_schema


def get_model_name_map(unique_models: Set[Type['main.BaseModel']]) -> Dict[Type['main.BaseModel'], str]:
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


def get_flat_models_from_model(model: Type['main.BaseModel']) -> Set[Type['main.BaseModel']]:
    """
    Take a single ``model`` and generate a set with itself and all the sub-models in the tree. I.e. if you pass
    model ``Foo`` (subclass of Pydantic ``BaseModel``) as ``model``, and it has a field of type ``Bar`` (also
    subclass of ``BaseModel``) and that model ``Bar`` has a field of type ``Baz`` (also subclass of ``BaseModel``),
    the return value will be ``set([Foo, Bar, Baz])``.

    :param model: a Pydantic ``BaseModel`` subclass
    :return: a set with the initial model and all its sub-models
    """
    flat_models: Set[Type['main.BaseModel']] = set()
    flat_models.add(model)
    fields = cast(Sequence[Field], model.__fields__.values())
    flat_models |= get_flat_models_from_fields(fields)
    return flat_models


def get_flat_models_from_field(field: Field) -> Set[Type['main.BaseModel']]:
    """
    Take a single Pydantic ``Field`` (from a model) that could have been declared as a sublcass of BaseModel
    (so, it could be a submodel), and generate a set with its model and all the sub-models in the tree.
    I.e. if you pass a field that was declared to be of type ``Foo`` (subclass of BaseModel) as ``field``, and that
    model ``Foo`` has a field of type ``Bar`` (also subclass of ``BaseModel``) and that model ``Bar`` has a field of
    type ``Baz`` (also subclass of ``BaseModel``), the return value will be ``set([Foo, Bar, Baz])``.

    :param field: a Pydantic ``Field``
    :return: a set with the model used in the declaration for this field, if any, and all its sub-models
    """
    flat_models: Set[Type['main.BaseModel']] = set()
    if field.sub_fields:
        flat_models |= get_flat_models_from_fields(field.sub_fields)
    elif lenient_issubclass(field.type_, main.BaseModel):
        flat_models |= get_flat_models_from_model(field.type_)
    return flat_models


def get_flat_models_from_fields(fields: Sequence[Field]) -> Set[Type['main.BaseModel']]:
    """
    Take a list of Pydantic  ``Field``s (from a model) that could have been declared as sublcasses of ``BaseModel``
    (so, any of them could be a submodel), and generate a set with their models and all the sub-models in the tree.
    I.e. if you pass a the fields of a model ``Foo`` (subclass of ``BaseModel``) as ``fields``, and on of them has a
    field of type ``Bar`` (also subclass of ``BaseModel``) and that model ``Bar`` has a field of type ``Baz`` (also
    subclass of ``BaseModel``), the return value will be ``set([Foo, Bar, Baz])``.

    :param fields: a list of Pydantic ``Field``s
    :return: a set with any model declared in the fields, and all their sub-models
    """
    flat_models: Set[Type['main.BaseModel']] = set()
    for field in fields:
        flat_models |= get_flat_models_from_field(field)
    return flat_models


def get_flat_models_from_models(models: Sequence[Type['main.BaseModel']]) -> Set[Type['main.BaseModel']]:
    """
    Take a list of ``models`` and generate a set with them and all their sub-models in their trees. I.e. if you pass
    a list of two models, ``Foo`` and ``Bar``, both subclasses of Pydantic ``BaseModel`` as models, and ``Bar`` has
    a field of type ``Baz`` (also subclass of ``BaseModel``), the return value will be ``set([Foo, Bar, Baz])``.
    """
    flat_models: Set[Type['main.BaseModel']] = set()
    for model in models:
        flat_models |= get_flat_models_from_model(model)
    return flat_models


def get_long_model_name(model: Type['main.BaseModel']) -> str:
    return f'{model.__module__}__{model.__name__}'.replace('.', '__')


def field_type_schema(
    field: Field,
    *,
    by_alias: bool,
    model_name_map: Dict[Type['main.BaseModel'], str],
    schema_overrides: bool = False,
    ref_prefix: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Used by ``field_schema()``, you probably should be using that function.

    Take a single ``field`` and generate the schema for its type only, not including additional
    information as title, etc. Also return additional schema definitions, from sub-models.
    """
    definitions = {}
    ref_prefix = ref_prefix or default_prefix
    if field.shape is Shape.LIST:
        f_schema, f_definitions = field_singleton_schema(
            field, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(f_definitions)
        return {'type': 'array', 'items': f_schema}, definitions
    elif field.shape is Shape.SET:
        f_schema, f_definitions = field_singleton_schema(
            field, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(f_definitions)
        return {'type': 'array', 'uniqueItems': True, 'items': f_schema}, definitions
    elif field.shape is Shape.MAPPING:
        dict_schema: Dict[str, Any] = {'type': 'object'}
        key_field = cast(Field, field.key_field)
        regex = getattr(key_field.type_, 'regex', None)
        f_schema, f_definitions = field_singleton_schema(
            field, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(f_definitions)
        if regex:
            # Dict keys have a regex pattern
            # f_schema might be a schema or empty dict, add it either way
            dict_schema['patternProperties'] = {regex.pattern: f_schema}
        elif f_schema:
            # The dict values are not simply Any, so they need a schema
            dict_schema['additionalProperties'] = f_schema
        return dict_schema, definitions
    elif field.shape is Shape.TUPLE:
        sub_schema = []
        sub_fields = cast(List[Field], field.sub_fields)
        for sf in sub_fields:
            sf_schema, sf_definitions = field_type_schema(
                sf, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
            )
            definitions.update(sf_definitions)
            sub_schema.append(sf_schema)
        if len(sub_schema) == 1:
            sub_schema = sub_schema[0]  # type: ignore
        return {'type': 'array', 'items': sub_schema}, definitions
    else:
        assert field.shape is Shape.SINGLETON, field.shape
        f_schema, f_definitions = field_singleton_schema(
            field,
            by_alias=by_alias,
            model_name_map=model_name_map,
            schema_overrides=schema_overrides,
            ref_prefix=ref_prefix,
        )
        definitions.update(f_definitions)
        return f_schema, definitions


def model_process_schema(
    model: Type['main.BaseModel'],
    *,
    by_alias: bool = True,
    model_name_map: Dict[Type['main.BaseModel'], str],
    ref_prefix: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Used by ``model_schema()``, you probably should be using that function.

    Take a single ``model`` and generate its schema. Also return additional schema definitions, from sub-models. The
    sub-models of the returned schema will be referenced, but their definitions will not be included in the schema. All
    the definitions are returned as the second value.
    """
    ref_prefix = ref_prefix or default_prefix
    s = {'title': model.__config__.title or model.__name__}
    if model.__doc__:
        s['description'] = clean_docstring(model.__doc__)
    m_schema, m_definitions = model_type_schema(
        model, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
    )
    s.update(m_schema)
    return s, m_definitions


def model_type_schema(
    model: Type['main.BaseModel'],
    *,
    by_alias: bool,
    model_name_map: Dict[Type['main.BaseModel'], str],
    ref_prefix: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    You probably should be using ``model_schema()``, this function is indirectly used by that function.

    Take a single ``model`` and generate the schema for its type only, not including additional
    information as title, etc. Also return additional schema definitions, from sub-models.
    """
    ref_prefix = ref_prefix or default_prefix
    properties = {}
    required = []
    definitions: Dict[str, Any] = {}
    for k, f in model.__fields__.items():
        try:
            f_schema, f_definitions = field_schema(
                f, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
            )
        except SkipField as skip:
            warnings.warn(skip.message, UserWarning)
            continue
        definitions.update(f_definitions)
        if by_alias:
            properties[f.alias] = f_schema
            if f.required:
                required.append(f.alias)
        else:
            properties[k] = f_schema
            if f.required:
                required.append(k)
    out_schema = {'type': 'object', 'properties': properties}
    if required:
        out_schema['required'] = required
    return out_schema, definitions


def field_singleton_sub_fields_schema(
    sub_fields: Sequence[Field],
    *,
    by_alias: bool,
    model_name_map: Dict[Type['main.BaseModel'], str],
    schema_overrides: bool = False,
    ref_prefix: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    This function is indirectly used by ``field_schema()``, you probably should be using that function.

    Take a list of Pydantic ``Field`` from the declaration of a type with parameters, and generate their
    schema. I.e., fields used as "type parameters", like ``str`` and ``int`` in ``Tuple[str, int]``.
    """
    ref_prefix = ref_prefix or default_prefix
    definitions = {}
    sub_fields = [sf for sf in sub_fields if sf.include_in_schema()]
    if len(sub_fields) == 1:
        return field_type_schema(
            sub_fields[0],
            by_alias=by_alias,
            model_name_map=model_name_map,
            schema_overrides=schema_overrides,
            ref_prefix=ref_prefix,
        )
    else:
        sub_field_schemas = []
        for sf in sub_fields:
            sub_schema, sub_definitions = field_type_schema(
                sf,
                by_alias=by_alias,
                model_name_map=model_name_map,
                schema_overrides=schema_overrides,
                ref_prefix=ref_prefix,
            )
            definitions.update(sub_definitions)
            sub_field_schemas.append(sub_schema)
        return {'anyOf': sub_field_schemas}, definitions


validation_attribute_to_schema_keyword = {
    'min_length': 'minLength',
    'max_length': 'maxLength',
    'regex': 'pattern',
    'gt': 'exclusiveMinimum',
    'lt': 'exclusiveMaximum',
    'ge': 'minimum',
    'le': 'maximum',
    'multiple_of': 'multipleOf',
}

# Order is important, subclasses of str must go before str, etc
field_class_to_schema_enum_enabled: Tuple[Tuple[Any, Dict[str, Any]], ...] = (
    (EmailStr, {'type': 'string', 'format': 'email'}),
    (UrlStr, {'type': 'string', 'format': 'uri'}),
    (DSN, {'type': 'string', 'format': 'dsn'}),
    (str, {'type': 'string'}),
    (bytes, {'type': 'string', 'format': 'binary'}),
    (bool, {'type': 'boolean'}),
    (int, {'type': 'integer'}),
    (float, {'type': 'number'}),
    (Decimal, {'type': 'number'}),
    (UUID1, {'type': 'string', 'format': 'uuid1'}),
    (UUID3, {'type': 'string', 'format': 'uuid3'}),
    (UUID4, {'type': 'string', 'format': 'uuid4'}),
    (UUID5, {'type': 'string', 'format': 'uuid5'}),
    (UUID, {'type': 'string', 'format': 'uuid'}),
    (NameEmail, {'type': 'string', 'format': 'name-email'}),
    (dict, {'type': 'object'}),
    (list, {'type': 'array'}),
    (tuple, {'type': 'array'}),
    (set, {'type': 'array', 'uniqueItems': True}),
)


# Order is important, subclasses of Path must go before Path, etc
field_class_to_schema_enum_disabled = (
    (FilePath, {'type': 'string', 'format': 'file-path'}),
    (DirectoryPath, {'type': 'string', 'format': 'directory-path'}),
    (Path, {'type': 'string', 'format': 'path'}),
    (datetime, {'type': 'string', 'format': 'date-time'}),
    (date, {'type': 'string', 'format': 'date'}),
    (time, {'type': 'string', 'format': 'time'}),
    (timedelta, {'type': 'number', 'format': 'time-delta'}),
    (Json, {'type': 'string', 'format': 'json-string'}),
)


def field_singleton_schema(  # noqa: C901 (ignore complexity)
    field: Field,
    *,
    by_alias: bool,
    model_name_map: Dict[Type['main.BaseModel'], str],
    schema_overrides: bool = False,
    ref_prefix: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    This function is indirectly used by ``field_schema()``, you should probably be using that function.

    Take a single Pydantic ``Field``, and return its schema and any additional definitions from sub-models.
    """

    ref_prefix = ref_prefix or default_prefix
    definitions: Dict[str, Any] = {}
    if field.sub_fields:
        return field_singleton_sub_fields_schema(
            field.sub_fields,
            by_alias=by_alias,
            model_name_map=model_name_map,
            schema_overrides=schema_overrides,
            ref_prefix=ref_prefix,
        )
    if field.type_ is Any:
        return {}, definitions  # no restrictions
    if is_callable_type(field.type_):
        raise SkipField(f'Callable {field.name} was excluded from schema since JSON schema has no equivalent type.')
    f_schema: Dict[str, Any] = {}
    if issubclass(field.type_, Enum):
        f_schema.update({'enum': [item.value for item in field.type_]})  # type: ignore
        # Don't return immediately, to allow adding specific types
    for field_name, schema_name in validation_attribute_to_schema_keyword.items():
        field_value = getattr(field.type_, field_name, None)
        if field_value is not None:
            if field_name == 'regex':
                field_value = field_value.pattern
            f_schema[schema_name] = field_value
    for type_, t_schema in field_class_to_schema_enum_enabled:
        if issubclass(field.type_, type_):
            f_schema.update(t_schema)
            break
    # Return schema, with or without enum definitions
    if f_schema:
        return f_schema, definitions
    for type_, t_schema in field_class_to_schema_enum_disabled:
        if issubclass(field.type_, type_):
            return t_schema, definitions
    if issubclass(field.type_, main.BaseModel):
        sub_schema, sub_definitions = model_process_schema(
            field.type_, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(sub_definitions)
        if not schema_overrides:
            model_name = model_name_map[field.type_]
            definitions[model_name] = sub_schema
            return {'$ref': f'{ref_prefix}{model_name}'}, definitions
        else:
            return sub_schema, definitions
    raise ValueError(f'Value not declarable with JSON Schema, field: {field}')


def encode_default(dft: Any) -> Any:
    if isinstance(dft, (int, float, str)):
        return dft
    elif isinstance(dft, (tuple, list, set)):
        t = type(dft)
        return t(encode_default(v) for v in dft)
    elif isinstance(dft, dict):
        return {encode_default(k): encode_default(v) for k, v in dft.items()}
    else:
        return pydantic_encoder(dft)


_map_types_constraint: Dict[Any, Callable[..., type]] = {int: conint, float: confloat, Decimal: condecimal}


def get_annotation_from_schema(annotation: Any, schema: Schema) -> Type[Any]:
    """
    Get an annotation with validation implemented for numbers and strings based on the schema.

    :param annotation: an annotation from a field specification, as ``str``, ``ConstrainedStr``
    :param schema: an instance of Schema, possibly with declarations for validations and JSON Schema
    :return: the same ``annotation`` if unmodified or a new annotation with validation in place
    """
    if isinstance(annotation, type):
        attrs: Optional[Tuple[str, ...]] = None
        constraint_func: Optional[Callable[..., type]] = None
        if issubclass(annotation, str) and not issubclass(annotation, (EmailStr, DSN, UrlStr, ConstrainedStr)):
            attrs = ('max_length', 'min_length', 'regex')
            constraint_func = constr
        elif lenient_issubclass(annotation, numeric_types) and not issubclass(
            annotation, (ConstrainedInt, ConstrainedFloat, ConstrainedDecimal, bool)
        ):
            # Is numeric type
            attrs = ('gt', 'lt', 'ge', 'le', 'multiple_of')
            numeric_type = next(t for t in numeric_types if issubclass(annotation, t))  # pragma: no branch
            constraint_func = _map_types_constraint[numeric_type]

        if attrs:
            kwargs = {
                attr_name: attr
                for attr_name, attr in ((attr_name, getattr(schema, attr_name)) for attr_name in attrs)
                if attr is not None
            }
            if kwargs:
                constraint_func = cast(Callable[..., type], constraint_func)
                return constraint_func(**kwargs)
    return annotation


class SkipField(Exception):
    """
    Utility exception used to exclude fields from schema.
    """

    def __init__(self, message: str) -> None:
        self.message = message
