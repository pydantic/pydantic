from datetime import datetime
from typing import List, Optional

import attr
import cattr
from attr.validators import deep_iterable, instance_of, optional
from pydantic.datetime_parse import parse_datetime
from test_pydantic import TestPydantic


cattr.register_structure_hook(datetime, lambda o, t: parse_datetime(o))


# Handles optional fields
def structure_attrs_fromdict(obj, cl):
    # type: (Mapping, Type) -> Any
    """Instantiate an attrs class from a mapping (dict) that ignores unknown
    fields `cattr issue <https://github.com/Tinche/cattrs/issues/35>`_"""
    # For public use.

    # conv_obj = obj.copy()  # Dict of converted parameters.
    conv_obj = dict()  # Start fresh

    # dispatch = self._structure_func.dispatch
    dispatch = cattr.global_converter._structure_func.dispatch  # Ugly I know
    for a in cl.__attrs_attrs__:
        # We detect the type by metadata.
        type_ = a.type
        if type_ is None:
            # No type.
            continue
        name = a.name
        try:
            val = obj[name]
        except KeyError:
            continue
        if val is None:
            conv_obj[name] = val
        else:
            conv_obj[name] = dispatch(type_)(val, type_)
    return cl(**conv_obj)


def max_length(max_length: int):
    def validator(inst, attr, value):
        if len(value) > max_length:
            raise ValueError("Too long")

    return validator


def min_length(min_length: int):
    def validator(inst, attr, value):
        if len(value) < min_length:
            raise ValueError("Too short")

    return validator


def is_positive(inst, attr, value):
    if value <= 0:
        raise ValueError("Not positive")


class TestCattrs:
    package = 'cattrs'

    def __init__(self, allow_extra):
        @attr.dataclass
        class Location:
            latitude: Optional[float] = attr.ib(default=None, validator=optional(instance_of(float)))
            longitude: Optional[float] = attr.ib(default=None, validator=optional(instance_of(float)))

        @attr.dataclass
        class Skill:
            subject: str = attr.ib(validator=instance_of(str))
            subject_id: int = attr.ib(validator=instance_of(int))
            category: str = attr.ib(validator=instance_of(str))
            qual_level: str = attr.ib(validator=instance_of(str))
            qual_level_id: int = attr.ib(validator=instance_of(int))
            qual_level_ranking: float = attr.ib(default=0, validator=instance_of(float))

        @attr.dataclass
        class Model:
            id: int = attr.ib(validator=instance_of(int))
            client_name: str = attr.ib(validator=[instance_of(str), max_length(255)])
            sort_index: float = attr.ib(validator=instance_of(float))
            grecaptcha_response: str = attr.ib(validator=[instance_of(str), min_length(20), max_length(1000)])
            location: Optional[Location] = attr.ib(default=None, validator=optional(instance_of(Location)))
            contractor: Optional[int] = attr.ib(default=None, validator=optional([instance_of(int), is_positive]))
            upstream_http_referrer: Optional[str] = attr.ib(
                default=None,
                validator=optional([instance_of(str), max_length(1023)])
            )
            client_phone: Optional[str] = attr.ib(default=None, validator=optional([instance_of(str), max_length(255)]))
            last_updated: Optional[datetime] = attr.ib(default=None, validator=optional(instance_of(datetime)))
            skills: List[Skill] = attr.ib(
                factory=list,
                validator=deep_iterable(instance_of(Skill), iterable_validator=None)
            )

        if allow_extra:
            cattr.register_structure_hook(Model, structure_attrs_fromdict)
            cattr.register_structure_hook(Location, structure_attrs_fromdict)
            cattr.register_structure_hook(Skill, structure_attrs_fromdict)
        self.model = Model

    def validate(self, data):
        try:
            return True, cattr.structure(data, self.model)
        except ValueError as e:
            return False, str(e)
        except TypeError as e:
            return False, str(e)
