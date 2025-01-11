import re
from typing import Annotated, Generic, TypeVar

import pytest

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    PydanticDeprecatedSince20,
    PydanticUserError,
    ValidationError,
    create_model,
    errors,
    field_validator,
    validator,
)


def test_create_model() -> None:
    FooModel = create_model(
        'FooModel',
        foo=(str, ...),
        bar=(int, 123),
        baz=int,
        qux=Annotated[int, Field(title='QUX')],
    )
    assert issubclass(FooModel, BaseModel)
    assert FooModel.model_config == BaseModel.model_config
    assert FooModel.__name__ == 'FooModel'
    assert FooModel.model_fields.keys() == {'foo', 'bar', 'baz', 'qux'}
    assert FooModel.model_fields['foo'].is_required()
    assert not FooModel.model_fields['bar'].is_required()
    assert FooModel.model_fields['baz'].is_required()

    assert FooModel.model_fields['qux'].title == 'QUX'

    assert not FooModel.__pydantic_decorators__.validators
    assert not FooModel.__pydantic_decorators__.root_validators
    assert not FooModel.__pydantic_decorators__.field_validators
    assert not FooModel.__pydantic_decorators__.field_serializers

    assert FooModel.__module__ == 'tests.test_create_model'


def test_create_model_invalid_tuple():
    with pytest.raises(PydanticUserError) as exc_info:
        create_model('FooModel', foo=(tuple[int, int], (1, 2), 'more'))

    assert exc_info.value.code == 'create-model-field-definitions'


def test_create_model_usage():
    FooModel = create_model('FooModel', foo=(str, ...), bar=(int, 123))
    m = FooModel(foo='hello')
    assert m.foo == 'hello'
    assert m.bar == 123
    with pytest.raises(ValidationError):
        FooModel()
    with pytest.raises(ValidationError):
        FooModel(foo='hello', bar='xxx')


def test_create_model_private_attr() -> None:
    FooModel = create_model('FooModel', _priv1=int, _priv2=(int, PrivateAttr(default=2)))
    assert set(FooModel.__private_attributes__) == {'_priv1', '_priv2'}

    m = FooModel()
    m._priv1 = 1
    assert m._priv1 == 1
    assert m._priv2 == 2


def test_create_model_pickle(create_module):
    """
    Pickle will work for dynamically created model only if it was defined globally with its class name
    and module where it's defined was specified
    """

    @create_module
    def module():
        import pickle

        from pydantic import create_model

        FooModel = create_model('FooModel', foo=(str, ...), bar=(int, 123), __module__=__name__)

        m = FooModel(foo='hello')
        d = pickle.dumps(m)
        m2 = pickle.loads(d)
        assert m2.foo == m.foo == 'hello'
        assert m2.bar == m.bar == 123
        assert m2 == m
        assert m2 is not m


def test_create_model_multi_inheritance():
    class Mixin:
        pass

    Generic_T = Generic[TypeVar('T')]
    FooModel = create_model('FooModel', value=(int, ...), __base__=(BaseModel, Generic_T))

    assert FooModel.__orig_bases__ == (BaseModel, Generic_T)


def test_create_model_must_not_reset_parent_namespace():
    # It's important to use the annotation `'namespace'` as this is a particular string that is present
    # in the parent namespace if you reset the parent namespace in the call to `create_model`.

    AbcModel = create_model('AbcModel', abc=('namespace', None))
    with pytest.raises(
        PydanticUserError,
        match=re.escape(
            '`AbcModel` is not fully defined; you should define `namespace`, then call `AbcModel.model_rebuild()`.'
        ),
    ):
        AbcModel(abc=1)

    # Rebuild the model now that `namespace` is defined
    namespace = int  # noqa F841
    AbcModel.model_rebuild()

    assert AbcModel(abc=1).abc == 1

    with pytest.raises(ValidationError) as exc_info:
        AbcModel(abc='a')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('abc',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]


