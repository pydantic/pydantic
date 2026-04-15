The `pydantic_extra_types.isbn` module provides functionality to receive and validate ISBN.

ISBN (International Standard Book Number) is a numeric commercial book identifier which is intended to be unique. This module provides an ISBN type for Pydantic models.

## ISBN

Bases: `str`

Represents a ISBN and provides methods for conversion, validation, and serialization.

```py
from pydantic import BaseModel

from pydantic_extra_types.isbn import ISBN


class Book(BaseModel):
    isbn: ISBN


book = Book(isbn='8537809667')
print(book)
# > isbn='9788537809662'

```

### validate_isbn_format

```python
validate_isbn_format(value: str) -> None

```

Validate a ISBN format from the provided str value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `str` | The str value representing the ISBN in 10 or 13 digits. | *required* |

Raises:

| Type | Description | | --- | --- | | `PydanticCustomError` | If the ISBN is not valid. |

Source code in `pydantic_extra_types/isbn.py`

```python
@staticmethod
def validate_isbn_format(value: str) -> None:
    """Validate a ISBN format from the provided str value.

    Args:
        value: The str value representing the ISBN in 10 or 13 digits.

    Raises:
        PydanticCustomError: If the ISBN is not valid.
    """
    isbn_length = len(value)

    if isbn_length not in (10, 13):
        raise PydanticCustomError('isbn_length', f'Length for ISBN must be 10 or 13 digits, not {isbn_length}')

    if isbn_length == 10:
        if not value[:-1].isdigit() or ((value[-1] != 'X') and (not value[-1].isdigit())):
            raise PydanticCustomError('isbn10_invalid_characters', 'First 9 digits of ISBN-10 must be integers')
        if isbn10_digit_calc(value) != value[-1]:
            raise PydanticCustomError('isbn_invalid_digit_check_isbn10', 'Provided digit is invalid for given ISBN')

    if isbn_length == 13:
        if not value.isdigit():
            raise PydanticCustomError('isbn13_invalid_characters', 'All digits of ISBN-13 must be integers')
        if value[:3] not in ('978', '979'):
            raise PydanticCustomError(
                'isbn_invalid_early_characters', 'The first 3 digits of ISBN-13 must be 978 or 979'
            )
        if isbn13_digit_calc(value) != value[-1]:
            raise PydanticCustomError('isbn_invalid_digit_check_isbn13', 'Provided digit is invalid for given ISBN')

```

### convert_isbn10_to_isbn13

```python
convert_isbn10_to_isbn13(value: str) -> str

```

Convert an ISBN-10 to ISBN-13.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `str` | The ISBN-10 value to be converted. | *required* |

Returns:

| Type | Description | | --- | --- | | `str` | The converted ISBN or the original value if no conversion is necessary. |

Source code in `pydantic_extra_types/isbn.py`

```python
@staticmethod
def convert_isbn10_to_isbn13(value: str) -> str:
    """Convert an ISBN-10 to ISBN-13.

    Args:
        value: The ISBN-10 value to be converted.

    Returns:
        The converted ISBN or the original value if no conversion is necessary.
    """
    if len(value) == 10:
        base_isbn = f'978{value[:-1]}'
        isbn13_digit = isbn13_digit_calc(base_isbn)
        return ISBN(f'{base_isbn}{isbn13_digit}')

    return ISBN(value)

```

## isbn10_digit_calc

```python
isbn10_digit_calc(isbn: str) -> str

```

Calculate the ISBN-10 check digit from the provided str value. More information on the validation algorithm on [Wikipedia](https://en.wikipedia.org/wiki/ISBN#Check_digits)

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `isbn` | `str` | The str value representing the ISBN in 10 digits. | *required* |

Returns:

| Type | Description | | --- | --- | | `str` | The calculated last digit of the ISBN-10 value. |

Source code in `pydantic_extra_types/isbn.py`

```python
def isbn10_digit_calc(isbn: str) -> str:
    """Calculate the ISBN-10 check digit from the provided str value. More information on the validation algorithm on [Wikipedia](https://en.wikipedia.org/wiki/ISBN#Check_digits)

    Args:
        isbn: The str value representing the ISBN in 10 digits.

    Returns:
        The calculated last digit of the ISBN-10 value.
    """
    total = sum(int(digit) * (10 - idx) for idx, digit in enumerate(isbn[:9]))
    diff = (11 - total) % 11
    valid_check_digit = 'X' if diff == 10 else str(diff)
    return valid_check_digit

```

## isbn13_digit_calc

```python
isbn13_digit_calc(isbn: str) -> str

```

Calc a ISBN-13 last digit from the provided str value. More information on the validation algorithm on [Wikipedia](https://en.wikipedia.org/wiki/ISBN#Check_digits)

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `isbn` | `str` | The str value representing the ISBN in 13 digits. | *required* |

Returns:

| Type | Description | | --- | --- | | `str` | The calculated last digit of the ISBN-13 value. |

Source code in `pydantic_extra_types/isbn.py`

```python
def isbn13_digit_calc(isbn: str) -> str:
    """Calc a ISBN-13 last digit from the provided str value. More information on the validation algorithm on [Wikipedia](https://en.wikipedia.org/wiki/ISBN#Check_digits)

    Args:
        isbn: The str value representing the ISBN in 13 digits.

    Returns:
        The calculated last digit of the ISBN-13 value.
    """
    total = sum(int(digit) * factor for digit, factor in zip(isbn[:12], it.cycle((1, 3))))

    check_digit = (10 - total) % 10

    return str(check_digit)

```
