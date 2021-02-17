import sys
from typing import get_type_hints

import pytest

from pydantic import BaseModel, Field
from pydantic.fields import Undefined
from pydantic.typing import Annotated

pytestmark = pytest.mark.skipif(not Annotated, reason='typing_extensions not installed')


@pytest.mark.parametrize(
    ['hint_fn', 'value'],
    [
        # Test Annotated types with arbitrary metadata
        pytest.param(
            lambda: Annotated[int, 0],
            5,
            id='misc-default',
        ),
        pytest.param(
            lambda: Annotated[int, 0],
            Field(default=5, ge=0),
            id='misc-field-default-constraint',
        ),
        # Test valid Annotated Field uses
        pytest.param(
            lambda: Annotated[int, Field(description='Test')],
            5,
            id='annotated-field-value-default',
        ),
        pytest.param(
            lambda: Annotated[int, Field(default_factory=lambda: 5, description='Test')],
            Undefined,
            id='annotated-field-default_factory',
        ),
    ],
)
def test_annotated(hint_fn, value):
    hint = hint_fn()

    class M(BaseModel):
        x: hint = value

    assert M().x == 5
    assert M(x=10).x == 10

    # get_type_hints doesn't recognize typing_extensions.Annotated, so will return the full
    # annotation. 3.9 w/ stock Annotated will return the wrapped type by default, but return the
    # full thing with the new include_extras flag.
    if sys.version_info >= (3, 9):
        assert get_type_hints(M)['x'] is int
        assert get_type_hints(M, include_extras=True)['x'] == hint
    else:
        assert get_type_hints(M)['x'] == hint


@pytest.mark.parametrize(
    ['hint_fn', 'value', 'subclass_ctx'],
    [
        pytest.param(
            lambda: Annotated[int, Field(5)],
            Undefined,
            pytest.raises(ValueError, match='`Field` default cannot be set in `Annotated`'),
            id='annotated-field-default',
        ),
        pytest.param(
            lambda: Annotated[int, Field(), Field()],
            Undefined,
            pytest.raises(ValueError, match='cannot specify multiple `Annotated` `Field`s'),
            id='annotated-field-dup',
        ),
        pytest.param(
            lambda: Annotated[int, Field()],
            Field(),
            pytest.raises(ValueError, match='cannot specify `Annotated` and value `Field`'),
            id='annotated-field-value-field-dup',
        ),
        pytest.param(
            lambda: Annotated[int, Field(default_factory=lambda: 5)],  # The factory is not used
            5,
            pytest.raises(ValueError, match='cannot specify both default and default_factory'),
            id='annotated-field-default_factory-value-default',
        ),
    ],
)
def test_annotated_model_exceptions(hint_fn, value, subclass_ctx):
    hint = hint_fn()
    with subclass_ctx:

        class M(BaseModel):
            x: hint = value


@pytest.mark.parametrize(
    ['hint_fn', 'value', 'empty_init_ctx'],
    [
        pytest.param(
            lambda: Annotated[int, 0],
            Undefined,
            pytest.raises(ValueError, match='field required'),
            id='misc-no-default',
        ),
        pytest.param(
            lambda: Annotated[int, Field()],
            Undefined,
            pytest.raises(ValueError, match='field required'),
            id='annotated-field-no-default',
        ),
    ],
)
def test_annotated_instance_exceptions(hint_fn, value, empty_init_ctx):
    hint = hint_fn()

    class M(BaseModel):
        x: hint = value

    with empty_init_ctx:
        assert M().x == 5


def test_field_reuse():
    field = Field(description='Long description')

    class Model(BaseModel):
        one: int = field

    assert Model(one=1).dict() == {'one': 1}

    class AnnotatedModel(BaseModel):
        one: Annotated[int, field]

    assert AnnotatedModel(one=1).dict() == {'one': 1}