def test_config_and_base():
    with pytest.raises(errors.PydanticUserError):
        create_model('FooModel', __config__=BaseModel.model_config, __base__=BaseModel)


def test_inheritance():
    class BarModel(BaseModel):
        x: int = 1
        y: int = 2

    model = create_model('FooModel', foo=(str, ...), bar=(int, 123), __base__=BarModel)
    assert model.model_fields.keys() == {'foo', 'bar', 'x', 'y'}
    m = model(foo='a', x=4)
    assert m.model_dump() == {'bar': 123, 'foo': 'a', 'x': 4, 'y': 2}

    # bases as a tuple
    model = create_model('FooModel', foo=(str, ...), bar=(int, 123), __base__=(BarModel,))
    assert model.model_fields.keys() == {'foo', 'bar', 'x', 'y'}
    m = model(foo='a', x=4)
    assert m.model_dump() == {'bar': 123, 'foo': 'a', 'x': 4, 'y': 2}


def test_custom_config():
    config = ConfigDict(frozen=True)
    expected_config = BaseModel.model_config.copy()
    expected_config['frozen'] = True

    model = create_model('FooModel', foo=(int, ...), __config__=config)
    m = model(**{'foo': '987'})
    assert m.foo == 987
    assert model.model_config == expected_config
    with pytest.raises(ValidationError):
        m.foo = 654


def test_custom_config_inherits():
    class Config(ConfigDict):
        custom_config: bool

    config = Config(custom_config=True, validate_assignment=True)
    expected_config = Config(BaseModel.model_config)
    expected_config.update(config)

    model = create_model('FooModel', foo=(int, ...), __config__=config)
    m = model(**{'foo': '987'})
    assert m.foo == 987
    assert model.model_config == expected_config
    with pytest.raises(ValidationError):
        m.foo = ['123']


def test_custom_config_extras():
    config = ConfigDict(extra='forbid')

    model = create_model('FooModel', foo=(int, ...), __config__=config)
    assert model(foo=654)
    with pytest.raises(ValidationError):
        model(bar=654)


def test_inheritance_validators():
    class BarModel(BaseModel):
        @field_validator('a', check_fields=False)
        @classmethod
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    model = create_model('FooModel', a=(str, 'cake'), __base__=BarModel)
    assert model().a == 'cake'
    assert model(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError):
        model(a='something else')


def test_inheritance_validators_always():
    class BarModel(BaseModel):
        @field_validator('a', check_fields=False)
        @classmethod
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    model = create_model('FooModel', a=(str, Field('cake', validate_default=True)), __base__=BarModel)
    with pytest.raises(ValidationError):
        model()
    assert model(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError):
        model(a='something else')


def test_inheritance_validators_all():
    with pytest.warns(PydanticDeprecatedSince20, match='Pydantic V1 style `@validator` validators are deprecated'):

        class BarModel(BaseModel):
            @validator('*')
            @classmethod
            def check_all(cls, v):
                return v * 2

    model = create_model('FooModel', a=(int, ...), b=(int, ...), __base__=BarModel)
    assert model(a=2, b=6).model_dump() == {'a': 4, 'b': 12}


def test_field_invalid_identifier() -> None:
    model = create_model('FooModel', **{'invalid-identifier': (int, ...)})
    m = model(**{'invalid-identifier': '123'})
    assert m.model_dump() == {'invalid-identifier': 123}
    with pytest.raises(ValidationError) as exc_info:
        model()
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('invalid-identifier',), 'msg': 'Field required', 'type': 'missing'}
    ]


