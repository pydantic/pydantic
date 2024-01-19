import json
import re
import sys
from contextlib import nullcontext as does_not_raise
from decimal import Decimal
from inspect import signature
from typing import Any, ContextManager, Iterable, NamedTuple, Optional, Type, Union

from dirty_equals import HasRepr, IsPartialDict
from pydantic_core import SchemaError, SchemaSerializer, SchemaValidator

from pydantic import (
    BaseConfig,
    BaseModel,
    Field,
    GenerateSchema,
    PrivateAttr,
    PydanticDeprecatedSince20,
    PydanticSchemaGenerationError,
    ValidationError,
    create_model,
    field_validator,
    validate_call,
)
from pydantic._internal._config import ConfigWrapper, config_defaults
from pydantic._internal._mock_val_ser import MockValSer
from pydantic._internal._typing_extra import get_type_hints
from pydantic.config import ConfigDict, JsonValue
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic.errors import PydanticUserError
from pydantic.fields import FieldInfo
from pydantic.type_adapter import TypeAdapter
from pydantic.warnings import PydanticDeprecationWarning

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

import pytest


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


def _equals(a: Union[str, Iterable[str]], b: Union[str, Iterable[str]]) -> bool:
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
            class Config(MyConfig):
                ...

        class MyModel(MyBaseModel):
            ...

        MyModel.model_config['title'] = 'MyTitle'
        MyModel.model_config['frozen'] = True
        assert 'str_to_lower' not in MyModel.model_config

    def test_base_config_custom_init_signature(self):
        class MyModel(BaseModel):
            id: int
            name: str = 'John Doe'
            f__: str = Field(..., alias='foo')

            model_config = ConfigDict(extra='allow')

            def __init__(self, id: int = 1, bar=2, *, baz: Any, **data):
                super().__init__(id=id, **data)
                self.bar = bar
                self.baz = baz

        sig = signature(MyModel)
        assert _equals(
            map(str, sig.parameters.values()),
            ('id: int = 1', 'bar=2', 'baz: Any', "name: str = 'John Doe'", 'foo: str', '**data'),
        )
        assert _equals(str(sig), "(id: int = 1, bar=2, *, baz: Any, name: str = 'John Doe', foo: str, **data) -> None")

    def test_base_config_custom_init_signature_with_no_var_kw(self):
        class Model(BaseModel):
            a: float
            b: int = 2
            c: int

            def __init__(self, a: float, b: int):
                super().__init__(a=a, b=b, c=1)

            model_config = ConfigDict(extra='allow')

        assert _equals(str(signature(Model)), '(a: float, b: int) -> None')

    def test_base_config_use_field_name(self):
        class Foo(BaseModel):
            foo: str = Field(..., alias='this is invalid')

            model_config = ConfigDict(populate_by_name=True)

        assert _equals(str(signature(Foo)), '(*, foo: str) -> None')

    def test_base_config_does_not_use_reserved_word(self):
        class Foo(BaseModel):
            from_: str = Field(..., alias='from')

            model_config = ConfigDict(populate_by_name=True)

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

        assert _equals(str(signature(Model)), '(extra_data: int = 1, **foobar: Any) -> None')

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
        self, BaseConfigModelWithStrictConfig: Type[BaseModel]
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
        'use_construct, populate_by_name_config, arg_name, expectation',
        [
            [False, True, 'bar', does_not_raise()],
            [False, True, 'bar_', does_not_raise()],
            [False, False, 'bar', does_not_raise()],
            [False, False, 'bar_', pytest.raises(ValueError)],
            [True, True, 'bar', does_not_raise()],
            [True, True, 'bar_', does_not_raise()],
            [True, False, 'bar', does_not_raise()],
            [True, False, 'bar_', does_not_raise()],
        ],
    )
    def test_populate_by_name_config(
        self,
        use_construct: bool,
        populate_by_name_config: bool,
        arg_name: str,
        expectation: ContextManager,
    ):
        expected_value: int = 7

        class Foo(BaseModel):
            bar_: int = Field(..., alias='bar')

            model_config = dict(populate_by_name=populate_by_name_config)

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
        with pytest.warns(
            PydanticDeprecatedSince20, match='Support for class-based `config` is deprecated, use ConfigDict instead.'
        ):

            class Config(BaseConfig):
                pass

    def test_config_class_attributes_are_deprecated(self):
        with pytest.warns(
            PydanticDeprecatedSince20,
            match='Support for class-based `config` is deprecated, use ConfigDict instead.',
        ):
            assert BaseConfig.validate_assignment is False

        with pytest.warns(
            PydanticDeprecatedSince20,
            match='Support for class-based `config` is deprecated, use ConfigDict instead.',
        ):
            assert BaseConfig().validate_assignment is False

        with pytest.warns(
            PydanticDeprecatedSince20,
            match='Support for class-based `config` is deprecated, use ConfigDict instead.',
        ):

            class Config(BaseConfig):
                pass

        with pytest.warns(
            PydanticDeprecatedSince20,
            match='Support for class-based `config` is deprecated, use ConfigDict instead.',
        ):
            assert Config.validate_assignment is False

        with pytest.warns(
            PydanticDeprecatedSince20,
            match='Support for class-based `config` is deprecated, use ConfigDict instead.',
        ):
            assert Config().validate_assignment is False

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
* 'allow_population_by_field_name' has been renamed to 'populate_by_name'
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
    extra_error = re.escape(
        "Input should be 'allow', 'forbid' or 'ignore'"
        " [type=literal_error, input_value='invalid-value', input_type=str]"
    )
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
        model_config = ConfigDict(populate_by_name=True)

    assert BaseModel.model_config.get('frozen') is None
    assert BaseModel.model_config.get('populate_by_name') is None
    assert BaseModel.model_config.get('extra') is None
    assert BaseModel.model_config.get('use_enum_values') is None

    assert Parent.model_config.get('frozen') is True
    assert Parent.model_config.get('populate_by_name') is None
    assert Parent.model_config.get('extra') == 'forbid'
    assert Parent.model_config.get('use_enum_values') is None

    assert Mixin.model_config.get('frozen') is None
    assert Mixin.model_config.get('populate_by_name') is None
    assert Mixin.model_config.get('extra') is None
    assert Mixin.model_config.get('use_enum_values') is True

    assert Child.model_config.get('frozen') is True
    assert Child.model_config.get('populate_by_name') is True
    assert Child.model_config.get('extra') == 'forbid'
    assert Child.model_config.get('use_enum_values') is True


