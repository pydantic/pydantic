import pytest

from pydantic import PydanticUserError
from pydantic._internal._decorators import inspect_annotated_serializer, inspect_validator


def _two_pos_required_args(a, b):
    pass


def _two_pos_required_args_extra_optional(a, b, c=1, d=2, *, e=3):
    pass


def _three_pos_required_args(a, b, c):
    pass


def _one_pos_required_arg_one_optional(a, b=1):
    pass


@pytest.mark.parametrize(
    [
        'obj',
        'mode',
        'expected',
    ],
    [
        (str, 'plain', False),
        (float, 'plain', False),
        (int, 'plain', False),
        (lambda a: str(a), 'plain', False),
        (lambda a='': str(a), 'plain', False),
        (_two_pos_required_args, 'plain', True),
        (_two_pos_required_args, 'wrap', False),
        (_two_pos_required_args_extra_optional, 'plain', True),
        (_two_pos_required_args_extra_optional, 'wrap', False),
        (_three_pos_required_args, 'wrap', True),
        (_one_pos_required_arg_one_optional, 'plain', False),
    ],
)
def test_inspect_validator(obj, mode, expected):
    assert inspect_validator(obj, mode=mode) == expected


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


@pytest.mark.parametrize(
    [
        'obj',
        'mode',
        'expected',
    ],
    [
        (str, 'plain', False),
        (float, 'plain', False),
        (int, 'plain', False),
        (lambda a: str(a), 'plain', False),
        (lambda a='': str(a), 'plain', False),
        (_two_pos_required_args, 'plain', True),
        (_two_pos_required_args, 'wrap', False),
        (_two_pos_required_args_extra_optional, 'plain', True),
        (_two_pos_required_args_extra_optional, 'wrap', False),
        (_three_pos_required_args, 'wrap', True),
        (_one_pos_required_arg_one_optional, 'plain', False),
    ],
)
def test_inspect_annotated_serializer(obj, mode, expected):
    assert inspect_annotated_serializer(obj, mode=mode) == expected


@pytest.mark.parametrize('mode', ['plain', 'wrap'])
def test_inspect_annotated_serializer_invalid_number_of_arguments(mode):
    # TODO: add more erroneous cases
    def serializer():
        pass

    with pytest.raises(PydanticUserError) as e:
        inspect_annotated_serializer(serializer, mode=mode)

    assert e.value.code == 'field-serializer-signature'
