import dataclasses
import re
import sys
from typing import Any, ClassVar, Dict, List, Optional, Union

import pytest
from dirty_equals import IsListOrTuple, IsStr

from pydantic_core import ArgsKwargs, SchemaValidator, ValidationError, core_schema

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (ArgsKwargs(('hello', True)), ({'a': 'hello', 'b': True}, None)),
        ({'a': 'hello', 'b': True}, ({'a': 'hello', 'b': True}, None)),
        ({'a': 'hello', 'b': 'true'}, ({'a': 'hello', 'b': True}, None)),
        (ArgsKwargs(('hello', True)), ({'a': 'hello', 'b': True}, None)),
        (ArgsKwargs((), {'a': 'hello', 'b': True}), ({'a': 'hello', 'b': True}, None)),
        (
            ArgsKwargs(('hello',), {'a': 'hello', 'b': True}),
            Err(
                'Got multiple values for argument',
                errors=[
                    {
                        'type': 'multiple_argument_values',
                        'loc': ('a',),
                        'msg': 'Got multiple values for argument',
                        'input': 'hello',
                    }
                ],
            ),
        ),
        (
            {'a': 'hello'},
            Err(
                'Field required',
                errors=[{'type': 'missing', 'loc': ('b',), 'msg': 'Field required', 'input': {'a': 'hello'}}],
            ),
        ),
    ],
)
def test_dataclass_args(py_and_json: PyAndJson, input_value, expected):
    schema = core_schema.dataclass_args_schema(
        'MyDataclass',
        [
            core_schema.dataclass_field(name='a', schema=core_schema.str_schema(), kw_only=False),
            core_schema.dataclass_field(name='b', schema=core_schema.bool_schema(), kw_only=False),
        ],
    )
    v = py_and_json(schema)
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)

        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (ArgsKwargs(('hello', True)), ({'a': 'hello'}, (True,))),
        (ArgsKwargs(('hello', 'true')), ({'a': 'hello'}, (True,))),
        (ArgsKwargs(('hello', True)), ({'a': 'hello'}, (True,))),
        (ArgsKwargs((), {'a': 'hello', 'b': True}), ({'a': 'hello'}, (True,))),
        (
            ArgsKwargs(('hello',), {'a': 'hello', 'b': True}),
            Err(
                'Got multiple values for argument',
                errors=[
                    {
                        'type': 'multiple_argument_values',
                        'loc': ('a',),
                        'msg': 'Got multiple values for argument',
                        'input': 'hello',
                    }
                ],
            ),
        ),
        (
            {'a': 'hello'},
            Err(
                'Field required',
                errors=[{'type': 'missing', 'loc': ('b',), 'msg': 'Field required', 'input': {'a': 'hello'}}],
            ),
        ),
        (
            {'a': 'hello', 'b': 'wrong'},
            Err(
                'Input should be a valid boolean, unable to interpret input',
                errors=[
                    {
                        'type': 'bool_parsing',
                        'loc': ('b',),
                        'msg': 'Input should be a valid boolean, unable to interpret input',
                        'input': 'wrong',
                    }
                ],
            ),
        ),
    ],
)
def test_dataclass_args_init_only(py_and_json: PyAndJson, input_value, expected):
    schema = core_schema.dataclass_args_schema(
        'MyDataclass',
        [
            core_schema.dataclass_field(name='a', schema=core_schema.str_schema(), kw_only=False),
            core_schema.dataclass_field(name='b', schema=core_schema.bool_schema(), kw_only=False, init_only=True),
        ],
        collect_init_only=True,
    )
    v = py_and_json(schema)

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)

        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'a': 'hello'}, ({'a': 'hello'}, ())),
        (ArgsKwargs((), {'a': 'hello'}), ({'a': 'hello'}, ())),
        (
            ('hello',),
            Err(
                'Input should be (an object|a dictionary or an instance of MyDataclass)',
                errors=[
                    {
                        'type': 'dataclass_type',
                        'loc': (),
                        'msg': IsStr(regex='Input should be (an object|a dictionary or an instance of MyDataclass)'),
                        'input': IsListOrTuple('hello'),
                        'ctx': {'class_name': 'MyDataclass'},
                    }
                ],
            ),
        ),
    ],
)
def test_dataclass_args_init_only_no_fields(py_and_json: PyAndJson, input_value, expected):
    schema = core_schema.dataclass_args_schema(
        'MyDataclass', [core_schema.dataclass_field(name='a', schema=core_schema.str_schema())], collect_init_only=True
    )
    v = py_and_json(schema)

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message) as exc_info:
            v.validate_test(input_value)

        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


def test_aliases(py_and_json: PyAndJson):
    schema = core_schema.dataclass_args_schema(
        'MyDataclass',
        [
            core_schema.dataclass_field(name='a', schema=core_schema.str_schema(), validation_alias='Apple'),
            core_schema.dataclass_field(name='b', schema=core_schema.bool_schema(), validation_alias=['Banana', 1]),
            core_schema.dataclass_field(
                name='c', schema=core_schema.int_schema(), validation_alias=['Carrot', 'v'], init_only=True
            ),
        ],
        collect_init_only=True,
    )
    v = py_and_json(schema)
    assert v.validate_test({'Apple': 'a', 'Banana': ['x', 'false'], 'Carrot': {'v': '42'}}) == (
        {'a': 'a', 'b': False},
        (42,),
    )


