from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable
from contextlib import AbstractContextManager
from contextlib import nullcontext as does_not_raise
from dataclasses import dataclass
from decimal import Decimal
from inspect import signature
from typing import Annotated, Any, NamedTuple, Optional, Union

import pytest
from dirty_equals import HasRepr, IsPartialDict
from pydantic_core import SchemaError, SchemaSerializer, SchemaValidator
from typing_extensions import TypedDict

from pydantic import (
    BaseConfig,
    BaseModel,
    Field,
    PrivateAttr,
    PydanticDeprecatedSince20,
    PydanticSchemaGenerationError,
    ValidationError,
    create_model,
    dataclasses,
    field_validator,
    validate_call,
    with_config,
)
from pydantic._internal._config import ConfigWrapper, config_defaults
from pydantic._internal._generate_schema import GenerateSchema
from pydantic._internal._mock_val_ser import MockValSer
from pydantic._internal._typing_extra import get_type_hints
from pydantic.config import ConfigDict, JsonValue
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic.dataclasses import rebuild_dataclass
from pydantic.errors import PydanticUserError
from pydantic.fields import ComputedFieldInfo, FieldInfo
from pydantic.type_adapter import TypeAdapter
from pydantic.warnings import PydanticDeprecatedSince210, PydanticDeprecationWarning

from .conftest import CallCounter


@pytest.fixture(scope='session', name='BaseConfigModelWithStrictConfig')
def model_with_strict_config():
    class ModelWithStrictConfig(BaseModel):
        a: int
        # strict=False overrides the Config
        b: Annotated[int, Field(strict=False)]
        # strict=None or not including it is equivalent
        # lets this field be overridden by the Config
        c: Annotated[int, Field(strict=None)]
        d: Annotated[int, Field()]

        model_config = ConfigDict(strict=True)

    return ModelWithStrictConfig


def _equals(a: str | Iterable[str], b: str | Iterable[str]) -> bool:
    """
    Compare strings with spaces removed
    """
    if isinstance(a, str) and isinstance(b, str):
        return a.replace(' ', '') == b.replace(' ', '')
    elif isinstance(a, Iterable) and isinstance(b, Iterable):
        return all(_equals(a_, b_) for a_, b_ in zip(a, b))
    else:
        raise TypeError(f'arguments must be both strings or both lists, not {type(a)}, {type(b)}')


def test_config_dict_missing_keys():
    assert ConfigDict().get('missing_property') is None

    with pytest.raises(KeyError, match="'missing_property'"):
        ConfigDict()['missing_property']


