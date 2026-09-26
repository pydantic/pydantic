"""The streaming json path must be invisible: same objects, same errors, same everything.

`validate_json` can read a document straight off the json cursor instead of building a
`JsonValue` tree first. Nothing about that is supposed to be observable, so the test for it is
differential: run the same schema and the same documents down both paths and compare.

Two things make this a real test rather than a green light:

* the fast path is chosen once per process, so each side runs in its own subprocess;
* a differential test passes trivially if the fast path never engaged, so every case that is
  supposed to stream asserts `_stream_plan_accepted`, and the cases that are supposed to be
  refused assert the opposite.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pydantic_core import SchemaValidator, core_schema

# each side has to run in its own process, because the path is chosen once per process
pytestmark = pytest.mark.skipif(sys.platform == 'emscripten', reason='no subprocesses on emscripten')

DISABLE_ENV = 'PYDANTIC_DISABLE_JSON_STREAMING'
SELF = Path(__file__).resolve()
ROOT = SELF.parent.parent


def _cls(name: str) -> type:
    return type(
        name, (), {'__slots__': ('__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__')}
    )


def _model(name: str, fields: dict, **kwargs) -> dict:
    return core_schema.model_schema(
        cls=_cls(name),
        schema=core_schema.model_fields_schema(
            fields={
                k: (v if isinstance(v, dict) and v.get('type') == 'model-field' else core_schema.model_field(schema=v))
                for k, v in fields.items()
            },
            **kwargs,
        ),
    )


STR = core_schema.str_schema()
INT = core_schema.int_schema()
FLOAT = core_schema.float_schema()
BOOL = core_schema.bool_schema()

ADDRESS = _model('Address', {'street': STR, 'city': STR})

# name -> (schema, should the plan take it, documents)
CASES: dict[str, tuple[dict, bool, list[str | bytes]]] = {
    'scalars': (
        _model('Scalars', {'i': INT, 's': STR, 'b': BOOL, 'f': FLOAT}),
        True,
        [
            '{"i": 1, "s": "x", "b": true, "f": 1.5}',
            # an int is a valid float; a float is not a valid int
            '{"i": 1, "s": "x", "b": true, "f": 3}',
            '{"i": 1.5, "s": "x", "b": true, "f": 1.5}',
            '{"i": 99999999999999999999999, "s": "x", "b": true, "f": 1.5}',
            '{"i": 1, "s": "x", "b": true, "f": 1e400}',
            '{"i": 1, "s": "x", "b": true, "f": -1e400}',
            # a float field decoded by the float decoder still has to agree with the ordinary
            # path on an integer literal, including one too big for i64
            '{"i": 1, "s": "x", "b": true, "f": 99999999999999999999999}',
            '{"i": 1, "s": "x", "b": true, "f": -99999999999999999999999}',
            '{"i": 1, "s": "x", "b": true, "f": 0}',
            '{"i": 1, "s": "x", "b": true, "f": -0}',
            '{"i": 1, "s": null, "b": true, "f": 1.5}',
            '{"i": 1, "b": true, "f": 1.5}',
            '{"i": 1, "s": "x", "b": true, "f": 1.5, "unknown": [1, 2]}',
            '{"i": 1, "s": "a", "s": "b", "b": true, "f": 1.5}',
            'not json',
            '[]',
        ],
    ),
    'nested': (
        _model('Outer', {'name': STR, 'address': ADDRESS}),
        True,
        [
            '{"name": "n", "address": {"street": "s", "city": "c"}}',
            # the sub-object is consumed either way, and has to be re-read to report this
            '{"name": "n", "address": {"street": 1, "city": "c"}}',
            '{"name": "n", "address": {"street": "s"}}',
            '{"name": "n", "address": null}',
            '{"name": "n", "address": "not an object"}',
            '{"name": "n"}',
        ],
    ),
    'containers': (
        _model(
            'Containers',
            {
                'tags': core_schema.list_schema(items_schema=STR),
                'nums': core_schema.list_schema(items_schema=INT),
                'grid': core_schema.list_schema(items_schema=core_schema.list_schema(items_schema=FLOAT)),
                'map': core_schema.dict_schema(keys_schema=STR, values_schema=STR),
                'models': core_schema.dict_schema(keys_schema=STR, values_schema=ADDRESS),
            },
        ),
        True,
        [
            '{"tags": ["a"], "nums": [1], "grid": [[1.5, 2]], "map": {"k": "v"},'
            ' "models": {"a": {"street": "s", "city": "c"}}}',
            '{"tags": [], "nums": [], "grid": [], "map": {}, "models": {}}',
            # an array that goes wrong part way through is already half converted
            '{"tags": ["a", 1], "nums": [1], "grid": [[1.5]], "map": {"k": "v"}, "models": {}}',
            '{"tags": ["a"], "nums": [1], "grid": [[1.5], "no"], "map": {"k": "v"}, "models": {}}',
            '{"tags": ["a"], "nums": [1], "grid": [[1.5]], "map": {"k": 1}, "models": {}}',
            '{"tags": ["a"], "nums": [1], "grid": [[1.5]], "map": {"k": "v"}, "models": {"a": {"street": 1}}}',
        ],
    ),
    'lengths': (
        _model(
            'Lengths',
            {
                'at_least_two': core_schema.list_schema(items_schema=STR, min_length=2),
                'at_most_two': core_schema.list_schema(items_schema=INT, max_length=2),
                'map': core_schema.dict_schema(keys_schema=STR, values_schema=STR, min_length=1),
            },
        ),
        True,
        [
            '{"at_least_two": ["a", "b"], "at_most_two": [1, 2], "map": {"k": "v"}}',
            '{"at_least_two": ["a"], "at_most_two": [1], "map": {"k": "v"}}',
            '{"at_least_two": ["a", "b"], "at_most_two": [1, 2, 3], "map": {"k": "v"}}',
            '{"at_least_two": ["a", "b"], "at_most_two": [], "map": {}}',
            # a repeated key makes the object shorter than the members read
            '{"at_least_two": ["a", "b"], "at_most_two": [], "map": {"k": "v", "k": "w"}}',
        ],
    ),
    'optional': (
        _model(
            'Optional',
            {
                'maybe': core_schema.nullable_schema(STR),
                'defaulted': core_schema.with_default_schema(STR, default='-'),
                'both': core_schema.with_default_schema(core_schema.nullable_schema(INT), default=None),
                'on_error': core_schema.with_default_schema(STR, default='D', on_error='default'),
            },
        ),
        True,
        [
            '{"maybe": "x", "defaulted": "y", "both": 1, "on_error": "z"}',
            '{"maybe": null, "both": null}',
            '{}',
            # present but wrong: the default takes over rather than erroring
            '{"maybe": "x", "on_error": 123}',
            '{"maybe": 1}',
        ],
    ),
    'aliases': (
        _model(
            'Aliased',
            {
                'one': core_schema.model_field(schema=STR, validation_alias='ONE'),
                'choice': core_schema.model_field(schema=STR, validation_alias=[['c1'], ['c2']]),
                'plain': STR,
            },
        ),
        True,
        [
            '{"ONE": "a", "c1": "b", "plain": "c"}',
            '{"ONE": "a", "c2": "b", "plain": "c"}',
            # both choices present: the earlier alias wins wherever it appears
            '{"ONE": "a", "c1": "first", "c2": "second", "plain": "c"}',
            '{"ONE": "a", "c2": "second", "c1": "first", "plain": "c"}',
            # the field name is not a lookup when an alias is defined and by_name is off
            '{"one": "a", "c1": "b", "plain": "c"}',
            '{"ONE": "a", "one": "ignored", "c1": "b", "plain": "c"}',
        ],
    ),
    'forbid': (
        _model('Forbid', {'a': STR}, extra_behavior='forbid'),
        True,
        ['{"a": "x"}', '{"a": "x", "b": 1}', '{"b": 1, "c": 2}', '{}'],
    ),
    'dict_root': (
        core_schema.dict_schema(keys_schema=STR, values_schema=ADDRESS),
        True,
        [
            '{"a": {"street": "s", "city": "c"}}',
            '{}',
            '{"a": {"street": "s", "city": "c"}, "b": {"street": 1, "city": "c"}}',
            '[]',
        ],
    ),
    # the ordinary path decodes every string in the document, so it rejects invalid utf-8 even
    # in a field the model ignores; the cursor skips those values without decoding them
    'bad_utf8_in_ignored_fields': (
        _model('Kept', {'kept': STR}),
        True,
        [
            b'{"kept": "ok", "ignored": "\xff"}',
            b'{"kept": "ok", "ignored": ["\xff"]}',
            b'{"kept": "ok", "ignored": {"k": "\xff"}}',
            b'{"kept": "ok", "ignored": [[{"deep": "\xff"}]]}',
            b'{"kept": "\xff"}',
            b'{"kept": "ok", "\xff": 1}',
            b'{"kept": "ok", "ignored": "fine"}',
        ],
    ),
    # the root list's own length bound: the fast path builds the list itself, so it has to be
    # the one to check it
    'constrained_root_list': (
        core_schema.list_schema(items_schema=ADDRESS, min_length=2, max_length=3),
        True,
        [
            '[{"street": "s", "city": "c"}]',
            '[{"street": "s", "city": "c"}, {"street": "s", "city": "c"}]',
            '[{"street": "s", "city": "c"}, {"street": "s", "city": "c"}, {"street": "s", "city": "c"},'
            ' {"street": "s", "city": "c"}]',
            '[]',
            '[{"street": 1, "city": "c"}, {"street": "s", "city": "c"}]',
        ],
    ),
    # a path alias has to look inside the value to know whether it matches, which is the one
    # thing a cursor cannot do before reading it
    'path_alias_refused': (
        _model('Pathy', {'deep': core_schema.model_field(schema=STR, validation_alias=[['p', 'q']])}),
        False,
        ['{"p": {"q": "x"}}', '{"deep": "x"}'],
    ),
    'extra_allow_refused': (
        _model('Extras', {'a': STR}, extra_behavior='allow'),
        False,
        ['{"a": "x", "b": 1}', '{"a": "x"}'],
    ),
}

LIST_ROOT = {'scalars', 'nested', 'containers', 'optional', 'aliases'}


def _build(case: str) -> tuple[SchemaValidator, list[str]]:
    schema, _, docs = CASES[case]
    return SchemaValidator(schema), docs


def _dump(value):
    """A comparable rendering that keeps attribute order, which `model_dump` exposes."""
    if isinstance(value, list):
        return [_dump(v) for v in value]
    if hasattr(value, '__pydantic_fields_set__'):
        return [
            '<model>',
            sorted(value.__pydantic_fields_set__),
            _dump(value.__pydantic_extra__),
            [[k, _dump(v)] for k, v in value.__dict__.items()],
        ]
    if isinstance(value, dict):
        return [[k, _dump(v)] for k, v in value.items()]
    return value


def _child(case: str, in_array: bool = False) -> None:
    """Run one case in this process and print the outcome of every document."""
    from pydantic_core import ValidationError

    validator, docs = _build(case)
    if in_array:
        # every well-formed document for this case, as one array, which is a different entry point
        schema, _, _ = CASES[case]
        validator = SchemaValidator(core_schema.list_schema(items_schema=schema))
        docs = ['[' + ', '.join(d for d in docs if isinstance(d, str) and d.startswith('{')) + ']']

    out = {'accepted': validator._stream_plan_accepted, 'results': []}
    for doc in docs:
        try:
            out['results'].append(['ok', _dump(validator.validate_json(doc))])
        except ValidationError as e:
            out['results'].append(['err', e.errors(include_url=False)])
        # any difference at all is a difference, so nothing is allowed to escape here
        except Exception as e:
            out['results'].append(['exc', type(e).__name__, str(e)[:200]])
    print(json.dumps(out, default=repr))


def _run(case: str, stream: bool, in_array: bool = False) -> dict:
    env = dict(os.environ)
    env.pop(DISABLE_ENV, None)
    if not stream:
        env[DISABLE_ENV] = '1'
    # loaded by path rather than as `tests.test_streaming_json`, so the child does not depend on
    # which directory pytest was started from
    script = (
        'import importlib.util\n'
        f'spec = importlib.util.spec_from_file_location("_streaming_cases", {str(SELF)!r})\n'
        'module = importlib.util.module_from_spec(spec)\n'
        'spec.loader.exec_module(module)\n'
        f'module._child({case!r}, in_array={in_array!r})\n'
    )
    proc = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, cwd=ROOT, env=env)
    assert proc.returncode == 0, f'{case} ({"stream" if stream else "tree"}) failed:\n{proc.stderr[-3000:]}'
    return json.loads(proc.stdout)


@pytest.mark.parametrize('case', sorted(CASES))
def test_streaming_matches_the_tree(case: str) -> None:
    _, should_stream, _ = CASES[case]
    tree = _run(case, stream=False)
    stream = _run(case, stream=True)

    # without this the comparison below can pass because neither side ever took the fast path
    assert stream['accepted'] is should_stream, (
        f'{case}: expected the plan to {"accept" if should_stream else "refuse"} this schema'
    )
    assert tree['results'] == stream['results']


@pytest.mark.parametrize('case', sorted(LIST_ROOT))
def test_streaming_matches_the_tree_in_an_array(case: str) -> None:
    """The same documents as elements of an array, which replays a failed element on its own."""
    tree = _run(case, stream=False, in_array=True)
    stream = _run(case, stream=True, in_array=True)

    assert stream['accepted'] is True
    assert tree['results'] == stream['results']