@dataclasses.dataclass
class FooDataclass:
    a: str
    b: bool


def test_dataclass():
    schema = core_schema.dataclass_schema(
        FooDataclass,
        core_schema.dataclass_args_schema(
            'FooDataclass',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
            ],
        ),
        ['a', 'b'],
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': 'hello', 'b': True})
    assert dataclasses.is_dataclass(foo)
    assert foo.a == 'hello'
    assert foo.b is True

    assert dataclasses.asdict(v.validate_python(FooDataclass(a='hello', b=True))) == {'a': 'hello', 'b': True}

    with pytest.raises(ValidationError, match='Input should be an instance of FooDataclass') as exc_info:
        v.validate_python({'a': 'hello', 'b': True}, strict=True)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'dataclass_exact_type',
            'loc': (),
            'msg': 'Input should be an instance of FooDataclass',
            'input': {'a': 'hello', 'b': True},
            'ctx': {'class_name': 'FooDataclass'},
        }
    ]


@dataclasses.dataclass
class FooDataclassSame(FooDataclass):
    pass


@dataclasses.dataclass
class FooDataclassMore(FooDataclass):
    c: str


@dataclasses.dataclass
class DuplicateDifferent:
    a: str
    b: bool


@pytest.mark.parametrize(
    'revalidate_instances,input_value,expected',
    [
        ('always', {'a': 'hello', 'b': True}, {'a': 'hello', 'b': True}),
        ('always', FooDataclass(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('always', FooDataclassSame(a='hello', b=True), {'a': 'hello', 'b': True}),
        # no error because we only look for fields in schema['fields']
        ('always', FooDataclassMore(a='hello', b=True, c='more'), {'a': 'hello', 'b': True}),
        ('always', FooDataclassSame(a='hello', b='wrong'), Err(r'b\s+Input should be a valid boolean,')),
        ('always', DuplicateDifferent(a='hello', b=True), Err('should be a dictionary or an instance of FooDataclass')),
        # revalidate_instances='subclass-instances'
        ('subclass-instances', {'a': 'hello', 'b': True}, {'a': 'hello', 'b': True}),
        ('subclass-instances', FooDataclass(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('subclass-instances', FooDataclass(a=b'hello', b='true'), {'a': b'hello', 'b': 'true'}),
        ('subclass-instances', FooDataclassSame(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('subclass-instances', FooDataclassSame(a=b'hello', b='true'), {'a': 'hello', 'b': True}),
        # no error because we only look for fields in schema['fields']
        ('subclass-instances', FooDataclassMore(a='hello', b=True, c='more'), {'a': 'hello', 'b': True}),
        ('subclass-instances', FooDataclassSame(a='hello', b='wrong'), Err(r'b\s+Input should be a valid boolean,')),
        ('subclass-instances', DuplicateDifferent(a='hello', b=True), Err('dictionary or an instance of FooDataclass')),
        # revalidate_instances='never'
        ('never', {'a': 'hello', 'b': True}, {'a': 'hello', 'b': True}),
        ('never', FooDataclass(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('never', FooDataclassSame(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('never', FooDataclassMore(a='hello', b=True, c='more'), {'a': 'hello', 'b': True, 'c': 'more'}),
        ('never', FooDataclassMore(a='hello', b='wrong', c='more'), {'a': 'hello', 'b': 'wrong', 'c': 'more'}),
        ('never', DuplicateDifferent(a='hello', b=True), Err('should be a dictionary or an instance of FooDataclass')),
    ],
)
def test_dataclass_subclass(revalidate_instances, input_value, expected):
    schema = core_schema.dataclass_schema(
        FooDataclass,
        core_schema.dataclass_args_schema(
            'FooDataclass',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
            ],
            extra_behavior='forbid',
        ),
        ['a', 'b'],
        revalidate_instances=revalidate_instances,
    )
    v = SchemaValidator(schema)

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message) as exc_info:
            print(v.validate_python(input_value))

        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        dc = v.validate_python(input_value)
        assert dataclasses.is_dataclass(dc)
        assert dataclasses.asdict(dc) == expected


def test_dataclass_subclass_strict_never_revalidate():
    v = SchemaValidator(
        core_schema.dataclass_schema(
            FooDataclass,
            core_schema.dataclass_args_schema(
                'FooDataclass',
                [
                    core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                    core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
                ],
            ),
            ['a', 'b'],
            revalidate_instances='never',
            strict=True,
        )
    )

    foo = FooDataclass(a='hello', b=True)
    assert v.validate_python(foo) is foo
    sub_foo = FooDataclassSame(a='hello', b=True)
    assert v.validate_python(sub_foo) is sub_foo

    # this fails but that's fine, in realty `ArgsKwargs` should only be used via validate_init
    with pytest.raises(ValidationError, match='Input should be an instance of FooDataclass'):
        v.validate_python(ArgsKwargs((), {'a': 'hello', 'b': True}))


def test_dataclass_subclass_subclass_revalidate():
    v = SchemaValidator(
        core_schema.dataclass_schema(
            FooDataclass,
            core_schema.dataclass_args_schema(
                'FooDataclass',
                [
                    core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                    core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
                ],
            ),
            ['a', 'b'],
            revalidate_instances='subclass-instances',
            strict=True,
        )
    )

    foo = FooDataclass(a='hello', b=True)
    assert v.validate_python(foo) is foo
    sub_foo = FooDataclassSame(a='hello', b='True')
    sub_foo2 = v.validate_python(sub_foo)
    assert sub_foo2 is not sub_foo
    assert type(sub_foo2) is FooDataclass
    assert dataclasses.asdict(sub_foo2) == dict(a='hello', b=True)


def test_dataclass_post_init():
    @dataclasses.dataclass
    class Foo:
        a: str
        b: bool

        def __post_init__(self):
            self.a = self.a.upper()

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
            ],
        ),
        ['a', 'b'],
        post_init=True,
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': 'hello', 'b': True})
    assert foo.a == 'HELLO'
    assert foo.b is True


def test_dataclass_post_init_args():
    c_value = None

    @dataclasses.dataclass
    class Foo:
        a: str
        b: bool
        c: dataclasses.InitVar[int]

        def __post_init__(self, c: int):
            nonlocal c_value
            c_value = c

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
                core_schema.dataclass_field(name='c', schema=core_schema.int_schema(), init_only=True),
            ],
            collect_init_only=True,
        ),
        ['a', 'b'],
        post_init=True,
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': b'hello', 'b': 'true', 'c': '42'})
    assert foo.a == 'hello'
    assert foo.b is True
    assert not hasattr(foo, 'c')
    assert c_value == 42


def test_dataclass_post_init_args_multiple():
    dc_args = None

    @dataclasses.dataclass
    class Foo:
        a: str
        b: dataclasses.InitVar[bool]
        c: dataclasses.InitVar[int]

        def __post_init__(self, *args):
            nonlocal dc_args
            dc_args = args

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema(), init_only=True),
                core_schema.dataclass_field(name='c', schema=core_schema.int_schema(), init_only=True),
            ],
            collect_init_only=True,
        ),
        ['a', 'b'],
        post_init=True,
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': b'hello', 'b': 'true', 'c': '42'})
    assert dataclasses.asdict(foo) == {'a': 'hello'}
    assert dc_args == (True, 42)


@pytest.mark.parametrize(
    'revalidate_instances,input_value,expected',
    [
        ('always', {'a': b'hello', 'b': 'true'}, {'a': 'hello', 'b': True}),
        ('always', FooDataclass(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('always', FooDataclass(a=b'hello', b='true'), {'a': 'hello', 'b': True}),
        ('never', {'a': b'hello', 'b': 'true'}, {'a': 'hello', 'b': True}),
        ('never', FooDataclass(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('never', FooDataclass(a=b'hello', b='true'), {'a': b'hello', 'b': 'true'}),
    ],
)
def test_dataclass_exact_validation(revalidate_instances, input_value, expected):
    schema = core_schema.dataclass_schema(
        FooDataclass,
        core_schema.dataclass_args_schema(
            'FooDataclass',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
            ],
        ),
        ['a', 'b'],
        revalidate_instances=revalidate_instances,
    )

    v = SchemaValidator(schema)
    foo = v.validate_python(input_value)
    assert dataclasses.asdict(foo) == expected


def test_dataclass_field_after_validator():
    @dataclasses.dataclass
    class Foo:
        a: int
        b: str

        @classmethod
        def validate_b(cls, v: str, info: core_schema.FieldValidationInfo) -> str:
            assert v == 'hello'
            assert info.field_name == 'b'
            assert info.data == {'a': 1}
            return 'hello world!'

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.int_schema()),
                core_schema.dataclass_field(
                    name='b',
                    schema=core_schema.field_after_validator_function(Foo.validate_b, 'b', core_schema.str_schema()),
                ),
            ],
        ),
        ['a', 'b'],
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': 1, 'b': b'hello'})
    assert dataclasses.asdict(foo) == {'a': 1, 'b': 'hello world!'}


def test_dataclass_field_plain_validator():
    @dataclasses.dataclass
    class Foo:
        a: int
        b: str

        @classmethod
        def validate_b(cls, v: bytes, info: core_schema.FieldValidationInfo) -> str:
            assert v == b'hello'
            assert info.field_name == 'b'
            assert info.data == {'a': 1}
            return 'hello world!'

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.int_schema()),
                core_schema.dataclass_field(
                    name='b', schema=core_schema.field_plain_validator_function(Foo.validate_b, 'b')
                ),
            ],
        ),
        ['a', 'b'],
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': 1, 'b': b'hello'})
    assert dataclasses.asdict(foo) == {'a': 1, 'b': 'hello world!'}


