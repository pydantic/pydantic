from typing import Any

from pydantic._internal._generics import TypeVarType


class DeferredField:
    def __init__(self, bases: tuple[type[Any], ...], ann_name: str):
        self.bases = bases
        self.ann_name = ann_name
        self.substitutions: list[dict[TypeVarType, Any]] = []

    def replace_types(self, typevars_map: dict[TypeVarType, Any]) -> None:
        if typevars_map:
            self.substitutions.append(typevars_map)