def test_config_wrapper_match():
    localns = {'_GenerateSchema': GenerateSchema, 'GenerateSchema': GenerateSchema, 'JsonValue': JsonValue}
    config_dict_annotations = [(k, str(v)) for k, v in get_type_hints(ConfigDict, localns=localns).items()]
    config_dict_annotations.sort()
    # remove config
    config_wrapper_annotations = [
        (k, str(v)) for k, v in get_type_hints(ConfigWrapper, localns=localns).items() if k != 'config_dict'
    ]
    config_wrapper_annotations.sort()

    assert (
        config_dict_annotations == config_wrapper_annotations
    ), 'ConfigDict and ConfigWrapper must have the same annotations (except ConfigWrapper.config_dict)'


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
    assert isinstance(exc_info.value.__cause__, ExceptionGroup)
    assert len(exc_info.value.__cause__.exceptions) == 1
    src_exc = exc_info.value.__cause__.exceptions[0]
    assert repr(src_exc) == "AssertionError('Must be greater than 5\\nassert 4 > 5')"
    assert len(src_exc.__notes__) == 1
    assert src_exc.__notes__[0] == '\nPydantic: cause of loc: foo'


def test_config_defaults_match():
    localns = {'_GenerateSchema': GenerateSchema, 'GenerateSchema': GenerateSchema}
    config_dict_keys = sorted(list(get_type_hints(ConfigDict, localns=localns).keys()))
    config_defaults_keys = sorted(list(config_defaults.keys()))

    assert config_dict_keys == config_defaults_keys, 'ConfigDict and config_defaults must have the same keys'


def test_config_is_not_inherited_in_model_fields():
    from typing import List

    from pydantic import BaseModel, ConfigDict

    class Inner(BaseModel):
        a: str

    class Outer(BaseModel):
        # this cause the inner model incorrectly dumpped:
        model_config = ConfigDict(str_to_lower=True)

        x: List[str]  # should be converted to lower
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


def test_config_model_defer_build():
    class MyModel(BaseModel, defer_build=True):
        x: int

    assert isinstance(MyModel.__pydantic_validator__, MockValSer)
    assert isinstance(MyModel.__pydantic_serializer__, MockValSer)

    m = MyModel(x=1)
    assert m.x == 1

    assert isinstance(MyModel.__pydantic_validator__, SchemaValidator)
    assert isinstance(MyModel.__pydantic_serializer__, SchemaSerializer)


def test_config_type_adapter_defer_build():
    class MyModel(BaseModel, defer_build=True):
        x: int

    ta = TypeAdapter(MyModel)

    assert isinstance(ta.validator, MockValSer)
    assert isinstance(ta.serializer, MockValSer)

    m = ta.validate_python({'x': 1})
    assert m.x == 1
    m2 = ta.validate_python({'x': 2})
    assert m2.x == 2

    # in the future, can reassign said validators to the TypeAdapter
    assert isinstance(MyModel.__pydantic_validator__, SchemaValidator)
    assert isinstance(MyModel.__pydantic_serializer__, SchemaSerializer)


def test_config_model_defer_build_nested():
    class MyNestedModel(BaseModel, defer_build=True):
        x: int

    class MyModel(BaseModel):
        y: MyNestedModel

    assert isinstance(MyNestedModel.__pydantic_validator__, MockValSer)
    assert isinstance(MyNestedModel.__pydantic_serializer__, MockValSer)

    m = MyModel(y={'x': 1})
    assert m.model_dump() == {'y': {'x': 1}}

    assert isinstance(MyNestedModel.__pydantic_validator__, MockValSer)
    assert isinstance(MyNestedModel.__pydantic_serializer__, MockValSer)


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