def test_dataclass_field_before_validator():
    @dataclasses.dataclass
    class Foo:
        a: int
        b: str

        @classmethod
        def validate_b(cls, v: bytes, info: core_schema.FieldValidationInfo) -> bytes:
            assert v == b'hello'
            assert info.field_name == 'b'
            assert info.data == {'a': 1}
            return b'hello world!'

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.int_schema()),
                core_schema.dataclass_field(
                    name='b',
                    schema=core_schema.field_before_validator_function(Foo.validate_b, 'b', core_schema.str_schema()),
                ),
            ],
        ),
        ['a', 'b'],
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': 1, 'b': b'hello'})
    assert dataclasses.asdict(foo) == {'a': 1, 'b': 'hello world!'}


def test_dataclass_field_wrap_validator1():
    @dataclasses.dataclass
    class Foo:
        a: int
        b: str

        @classmethod
        def validate_b(
            cls, v: bytes, nxt: core_schema.ValidatorFunctionWrapHandler, info: core_schema.FieldValidationInfo
        ) -> str:
            assert v == b'hello'
            v = nxt(v)
            assert v == 'hello'
            assert info.field_name == 'b'
            assert info.data == {'a': 1}
            return 'hello world!'

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.int_schema()),
                core_schema.dataclass_field(
                    name='b',
                    schema=core_schema.field_wrap_validator_function(Foo.validate_b, 'b', core_schema.str_schema()),
                ),
            ],
        ),
        ['a', 'b'],
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': 1, 'b': b'hello'})
    assert dataclasses.asdict(foo) == {'a': 1, 'b': 'hello world!'}