class TestsBaseConfig:
    @pytest.mark.filterwarnings('ignore:.* is deprecated.*:DeprecationWarning')
    def test_base_config_equality_defaults_of_config_dict_class(self):
        for key, value in config_defaults.items():
            assert getattr(BaseConfig, key) == value

    def test_config_and_module_config_cannot_be_used_together(self):
        with pytest.raises(PydanticUserError):

            class MyModel(BaseModel):
                model_config = ConfigDict(title='MyTitle')

                class Config:
                    title = 'MyTitleConfig'

    @pytest.mark.filterwarnings('ignore:.* is deprecated.*:DeprecationWarning')
    def test_base_config_properly_converted_to_dict(self):
        class MyConfig(BaseConfig):
            title = 'MyTitle'
            frozen = True

        class MyBaseModel(BaseModel):
            class Config(MyConfig): ...

        class MyModel(MyBaseModel): ...

        MyModel.model_config['title'] = 'MyTitle'
        MyModel.model_config['frozen'] = True
        assert 'str_to_lower' not in MyModel.model_config

    def test_base_config_custom_init_signature(self):
        class MyModel(BaseModel):
            id: int
            name: str = 'John Doe'
            f__: str = Field(alias='foo')

            model_config = ConfigDict(extra='allow')

            def __init__(self, id: int = 1, bar=2, *, baz: Any, **data):
                super().__init__(id=id, **data)
                self.bar = bar
                self.baz = baz

        sig = signature(MyModel)

        # Get the actual parameters as strings
        param_strings = list(map(str, sig.parameters.values()))

        # Check that all expected parameters exist (ignoring quote formatting)
        assert len(param_strings) == 6
        assert any(p.startswith('id:') and '1' in p for p in param_strings)
        assert 'bar=2' in param_strings
        assert any(p.startswith('baz:') and 'Any' in p for p in param_strings)
        assert any(p.startswith('name:') and 'John Doe' in p for p in param_strings)
        assert any(p.startswith('foo:') and 'str' in p for p in param_strings)
        assert '**data' in param_strings

    def test_base_config_custom_init_signature_with_no_var_kw(self):
        class Model(BaseModel):
            a: float
            b: int = 2
            c: int

            def __init__(self, a: float, b: int):
                super().__init__(a=a, b=b, c=1)

            model_config = ConfigDict(extra='allow')

        sig_str = str(signature(Model))
        assert 'a:' in sig_str and 'float' in sig_str
        assert 'b:' in sig_str and 'int' in sig_str
        assert '-> None' in sig_str

    def test_base_config_use_field_name(self):
        class Foo(BaseModel):
            foo: str = Field(alias='this is invalid')

            model_config = ConfigDict(validate_by_name=True)

        assert _equals(str(signature(Foo)), '(*, foo: str) -> None')

    def test_base_config_does_not_use_reserved_word(self):
        class Foo(BaseModel):
            from_: str = Field(alias='from')

            model_config = ConfigDict(validate_by_name=True)

        assert _equals(str(signature(Foo)), '(*, from_: str) -> None')

    def test_base_config_extra_allow_no_conflict(self):
        class Model(BaseModel):
            spam: str

            model_config = ConfigDict(extra='allow')

        assert _equals(str(signature(Model)), '(*, spam: str, **extra_data: Any) -> None')

    def test_base_config_extra_allow_conflict_twice(self):
        class Model(BaseModel):
            extra_data: str
            extra_data_: str

            model_config = ConfigDict(extra='allow')

        assert _equals(str(signature(Model)), '(*, extra_data: str, extra_data_: str, **extra_data__: Any) -> None')

    def test_base_config_extra_allow_conflict_custom_signature(self):
        class Model(BaseModel):
            extra_data: int

            def __init__(self, extra_data: int = 1, **foobar: Any):
                super().__init__(extra_data=extra_data, **foobar)

            model_config = ConfigDict(extra='allow')

        sig_str = str(signature(Model))
        assert 'extra_data:' in sig_str and 'int' in sig_str and '1' in sig_str
        assert '**foobar:' in sig_str and 'Any' in sig_str
        assert '-> None' in sig_str

    def test_base_config_private_attribute_intersection_with_extra_field(self):
        class Model(BaseModel):
            _foo = PrivateAttr('private_attribute')

            model_config = ConfigDict(extra='allow')

        assert set(Model.__private_attributes__) == {'_foo'}
        m = Model(_foo='field')
        assert m._foo == 'private_attribute'
        assert m.__dict__ == {}
        assert m.__pydantic_extra__ == {'_foo': 'field'}
        assert m.model_dump() == {'_foo': 'field'}
        m._foo = 'still_private'
        assert m._foo == 'still_private'
        assert m.__dict__ == {}
        assert m.__pydantic_extra__ == {'_foo': 'field'}
        assert m.model_dump() == {'_foo': 'field'}

    def test_base_config_parse_model_with_strict_config_disabled(
        self, BaseConfigModelWithStrictConfig: type[BaseModel]
    ) -> None:
        class Model(BaseConfigModelWithStrictConfig):
            model_config = ConfigDict(strict=False)

        values = [
            Model(a='1', b=2, c=3, d=4),
            Model(a=1, b=2, c='3', d=4),
            Model(a=1, b=2, c=3, d='4'),
            Model(a=1, b='2', c=3, d=4),
            Model(a=1, b=2, c=3, d=4),
        ]
        assert all(v.model_dump() == {'a': 1, 'b': 2, 'c': 3, 'd': 4} for v in values)

    def test_finite_float_config(self):
        class Model(BaseModel):
            a: float

            model_config = ConfigDict(allow_inf_nan=False)

        assert Model(a=42).a == 42
        with pytest.raises(ValidationError) as exc_info:
            Model(a=float('nan'))
        # insert_assert(exc_info.value.errors(include_url=False))
        assert exc_info.value.errors(include_url=False) == [
            {
                'type': 'finite_number',
                'loc': ('a',),
                'msg': 'Input should be a finite number',
                'input': HasRepr('nan'),
            }
        ]

    @pytest.mark.parametrize(
        'enabled,str_check,result_str_check',
        [
            (True, '  123  ', '123'),
            (True, '  123\t\n', '123'),
            (False, '  123  ', '  123  '),
        ],
    )
    def test_str_strip_whitespace(self, enabled, str_check, result_str_check):
        class Model(BaseModel):
            str_check: str

            model_config = ConfigDict(str_strip_whitespace=enabled)

        m = Model(str_check=str_check)
        assert m.str_check == result_str_check

    @pytest.mark.parametrize(
        'enabled,str_check,result_str_check',
        [(True, 'ABCDefG', 'ABCDEFG'), (False, 'ABCDefG', 'ABCDefG')],
    )
    def test_str_to_upper(self, enabled, str_check, result_str_check):
        class Model(BaseModel):
            str_check: str

            model_config = ConfigDict(str_to_upper=enabled)

        m = Model(str_check=str_check)

        assert m.str_check == result_str_check

    @pytest.mark.parametrize(
        'enabled,str_check,result_str_check',
        [(True, 'ABCDefG', 'abcdefg'), (False, 'ABCDefG', 'ABCDefG')],
    )
    def test_str_to_lower(self, enabled, str_check, result_str_check):
        class Model(BaseModel):
            str_check: str

            model_config = ConfigDict(str_to_lower=enabled)

        m = Model(str_check=str_check)

        assert m.str_check == result_str_check

    def test_namedtuple_arbitrary_type(self):
        class CustomClass:
            pass

        class Tup(NamedTuple):
            c: CustomClass

        class Model(BaseModel):
            x: Tup

            model_config = ConfigDict(arbitrary_types_allowed=True)

        data = {'x': Tup(c=CustomClass())}
        model = Model.model_validate(data)
        assert isinstance(model.x.c, CustomClass)
        with pytest.raises(PydanticSchemaGenerationError):

            class ModelNoArbitraryTypes(BaseModel):
                x: Tup

    @pytest.mark.parametrize(
        'use_construct, validate_by_name_config, arg_name, expectation',
        [
            [False, True, 'bar', does_not_raise()],
            [False, True, 'bar_', does_not_raise()],
            [False, False, 'bar', does_not_raise()],
            pytest.param(
                False,
                False,
                'bar_',
                pytest.raises(ValueError),
                marks=pytest.mark.thread_unsafe(reason='`pytest.raises()` is thread unsafe'),
            ),
            [True, True, 'bar', does_not_raise()],
            [True, True, 'bar_', does_not_raise()],
            [True, False, 'bar', does_not_raise()],
            [True, False, 'bar_', does_not_raise()],
        ],
    )
    def test_validate_by_name_config(
        self,
        use_construct: bool,
        validate_by_name_config: bool,
        arg_name: str,
        expectation: AbstractContextManager,
    ):
        expected_value: int = 7

        class Foo(BaseModel):
            bar_: int = Field(alias='bar')

            model_config = dict(validate_by_name=validate_by_name_config)

        with expectation:
            if use_construct:
                f = Foo.model_construct(**{arg_name: expected_value})
            else:
                f = Foo(**{arg_name: expected_value})
            assert f.bar_ == expected_value

    def test_immutable_copy_with_frozen(self):
        class Model(BaseModel):
            a: int
            b: int

            model_config = ConfigDict(frozen=True)

        m = Model(a=40, b=10)
        assert m == m.model_copy()

    def test_config_class_is_deprecated(self):
        with pytest.warns(PydanticDeprecatedSince20) as all_warnings:

            class Config(BaseConfig):
                pass

        # typing-extensions swallows one of the warnings, so we need to support
        # both ways for now.
        assert len(all_warnings) in [1, 2]
        expected_warnings = [
            'Support for class-based `config` is deprecated, use ConfigDict instead',
        ]
        if len(all_warnings) == 2:
            expected_warnings.insert(0, 'BaseConfig is deprecated. Use the `pydantic.ConfigDict` instead')
        assert [w.message.message for w in all_warnings] == expected_warnings

    def test_config_class_attributes_are_deprecated(self):
        with pytest.warns(PydanticDeprecatedSince20) as all_warnings:
            assert BaseConfig.validate_assignment is False
            assert BaseConfig().validate_assignment is False

            class Config(BaseConfig):
                pass

            assert Config.validate_assignment is False
            assert Config().validate_assignment is False
        assert len(all_warnings) == 7
        expected_warnings = {
            'Support for class-based `config` is deprecated, use ConfigDict instead',
            'BaseConfig is deprecated. Use the `pydantic.ConfigDict` instead',
        }
        assert set(w.message.message for w in all_warnings) <= expected_warnings

    @pytest.mark.filterwarnings('ignore:.* is deprecated.*:DeprecationWarning')
    def test_config_class_missing_attributes(self):
        with pytest.raises(AttributeError, match="type object 'BaseConfig' has no attribute 'missing_attribute'"):
            BaseConfig.missing_attribute

        with pytest.raises(AttributeError, match="'BaseConfig' object has no attribute 'missing_attribute'"):
            BaseConfig().missing_attribute

        class Config(BaseConfig):
            pass

        with pytest.raises(AttributeError, match="type object 'Config' has no attribute 'missing_attribute'"):
            Config.missing_attribute

        with pytest.raises(AttributeError, match="'Config' object has no attribute 'missing_attribute'"):
            Config().missing_attribute


