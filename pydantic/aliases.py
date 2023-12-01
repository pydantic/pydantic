"""Support for alias configurations."""
from __future__ import annotations

import dataclasses
from typing import Callable

from ._internal import _internal_dataclass

__all__ = ('AliasGenerator', 'AliasPath', 'AliasChoices')


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class AliasGenerator:
    """Usage docs: https://docs.pydantic.dev/2.6/concepts/alias#alias-generator

    A data class used by `alias_generator` as a convenience to create various aliases.

    Attributes:
        validation_alias: A callable that takes a field name and returns a validation alias for it.
        alias: A callable that takes a field name and returns an alias for it.
        serialization_alias: A callable that takes a field name and returns a serialization alias for it.
    """

    validation_alias: Callable[[str], str | AliasPath | AliasChoices] | None = None
    alias: Callable[[str], str] | None = None
    serialization_alias: Callable[[str], str] | None = None

    def __init__(
        self,
        alias: Callable[[str], str] | None = None,
        *,
        validation_alias: Callable[[str], str | AliasPath | AliasChoices] | None = None,
        serialization_alias: Callable[[str], str] | None = None,
    ) -> None:
        """Initialize the alias generator."""
        self.validation_alias = validation_alias
        self.alias = alias
        self.serialization_alias = serialization_alias

    def __call__(
        self, field_name: str
    ) -> tuple[str | list[str | int] | list[list[str | int]] | None, str | None, str | None]:
        """Generate aliases for validation, serialization, and alias.

        Returns:
            A tuple of three aliases - validation, alias, and serialization.
        """
        validation_alias, alias, serialization_alias = None, None, None

        if self.validation_alias is not None:
            validation_alias = self.validation_alias(field_name)
            if validation_alias:
                if not isinstance(validation_alias, (str, AliasChoices, AliasPath)):
                    raise TypeError(
                        'Invalid `validation_alias` type. `validation_alias_generator` must produce'
                        'a `validation_alias` of type `str`, `AliasChoices`, or `AliasPath`'
                    )
                if isinstance(validation_alias, (AliasChoices, AliasPath)):
                    validation_alias = validation_alias.convert_to_aliases()
        if self.serialization_alias is not None:
            serialization_alias = self.serialization_alias(field_name)
            if serialization_alias and not isinstance(serialization_alias, str):
                raise TypeError(
                    'Invalid `serialization_alias` type. `serialization_alias_generator` must produce'
                    'a `serialization_alias` of type `str`'
                )
        if self.alias is not None:
            alias = self.alias(field_name)
            if alias and not isinstance(alias, str):
                raise TypeError('Invalid `alias` type. `alias_generator` must produce a `alias` of type `str`')

        return validation_alias, alias, serialization_alias


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class AliasPath:
    """Usage docs: https://docs.pydantic.dev/2.6/concepts/fields#aliaspath-and-aliaschoices

    A data class used by `validation_alias` as a convenience to create aliases.

    Attributes:
        path: A list of string or integer aliases.
    """

    path: list[int | str]

    def __init__(self, first_arg: str, *args: str | int) -> None:
        self.path = [first_arg] + list(args)

    def convert_to_aliases(self) -> list[str | int]:
        """Converts arguments to a list of string or integer aliases.

        Returns:
            The list of aliases.
        """
        return self.path


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class AliasChoices:
    """Usage docs: https://docs.pydantic.dev/2.6/concepts/fields#aliaspath-and-aliaschoices

    A data class used by `validation_alias` as a convenience to create aliases.

    Attributes:
        choices: A list containing a string or `AliasPath`.
    """

    choices: list[str | AliasPath]

    def __init__(self, first_choice: str | AliasPath, *choices: str | AliasPath) -> None:
        self.choices = [first_choice] + list(choices)

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
