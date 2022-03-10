from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from dateutil.parser import parse
from typing import List, Optional

import jsons


class TestJsons:
    package = 'jsons'
    version = jsons.__version__

    def __init__(self, allow_extra):
        class Validated(ABC):
            @abstractmethod
            def validate(self):
                raise NotImplementedError

        class PositiveInt(int, Validated):
            def validate(self):
                return self > 0

        def constr_str(max_length, min_length=0):
            class ConstrStr(str, Validated):
                def validate(self):
                    return min_length <= len(self) <= max_length
            return ConstrStr

        jsons.set_validator(lambda v: v.validate(), Validated)
        jsons.set_deserializer(lambda v, cls, **_: cls(v), Validated)
        jsons.set_deserializer(lambda dt, cls, **_: parse(dt), datetime)

        @dataclass
        class Model:
            # dataclass needs non-default fields first
            id: int
            sort_index: float
            grecaptcha_response: constr_str(1000, 20)
            client_name: constr_str(255)
            # client_email: EmailStr = None
            client_phone: Optional[constr_str(255)] = None

            @dataclass
            class Location:
                latitude: Optional[float] = None
                longitude: Optional[float] = None

            location: Optional[Location] = None

            contractor: Optional[PositiveInt] = None
            upstream_http_referrer: Optional[constr_str(1023)] = None
            last_updated: Optional[datetime] = None

            @dataclass
            class Skill:
                subject: str
                subject_id: int
                category: str
                qual_level: str
                qual_level_id: int
                qual_level_ranking: float = 0

            skills: List[Skill] = field(default_factory=list)

        self.allow_extra = allow_extra  # unused
        self.model = Model

    def validate(self, data):
        try:
            return True, jsons.load(data, self.model)
        except (jsons.exceptions.DeserializationError, jsons.exceptions.ValidationError) as e:
            return False, e

    def to_json(self, model):
        return jsons.dump(model)