def test_config_key_deprecation():
    config_dict = {
        'allow_mutation': None,
        'error_msg_templates': None,
        'fields': None,
        'getter_dict': None,
        'schema_extra': None,
        'smart_union': None,
        'underscore_attrs_are_private': None,
        'allow_population_by_field_name': None,
        'anystr_lower': None,
        'anystr_strip_whitespace': None,
        'anystr_upper': None,
        'keep_untouched': None,
        'max_anystr_length': None,
        'min_anystr_length': None,
        'orm_mode': None,
        'validate_all': None,
    }

    warning_message = """
Valid config keys have changed in V2:
* 'allow_population_by_field_name' has been renamed to 'validate_by_name'
* 'anystr_lower' has been renamed to 'str_to_lower'
* 'anystr_strip_whitespace' has been renamed to 'str_strip_whitespace'
* 'anystr_upper' has been renamed to 'str_to_upper'
* 'keep_untouched' has been renamed to 'ignored_types'
* 'max_anystr_length' has been renamed to 'str_max_length'
* 'min_anystr_length' has been renamed to 'str_min_length'
* 'orm_mode' has been renamed to 'from_attributes'
* 'schema_extra' has been renamed to 'json_schema_extra'
* 'validate_all' has been renamed to 'validate_default'
* 'allow_mutation' has been removed
* 'error_msg_templates' has been removed
* 'fields' has been removed
* 'getter_dict' has been removed
* 'smart_union' has been removed
* 'underscore_attrs_are_private' has been removed
    """.strip()

    with pytest.warns(UserWarning, match=re.escape(warning_message)):

        class MyModel(BaseModel):
            model_config = config_dict

    with pytest.warns(UserWarning, match=re.escape(warning_message)):
        create_model('MyCreatedModel', __config__=config_dict)

    with pytest.warns(UserWarning, match=re.escape(warning_message)):

        @pydantic_dataclass(config=config_dict)
        class MyDataclass:
            pass

    with pytest.warns(UserWarning, match=re.escape(warning_message)):

        @validate_call(config=config_dict)
        def my_function():
            pass