def test_dataclass_field_wrap_validator2():
    @dataclasses.dataclass
    class Foo:
        a: int
        b: str

        @classmethod
        def validate_b(
            cls, v: bytes, nxt: core_schema.ValidatorFunctionWrapHandler, info: core_schema.FieldValidationInfo
        ) -> bytes:
            assert v == b'hello'
            assert info.field_name == 'b'
            assert info.data == {'a': 1}
            return nxt(b'hello world!')

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.int_schema()),
                core_schema.dataclass_field(
                    name='b',
                    schema=core_schema.field_wrap_validator_function(Foo.validate_b, 'b', core_schema.str_schema()),
                ),
            ],
        ),
        ['a', 'b'],
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': 1, 'b': b'hello'})
    assert dataclasses.asdict(foo) == {'a': 1, 'b': 'hello world!'}


def test_dataclass_self_init():
    @dataclasses.dataclass(init=False)
    class Foo:
        a: str
        b: bool

        def __init__(self, *args, **kwargs):
            v.validate_python(ArgsKwargs(args, kwargs), self_instance=self)

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema(), kw_only=False),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema(), kw_only=False),
            ],
        ),
        ['a', 'b'],
    )
    v = SchemaValidator(schema)

    foo = Foo(b'hello', 'True')
    assert dataclasses.is_dataclass(foo)
    assert dataclasses.asdict(foo) == {'a': 'hello', 'b': True}


def test_dataclass_self_init_alias():
    @dataclasses.dataclass(init=False)
    class Foo:
        a: str
        b: bool

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema(), validation_alias='aAlias'),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema(), validation_alias=['bAlias', 0]),
            ],
        ),
        ['a', 'b'],
    )
    v = SchemaValidator(schema)

    def __init__(self, *args, **kwargs):
        v.validate_python(ArgsKwargs(args, kwargs), self_instance=self)

    Foo.__init__ = __init__

    foo = Foo(aAlias=b'hello', bAlias=['True'])
    assert dataclasses.is_dataclass(foo)
    assert dataclasses.asdict(foo) == {'a': 'hello', 'b': True}

    with pytest.raises(ValidationError) as exc_info:
        Foo(aAlias=b'hello', bAlias=['wrong'])

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'bool_parsing',
            'loc': ('bAlias', 0),
            'msg': 'Input should be a valid boolean, unable to interpret input',
            'input': 'wrong',
        }
    ]


def test_dataclass_self_init_alias_field_name():
    @dataclasses.dataclass(init=False)
    class Foo:
        a: str
        b: bool

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema(), validation_alias='aAlias'),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema(), validation_alias=['bAlias', 0]),
            ],
        ),
        ['a', 'b'],
        config={'loc_by_alias': False},
    )
    v = SchemaValidator(schema)

    def __init__(self, *args, **kwargs):
        v.validate_python(ArgsKwargs(args, kwargs), self_instance=self)

    Foo.__init__ = __init__

    foo = Foo(aAlias=b'hello', bAlias=['True'])
    assert dataclasses.asdict(foo) == {'a': 'hello', 'b': True}

    with pytest.raises(ValidationError) as exc_info:
        Foo(aAlias=b'hello', bAlias=['wrong'])

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'bool_parsing',
            'loc': ('b',),
            'msg': 'Input should be a valid boolean, unable to interpret input',
            'input': 'wrong',
        }
    ]


def test_dataclass_self_init_post_init():
    calls = []

    @dataclasses.dataclass(init=False)
    class Foo:
        a: str
        b: bool
        # _: dataclasses.KW_ONLY
        c: dataclasses.InitVar[int]

        def __init__(self, *args, **kwargs):
            v.validate_python(ArgsKwargs(args, kwargs), self_instance=self)

        def __post_init__(self, c):
            calls.append(c)

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema(), kw_only=False),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema(), kw_only=False),
                core_schema.dataclass_field(name='c', schema=core_schema.int_schema(), init_only=True),
            ],
            collect_init_only=True,
        ),
        ['a', 'b', 'c'],
        post_init=True,
    )
    v = SchemaValidator(schema)

    foo = Foo(b'hello', 'True', c='123')
    assert dataclasses.is_dataclass(foo)
    assert dataclasses.asdict(foo) == {'a': 'hello', 'b': True}
    assert calls == [123]


