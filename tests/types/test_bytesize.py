import pytest

from pydantic import ByteSize


@pytest.mark.parametrize(
    'size,decimal,expected',
    [
        (1023, False, '1023B'),
        (1048575, False, '1.0MiB'),
        (-1048575, False, '-1.0MiB'),
        (1024**5 * 1024 - 1, False, '1.0EiB'),
        (999, True, '999B'),
        (999_999, True, '1.0MB'),
        (999_949, True, '999.9KB'),
    ],
)
def test_bytesize_human_readable_unit_boundary(size: int, decimal: bool, expected: str) -> None:
    """https://github.com/pydantic/pydantic/issues/14056"""

    assert ByteSize(size).human_readable(decimal=decimal) == expected