def test_invalid_extra():
    ConfigDict(extra='invalid-value')
    extra_error = re.escape('Invalid extra_behavior: `invalid-value`')
    config_dict = {'extra': 'invalid-value'}

    with pytest.raises(SchemaError, match=extra_error):

        class MyModel(BaseModel):
            model_config = config_dict

    with pytest.raises(SchemaError, match=extra_error):
        create_model('MyCreatedModel', __config__=config_dict)

    with pytest.raises(SchemaError, match=extra_error):

        @pydantic_dataclass(config=config_dict)
        class MyDataclass:
            pass


def test_invalid_config_keys():
    @validate_call(config={'alias_generator': lambda x: x})
    def my_function():
        pass


def test_multiple_inheritance_config():
    class Parent(BaseModel):
        model_config = ConfigDict(frozen=True, extra='forbid')

    class Mixin(BaseModel):
        model_config = ConfigDict(use_enum_values=True)

    class Child(Mixin, Parent):
        model_config = ConfigDict(validate_by_name=True)

    assert BaseModel.model_config.get('frozen') is None
    assert BaseModel.model_config.get('validate_by_name') is None
    assert BaseModel.model_config.get('extra') is None
    assert BaseModel.model_config.get('use_enum_values') is None

    assert Parent.model_config.get('frozen') is True
    assert Parent.model_config.get('validate_by_name') is None
    assert Parent.model_config.get('extra') == 'forbid'
    assert Parent.model_config.get('use_enum_values') is None

    assert Mixin.model_config.get('frozen') is None
    assert Mixin.model_config.get('validate_by_name') is None
    assert Mixin.model_config.get('extra') is None
    assert Mixin.model_config.get('use_enum_values') is True

    assert Child.model_config.get('frozen') is True
    assert Child.model_config.get('validate_by_name') is True
    assert Child.model_config.get('extra') == 'forbid'
    assert Child.model_config.get('use_enum_values') is True


@pytest.mark.thread_unsafe(reason='Flaky')
def test_config_wrapper_match():
    localns = {
        '_GenerateSchema': GenerateSchema,
        'GenerateSchema': GenerateSchema,
        'JsonValue': JsonValue,
        'FieldInfo': FieldInfo,
        'ComputedFieldInfo': ComputedFieldInfo,
    }
    config_dict_annotations = [(k, str(v)) for k, v in get_type_hints(ConfigDict, localns=localns).items()]
    config_dict_annotations.sort()
    # remove config
    config_wrapper_annotations = [
        (k, str(v)) for k, v in get_type_hints(ConfigWrapper, localns=localns).items() if k != 'config_dict'
    ]
    config_wrapper_annotations.sort()

    assert config_dict_annotations == config_wrapper_annotations, (
        'ConfigDict and ConfigWrapper must have the same annotations (except ConfigWrapper.config_dict)'
    )


@pytest.mark.skipif(sys.version_info < (3, 11), reason='requires backport pre 3.11, fully tested in pydantic core')
def test_config_validation_error_cause():
    class Foo(BaseModel):
        foo: int

        @field_validator('foo')
        def check_foo(cls, v):
            assert v > 5, 'Must be greater than 5'

    # Should be disabled by default:
    with pytest.raises(ValidationError) as exc_info:
        Foo(foo=4)
    assert exc_info.value.__cause__ is None

    Foo.model_config = ConfigDict(validation_error_cause=True)
    Foo.model_rebuild(force=True)
    with pytest.raises(ValidationError) as exc_info:
        Foo(foo=4)
    # Confirm python error attached as a cause, and error location specified in a note:
    assert exc_info.value.__cause__ is not None
    assert isinstance(exc_info.value.__cause__, ExceptionGroup)  # noqa: F821
    assert len(exc_info.value.__cause__.exceptions) == 1
    src_exc = exc_info.value.__cause__.exceptions[0]
    assert repr(src_exc) == "AssertionError('Must be greater than 5\\nassert 4 > 5')"
    assert len(src_exc.__notes__) == 1
    assert src_exc.__notes__[0] == '\nPydantic: cause of loc: foo'


def test_config_defaults_match():
    localns = {
        '_GenerateSchema': GenerateSchema,
        'GenerateSchema': GenerateSchema,
        'FieldInfo': FieldInfo,
        'ComputedFieldInfo': ComputedFieldInfo,
    }
    config_dict_keys = sorted(list(get_type_hints(ConfigDict, localns=localns).keys()))
    config_defaults_keys = sorted(list(config_defaults.keys()))

    assert config_dict_keys == config_defaults_keys, 'ConfigDict and config_defaults must have the same keys'


def test_config_is_not_inherited_in_model_fields():
    from pydantic import BaseModel, ConfigDict

    class Inner(BaseModel):
        a: str

    class Outer(BaseModel):
        # this cause the inner model incorrectly dumpped:
        model_config = ConfigDict(str_to_lower=True)

        x: list[str]  # should be converted to lower
        inner: Inner  # should not have fields converted to lower

    m = Outer.model_validate(dict(x=['Abc'], inner=dict(a='Def')))

    assert m.model_dump() == {'x': ['abc'], 'inner': {'a': 'Def'}}