def test_dataclass_validate_assignment():
    schema = core_schema.dataclass_schema(
        FooDataclass,
        core_schema.dataclass_args_schema(
            'FooDataclass',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema(), kw_only=False),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema(), kw_only=False),
            ],
        ),
        ['a', 'b'],
    )
    v = SchemaValidator(schema)

    foo = v.validate_python({'a': 'hello', 'b': 'True'})
    assert dataclasses.asdict(foo) == {'a': 'hello', 'b': True}
    v.validate_assignment(foo, 'a', b'world')
    assert dataclasses.asdict(foo) == {'a': 'world', 'b': True}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(foo, 'a', 123)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'string_type', 'loc': ('a',), 'msg': 'Input should be a valid string', 'input': 123}
    ]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(foo, 'c', '123')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'no_such_attribute',
            'loc': ('c',),
            'msg': "Object has no attribute 'c'",
            'input': '123',
            'ctx': {'attribute': 'c'},
        }
    ]
    assert not hasattr(foo, 'c')

    # wrong arguments
    with pytest.raises(AttributeError, match="'str' object has no attribute 'a'"):
        v.validate_assignment('field_a', 'c', 123)


def test_validate_assignment_function():
    @dataclasses.dataclass
    class MyDataclass:
        field_a: str
        field_b: int
        field_c: int

    calls = []

    def func(x, info):
        calls.append(str(info))
        return x * 2

    v = SchemaValidator(
        core_schema.dataclass_schema(
            MyDataclass,
            core_schema.dataclass_args_schema(
                'MyDataclass',
                [
                    core_schema.dataclass_field('field_a', core_schema.str_schema()),
                    core_schema.dataclass_field(
                        'field_b', core_schema.field_after_validator_function(func, 'field_b', core_schema.int_schema())
                    ),
                    core_schema.dataclass_field('field_c', core_schema.int_schema()),
                ],
            ),
            ['field_a', 'field_b', 'field_c'],
        )
    )

    m = v.validate_python({'field_a': 'x', 'field_b': 123, 'field_c': 456})
    assert m.field_a == 'x'
    assert m.field_b == 246
    assert m.field_c == 456
    assert calls == ["ValidationInfo(config=None, context=None, data={'field_a': 'x'}, field_name='field_b')"]

    v.validate_assignment(m, 'field_b', '111')

    assert m.field_b == 222
    assert calls == [
        "ValidationInfo(config=None, context=None, data={'field_a': 'x'}, field_name='field_b')",
        "ValidationInfo(config=None, context=None, data={'field_a': 'x', 'field_c': 456}, field_name='field_b')",
    ]


def test_frozen():
    @dataclasses.dataclass
    class MyModel:
        f: str

    v = SchemaValidator(
        core_schema.dataclass_schema(
            MyModel,
            core_schema.dataclass_args_schema('MyModel', [core_schema.dataclass_field('f', core_schema.str_schema())]),
            ['f'],
            frozen=True,
        )
    )

    m = v.validate_python({'f': 'x'})
    assert m.f == 'x'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(m, 'f', 'y')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_instance', 'loc': (), 'msg': 'Instance is frozen', 'input': 'y'}
    ]


def test_frozen_field():
    @dataclasses.dataclass
    class MyModel:
        f: str

    v = SchemaValidator(
        core_schema.dataclass_schema(
            MyModel,
            core_schema.dataclass_args_schema(
                'MyModel', [core_schema.dataclass_field('f', core_schema.str_schema(), frozen=True)]
            ),
            ['f'],
        )
    )

    m = v.validate_python({'f': 'x'})
    assert m.f == 'x'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(m, 'f', 'y')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_field', 'loc': ('f',), 'msg': 'Field is frozen', 'input': 'y'}
    ]


@pytest.mark.parametrize(
    'config,schema_extra_behavior_kw',
    [
        (core_schema.CoreConfig(extra_fields_behavior='ignore'), {}),
        (core_schema.CoreConfig(extra_fields_behavior='ignore'), {'extra_behavior': None}),
        (core_schema.CoreConfig(), {'extra_behavior': 'ignore'}),
        (None, {'extra_behavior': 'ignore'}),
        (core_schema.CoreConfig(extra_fields_behavior='allow'), {'extra_behavior': 'ignore'}),
    ],
)
def test_extra_behavior_ignore(config: Union[core_schema.CoreConfig, None], schema_extra_behavior_kw: Dict[str, Any]):
    @dataclasses.dataclass
    class MyModel:
        f: str

    v = SchemaValidator(
        core_schema.dataclass_schema(
            MyModel,
            core_schema.dataclass_args_schema(
                'MyModel', [core_schema.dataclass_field('f', core_schema.str_schema())], **schema_extra_behavior_kw
            ),
            ['f'],
        ),
        config=config,
    )

    m: MyModel = v.validate_python({'f': 'x', 'extra_field': 123})
    assert m.f == 'x'
    assert not hasattr(m, 'extra_field')

    v.validate_assignment(m, 'f', 'y')
    assert m.f == 'y'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(m, 'not_f', 'xyz')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'no_such_attribute',
            'loc': ('not_f',),
            'msg': "Object has no attribute 'not_f'",
            'input': 'xyz',
            'ctx': {'attribute': 'not_f'},
        }
    ]
    assert not hasattr(m, 'not_f')


