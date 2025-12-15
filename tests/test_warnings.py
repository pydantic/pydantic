from pydantic import PydanticDeprecatedSince20, PydanticDeprecationWarning
from pydantic.version import version_short


def test_pydantic_deprecation_warning():
    warning = PydanticDeprecationWarning('Warning message', 'Arbitrary argument', since=(2, 1), expected_removal=(4, 0))

    assert str(warning) == 'Warning message. Deprecated in Pydantic V2.1 to be removed in V4.0.'
    assert warning.args[0] == 'Warning message'
    assert warning.args[1] == 'Arbitrary argument'


def test_pydantic_deprecation_warning_tailing_dot_in_message():
    warning = PydanticDeprecationWarning('Warning message.', since=(2, 1), expected_removal=(4, 0))

    assert str(warning) == 'Warning message. Deprecated in Pydantic V2.1 to be removed in V4.0.'
    assert warning.args[0] == 'Warning message.'


def test_pydantic_deprecation_warning_calculated_expected_removal():
    warning = PydanticDeprecationWarning('Warning message', since=(2, 1))

    assert str(warning) == 'Warning message. Deprecated in Pydantic V2.1 to be removed in V3.0.'


def test_pydantic_deprecation_warning_2_0_migration_guide_link():
    warning = PydanticDeprecationWarning('Warning message', since=(2, 0))

    assert (
        str(warning)
        == f'Warning message. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/{version_short()}/migration/'
    )


def test_pydantic_deprecated_since_2_0_warning():
    warning = PydanticDeprecatedSince20('Warning message')

    assert isinstance(warning, PydanticDeprecationWarning)
    assert warning.message == 'Warning message'
    assert warning.since == (2, 0)
    assert warning.expected_removal == (3, 0)
