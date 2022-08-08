#!/usr/bin/env python3
"""
Build a table of Python / Pydantic to JSON Schema mappings.

Done like this rather than as a raw rst table to make future edits easier.

Please edit this file directly not .tmp_schema_mappings.html
"""
import json
import re
from pathlib import Path

table = [
    [
        'None',
        'null',
        '',
        'JSON Schema Core',
        'Same for `type(None)` or `Literal[None]`'
    ],
    [
        'bool',
        'boolean',
        '',
        'JSON Schema Core',
        ''
    ],
    [
        'str',
        'string',
        '',
        'JSON Schema Core',
        ''
    ],
    [
        'float',
        'number',
        '',
        'JSON Schema Core',
        ''
    ],
    [
        'int',
        'integer',
        '',
        'JSON Schema Validation',
        ''
    ],
    [
        'dict',
        'object',
        '',
        'JSON Schema Core',
        ''
    ],
    [
        'list',
        'array',
        {'items': {}},
        'JSON Schema Core',
        ''
    ],
    [
        'tuple',
        'array',
        {'items': {}},
        'JSON Schema Core',
        ''
    ],
    [
        'set',
        'array',
        {'items': {}, 'uniqueItems': True},
        'JSON Schema Validation',
        ''
    ],
    [
        'frozenset',
        'array',
        {'items': {}, 'uniqueItems': True},
        'JSON Schema Validation',
        ''
    ],
    [
        'List[str]',
        'array',
        {'items': {'type': 'string'}},
        'JSON Schema Validation',
        'And equivalently for any other sub type, e.g. `List[int]`.'
    ],
    [
        'Tuple[str, ...]',
        'array',
        {'items': {'type': 'string'}},
        'JSON Schema Validation',
        'And equivalently for any other sub type, e.g. `Tuple[int, ...]`.'
    ],
    [
        'Tuple[str, int]',
        'array',
        {'items': [{'type': 'string'}, {'type': 'integer'}], 'minItems': 2, 'maxItems': 2},
        'JSON Schema Validation',
        (
            'And equivalently for any other set of subtypes. Note: If using schemas for OpenAPI, '
            'you shouldn\'t use this declaration, as it would not be valid in OpenAPI (although it is '
            'valid in JSON Schema).'
        )
    ],
    [
        'Dict[str, int]',
        'object',
        {'additionalProperties': {'type': 'integer'}},
        'JSON Schema Validation',
        (
            'And equivalently for any other subfields for dicts. Have in mind that although you can use other types as '
            'keys for dicts with Pydantic, only strings are valid keys for JSON, and so, only str is valid as '
            'JSON Schema key types.'
         )
    ],
    [
        'Union[str, int]',
        'anyOf',
        {'anyOf': [{'type': 'string'}, {'type': 'integer'}]},
        'JSON Schema Validation',
        'And equivalently for any other subfields for unions.'
    ],
    [
        'Enum',
        'enum',
        '{"enum": [...]}',
        'JSON Schema Validation',
        'All the literal values in the enum are included in the definition.'
    ],
    [
        'SecretStr',
        'string',
        {'writeOnly': True},
        'JSON Schema Validation',
        ''
    ],
    [
        'SecretBytes',
        'string',
        {'writeOnly': True},
        'JSON Schema Validation',
        ''
    ],
    [
        'EmailStr',
        'string',
        {'format': 'email'},
        'JSON Schema Validation',
        ''
    ],
    [
        'NameEmail',
        'string',
        {'format': 'name-email'},
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'AnyUrl',
        'string',
        {'format': 'uri'},
        'JSON Schema Validation',
        ''
    ],
    [
        'Pattern',
        'string',
        {'format': 'regex'},
        'JSON Schema Validation',
        ''
    ],
    [
        'bytes',
        'string',
        {'format': 'binary'},
        'OpenAPI',
        ''
    ],
    [
        'Decimal',
        'number',
        '',
        'JSON Schema Core',
        ''
    ],
    [
        'UUID1',
        'string',
        {'format': 'uuid1'},
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'UUID3',
        'string',
        {'format': 'uuid3'},
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'UUID4',
        'string',
        {'format': 'uuid4'},
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'UUID5',
        'string',
        {'format': 'uuid5'},
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'UUID',
        'string',
        {'format': 'uuid'},
        'Pydantic standard "format" extension',
        'Suggested in OpenAPI.'
    ],
    [
        'FilePath',
        'string',
        {'format': 'file-path'},
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'DirectoryPath',
        'string',
        {'format': 'directory-path'},
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'Path',
        'string',
        {'format': 'path'},
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'datetime',
        'string',
        {'format': 'date-time'},
        'JSON Schema Validation',
        ''
    ],
    [
        'date',
        'string',
        {'format': 'date'},
        'JSON Schema Validation',
        ''
    ],
    [
        'time',
        'string',
        {'format': 'time'},
        'JSON Schema Validation',
        ''
    ],
    [
        'timedelta',
        'number',
        {'format': 'time-delta'},
        'Difference in seconds (a `float`), with Pydantic standard "format" extension',
        'Suggested in JSON Schema repository\'s issues by maintainer.'
    ],
    [
        'Json',
        'string',
        {'format': 'json-string'},
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'IPv4Address',
        'string',
        {'format': 'ipv4'},
        'JSON Schema Validation',
        ''
    ],
    [
        'IPv6Address',
        'string',
        {'format': 'ipv6'},
        'JSON Schema Validation',
        ''
    ],
    [
        'IPvAnyAddress',
        'string',
        {'format': 'ipvanyaddress'},
        'Pydantic standard "format" extension',
        'IPv4 or IPv6 address as used in `ipaddress` module',
    ],
    [
        'IPv4Interface',
        'string',
        {'format': 'ipv4interface'},
        'Pydantic standard "format" extension',
        'IPv4 interface as used in `ipaddress` module',
    ],
    [
        'IPv6Interface',
        'string',
        {'format': 'ipv6interface'},
        'Pydantic standard "format" extension',
        'IPv6 interface as used in `ipaddress` module',
    ],
    [
        'IPvAnyInterface',
        'string',
        {'format': 'ipvanyinterface'},
        'Pydantic standard "format" extension',
        'IPv4 or IPv6 interface as used in `ipaddress` module',
    ],
    [
        'IPv4Network',
        'string',
        {'format': 'ipv4network'},
        'Pydantic standard "format" extension',
        'IPv4 network as used in `ipaddress` module',
    ],
    [
        'IPv6Network',
        'string',
        {'format': 'ipv6network'},
        'Pydantic standard "format" extension',
        'IPv6 network as used in `ipaddress` module',
    ],
    [
        'IPvAnyNetwork',
        'string',
        {'format': 'ipvanynetwork'},
        'Pydantic standard "format" extension',
        'IPv4 or IPv6 network as used in `ipaddress` module',
    ],
    [
        'StrictBool',
        'boolean',
        '',
        'JSON Schema Core',
        ''
    ],
    [
        'StrictStr',
        'string',
        '',
        'JSON Schema Core',
        ''
    ],
    [
        'ConstrainedStr',
        'string',
        '',
        'JSON Schema Core',
        (
            'If the type has values declared for the constraints, they are included as validations. '
            'See the mapping for `constr` below.'
        )
    ],
    [
        'constr(regex=\'^text$\', min_length=2, max_length=10)',
        'string',
        {'pattern': '^text$', 'minLength': 2, 'maxLength': 10},
        'JSON Schema Validation',
        'Any argument not passed to the function (not defined) will not be included in the schema.'
    ],
    [
        'ConstrainedInt',
        'integer',
        '',
        'JSON Schema Core',
        (
            'If the type has values declared for the constraints, they are included as validations. '
            'See the mapping for `conint` below.'
        )
    ],
    [
        'conint(gt=1, ge=2, lt=6, le=5, multiple_of=2)',
        'integer',
        {'maximum': 5, 'exclusiveMaximum': 6, 'minimum': 2, 'exclusiveMinimum': 1, 'multipleOf': 2},
        '',
        'Any argument not passed to the function (not defined) will not be included in the schema.'
    ],
    [
        'PositiveInt',
        'integer',
        {'exclusiveMinimum': 0},
        'JSON Schema Validation',
        ''
    ],
    [
        'NegativeInt',
        'integer',
        {'exclusiveMaximum': 0},
        'JSON Schema Validation',
        ''
    ],
    [
        'NonNegativeInt',
        'integer',
        {'minimum': 0},
        'JSON Schema Validation',
        ''
    ],
    [
        'NonPositiveInt',
        'integer',
        {'maximum': 0},
        'JSON Schema Validation',
        ''
    ],
    [
        'ConstrainedFloat',
        'number',
        '',
        'JSON Schema Core',
        (
            'If the type has values declared for the constraints, they are included as validations. '
            'See the mapping for `confloat` below.'
        )
    ],
    [
        'confloat(gt=1, ge=2, lt=6, le=5, multiple_of=2)',
        'number',
        {'maximum': 5, 'exclusiveMaximum': 6, 'minimum': 2, 'exclusiveMinimum': 1, 'multipleOf': 2},
        'JSON Schema Validation',
        'Any argument not passed to the function (not defined) will not be included in the schema.'
    ],
    [
        'PositiveFloat',
        'number',
        {'exclusiveMinimum': 0},
        'JSON Schema Validation',
        ''
    ],
    [
        'NegativeFloat',
        'number',
        {'exclusiveMaximum': 0},
        'JSON Schema Validation',
        ''
    ],
    [
        'NonNegativeFloat',
        'number',
        {'minimum': 0},
        'JSON Schema Validation',
        ''
    ],
    [
        'NonPositiveFloat',
        'number',
        {'maximum': 0},
        'JSON Schema Validation',
        ''
    ],
    [
        'ConstrainedDecimal',
        'number',
        '',
        'JSON Schema Core',
        (
            'If the type has values declared for the constraints, they are included as validations. '
            'See the mapping for `condecimal` below.'
        )
    ],
    [
        'condecimal(gt=1, ge=2, lt=6, le=5, multiple_of=2)',
        'number',
        {'maximum': 5, 'exclusiveMaximum': 6, 'minimum': 2, 'exclusiveMinimum': 1, 'multipleOf': 2},
        'JSON Schema Validation',
        'Any argument not passed to the function (not defined) will not be included in the schema.'
    ],
    [
        'BaseModel',
        'object',
        '',
        'JSON Schema Core',
        'All the properties defined will be defined with standard JSON Schema, including submodels.'
    ],
    [
        'Color',
        'string',
        {'format': 'color'},
        'Pydantic standard "format" extension',
        '',
    ],
]