@pytest.mark.parametrize(
    'config,schema_extra_behavior_kw',
    [
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {}),
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {'extra_behavior': None}),
        (core_schema.CoreConfig(), {'extra_behavior': 'forbid'}),
        (None, {'extra_behavior': 'forbid'}),
        (core_schema.CoreConfig(extra_fields_behavior='ignore'), {'extra_behavior': 'forbid'}),
    ],
)
def test_extra_behavior_forbid(config: Union[core_schema.CoreConfig, None], schema_extra_behavior_kw: Dict[str, Any]):
    @dataclasses.dataclass
    class MyModel:
        f: str

    v = SchemaValidator(
        core_schema.dataclass_schema(
            MyModel,
            core_schema.dataclass_args_schema(
                'MyModel', [core_schema.dataclass_field('f', core_schema.str_schema())], **schema_extra_behavior_kw
            ),
            ['f'],
        ),
        config=config,
    )

    m: MyModel = v.validate_python({'f': 'x'})
    assert m.f == 'x'

    v.validate_assignment(m, 'f', 'y')
    assert m.f == 'y'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(m, 'not_f', 'xyz')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'no_such_attribute',
            'loc': ('not_f',),
            'msg': "Object has no attribute 'not_f'",
            'input': 'xyz',
            'ctx': {'attribute': 'not_f'},
        }
    ]
    assert not hasattr(m, 'not_f')


@pytest.mark.parametrize(
    'config,schema_extra_behavior_kw',
    [
        (core_schema.CoreConfig(extra_fields_behavior='allow'), {}),
        (core_schema.CoreConfig(extra_fields_behavior='allow'), {'extra_behavior': None}),
        (core_schema.CoreConfig(), {'extra_behavior': 'allow'}),
        (None, {'extra_behavior': 'allow'}),
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {'extra_behavior': 'allow'}),
    ],
)
def test_extra_behavior_allow(config: Union[core_schema.CoreConfig, None], schema_extra_behavior_kw: Dict[str, Any]):
    @dataclasses.dataclass
    class MyModel:
        f: str

    v = SchemaValidator(
        core_schema.dataclass_schema(
            MyModel,
            core_schema.dataclass_args_schema(
                'MyModel', [core_schema.dataclass_field('f', core_schema.str_schema())], **schema_extra_behavior_kw
            ),
            ['f'],
            config=config,
        )
    )

    m: MyModel = v.validate_python({'f': 'x', 'extra_field': '123'})
    assert m.f == 'x'
    assert getattr(m, 'extra_field') == '123'

    v.validate_assignment(m, 'f', 'y')
    assert m.f == 'y'

    v.validate_assignment(m, 'not_f', '123')
    assert getattr(m, 'not_f') == '123'


def test_function_validator_wrapping_args_schema_after() -> None:
    calls: List[Any] = []

    def func(*args: Any) -> Any:
        calls.append(args)
        return args[0]

    @dataclasses.dataclass
    class Model:
        number: int = 1

    cs = core_schema.dataclass_schema(
        Model,
        core_schema.no_info_after_validator_function(
            func,
            core_schema.dataclass_args_schema(
                'Model', [core_schema.dataclass_field('number', core_schema.int_schema())]
            ),
        ),
        ['number'],
    )

    v = SchemaValidator(cs)

    instance: Model = v.validate_python({'number': 1})
    assert instance.number == 1
    assert calls == [(({'number': 1}, None),)]
    v.validate_assignment(instance, 'number', 2)
    assert instance.number == 2
    assert calls == [(({'number': 1}, None),), (({'number': 2}, None),)]


def test_function_validator_wrapping_args_schema_before() -> None:
    calls: List[Any] = []

    def func(*args: Any) -> Any:
        calls.append(args)
        return args[0]

    @dataclasses.dataclass
    class Model:
        number: int = 1

    cs = core_schema.dataclass_schema(
        Model,
        core_schema.no_info_before_validator_function(
            func,
            core_schema.dataclass_args_schema(
                'Model', [core_schema.dataclass_field('number', core_schema.int_schema())]
            ),
        ),
        ['number'],
    )

    v = SchemaValidator(cs)

    instance: Model = v.validate_python({'number': 1})
    assert instance.number == 1
    assert calls == [({'number': 1},)]
    v.validate_assignment(instance, 'number', 2)
    assert instance.number == 2
    assert calls == [({'number': 1},), ({'number': 2},)]