@pytest.mark.parametrize(
    'config,input_str',
    (
        ({}, 'type=string_type, input_value=123, input_type=int'),
        ({'hide_input_in_errors': False}, 'type=string_type, input_value=123, input_type=int'),
        ({'hide_input_in_errors': True}, 'type=string_type'),
    ),
)
def test_hide_input_in_errors(config, input_str):
    class Model(BaseModel):
        x: str

        model_config = ConfigDict(**config)

    with pytest.raises(ValidationError, match=re.escape(f'Input should be a valid string [{input_str}]')):
        Model(x=123)


parametrize_inf_nan_capable_type = pytest.mark.parametrize('inf_nan_capable_type', [float, Decimal])
parametrize_inf_nan_capable_value = pytest.mark.parametrize('inf_nan_value', ['Inf', 'NaN'])


@parametrize_inf_nan_capable_value
@parametrize_inf_nan_capable_type
def test_config_inf_nan_enabled(inf_nan_capable_type, inf_nan_value):
    class Model(BaseModel):
        model_config = ConfigDict(allow_inf_nan=True)
        value: inf_nan_capable_type

    assert Model(value=inf_nan_capable_type(inf_nan_value))


@parametrize_inf_nan_capable_value
@parametrize_inf_nan_capable_type
def test_config_inf_nan_disabled(inf_nan_capable_type, inf_nan_value):
    class Model(BaseModel):
        model_config = ConfigDict(allow_inf_nan=False)
        value: inf_nan_capable_type

    with pytest.raises(ValidationError) as e:
        Model(value=inf_nan_capable_type(inf_nan_value))

    assert e.value.errors(include_url=False)[0] == IsPartialDict(
        {
            'loc': ('value',),
            'msg': 'Input should be a finite number',
            'type': 'finite_number',
        }
    )


@pytest.mark.parametrize(
    'config,expected',
    (
        (ConfigDict(), 'ConfigWrapper()'),
        (ConfigDict(title='test'), "ConfigWrapper(title='test')"),
    ),
)
def test_config_wrapper_repr(config, expected):
    assert repr(ConfigWrapper(config=config)) == expected


def test_config_wrapper_get_item():
    config_wrapper = ConfigWrapper(config=ConfigDict(title='test'))

    assert config_wrapper.title == 'test'
    with pytest.raises(AttributeError, match="Config has no attribute 'test'"):
        config_wrapper.test


def test_config_inheritance_with_annotations():
    class Parent(BaseModel):
        model_config: ConfigDict = {'extra': 'allow'}

    class Child(Parent):
        model_config: ConfigDict = {'str_to_lower': True}

    assert Child.model_config == {'extra': 'allow', 'str_to_lower': True}


def test_json_encoders_model() -> None:
    with pytest.warns(PydanticDeprecationWarning):

        class Model(BaseModel):
            model_config = ConfigDict(json_encoders={Decimal: lambda x: str(x * 2), int: lambda x: str(x * 3)})
            value: Decimal
            x: int

    assert json.loads(Model(value=Decimal('1.1'), x=1).model_dump_json()) == {'value': '2.2', 'x': '3'}


@pytest.mark.filterwarnings('ignore::pydantic.warnings.PydanticDeprecationWarning')
def test_json_encoders_type_adapter() -> None:
    config = ConfigDict(json_encoders={Decimal: lambda x: str(x * 2), int: lambda x: str(x * 3)})

    ta = TypeAdapter(int, config=config)
    assert json.loads(ta.dump_json(1)) == '3'

    ta = TypeAdapter(Decimal, config=config)
    assert json.loads(ta.dump_json(Decimal('1.1'))) == '2.2'

    ta = TypeAdapter(Union[Decimal, int], config=config)
    assert json.loads(ta.dump_json(Decimal('1.1'))) == '2.2'
    assert json.loads(ta.dump_json(1)) == '2'


@pytest.mark.parametrize('defer_build', [True, False])
def test_config_model_defer_build(defer_build: bool, generate_schema_calls: CallCounter):
    config = ConfigDict(defer_build=defer_build)

    class MyModel(BaseModel):
        model_config = config
        x: int

    if defer_build:
        assert isinstance(MyModel.__pydantic_validator__, MockValSer)
        assert isinstance(MyModel.__pydantic_serializer__, MockValSer)
        assert generate_schema_calls.count == 0, 'Should respect defer_build'
    else:
        assert isinstance(MyModel.__pydantic_validator__, SchemaValidator)
        assert isinstance(MyModel.__pydantic_serializer__, SchemaSerializer)
        assert generate_schema_calls.count == 1, 'Should respect defer_build'

    m = MyModel(x=1)
    assert m.x == 1
    assert m.model_dump()['x'] == 1
    assert m.model_validate({'x': 2}).x == 2
    assert m.model_json_schema()['type'] == 'object'

    assert isinstance(MyModel.__pydantic_validator__, SchemaValidator)
    assert isinstance(MyModel.__pydantic_serializer__, SchemaSerializer)
    assert generate_schema_calls.count == 1, 'Should not build duplicated core schemas'


