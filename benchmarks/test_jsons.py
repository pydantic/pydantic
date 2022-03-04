from dataclasses import dataclass, field
from datetime import datetime
from dateutil.parser import parse
from typing import List, Optional

import jsons

jsons.set_deserializer(lambda dt, cls, **_: parse(dt), datetime)


class TestJsons:
    package = 'jsons'
    version = jsons.__version__

    def __init__(self, allow_extra):
        @dataclass
        class Model:
            # dataclass needs non-default fields first
            id: int
            sort_index: float
            grecaptcha_response: str
            client_name: str
            # client_email: EmailStr = None
            client_phone: Optional[str] = None

            def __post_init__(self):
                def check_length(s, max_length, min_length=0):
                    if not (s is None or min_length <= len(s) <= max_length):
                        raise ValueError
                check_length(self.client_name, 255)
                check_length(self.client_phone, 255)
                check_length(self.upstream_http_referrer, 1023)
                check_length(self.grecaptcha_response, 1000, 20)
                if not self.contractor > 0:
                    raise ValueError

            @dataclass
            class Location:
                latitude: Optional[float] = None
                longitude: Optional[float] = None

            location: Optional[Location] = None

            contractor: Optional[int] = None
            upstream_http_referrer: Optional[str] = None
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
        except (ValueError, jsons.exceptions.DeserializationError) as e:
            return False, e

    def to_json(self, model):
        return jsons.dump(model)
