"""
This script generates the schema for the schema - e.g.
a definition of what inputs can be provided to `SchemaValidator()`.

The schema is generated from `pydantic_core/core_schema.py`.
"""
from __future__ import annotations as _annotations

import importlib.util
import re
from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, ForwardRef, List, Type, Union

from typing_extensions import get_args, is_typeddict

try:
    from typing import get_origin
except ImportError:

    def get_origin(t):
        return getattr(t, '__origin__', None)


THIS_DIR = Path(__file__).parent
SAVE_PATH = THIS_DIR / 'src' / 'self_schema.py'

if TYPE_CHECKING:
    from pydantic_core import core_schema
else:
    # can't import core_schema.py directly as pydantic-core might not be installed
    core_schema_spec = importlib.util.spec_from_file_location(
        '_typing', str(THIS_DIR / 'pydantic_core' / 'core_schema.py')
    )
    core_schema = importlib.util.module_from_spec(core_schema_spec)
    core_schema_spec.loader.exec_module(core_schema)

# the validator for referencing schema (Schema is used recursively, so has to use a reference)
schema_ref_validator = {'type': 'recursive-ref', 'schema_ref': 'root-schema'}


def get_schema(obj) -> core_schema.CoreSchema:
    if isinstance(obj, str):
        return {'type': obj}
    elif obj in (datetime, timedelta, date, time, bool, int, float, str):
        return {'type': obj.__name__}
    elif is_typeddict(obj):
        return type_dict_schema(obj)
    elif obj == Any or obj == type:
        return {'type': 'any'}

    origin = get_origin(obj)
    assert origin is not None, f'origin cannot be None, obj={obj}, you probably need to fix generate_self_schema.py'
    if origin is Union:
        return union_schema(obj)
    elif obj is Callable or origin is Callable:
        return {'type': 'callable'}
    elif origin is core_schema.Literal:
        expected = all_literal_values(obj)
        assert expected, f'literal "expected" cannot be empty, obj={obj}'
        return {'type': 'literal', 'expected': expected}
    elif issubclass(origin, List):
        return {'type': 'list', 'items_schema': get_schema(obj.__args__[0])}
    elif issubclass(origin, Dict):
        return {
            'type': 'dict',
            'keys_schema': get_schema(obj.__args__[0]),
            'values_schema': get_schema(obj.__args__[1]),
        }
    elif issubclass(origin, Type):
        # can't really use 'is-instance' since this is used for the class_ parameter of 'is-instance' validators
        return {'type': 'any'}
    else:
        # debug(obj)
        raise TypeError(f'Unknown type: {obj!r}')


def type_dict_schema(typed_dict) -> dict[str, Any]:
    required_keys = getattr(typed_dict, '__required_keys__', set())
    fields = {}

    for field_name, field_type in typed_dict.__annotations__.items():
        required = field_name in required_keys
        schema = None
        if type(field_type) == ForwardRef:
            fr_arg = field_type.__forward_arg__
            fr_arg, matched = re.subn(r'NotRequired\[(.+)]', r'\1', fr_arg)
            if matched:
                required = False

            fr_arg, matched = re.subn(r'Required\[(.+)]', r'\1', fr_arg)
            if matched:
                required = True

            if 'CoreSchema' == fr_arg or re.search('[^a-zA-Z]CoreSchema', fr_arg):
                if fr_arg == 'CoreSchema':
                    schema = schema_ref_validator
                elif fr_arg == 'List[CoreSchema]':
                    schema = {'type': 'list', 'items_schema': schema_ref_validator}
                elif fr_arg == 'Dict[str, CoreSchema]':
                    schema = {'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': schema_ref_validator}
                else:
                    raise ValueError(f'Unknown Schema forward ref: {fr_arg}')
            else:
                field_type = eval_forward_ref(field_type)

        if schema is None:
            if get_origin(field_type) == core_schema.Required:
                required = True
                field_type = field_type.__args__[0]
            if get_origin(field_type) == core_schema.NotRequired:
                required = False
                field_type = field_type.__args__[0]

            schema = get_schema(field_type)

        fields[field_name] = {'schema': schema, 'required': required}

    return {'type': 'typed-dict', 'description': typed_dict.__name__, 'fields': fields, 'extra_behavior': 'forbid'}


def union_schema(union_type: type[Union]) -> core_schema.UnionSchema:
    return {'type': 'union', 'choices': [get_schema(arg) for arg in union_type.__args__]}


def all_literal_values(type_: type[core_schema.Literal]) -> list[any]:
    if get_origin(type_) is core_schema.Literal:
        values = get_args(type_)
        return [x for value in values for x in all_literal_values(value)]
    else:
        return [type_]


def eval_forward_ref(type_: Any) -> Any:
    try:
        return type_._evaluate(core_schema.__dict__, None, set())
    except TypeError:
        # for older python (3.7 at least)
        return type_._evaluate(core_schema.__dict__, None)


def main() -> None:
    schema_union = core_schema.CoreSchema
    assert get_origin(schema_union) is Union, 'expected core_schema.CoreSchema to be a Union'

    choices = {}
    for s in schema_union.__args__:
        type_ = s.__annotations__['type']
        m = re.search(r"Literal\['(.+?)']", type_.__forward_arg__)
        assert m, f'Unknown schema type: {type_}'
        key = m.group(1)
        value = get_schema(s)
        if key == 'function' and value['fields']['mode']['schema']['expected'] == ['plain']:
            key = 'function-plain'
        elif key == 'tuple':
            if value['fields']['mode']['schema']['expected'] == ['positional']:
                key = 'tuple-positional'
            else:
                key = 'tuple-variable'

        choices[key] = value

    schema = {
        'type': 'tagged-union',
        'ref': 'root-schema',
        'discriminator': 'self-schema-discriminator',
        'choices': choices,
    }
    python_code = (
        f'# this file is auto-generated by generate_self_schema.py, DO NOT edit manually\nself_schema = {schema}\n'
    )
    try:
        from black import Mode, TargetVersion, format_file_contents
    except ImportError:
        pass
    else:
        mode = Mode(
            line_length=120,
            string_normalization=False,
            magic_trailing_comma=False,
            target_versions={TargetVersion.PY37, TargetVersion.PY38, TargetVersion.PY39, TargetVersion.PY310},
        )
        python_code = format_file_contents(python_code, fast=False, mode=mode)
    SAVE_PATH.write_text(python_code)
    print(f'Self schema definition written to {SAVE_PATH}')


if __name__ == '__main__':
    main()
