import re


def to_camel(snake: str) -> str:
    """
    Converts a snake_case string to PascalCase.
    """
    camel = snake.title()
    return re.sub('([0-9A-Za-z])_(?=[0-9A-Z])', lambda m: m.group(1), camel)


def to_lower_camel(snake: str) -> str:
    """
    Converts a snake_case string to camelCase.
    """
    camel = to_camel(snake)
    return re.sub('(^_*[A-Z])', lambda m: m.group(1).lower(), camel)


def to_snake(camel: str) -> str:
    """
    Converts a PascalCase or camelCase string to snake_case.
    """
    snake = re.sub(r'([a-zA-Z])([0-9])', lambda m: f'{m.group(1)}_{m.group(2)}', camel)
    snake = re.sub(r'([a-z0-9])([A-Z])', lambda m: f'{m.group(1)}_{m.group(2)}', snake)
    return snake.lower()
