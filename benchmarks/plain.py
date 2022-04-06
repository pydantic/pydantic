from decimal import Decimal


def validate_str(v: any) -> str:
    if isinstance(v, str):
        return v
    elif isinstance(v, bytes):
        return v.decode()
    elif isinstance(v, (int, float, Decimal)):
        return str(v)
    else:
        # return '[not a string]'
        raise TypeError(f'{type(v)} is not a string')


def validate_str_full(
    s,
    min_length: int | None,
    max_length: int | None,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
):
    s = validate_str(s)

    if strip_whitespace:
        s = s.strip()

    if min_length is not None and len(s) < min_length:
        raise ValueError(f'String is too short (min length: {min_length})')
    if max_length is not None and len(s) > max_length:
        raise ValueError(f'String is too long (max length: {max_length})')

    if to_lower:
        return s.lower()
    if to_upper:
        return s.upper()
    else:
        return s


def validate_str_list(
    items: list[any],
    min_length: int | None,
    max_length: int | None,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
):
    new_items = []
    for item in items:
        value = validate_str_recursive(item, min_length, max_length, strip_whitespace, to_lower, to_upper)
        new_items.append(value)
    return new_items


def validate_str_dict(
    items: dict[str, any],
    min_length: int | None,
    max_length: int | None,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
):
    new_items = {}
    for k, v in items.items():
        value = validate_str_recursive(v, min_length, max_length, strip_whitespace, to_lower, to_upper)
        new_items[k] = value
    return new_items


def validate_str_recursive(
    v: str | list[str] | dict[str, any],
    min_length: int | None,
    max_length: int | None,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
):
    if isinstance(v, list):
        return validate_str_list(v, min_length, max_length, strip_whitespace, to_lower, to_upper)
    elif isinstance(v, dict):
        return validate_str_dict(v, min_length, max_length, strip_whitespace, to_lower, to_upper)
    else:
        return validate_str_full(v, min_length, max_length, strip_whitespace, to_lower, to_upper)
