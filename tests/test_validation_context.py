from typing import Annotated

import pytest
from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError, ValidationInfo, ValidatorFunctionWrapHandler, WrapValidator


def test_context():
    def f(value, handler: ValidatorFunctionWrapHandler, info: ValidationInfo):
        return handler(value) + f'| context: {info.context}'

    ta = TypeAdapter(Annotated[str, WrapValidator(f)])

    assert ta.validate_python('foobar') == 'foobar| context: None'
    assert ta.validate_python('foobar', context={1: 10}) == 'foobar| context: {1: 10}'
    assert ta.validate_python('foobar', context='frogspawn') == 'foobar| context: frogspawn'

    assert ta.validate_json('"foobar"') == 'foobar| context: None'
    assert ta.validate_json('"foobar"', context={1: 10}) == 'foobar| context: {1: 10}'
    assert ta.validate_json('"foobar"', context='frogspawn') == 'foobar| context: frogspawn'


def test_mutable_context():
    def f(value, handler: ValidatorFunctionWrapHandler, info: ValidationInfo):
        info.context['foo'] = value
        return handler(value)

    ta = TypeAdapter(Annotated[str, WrapValidator(f)])

    mutable_context = {}
    assert ta.validate_python('foobar', context=mutable_context) == 'foobar'
    assert mutable_context == {'foo': 'foobar'}

    mutable_context = {}
    assert ta.validate_json('"foobar"', context=mutable_context) == 'foobar'
    assert mutable_context == {'foo': 'foobar'}


def test_typed_dict():
    def f1(value, handler: ValidatorFunctionWrapHandler, info: ValidationInfo):
        info.context['f1'] = value
        return handler(value) + f'| context: {info.context}'

    def f2(value, handler: ValidatorFunctionWrapHandler, info: ValidationInfo):
        info.context['f2'] = value
        return handler(value) + f'| context: {info.context}'

    # The functional syntax is required for the annotations to resolve, as `f1` and `f2` are function locals:
    Data = TypedDict('Data', {'f1': Annotated[str, WrapValidator(f1)], 'f2': Annotated[str, WrapValidator(f2)]})  # noqa: UP013

    ta = TypeAdapter(Data)

    expected = {
        'f1': "1| context: {'x': 'y', 'f1': '1'}",
        'f2': "2| context: {'x': 'y', 'f1': '1', 'f2': '2'}",
    }
    assert ta.validate_python({'f1': '1', 'f2': '2'}, context={'x': 'y'}) == expected
    assert ta.validate_json('{"f1": "1", "f2": "2"}', context={'x': 'y'}) == expected


def test_context_exceptions():
    def f(value, handler: ValidatorFunctionWrapHandler, info: ValidationInfo):
        if 'error' in info.context:
            raise ValueError('wrong')
        return handler(value)

    ta = TypeAdapter(Annotated[str, WrapValidator(f)])

    assert ta.validate_python('foobar', context={}) == 'foobar'
    assert ta.validate_json('"foobar"', context={}) == 'foobar'

    # `info.context` is `None` by default, so the membership test raises a `TypeError`,
    # which is not treated as a validation error:
    with pytest.raises(TypeError):
        ta.validate_python('foobar')
    with pytest.raises(TypeError):
        ta.validate_json('"foobar"')

    with pytest.raises(ValidationError, match=r'Value error, wrong \[type=value_error,'):
        ta.validate_python('foobar', context={'error'})
    with pytest.raises(ValidationError, match=r'Value error, wrong \[type=value_error,'):
        ta.validate_json('"foobar"', context={'error'})