@pytest.mark.parametrize('defer_build', [True, False])
def test_config_dataclass_defer_build(defer_build: bool, generate_schema_calls: CallCounter) -> None:
    config = ConfigDict(defer_build=defer_build)

    @pydantic_dataclass(config=config)
    class MyDataclass:
        x: int

    if defer_build:
        assert isinstance(MyDataclass.__pydantic_validator__, MockValSer)
        assert isinstance(MyDataclass.__pydantic_serializer__, MockValSer)
        assert generate_schema_calls.count == 0, 'Should respect defer_build'
    else:
        assert isinstance(MyDataclass.__pydantic_validator__, SchemaValidator)
        assert isinstance(MyDataclass.__pydantic_serializer__, SchemaSerializer)
        assert generate_schema_calls.count == 1, 'Should respect defer_build'

    m = MyDataclass(x=1)
    assert m.x == 1

    assert isinstance(MyDataclass.__pydantic_validator__, SchemaValidator)
    assert isinstance(MyDataclass.__pydantic_serializer__, SchemaSerializer)
    assert generate_schema_calls.count == 1, 'Should not build duplicated core schemas'


def test_dataclass_defer_build_override_on_rebuild_dataclass(generate_schema_calls: CallCounter) -> None:
    config = ConfigDict(defer_build=True)

    @pydantic_dataclass(config=config)
    class MyDataclass:
        x: int

    assert isinstance(MyDataclass.__pydantic_validator__, MockValSer)
    assert isinstance(MyDataclass.__pydantic_serializer__, MockValSer)
    assert generate_schema_calls.count == 0, 'Should respect defer_build'

    rebuild_dataclass(MyDataclass, force=True)
    assert isinstance(MyDataclass.__pydantic_validator__, SchemaValidator)
    assert isinstance(MyDataclass.__pydantic_serializer__, SchemaSerializer)
    assert generate_schema_calls.count == 1, 'Should have called generate_schema once'


@pytest.mark.parametrize('defer_build', [True, False])
def test_config_model_type_adapter_defer_build(defer_build: bool, generate_schema_calls: CallCounter):
    config = ConfigDict(defer_build=defer_build)

    class MyModel(BaseModel):
        model_config = config
        x: int

    assert generate_schema_calls.count == (0 if defer_build is True else 1)
    generate_schema_calls.reset()

    ta = TypeAdapter(MyModel)

    assert generate_schema_calls.count == 0, 'Should use model generated schema'

    assert ta.validate_python({'x': 1}).x == 1
    assert ta.validate_python({'x': 2}).x == 2
    assert ta.dump_python(MyModel.model_construct(x=1))['x'] == 1
    assert ta.json_schema()['type'] == 'object'

    assert generate_schema_calls.count == (1 if defer_build is True else 0), 'Should not build duplicate core schemas'


@pytest.mark.parametrize('defer_build', [True, False])
def test_config_plain_type_adapter_defer_build(defer_build: bool, generate_schema_calls: CallCounter):
    config = ConfigDict(defer_build=defer_build)

    ta = TypeAdapter(dict[str, int], config=config)

    assert generate_schema_calls.count == (0 if defer_build else 1)
    generate_schema_calls.reset()

    assert ta.validate_python({}) == {}
    assert ta.validate_python({'x': 1}) == {'x': 1}
    assert ta.dump_python({'x': 2}) == {'x': 2}
    assert ta.json_schema()['type'] == 'object'

    assert generate_schema_calls.count == (1 if defer_build else 0), 'Should not build duplicate core schemas'


@pytest.mark.parametrize('defer_build', [True, False])
def test_config_model_defer_build_nested(defer_build: bool, generate_schema_calls: CallCounter):
    config = ConfigDict(defer_build=defer_build)

    assert generate_schema_calls.count == 0

    class MyNestedModel(BaseModel):
        model_config = config
        x: int

    class MyModel(BaseModel):
        y: MyNestedModel

    assert isinstance(MyModel.__pydantic_validator__, SchemaValidator)
    assert isinstance(MyModel.__pydantic_serializer__, SchemaSerializer)

    expected_schema_count = 1 if defer_build is True else 2
    assert generate_schema_calls.count == expected_schema_count, 'Should respect defer_build'

    if defer_build:
        assert isinstance(MyNestedModel.__pydantic_validator__, MockValSer)
        assert isinstance(MyNestedModel.__pydantic_serializer__, MockValSer)
    else:
        assert isinstance(MyNestedModel.__pydantic_validator__, SchemaValidator)
        assert isinstance(MyNestedModel.__pydantic_serializer__, SchemaSerializer)

    m = MyModel(y={'x': 1})
    assert m.y.x == 1
    assert m.model_dump() == {'y': {'x': 1}}
    assert m.model_validate({'y': {'x': 1}}).y.x == 1
    assert m.model_json_schema()['type'] == 'object'

    if defer_build:
        assert isinstance(MyNestedModel.__pydantic_validator__, MockValSer)
        assert isinstance(MyNestedModel.__pydantic_serializer__, MockValSer)
    else:
        assert isinstance(MyNestedModel.__pydantic_validator__, SchemaValidator)
        assert isinstance(MyNestedModel.__pydantic_serializer__, SchemaSerializer)

    assert generate_schema_calls.count == expected_schema_count, 'Should not build duplicated core schemas'


def test_config_model_defer_build_ser_first():
    class M1(BaseModel, defer_build=True):
        a: str

    class M2(BaseModel, defer_build=True):
        b: M1

    m = M2.model_validate({'b': {'a': 'foo'}})
    assert m.b.model_dump() == {'a': 'foo'}


