def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))


def to_lower_camel(string: str) -> str:
    if len(string) >= 1:
        pascal_string = to_camel(string)
        return pascal_string[0].lower() + pascal_string[1:]
    return string.lower()
