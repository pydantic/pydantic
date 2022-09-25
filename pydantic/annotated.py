from dataclasses import dataclass


class PydanticAnnotation:
    __slots__ = ()


@dataclass
class Strict(PydanticAnnotation):
    strict: bool = True
