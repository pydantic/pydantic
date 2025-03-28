Support for alias configurations.

## AliasPath

```python
AliasPath(first_arg: str, *args: str | int)

```

Usage Documentation

[`AliasPath` and `AliasChoices`](../../concepts/alias/#aliaspath-and-aliaschoices)

A data class used by `validation_alias` as a convenience to create aliases.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `path` | `list[int | str]` | A list of string or integer aliases. |

Source code in `pydantic/aliases.py`

```python
def __init__(self, first_arg: str, *args: str | int) -> None:
    self.path = [first_arg] + list(args)

```

### convert_to_aliases

```python
convert_to_aliases() -> list[str | int]

```

Converts arguments to a list of string or integer aliases.

Returns:

| Type | Description | | --- | --- | | `list[str | int]` | The list of aliases. |

Source code in `pydantic/aliases.py`

```python
def convert_to_aliases(self) -> list[str | int]:
    """Converts arguments to a list of string or integer aliases.

    Returns:
        The list of aliases.
    """
    return self.path

```

### search_dict_for_path

```python
search_dict_for_path(d: dict) -> Any

```

Searches a dictionary for the path specified by the alias.

Returns:

| Type | Description | | --- | --- | | `Any` | The value at the specified path, or PydanticUndefined if the path is not found. |

Source code in `pydantic/aliases.py`

```python
def search_dict_for_path(self, d: dict) -> Any:
    """Searches a dictionary for the path specified by the alias.

    Returns:
        The value at the specified path, or `PydanticUndefined` if the path is not found.
    """
    v = d
    for k in self.path:
        if isinstance(v, str):
            # disallow indexing into a str, like for AliasPath('x', 0) and x='abc'
            return PydanticUndefined
        try:
            v = v[k]
        except (KeyError, IndexError, TypeError):
            return PydanticUndefined
    return v

```

## AliasChoices

```python
AliasChoices(
    first_choice: str | AliasPath, *choices: str | AliasPath
)

```

Usage Documentation

[`AliasPath` and `AliasChoices`](../../concepts/alias/#aliaspath-and-aliaschoices)

A data class used by `validation_alias` as a convenience to create aliases.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `choices` | `list[str | AliasPath]` | A list containing a string or AliasPath. |

Source code in `pydantic/aliases.py`

```python
def __init__(self, first_choice: str | AliasPath, *choices: str | AliasPath) -> None:
    self.choices = [first_choice] + list(choices)

```

### convert_to_aliases

```python
convert_to_aliases() -> list[list[str | int]]

```

Converts arguments to a list of lists containing string or integer aliases.

Returns:

| Type | Description | | --- | --- | | `list[list[str | int]]` | The list of aliases. |

Source code in `pydantic/aliases.py`

```python
def convert_to_aliases(self) -> list[list[str | int]]:
    """Converts arguments to a list of lists containing string or integer aliases.

    Returns:
        The list of aliases.
    """
    aliases: list[list[str | int]] = []
    for c in self.choices:
        if isinstance(c, AliasPath):
            aliases.append(c.convert_to_aliases())
        else:
            aliases.append([c])
    return aliases

```

## AliasGenerator

```python
AliasGenerator(
    alias: Callable[[str], str] | None = None,
    validation_alias: (
        Callable[[str], str | AliasPath | AliasChoices]
        | None
    ) = None,
    serialization_alias: Callable[[str], str] | None = None,
)

```

Usage Documentation

[Using an `AliasGenerator`](../../concepts/alias/#using-an-aliasgenerator)

A data class used by `alias_generator` as a convenience to create various aliases.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `alias` | `Callable[[str], str] | None` | A callable that takes a field name and returns an alias for it. | | `validation_alias` | `Callable[[str], str | AliasPath | AliasChoices] | None` | A callable that takes a field name and returns a validation alias for it. | | `serialization_alias` | `Callable[[str], str] | None` | A callable that takes a field name and returns a serialization alias for it. |

### generate_aliases

```python
generate_aliases(
    field_name: str,
) -> tuple[
    str | None,
    str | AliasPath | AliasChoices | None,
    str | None,
]

```

Generate `alias`, `validation_alias`, and `serialization_alias` for a field.

Returns:

| Type | Description | | --- | --- | | `tuple[str | None, str | AliasPath | AliasChoices | None, str | None]` | A tuple of three aliases - validation, alias, and serialization. |

Source code in `pydantic/aliases.py`

```python
def generate_aliases(self, field_name: str) -> tuple[str | None, str | AliasPath | AliasChoices | None, str | None]:
    """Generate `alias`, `validation_alias`, and `serialization_alias` for a field.

    Returns:
        A tuple of three aliases - validation, alias, and serialization.
    """
    alias = self._generate_alias('alias', (str,), field_name)
    validation_alias = self._generate_alias('validation_alias', (str, AliasChoices, AliasPath), field_name)
    serialization_alias = self._generate_alias('serialization_alias', (str,), field_name)

    return alias, validation_alias, serialization_alias  # type: ignore

```
