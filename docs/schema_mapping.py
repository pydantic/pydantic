#!/usr/bin/env python3
"""
Build a table of Python / Pydantic to JSON Schema mappings.

Done like this rather than as a raw rst table to make future edits easier.

Please edit this file directly not .tmp_schema_mappings.rst
"""

table = [
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
        '{"items": {}}',
        'JSON Schema Core',
        ''
    ],
    [
        'tuple',
        'array',
        '{"items": {}}',
        'JSON Schema Core',
        ''
    ],
    [
        'set',
        'array',
        '{"items": {}, {"uniqueItems": true}',
        'JSON Schema Validation',
        ''
    ],
    [
        'List[str]',
        'array',
        '{"items": {"type": "string"}}',
        'JSON Schema Validation',
        'And equivalently for any other sub type, e.g. List[int].'
    ],
    [
        'Tuple[str, int]',
        'array',
        '{"items": [{"type": "string"}, {"type": "integer"}]}',
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
        '{"additionalProperties": {"type": "integer"}}',
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
        '{"anyOf": [{"type": "string"}, {"type": "integer"}]}',
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
        '{"writeOnly": true}',
        'JSON Schema Validation',
        ''
    ],
    [
        'SecretBytes',
        'string',
        '{"writeOnly": true}',
        'JSON Schema Validation',
        ''
    ],
    [
        'EmailStr',
        'string',
        '{"format": "email"}',
        'JSON Schema Validation',
        ''
    ],
    [
        'NameEmail',
        'string',
        '{"format": "name-email"}',
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'UrlStr',
        'string',
        '{"format": "uri"}',
        'JSON Schema Validation',
        ''
    ],
    [
        'DSN',
        'string',
        '{"format": "dsn"}',
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'bytes',
        'string',
        '{"format": "binary"}',
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
        '{"format": "uuid1"}',
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'UUID3',
        'string',
        '{"format": "uuid3"}',
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'UUID4',
        'string',
        '{"format": "uuid4"}',
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'UUID5',
        'string',
        '{"format": "uuid5"}',
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'UUID',
        'string',
        '{"format": "uuid"}',
        'Pydantic standard "format" extension',
        'Suggested in OpenAPI.'
    ],
    [
        'FilePath',
        'string',
        '{"format": "file-path"}',
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'DirectoryPath',
        'string',
        '{"format": "directory-path"}',
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'Path',
        'string',
        '{"format": "path"}',
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'datetime',
        'string',
        '{"format": "date-time"}',
        'JSON Schema Validation',
        ''
    ],
    [
        'date',
        'string',
        '{"format": "date"}',
        'JSON Schema Validation',
        ''
    ],
    [
        'time',
        'string',
        '{"format": "time"}',
        'JSON Schema Validation',
        ''
    ],
    [
        'timedelta',
        'number',
        '{"format": "time-delta"}',
        'Difference in seconds (a ``float``), with Pydantic standard "format" extension',
        'Suggested in JSON Schema repository\'s issues by maintainer.'
    ],
    [
        'Json',
        'string',
        '{"format": "json-string"}',
        'Pydantic standard "format" extension',
        ''
    ],
    [
        'IPv4Address',
        'string',
        '{"format": "ipv4"}',
        'JSON Schema Validation',
        ''
    ],
    [
        'IPv6Address',
        'string',
        '{"format": "ipv6"}',
        'JSON Schema Validation',
        ''
    ],
    [
        'IPvAnyAddress',
        'string',
        '{"format": "ipvanyaddress"}',
        'Pydantic standard "format" extension',
        'IPv4 or IPv6 address as used in ``ipaddress`` module',
    ],
    [
        'IPv4Interface',
        'string',
        '{"format": "ipv4interface"}',
        'Pydantic standard "format" extension',
        'IPv4 interface as used in ``ipaddress`` module',
    ],
    [
        'IPv6Interface',
        'string',
        '{"format": "ipv6interface"}',
        'Pydantic standard "format" extension',
        'IPv6 interface as used in ``ipaddress`` module',
    ],
    [
        'IPvAnyInterface',
        'string',
        '{"format": "ipvanyinterface"}',
        'Pydantic standard "format" extension',
        'IPv4 or IPv6 interface as used in ``ipaddress`` module',
    ],
    [
        'IPv4Network',
        'string',
        '{"format": "ipv4network"}',
        'Pydantic standard "format" extension',
        'IPv4 network as used in ``ipaddress`` module',
    ],
    [
        'IPv6Network',
        'string',
        '{"format": "ipv6network"}',
        'Pydantic standard "format" extension',
        'IPv6 network as used in ``ipaddress`` module',
    ],
    [
        'IPvAnyNetwork',
        'string',
        '{"format": "ipvanynetwork"}',
        'Pydantic standard "format" extension',
        'IPv4 or IPv6 network as used in ``ipaddress`` module',
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
            'See the mapping for ``constr`` below.'
        )
    ],
    [
        'constr(regex=\'^text$\', min_length=2, max_length=10)',
        'string',
        '{"pattern": "^text$", "minLength": 2, "maxLength": 10}',
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
            'See the mapping for ``conint`` below.'
        )
    ],
    [
        'conint(gt=1, ge=2, lt=6, le=5, multiple_of=2)',
        'integer',
        '{"maximum": 5, "exclusiveMaximum": 6, "minimum": 2, "exclusiveMinimum": 1, "multipleOf": 2}',
        '',
        'Any argument not passed to the function (not defined) will not be included in the schema.'
    ],
    [
        'PositiveInt',
        'integer',
        '{"exclusiveMinimum": 0}',
        'JSON Schema Validation',
        ''
    ],
    [
        'NegativeInt',
        'integer',
        '{"exclusiveMaximum": 0}',
        'JSON Schema Validation',
        ''
    ],
    [
        'ConstrainedFloat',
        'number',
        '',
        'JSON Schema Core',
        (
            'If the type has values declared for the constraints, they are included as validations.'
            'See the mapping for ``confloat`` below.'
        )
    ],
    [
        'confloat(gt=1, ge=2, lt=6, le=5, multiple_of=2)',
        'number',
        '{"maximum": 5, "exclusiveMaximum": 6, "minimum": 2, "exclusiveMinimum": 1, "multipleOf": 2}',
        'JSON Schema Validation',
        'Any argument not passed to the function (not defined) will not be included in the schema.'
    ],
    [
        'PositiveFloat',
        'number',
        '{"exclusiveMinimum": 0}',
        'JSON Schema Validation',
        ''
    ],
    [
        'NegativeFloat',
        'number',
        '{"exclusiveMaximum": 0}',
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
            'See the mapping for ``condecimal`` below.'
        )
    ],
    [
        'condecimal(gt=1, ge=2, lt=6, le=5, multiple_of=2)',
        'number',
        '{"maximum": 5, "exclusiveMaximum": 6, "minimum": 2, "exclusiveMinimum": 1, "multipleOf": 2}',
        'JSON Schema Validation',
        'Any argument not passed to the function (not defined) will not be included in the schema.'
    ],
    [
        'BaseModel',
        'object',
        '',
        'JSON Schema Core',
        'All the properties defined will be defined with standard JSON Schema, including submodels.'
    ]
]

headings = [
    'Python type',
    'JSON Schema Type',
    'Additional JSON Schema',
    'Defined in',
    'Notes',
]

v = ''
col_width = 300
for _ in range(5):
    v += '+' + '-' * col_width
v += '+\n|'
for heading in headings:
    v += f' {heading:{col_width - 2}} |'
v += '\n'
for _ in range(5):
    v += '+' + '=' * col_width
v += '+'
for row in table:
    v += '\n|'
    for i, text in enumerate(row):
        text = f'``{text}``' if i < 3 and text else text
        v += f' {text:{col_width - 2}} |'
    v += '\n'
    for _ in range(5):
        v += '+' + '-' * col_width
    v += '+'

with open('.tmp_schema_mappings.rst', 'w') as f:
    f.write(v)