def test_function_validator_wrapping_args_schema_wrap() -> None:
    calls: List[Any] = []

    def func(*args: Any) -> Any:
        assert len(args) == 2
        input, handler = args
        output = handler(input)
        calls.append((input, output))
        return output

    @dataclasses.dataclass
    class Model:
        number: int = 1

    cs = core_schema.dataclass_schema(
        Model,
        core_schema.no_info_wrap_validator_function(
            func,
            core_schema.dataclass_args_schema(
                'Model', [core_schema.dataclass_field('number', core_schema.int_schema())]
            ),
        ),
        ['number'],
    )

    v = SchemaValidator(cs)

    instance: Model = v.validate_python({'number': 1})
    assert instance.number == 1
    assert calls == [({'number': 1}, ({'number': 1}, None))]
    v.validate_assignment(instance, 'number', 2)
    assert instance.number == 2
    assert calls == [({'number': 1}, ({'number': 1}, None)), ({'number': 2}, ({'number': 2}, None))]


@dataclasses.dataclass
class FooParentDataclass:
    foo: Optional[FooDataclass]


def test_custom_dataclass_names():
    # Note: normally you would use the same values for DataclassArgsSchema.dataclass_name and DataclassSchema.cls_name,
    # but I have purposely made them different here to show which parts of the errors are affected by which.
    # I have used square brackets in the names to hint that the most likely reason for using a value different from
    # cls.__name__ is for use with generic types.
    schema = core_schema.dataclass_schema(
        FooParentDataclass,
        core_schema.dataclass_args_schema(
            'FooParentDataclass',
            [
                core_schema.dataclass_field(
                    name='foo',
                    schema=core_schema.union_schema(
                        [
                            core_schema.dataclass_schema(
                                FooDataclass,
                                core_schema.dataclass_args_schema(
                                    'FooDataclass[dataclass_args_schema]',
                                    [
                                        core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                                        core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
                                    ],
                                ),
                                ['a', 'b'],
                                cls_name='FooDataclass[cls_name]',
                            ),
                            core_schema.none_schema(),
                        ]
                    ),
                )
            ],
        ),
        ['foo'],
    )

    v = SchemaValidator(schema)
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'foo': 123})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class_name': 'FooDataclass[dataclass_args_schema]'},
            'input': 123,
            'loc': ('foo', 'FooDataclass[cls_name]'),
            'msg': 'Input should be a dictionary or an instance of FooDataclass[dataclass_args_schema]',
            'type': 'dataclass_type',
        },
        {'input': 123, 'loc': ('foo', 'none'), 'msg': 'Input should be None', 'type': 'none_required'},
    ]


@pytest.mark.skipif(sys.version_info < (3, 10), reason='slots are only supported for dataclasses in Python >= 3.10')
def test_slots() -> None:
    @dataclasses.dataclass(slots=True)
    class Model:
        x: int

    schema = core_schema.dataclass_schema(
        Model,
        core_schema.dataclass_args_schema(
            'Model', [core_schema.dataclass_field(name='x', schema=core_schema.int_schema())]
        ),
        ['x'],
        slots=True,
    )

    val = SchemaValidator(schema)
    m: Model

    m = val.validate_python({'x': 123})
    assert m == Model(x=123)

    with pytest.raises(ValidationError):
        val.validate_python({'x': 'abc'})

    val.validate_assignment(m, 'x', 456)
    assert m.x == 456

    with pytest.raises(ValidationError):
        val.validate_assignment(m, 'x', 'abc')


@pytest.mark.skipif(sys.version_info < (3, 10), reason='slots are only supported for dataclasses in Python >= 3.10')
def test_dataclass_slots_field_before_validator():
    @dataclasses.dataclass(slots=True)
    class Foo:
        a: int
        b: str

        @classmethod
        def validate_b(cls, v: bytes, info: core_schema.FieldValidationInfo) -> bytes:
            assert v == b'hello'
            assert info.field_name == 'b'
            assert info.data == {'a': 1}
            return b'hello world!'

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.int_schema()),
                core_schema.dataclass_field(
                    name='b',
                    schema=core_schema.field_before_validator_function(Foo.validate_b, 'b', core_schema.str_schema()),
                ),
            ],
        ),
        ['a', 'b'],
        slots=True,
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': 1, 'b': b'hello'})
    assert dataclasses.asdict(foo) == {'a': 1, 'b': 'hello world!'}


@pytest.mark.skipif(sys.version_info < (3, 10), reason='slots are only supported for dataclasses in Python >= 3.10')
def test_dataclass_slots_field_after_validator():
    @dataclasses.dataclass(slots=True)
    class Foo:
        a: int
        b: str

        @classmethod
        def validate_b(cls, v: str, info: core_schema.FieldValidationInfo) -> str:
            assert v == 'hello'
            assert info.field_name == 'b'
            assert info.data == {'a': 1}
            return 'hello world!'

    schema = core_schema.dataclass_schema(
        Foo,
        core_schema.dataclass_args_schema(
            'Foo',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.int_schema()),
                core_schema.dataclass_field(
                    name='b',
                    schema=core_schema.field_after_validator_function(Foo.validate_b, 'b', core_schema.str_schema()),
                ),
            ],
        ),
        ['a', 'b'],
        slots=True,
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': 1, 'b': b'hello'})
    assert dataclasses.asdict(foo) == {'a': 1, 'b': 'hello world!'}


if sys.version_info < (3, 10):
    kwargs = {}
else:
    kwargs = {'slots': True}


@dataclasses.dataclass(**kwargs)
class FooDataclassSlots:
    a: str
    b: bool


