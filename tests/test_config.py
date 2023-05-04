import re
import sys
from contextlib import nullcontext as does_not_raise
from inspect import signature
from typing import Any, ContextManager, Iterable, NamedTuple, Type, Union, get_type_hints

from dirty_equals import HasRepr
from pydantic_core import SchemaError

from pydantic import (
    BaseConfig,
    BaseModel,
    Field,
    PrivateAttr,
    PydanticSchemaGenerationError,
    ValidationError,
    create_model,
    validate_call,
)
from pydantic._internal._config import ConfigWrapper, config_defaults
from pydantic.config import ConfigDict
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic.errors import PydanticUserError

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

        class Config:
            strict = True

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


@pytest.mark.filterwarnings('ignore:.* is deprecated.*:DeprecationWarning')
class TestsBaseConfig:
    def test_base_config_equality_defaults_of_config_dict_class(self):
        for key, value in config_defaults.items():
            assert getattr(BaseConfig, key) == value

    def test_config_and_module_config_cannot_be_used_together(self):
        with pytest.raises(PydanticUserError):

            class MyModel(BaseModel):
                model_config = ConfigDict(title='MyTitle')

                class Config:
                    title = 'MyTitleConfig'

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

            class Config:
                extra = 'allow'

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

            class Config:
                extra = 'allow'

        assert _equals(str(signature(Model)), '(a: float, b: int) -> None')

    def test_base_config_use_field_name(self):
        class Foo(BaseModel):
            foo: str = Field(..., alias='this is invalid')

            class Config:
                populate_by_name = True

        assert _equals(str(signature(Foo)), '(*, foo: str) -> None')

    def test_base_config_does_not_use_reserved_word(self):
        class Foo(BaseModel):
            from_: str = Field(..., alias='from')

            class Config:
                populate_by_name = True

        assert _equals(str(signature(Foo)), '(*, from_: str) -> None')

    def test_base_config_extra_allow_no_conflict(self):
        class Model(BaseModel):
            spam: str

            class Config:
                extra = 'allow'

        assert _equals(str(signature(Model)), '(*, spam: str, **extra_data: Any) -> None')

    def test_base_config_extra_allow_conflict_twice(self):
        class Model(BaseModel):
            extra_data: str
            extra_data_: str

            class Config:
                extra = 'allow'

        assert _equals(str(signature(Model)), '(*, extra_data: str, extra_data_: str, **extra_data__: Any) -> None')

    def test_base_config_extra_allow_conflict_custom_signature(self):
        class Model(BaseModel):
            extra_data: int

            def __init__(self, extra_data: int = 1, **foobar: Any):
                super().__init__(extra_data=extra_data, **foobar)

            class Config:
                extra = 'allow'

        assert _equals(str(signature(Model)), '(extra_data: int = 1, **foobar: Any) -> None')

    def test_base_config_private_attribute_intersection_with_extra_field(self):
        class Model(BaseModel):
            _foo = PrivateAttr('private_attribute')

            class Config:
                extra = 'allow'

        assert Model.__slots__ == {'_foo'}
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
            class Config:
                strict = False

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

            class Config:
                allow_inf_nan = False

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

            class Config:
                str_strip_whitespace = enabled

        m = Model(str_check=str_check)
        assert m.str_check == result_str_check

    @pytest.mark.parametrize(
        'enabled,str_check,result_str_check',
        [(True, 'ABCDefG', 'ABCDEFG'), (False, 'ABCDefG', 'ABCDefG')],
    )
    def test_str_to_upper(self, enabled, str_check, result_str_check):
        class Model(BaseModel):
            str_check: str

            class Config:
                str_to_upper = enabled

        m = Model(str_check=str_check)

        assert m.str_check == result_str_check

    @pytest.mark.parametrize(
        'enabled,str_check,result_str_check',
        [(True, 'ABCDefG', 'abcdefg'), (False, 'ABCDefG', 'ABCDefG')],
    )
    def test_str_to_lower(self, enabled, str_check, result_str_check):
        class Model(BaseModel):
            str_check: str

            class Config:
                str_to_lower = enabled

        m = Model(str_check=str_check)

        assert m.str_check == result_str_check

    def test_namedtuple_arbitrary_type(self):
        class CustomClass:
            pass

        class Tup(NamedTuple):
            c: CustomClass

        class Model(BaseModel):
            x: Tup

            class Config:
                arbitrary_types_allowed = True

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

            class Config(BaseConfig):
                populate_by_name = populate_by_name_config

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

            class Config:
                frozen = True

        m = Model(a=40, b=10)
        assert m == m.model_copy()

    def test_config_class_is_deprecated(self):
        with pytest.warns(
            DeprecationWarning, match='Support for class-based `config` is deprecated, use ConfigDict instead.'
        ):

            class Config(BaseConfig):
                pass

    def test_config_class_attributes_are_deprecated(self):
        with pytest.warns(
            DeprecationWarning,
            match='Support for class-based `config` is deprecated, use ConfigDict instead.',
        ):
            assert BaseConfig.validate_assignment is False

        with pytest.warns(
            DeprecationWarning,
            match='Support for class-based `config` is deprecated, use ConfigDict instead.',
        ):
            assert BaseConfig().validate_assignment is False

        class Config(BaseConfig):
            pass

        with pytest.warns(
            DeprecationWarning,
            match='Support for class-based `config` is deprecated, use ConfigDict instead.',
        ):
            assert Config.validate_assignment is False

        with pytest.warns(
            DeprecationWarning,
            match='Support for class-based `config` is deprecated, use ConfigDict instead.',
        ):
            assert Config().validate_assignment is False

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

    with pytest.raises(SchemaError, match='Invalid extra_behavior: `invalid-value`'):

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


@pytest.mark.skipif(sys.version_info < (3, 10), reason='different on older versions')
def test_config_wrapper_match():
    config_dict_annotations = [(k, str(v)) for k, v in get_type_hints(ConfigDict).items()]
    # remove config
    config_wrapper_annotations = [(k, str(v)) for k, v in get_type_hints(ConfigWrapper).items() if k != 'config_dict']

    assert (
        config_dict_annotations == config_wrapper_annotations
    ), 'ConfigDict and ConfigWrapper must have the same annotations (except ConfigWrapper.config_dict)'


@pytest.mark.skipif(sys.version_info < (3, 10), reason='different on older versions')
def test_config_defaults_match():
    config_dict_keys = list(get_type_hints(ConfigDict).keys())
    config_defaults_keys = list(config_defaults.keys())

    assert config_dict_keys == config_defaults_keys, 'ConfigDict and config_defaults must have the same keys'
