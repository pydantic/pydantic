#!/usr/bin/env python3
"""
This is used to generate flamegraphs, usage:

    perf record -g benchmarks/minimal.py

Then:

    perf script | stackcollapse-perf.pl | flamegraph.pl > flame.svg

Or just

    make flame

As per https://gist.github.com/KodrAus/97c92c07a90b1fdd6853654357fd557a
"""
import os
from pydantic_core import SchemaValidator, ValidationError
import json

size = 5
v = SchemaValidator(
    {
        'title': 'MyTestModel',
        'type': 'list',
        'items': {'type': 'model', 'fields': {f'f_{i}': {'type': 'str'} for i in range(size)}},
    }
)
# print(repr(v))

d = [{f'f_{i}': f'foobar_{i}' for i in range(size)} for _ in range(50)]
if os.getenv('JSON'):
    print('running validate_json...')
    j = json.dumps(d)
    for i in range(100_000):
        r = v.validate_json(j)
else:
    print('running validate_python...')
    for i in range(100_000):
        r = v.validate_python(d)
# debug(r)

try:
    r = v.validate_python({'name': 'John', 'age': 16, 'friends': [-1, 2, 3, -1], 'settings': {'a': 1.0, 'b': 2.0}})
except ValidationError as e:
    # print(e)
    pass
