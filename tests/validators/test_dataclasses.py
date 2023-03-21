import dataclasses
import re

import pytest
from dirty_equals import IsListOrTuple

from pydantic_core import ArgsKwargs, SchemaValidator, ValidationError, core_schema

from ..conftest import Err, PyAndJson


def test_args_kwargs():
    ak = ArgsKwargs(('hello', True))
    assert repr(ak) == "ArgsKwargs(args=('hello', True), kwargs={})"
    assert ak.args == ('hello', True)
    assert ak.kwargs is None
    ak2 = ArgsKwargs((), {'a': 123})
    assert repr(ak2) == "ArgsKwargs(args=(), kwargs={'a': 123})"
    assert ak2.args == ()
    assert ak2.kwargs == {'a': 123}


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
                'Missing required keyword argument',
                errors=[
                    {
                        'type': 'missing_keyword_argument',
                        'loc': ('b',),
                        'msg': 'Missing required keyword argument',
                        'input': {'a': 'hello'},
                    }
                ],
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

        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
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
                'Missing required keyword argument',
                errors=[
                    {
                        'type': 'missing_keyword_argument',
                        'loc': ('b',),
                        'msg': 'Missing required keyword argument',
                        'input': {'a': 'hello'},
                    }
                ],
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

        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
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
                'Input should be a dictionary or an instance of MyDataclass',
                errors=[
                    {
                        'type': 'dataclass_type',
                        'loc': (),
                        'msg': 'Input should be a dictionary or an instance of MyDataclass',
                        'input': IsListOrTuple('hello'),
                        'ctx': {'dataclass_name': 'MyDataclass'},
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
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)

        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
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
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': 'hello', 'b': True})
    assert dataclasses.is_dataclass(foo)
    assert foo.a == 'hello'
    assert foo.b is True

    assert dataclasses.asdict(v.validate_python(FooDataclass(a='hello', b=True))) == {'a': 'hello', 'b': True}

    with pytest.raises(ValidationError, match='Input should be an instance of FooDataclass') as exc_info:
        v.validate_python({'a': 'hello', 'b': True}, strict=True)

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'model_class_type',
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
    'input_value,expected',
    [
        ({'a': 'hello', 'b': True}, {'a': 'hello', 'b': True}),
        (FooDataclass(a='hello', b=True), {'a': 'hello', 'b': True}),
        (FooDataclassSame(a='hello', b=True), {'a': 'hello', 'b': True}),
        (FooDataclassMore(a='hello', b=True, c='more'), Err(r'c\s+Unexpected keyword argument')),
        (DuplicateDifferent(a='hello', b=True), Err('Input should be a dictionary or an instance of FooDataclass')),
    ],
)
def test_dataclass_subclass(input_value, expected):
    schema = core_schema.dataclass_schema(
        FooDataclass,
        core_schema.dataclass_args_schema(
            'FooDataclass',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
            ],
        ),
    )
    v = SchemaValidator(schema)

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message) as exc_info:
            v.validate_python(input_value)

        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        dc = v.validate_python(input_value)
        assert dataclasses.is_dataclass(dc)
        assert dataclasses.asdict(dc) == expected


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
        post_init=True,
    )

    v = SchemaValidator(schema)
    foo = v.validate_python({'a': b'hello', 'b': 'true', 'c': '42'})
    assert dataclasses.asdict(foo) == {'a': 'hello'}
    assert dc_args == (True, 42)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'a': b'hello', 'b': 'true'}, {'a': 'hello', 'b': True}),
        (FooDataclass(a='hello', b=True), {'a': 'hello', 'b': True}),
        (FooDataclass(a=b'hello', b='true'), {'a': 'hello', 'b': True}),
    ],
)
def test_dataclass_exact_validation(input_value, expected):

    schema = core_schema.dataclass_schema(
        FooDataclass,
        core_schema.dataclass_args_schema(
            'FooDataclass',
            [
                core_schema.dataclass_field(name='a', schema=core_schema.str_schema()),
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema()),
            ],
        ),
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
                    schema=core_schema.field_after_validator_function(Foo.validate_b, core_schema.str_schema()),
                ),
            ],
        ),
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
                    name='b', schema=core_schema.field_plain_validator_function(Foo.validate_b)
                ),
            ],
        ),
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
                    schema=core_schema.field_before_validator_function(Foo.validate_b, core_schema.str_schema()),
                ),
            ],
        ),
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
                    name='b', schema=core_schema.field_wrap_validator_function(Foo.validate_b, core_schema.str_schema())
                ),
            ],
        ),
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
                    name='b', schema=core_schema.field_wrap_validator_function(Foo.validate_b, core_schema.str_schema())
                ),
            ],
        ),
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
                core_schema.dataclass_field(name='b', schema=core_schema.bool_schema(), validation_alias='bAlias'),
            ],
        ),
    )
    v = SchemaValidator(schema)

    def __init__(self, *args, **kwargs):
        v.validate_python(ArgsKwargs(args, kwargs), self_instance=self)

    Foo.__init__ = __init__

    foo = Foo(aAlias=b'hello', bAlias='True')
    assert dataclasses.is_dataclass(foo)
    assert dataclasses.asdict(foo) == {'a': 'hello', 'b': True}


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
    )
    v = SchemaValidator(schema)

    foo = v.validate_python({'a': 'hello', 'b': 'True'})
    assert dataclasses.asdict(foo) == {'a': 'hello', 'b': True}
    v.validate_assignment(foo, 'a', b'world')
    assert dataclasses.asdict(foo) == {'a': 'world', 'b': True}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(foo, 'a', 123)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'string_type', 'loc': ('a',), 'msg': 'Input should be a valid string', 'input': 123}
    ]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(foo, 'c', 123)
    assert exc_info.value.errors() == [
        {
            'type': 'no_such_attribute',
            'loc': ('c',),
            'msg': "Object has no attribute 'c'",
            'input': 123,
            'ctx': {'attribute': 'c'},
        }
    ]

    # wrong arguments
    with pytest.raises(TypeError, match='self_instance should not be None on dataclass validate_assignment'):
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
                        'field_b', core_schema.field_after_validator_function(func, core_schema.int_schema())
                    ),
                    core_schema.dataclass_field('field_c', core_schema.int_schema()),
                ],
            ),
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