def test_repeat_base_usage():
    class Model(BaseModel):
        a: str

    assert Model.model_fields.keys() == {'a'}

    model = create_model('FooModel', b=(int, 1), __base__=Model)

    assert Model.model_fields.keys() == {'a'}
    assert model.model_fields.keys() == {'a', 'b'}

    model2 = create_model('Foo2Model', c=(int, 1), __base__=Model)

    assert Model.model_fields.keys() == {'a'}
    assert model.model_fields.keys() == {'a', 'b'}
    assert model2.model_fields.keys() == {'a', 'c'}

    model3 = create_model('Foo2Model', d=(int, 1), __base__=model)

    assert Model.model_fields.keys() == {'a'}
    assert model.model_fields.keys() == {'a', 'b'}
    assert model2.model_fields.keys() == {'a', 'c'}
    assert model3.model_fields.keys() == {'a', 'b', 'd'}


def test_dynamic_and_static():
    class A(BaseModel):
        x: int
        y: float
        z: str

    DynamicA = create_model('A', x=(int, ...), y=(float, ...), z=(str, ...))

    for field_name in ('x', 'y', 'z'):
        assert A.model_fields[field_name].default == DynamicA.model_fields[field_name].default


def test_create_model_field_and_model_title():
    m = create_model('M', __config__=ConfigDict(title='abc'), a=(str, Field(title='field-title')))
    assert m.model_json_schema() == {
        'properties': {'a': {'title': 'field-title', 'type': 'string'}},
        'required': ['a'],
        'title': 'abc',
        'type': 'object',
    }


def test_create_model_field_description():
    m = create_model('M', a=(str, Field(description='descr')), __doc__='Some doc')
    assert m.model_json_schema() == {
        'properties': {'a': {'description': 'descr', 'title': 'A', 'type': 'string'}},
        'required': ['a'],
        'title': 'M',
        'type': 'object',
        'description': 'Some doc',
    }


def test_create_model_with_doc():
    model = create_model('FooModel', foo=(str, ...), bar=(int, 123), __doc__='The Foo model')
    assert model.__name__ == 'FooModel'
    assert model.__doc__ == 'The Foo model'


def test_create_model_protected_namespace_default():
    with pytest.warns(
        UserWarning, match='Field "model_dump_something" in Model has conflict with protected namespace "model_dump"'
    ):
        create_model('Model', model_dump_something=(str, ...))


def test_create_model_custom_protected_namespace():
    with pytest.warns(UserWarning, match='Field "test_field" in Model has conflict with protected namespace "test_"'):
        create_model(
            'Model',
            __config__=ConfigDict(protected_namespaces=('test_',)),
            model_prefixed_field=(str, ...),
            test_field=(str, ...),
        )


def test_create_model_multiple_protected_namespace():
    with pytest.warns(
        UserWarning, match='Field "also_protect_field" in Model has conflict with protected namespace "also_protect_"'
    ):
        create_model(
            'Model',
            __config__=ConfigDict(protected_namespaces=('protect_me_', 'also_protect_')),
            also_protect_field=(str, ...),
        )


def test_json_schema_with_inner_models_with_duplicate_names():
    model_a = create_model(
        'a',
        inner=(str, ...),
    )
    model_b = create_model(
        'a',
        outer=(model_a, ...),
    )
    assert model_b.model_json_schema() == {
        '$defs': {
            'a': {
                'properties': {'inner': {'title': 'Inner', 'type': 'string'}},
                'required': ['inner'],
                'title': 'a',
                'type': 'object',
            }
        },
        'properties': {'outer': {'$ref': '#/$defs/a'}},
        'required': ['outer'],
        'title': 'a',
        'type': 'object',
    }


def test_resolving_forward_refs_across_modules(create_module):
    module = create_module(
        # language=Python
        """\
from __future__ import annotations
from dataclasses import dataclass
from pydantic import BaseModel

class X(BaseModel):
    pass

@dataclass
class Y:
    x: X
        """
    )
    Z = create_model('Z', y=(module.Y, ...))
    assert Z(y={'x': {}}).y is not None


def test_type_field_in_the_same_module():
    class A:
        pass

    B = create_model('B', a_cls=(type, A))
    b = B()
    assert b.a_cls == A