def test_defer_build_json_schema():
    class M(BaseModel, defer_build=True):
        a: int

    assert M.model_json_schema() == {
        'title': 'M',
        'type': 'object',
        'properties': {'a': {'title': 'A', 'type': 'integer'}},
        'required': ['a'],
    }


def test_partial_creation_with_defer_build():
    class M(BaseModel):
        a: int
        b: int

    def create_partial(model, optionals):
        override_fields = {}
        model.model_rebuild()
        for name, field in model.model_fields.items():
            if field.is_required() and name in optionals:
                assert field.annotation is not None
                override_fields[name] = (Optional[field.annotation], FieldInfo.merge_field_infos(field, default=None))

        return create_model(f'Partial{model.__name__}', __base__=model, **override_fields)

    partial = create_partial(M, {'a'})

    # Comment this away and the last assertion works
    assert M.model_json_schema()['required'] == ['a', 'b']

    # AssertionError: assert ['a', 'b'] == ['b']
    assert partial.model_json_schema()['required'] == ['b']


def test_model_config_as_model_field_raises():
    with pytest.raises(PydanticUserError) as exc_info:

        class MyModel(BaseModel):
            model_config: str

    assert exc_info.value.code == 'model-config-invalid-field-name'


def test_dataclass_allows_model_config_as_model_field():
    config_title = 'from_config'
    field_title = 'from_field'

    @pydantic_dataclass(config={'title': config_title})
    class MyDataclass:
        model_config: dict

    m = MyDataclass(model_config={'title': field_title})

    assert m.model_config['title'] == field_title
    assert m.__pydantic_config__['title'] == config_title


def test_with_config_disallowed_with_model():
    msg = 'Cannot use `with_config` on Model as it is a Pydantic model'

    with pytest.raises(PydanticUserError, match=msg):

        @with_config({'coerce_numbers_to_str': True})
        class Model(BaseModel):
            pass


def test_with_config_direct_kwargs():
    """Test that with_config accepts kwargs directly."""

    # Test with TypedDict
    @with_config(str_to_lower=True)
    class UserDict(TypedDict):
        name: str
        email: str

    ta = TypeAdapter(UserDict)
    assert ta.validate_python({'name': 'JOHN', 'email': 'JOHN@EXAMPLE.COM'}) == {
        'name': 'john',
        'email': 'john@example.com',
    }

    # Test with dataclass
    @dataclass
    @with_config(str_to_lower=True)
    class UserClass:
        name: str
        email: str

    ta2 = TypeAdapter(UserClass)
    user = ta2.validate_python({'name': 'JANE', 'email': 'JANE@EXAMPLE.COM'})
    assert user.name == 'jane'
    assert user.email == 'jane@example.com'


def test_with_config_error_both_config_and_kwargs():
    """Test that with_config raises an error when both config and kwargs are provided."""
    with pytest.raises(ValueError, match='Cannot specify both config and keyword arguments'):

        @with_config(ConfigDict(str_to_lower=True), str_to_upper=True)
        class Model(TypedDict):
            x: str


def test_with_config_equivalent_behavior():
    """Test that both ways of using with_config produce the same result."""

    # Original way with dict
    @with_config({'str_to_lower': True})
    class ModelDict(TypedDict):
        x: str

    # Original way with ConfigDict
    @with_config(ConfigDict(str_to_lower=True))
    class ModelConfigDict(TypedDict):
        x: str

    # New way with kwargs
    @with_config(str_to_lower=True)
    class ModelKwargs(TypedDict):
        x: str

    ta1 = TypeAdapter(ModelDict)
    ta2 = TypeAdapter(ModelConfigDict)
    ta3 = TypeAdapter(ModelKwargs)

    input_data = {'x': 'ABC'}
    expected = {'x': 'abc'}

    assert ta1.validate_python(input_data) == expected
    assert ta2.validate_python(input_data) == expected
    assert ta3.validate_python(input_data) == expected


def test_with_config_multiple_kwargs():
    """Test that with_config accepts multiple kwargs."""

    @with_config(str_to_lower=True, extra='allow', validate_default=True)
    class User(TypedDict):
        name: str
        email: str

    ta = TypeAdapter(User)
    result = ta.validate_python({'name': 'JOHN', 'email': 'JOHN@EXAMPLE.COM', 'extra_field': 'value'})
    assert result == {
        'name': 'john',
        'email': 'john@example.com',
        'extra_field': 'value',
    }


def test_with_config_nested_config():
    """Test with_config with nested configuration options."""

    @with_config(json_schema_extra={'examples': [{'name': 'example'}]})
    class User(TypedDict):
        name: str

    schema = TypeAdapter(User).json_schema()
    assert schema.get('examples') == [{'name': 'example'}]


def test_with_config_empty_kwargs():
    """Test with_config with empty kwargs."""

    @with_config()
    class User(TypedDict):
        name: str

    ta = TypeAdapter(User)
    result = ta.validate_python({'name': 'John'})
    assert result == {'name': 'John'}