headings = [
    'Python type',
    'JSON Schema Type',
    'Additional JSON Schema',
    'Defined in',
]


def md2html(s):
    return re.sub(r'`(.+?)`', r'<code>\1</code>', s)


def build_schema_mappings():
    rows = []

    for py_type, json_type, additional, defined_in, notes in table:
        if additional and not isinstance(additional, str):
            additional = json.dumps(additional)
        cols = [
            f'<code>{py_type}</code>',
            f'<code>{json_type}</code>',
            f'<code>{additional}</code>' if additional else '',
            md2html(defined_in)
        ]
        rows.append('\n'.join(f'  <td>\n    {c}\n  </td>' for c in cols))
        if notes:
            rows.append(
                f'  <td colspan=4 style="border-top: none; padding-top: 0">\n'
                f'    <em>{md2html(notes)}</em>\n'
                f'  </td>'
            )

    heading = '\n'.join(f'  <th>{h}</th>' for h in headings)
    body = '\n</tr>\n<tr>\n'.join(rows)
    text = f"""\
<!--
  Generated from docs/build/schema_mapping.py, DO NOT EDIT THIS FILE DIRECTLY.
  Instead edit docs/build/schema_mapping.py and run `make docs`.
-->

<table style="width:100%">
<thead>
<tr>
{heading}
</tr>
</thead>
<tbody>
<tr>
{body}
</tr>
</tbody>
</table>
"""
    (Path(__file__).parent / '..' / '.tmp_schema_mappings.html').write_text(text)


if __name__ == '__main__':
    build_schema_mappings()
