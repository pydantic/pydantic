from dataclasses import Field, MISSING, dataclass, field, is_dataclass
from datetime import datetime
from typing import Any, Dict, List, NewType, Optional, Type

import apischema
import importlib_metadata
from apischema import (ValidationError, field_input_converter, from_data,
                       schema, with_fields_set)

PositiveInt = NewType("PositiveInt", int)
schema(exc_min=0)(PositiveInt)


def coerce_contractor(s: str) -> PositiveInt:
    try:
        contractor = int(s)
    except ValueError:
        yield "contractor expected str"
    else:
        if contractor <= 0:
            yield "contractor < 0"
        return PositiveInt(contractor)


# Defined on top level in order to be able to evaluate annotations (see PEP 563)
# `apischema.set_type_hints` could be used instead, but I don't like it
@dataclass
class Location:
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class Skill:
    subject: str
    subject_id: int
    category: str
    qual_level: str
    qual_level_id: int
    qual_level_ranking: float = 0


@with_fields_set
@dataclass
class Model:
    id: int
    client_name: str = field(metadata=schema(max_len=255))
    sort_index: float
    # must be before fields with default value
    grecaptcha_response: str = field(metadata=schema(min_len=20, max_len=1000))
    client_phone: Optional[str] = field(default=None, metadata=schema(max_len=255))

    location: Optional[Location] = None

    # cannot use PositiveInt because of coercion
    # contractor: Optional[PositiveInt] = None
    contractor: Optional[PositiveInt] = field(
        default=None, metadata=field_input_converter(coerce_contractor)
    )
    upstream_http_referrer: Optional[str] = field(default=None,
                                                  metadata=schema(max_len=1023))
    last_updated: Optional[datetime] = None

    skills: List[Skill] = field(default_factory=list)


class TestApischema:
    package = apischema.__name__
    version = importlib_metadata.version("apischema")

    def __init__(self, allow_extra):
        self.allow_extra = allow_extra
        self.cls = Model

    def validate(self, data):
        try:
            result = from_data(data, self.cls, additional_properties=self.allow_extra)
        except ValidationError as e:
            return False, e
        else:
            return True, result


from apischema.alias import ALIAS_METADATA
from apischema.conversion import INPUT_METADATA
from apischema.data.from_data import (DataWithConstraint, FromData, check_type,
                                      apply_converter)
from apischema.fields import init_fields
from apischema.schema import CONSTRAINT_METADATA
from apischema.typing import get_type_hints
from apischema.utils import PREFIX
from apischema.validation.errors import exception, merge
from apischema.validation.mock import ValidatorMock
from apischema.validation.validator import Validator, get_validators, validate

FIELDS_CACHE = f"{PREFIX}fields"


class OptimizedFromData(FromData):
    def dataclass(self, cls: Type, data2: DataWithConstraint):
        assert is_dataclass(cls)
        data, constraint = data2
        check_type(data, dict)
        types = get_type_hints(cls)
        values: Dict[str, Any] = {}
        default: Dict[str, Field] = {}
        aliases: List[str] = []
        field_errors: Dict[str, ValidationError] = {}
        try:
            fields = getattr(cls, FIELDS_CACHE)
        except AttributeError:
            fields = tuple(init_fields(cls))
            setattr(cls, FIELDS_CACHE, fields)
        for field in fields:
            assert isinstance(field, Field)
            name = field.name
            metadata = field.metadata
            if ALIAS_METADATA in metadata:
                alias = metadata[ALIAS_METADATA]
            else:
                alias = name
            if alias in data:
                if CONSTRAINT_METADATA in metadata:
                    to_visit = data[alias], metadata[CONSTRAINT_METADATA]
                else:
                    to_visit = data[alias], None
                try:
                    if INPUT_METADATA in metadata:
                        param, converter = field.metadata[INPUT_METADATA]
                        tmp = self.visit(param, to_visit)
                        values[name] = apply_converter(tmp, converter)
                    else:
                        values[name] = self.visit(types[name], to_visit)
                except ValidationError as err:
                    field_errors[alias] = err
                aliases.append(alias)
            elif (field.default is not MISSING
                  or field.default_factory is not MISSING):
                default[name] = field
                aliases.append(alias)
            else:
                field_errors[alias] = ValidationError(["missing field"])
        if len(data) != len(aliases) and not self.additional_properties:
            remain = set(data).difference(aliases)
            field_errors.update((field, ValidationError(["field not allowed"]))
                                for field in sorted(remain))
        if field_errors:
            error = ValidationError(children=field_errors)
            partial: List[Validator] = []
            whole: List[Validator] = []
            for val in get_validators(cls):
                if val.can_be_called(values.keys()):
                    partial.append(val)
                else:
                    whole.append(val)
            try:
                validate(ValidatorMock(cls, values, default), partial)
            except ValidationError as err:
                error = merge(error, err)
            raise error
        validators = get_validators(cls)
        try:
            res = cls(**values)
        except Exception as err:
            raise ValidationError([exception(err)])
        validate(res, validators)
        return res


class TestApischemaOptimized(TestApischema):
    package = "apischema (optimized)"

    def validate(self, data):
        visitor = OptimizedFromData(self.allow_extra)
        try:
            return True, visitor.visit(self.cls, (data, None))
        except ValidationError as e:
            return False, e