def test_with_config_combination_with_standard_dataclass_features():
    """Test that with_config works in combination with standard dataclass features."""

    # The order matters: dataclass decorator should be applied first, then with_config
    @dataclasses.dataclass(frozen=True)
    @with_config(str_to_lower=True)
    class User:
        name: str
        email: str

    ta = TypeAdapter(User)
    user = ta.validate_python({'name': 'JOHN', 'email': 'JOHN@EXAMPLE.COM'})
    # Now the str_to_lower config is correctly applied
    assert user.name == 'john'
    assert user.email == 'john@example.com'

    # Test that it's frozen
    with pytest.raises(Exception):
        user.name = 'new'


def test_empty_config_with_annotations():
    class Model(BaseModel):
        model_config: ConfigDict = {}

    assert Model.model_config == {}


def test_generate_schema_deprecation_warning() -> None:
    with pytest.warns(
        PydanticDeprecatedSince210, match='The `schema_generator` setting has been deprecated since v2.10.'
    ):

        class Model(BaseModel):
            model_config = ConfigDict(schema_generator=GenerateSchema)


def test_populate_by_name_still_effective() -> None:
    class Model(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        a: int = Field(alias='A')

    assert Model.model_validate({'A': 1}).a == 1
    assert Model.model_validate({'a': 1}).a == 1


def test_user_error_on_alias_settings() -> None:
    with pytest.raises(
        PydanticUserError, match='At least one of `validate_by_alias` or `validate_by_name` must be set to True.'
    ):

        class Model(BaseModel):
            model_config = ConfigDict(validate_by_alias=False, validate_by_name=False)


def test_dynamic_default() -> None:
    class Model(BaseModel):
        model_config = ConfigDict(validate_by_alias=False)

    assert Model.model_config == {'validate_by_alias': False, 'validate_by_name': True}


def test_with_config_different_decorator_orders():
    """Test that with_config works with different decorator orders for dataclasses."""

    # Correct order: dataclass first, then with_config
    @dataclasses.dataclass
    @with_config(str_to_lower=True)
    class UserCorrect:
        name: str

    # Incorrect order: with_config first, then dataclass
    @with_config(str_to_lower=True)
    @dataclasses.dataclass
    class UserIncorrect:
        name: str

    ta1 = TypeAdapter(UserCorrect)
    ta2 = TypeAdapter(UserIncorrect)

    # Correct order - config is applied and name is lowercase
    user1 = ta1.validate_python({'name': 'JOHN'})
    assert user1.name == 'john'

    # Incorrect order - config is not applied properly, name remains uppercase
    user2 = ta2.validate_python({'name': 'JOHN'})
    assert user2.name == 'JOHN'


def test_with_config_none_values():
    """Test with_config with None values."""

    @with_config(arbitrary_types_allowed=True, strict=None)
    class Model(TypedDict):
        x: str

    # None values for config options that accept None should be respected
    # but the class itself will still have a default title in its schema
    schema = TypeAdapter(Model).json_schema()
    assert schema['title'] == 'Model'  # Default title based on class name

    # Check that our config was applied correctly even with None values
    @with_config(arbitrary_types_allowed=True, strict=None)
    class CustomModel:
        x: str

    config = getattr(CustomModel, '__pydantic_config__', {})
    assert config.get('arbitrary_types_allowed') is True
    assert 'strict' in config and config['strict'] is None


def test_with_config_validation_error_format():
    """Test that validation still works with custom config."""

    @with_config(str_to_lower=True)
    class User(TypedDict):
        name: str

    ta = TypeAdapter(User)

    # Test that validation still works with our config
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'name': 123})

    # The error message should indicate a validation failure
    assert 'Input should be a valid string' in str(exc_info.value)

    # And our str_to_lower config should still be applied
    assert ta.validate_python({'name': 'JOHN'}) == {'name': 'john'}


def test_with_config_overriding_behaviour():
    """Test that with_config properly overrides existing config."""

    # Create a base class with a config
    @with_config(str_to_lower=True)
    class BaseDict(TypedDict):
        name: str

    # Create a derived class that inherits the config
    class DerivedDict(BaseDict):
        email: str

    # Create another class that overrides the config
    @with_config(str_to_upper=True)
    class OverrideDict(BaseDict):
        email: str

    # Test inheritance behavior
    ta_base = TypeAdapter(BaseDict)
    ta_derived = TypeAdapter(DerivedDict)
    ta_override = TypeAdapter(OverrideDict)

    # Base behavior: lowercase
    assert ta_base.validate_python({'name': 'JOHN'}) == {'name': 'john'}

    # Derived should inherit the behavior: lowercase
    assert ta_derived.validate_python({'name': 'JOHN', 'email': 'JOHN@EXAMPLE.COM'}) == {
        'name': 'john',
        'email': 'john@example.com',
    }

    # Override should have its own behavior: uppercase
    assert ta_override.validate_python({'name': 'john', 'email': 'john@example.com'}) == {
        'name': 'JOHN',
        'email': 'JOHN@EXAMPLE.COM',
    }


def test_with_config_edge_case_empty_dict():
    """Test with_config with empty dict."""

    @with_config({})
    class Model(TypedDict):
        x: str

    ta = TypeAdapter(Model)
    assert ta.validate_python({'x': 'test'}) == {'x': 'test'}

    # Empty ConfigDict should be equivalent
    @with_config(ConfigDict())
    class Model2(TypedDict):
        x: str

    ta2 = TypeAdapter(Model2)
    assert ta2.validate_python({'x': 'test'}) == {'x': 'test'}