@dataclasses.dataclass(**kwargs)
class FooDataclassSameSlots(FooDataclassSlots):
    pass


@dataclasses.dataclass(**kwargs)
class FooDataclassMoreSlots(FooDataclassSlots):
    c: str


@dataclasses.dataclass(**kwargs)
class DuplicateDifferentSlots:
    a: str
    b: bool


@pytest.mark.parametrize(
    'revalidate_instances,input_value,expected',
    [
        ('always', {'a': 'hello', 'b': True}, {'a': 'hello', 'b': True}),
        ('always', FooDataclassSlots(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('always', FooDataclassSameSlots(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('always', FooDataclassMoreSlots(a='hello', b=True, c='more'), {'a': 'hello', 'b': True}),
        (
            'always',
            DuplicateDifferentSlots(a='hello', b=True),
            Err('should be a dictionary or an instance of FooDataclass'),
        ),
        # revalidate_instances='subclass-instances'
        ('subclass-instances', {'a': 'hello', 'b': True}, {'a': 'hello', 'b': True}),
        ('subclass-instances', FooDataclassSlots(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('subclass-instances', FooDataclassSlots(a=b'hello', b='true'), {'a': b'hello', 'b': 'true'}),
        ('subclass-instances', FooDataclassSameSlots(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('subclass-instances', FooDataclassSameSlots(a=b'hello', b='true'), {'a': 'hello', 'b': True}),
        # no error because we don't look for fields unless their in schema['fields']
        ('subclass-instances', FooDataclassMoreSlots(a='hello', b=True, c='more'), {'a': 'hello', 'b': True}),
        ('subclass-instances', FooDataclassSameSlots(a=b'hello', b='wrong'), Err('Input should be a valid boolean,')),
        (
            'subclass-instances',
            DuplicateDifferentSlots(a='hello', b=True),
            Err('dictionary or an instance of FooDataclass'),
        ),
        # revalidate_instances='never'
        ('never', {'a': 'hello', 'b': True}, {'a': 'hello', 'b': True}),
        ('never', FooDataclassSlots(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('never', FooDataclassSameSlots(a='hello', b=True), {'a': 'hello', 'b': True}),
        ('never', FooDataclassMoreSlots(a='hello', b=True, c='more'), {'a': 'hello', 'b': True, 'c': 'more'}),
        ('never', FooDataclassMoreSlots(a='hello', b='wrong', c='more'), {'a': 'hello', 'b': 'wrong', 'c': 'more'}),
        (
            'never',
            DuplicateDifferentSlots(a='hello', b=True),
            Err('should be a dictionary or an instance of FooDataclass'),
        ),
    ],
)
@pytest.mark.skipif(sys.version_info < (3, 10), reason='slots are only supported for dataclasses in Python >= 3.10')
def test_slots_dataclass_subclass(revalidate_instances, input_value, expected):
    schema = core_schema.dataclass_schema(
        FooDataclassSlots,
        core_schema.dataclass_args_schema(
            'FooDataclass',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
            ],
            extra_behavior='forbid',
        ),
        ['a', 'b'],
        revalidate_instances=revalidate_instances,
        slots=True,
    )
    v = SchemaValidator(schema)

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message) as exc_info:
            print(v.validate_python(input_value))

        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        dc = v.validate_python(input_value)
        assert dataclasses.is_dataclass(dc)
        assert dataclasses.asdict(dc) == expected


@pytest.mark.skipif(sys.version_info < (3, 10), reason='slots are only supported for dataclasses in Python >= 3.10')
def test_slots_mixed():
    @dataclasses.dataclass(slots=True)
    class Model:
        x: int
        y: dataclasses.InitVar[str]
        z: ClassVar[str] = 'z-classvar'

    @dataclasses.dataclass
    class SubModel(Model):
        x2: int
        y2: dataclasses.InitVar[str]
        z2: ClassVar[str] = 'z2-classvar'

    schema = core_schema.dataclass_schema(
        SubModel,
        core_schema.dataclass_args_schema(
            'SubModel',
            [
                core_schema.dataclass_field(name='x', schema=core_schema.int_schema()),
                core_schema.dataclass_field(name='y', init_only=True, schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='x2', schema=core_schema.int_schema()),
                core_schema.dataclass_field(name='y2', init_only=True, schema=core_schema.str_schema()),
            ],
        ),
        ['x'],
        slots=True,
    )
    v = SchemaValidator(schema)
    dc = v.validate_python({'x': 1, 'y': 'a', 'x2': 2, 'y2': 'b'})
    assert dc.x == 1
    assert dc.x2 == 2
    assert dataclasses.asdict(dc) == {'x': 1, 'x2': 2}


def test_dataclass_json():
    schema = core_schema.dataclass_schema(
        FooDataclass,
        core_schema.dataclass_args_schema(
            'FooDataclass',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
            ],
        ),
        ['a', 'b'],
    )
    v = SchemaValidator(schema)
    assert v.validate_json('{"a": "hello", "b": true}') == FooDataclass(a='hello', b=True)

    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('["a", "b"]')

    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class_name': 'FooDataclass'},
            'input': ['a', 'b'],
            'loc': (),
            'msg': 'Input should be an object',
            'type': 'dataclass_type',
        }
    ]
