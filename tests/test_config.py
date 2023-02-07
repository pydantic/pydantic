import sys
from contextlib import nullcontext as does_not_raise
from inspect import signature
from typing import Any, ContextManager, Iterable, NamedTuple, Type, Union

from dirty_equals import HasRepr

from pydantic import BaseConfig, BaseModel, Extra, Field, PrivateAttr, PydanticSchemaGenerationError, ValidationError
from pydantic.config import ConfigDict, _default_config
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


@pytest.mark.filterwarnings('ignore:.* is deprecated.*:DeprecationWarning')
class TestsBaseConfig:
    def test_base_config_equality_defaults_of_config_dict_class(self):
        for key, value in _default_config.items():
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

        expected = _default_config.copy()
        expected['title'] = 'MyTitle'
        expected['frozen'] = True
        for k, v in expected.items():
            assert MyModel.model_config[k] == v

    def test_base_config_custom_init_signature(self):
        class MyModel(BaseModel):
            id: int
            name: str = 'John Doe'
            f__: str = Field(..., alias='foo')

            class Config:
                extra = Extra.allow

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
                extra = Extra.allow

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
                extra = Extra.allow

        assert _equals(str(signature(Model)), '(*, spam: str, **extra_data: Any) -> None')

    def test_base_config_extra_allow_conflict_twice(self):
        class Model(BaseModel):
            extra_data: str
            extra_data_: str

            class Config:
                extra = Extra.allow

        assert _equals(str(signature(Model)), '(*, extra_data: str, extra_data_: str, **extra_data__: Any) -> None')

    def test_base_config_extra_allow_conflict_custom_signature(self):
        class Model(BaseModel):
            extra_data: int

            def __init__(self, extra_data: int = 1, **foobar: Any):
                super().__init__(extra_data=extra_data, **foobar)

            class Config:
                extra = Extra.allow

        assert _equals(str(signature(Model)), '(extra_data: int = 1, **foobar: Any) -> None')

    def test_base_config_private_attribute_intersection_with_extra_field(self):
        class Model(BaseModel):
            _foo = PrivateAttr('private_attribute')

            class Config:
                extra = Extra.allow

        assert Model.__slots__ == {'_foo'}
        m = Model(_foo='field')
        assert m._foo == 'private_attribute'
        assert m.__dict__ == m.model_dump() == {'_foo': 'field'}
        m._foo = 'still_private'
        assert m._foo == 'still_private'
        assert m.__dict__ == m.model_dump() == {'_foo': 'field'}

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
        # insert_assert(exc_info.value.errors())
        assert exc_info.value.errors() == [
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
        assert m == m.copy()

    def test_config_class_is_deprecated(self):
        with pytest.warns(
            DeprecationWarning, match='`BaseConfig` is deprecated and will be removed in a future version'
        ):

            class Config(BaseConfig):
                pass

    def test_config_class_attributes_are_deprecated(self):
        with pytest.warns(
            DeprecationWarning,
            match='Support for "config" as "BaseConfig" is deprecated and will be removed in a future version"',
        ):
            assert BaseConfig.validate_assignment is False

        with pytest.warns(
            DeprecationWarning,
            match='Support for "config" as "BaseConfig" is deprecated and will be removed in a future version"',
        ):
            assert BaseConfig().validate_assignment is False

        class Config(BaseConfig):
            pass

        with pytest.warns(
            DeprecationWarning,
            match='Support for "config" as "Config" is deprecated and will be removed in a future version"',
        ):
            assert Config.validate_assignment is False

        with pytest.warns(
            DeprecationWarning,
            match='Support for "config" as "Config" is deprecated and will be removed in a future version"',
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
