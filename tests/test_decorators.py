import pytest

from pydantic import PydanticUserError
from pydantic._internal._decorators import inspect_annotated_serializer, inspect_validator


def test_inspect_validator_error_wrap():
    def validator1(arg1):
        pass

    def validator4(arg1, arg2, arg3, arg4):
        pass

    with pytest.raises(PydanticUserError) as e:
        inspect_validator(validator1, mode='wrap')

    assert e.value.code == 'validator-signature'

    with pytest.raises(PydanticUserError) as e:
        inspect_validator(validator4, mode='wrap')

    assert e.value.code == 'validator-signature'


@pytest.mark.parametrize('mode', ['before', 'after', 'plain'])
def test_inspect_validator_error(mode):
    def validator():
        pass

    def validator3(arg1, arg2, arg3):
        pass

    with pytest.raises(PydanticUserError) as e:
        inspect_validator(validator, mode=mode)

    assert e.value.code == 'validator-signature'

    with pytest.raises(PydanticUserError) as e:
        inspect_validator(validator3, mode=mode)

    assert e.value.code == 'validator-signature'


@pytest.mark.parametrize('mode', ['plain', 'wrap'])
def test_inspect_annotated_serializer(mode):
    # TODO: add more erroneous cases
    def serializer():
        pass

    with pytest.raises(PydanticUserError) as e:
        inspect_annotated_serializer(serializer, mode=mode)

    assert e.value.code == 'field-serializer-signature'
