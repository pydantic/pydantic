from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import serpyco
from serpyco import string_field, number_field, ValidationError, nested_field, post_dump, pre_load, post_load
from serpyco.serializer import Serializer, DateTimeFieldEncoder

from pydantic import Extra


class TestSerpyco:
    package = "serpyco"
    version = "unknown"

    def __init__(self, allow_extra):
        @dataclass
        class Skill:
            subject: str
            subject_id: int
            category: str
            qual_level: str
            qual_level_id: int
            qual_level_ranking: float = 0

        @dataclass
        class Location:
            latitude: float = None
            longitude: float = None

        @dataclass
        class Model:
            id: int
            sort_index: float
            # client_email: EmailStr = None

            location: Location
            skills: List[Skill]
            last_updated: datetime
            grecaptcha_response: str = string_field(min_length=20, max_length=1000)
            contractor: int = number_field(minimum=0)
            client_name: str = string_field(max_length=255)
            upstream_http_referrer: Optional[str] = string_field(max_length=1023, default=None)

            client_phone: Optional[str] = string_field(max_length=255, default=None)

            extra: str = string_field(default=Extra.allow if allow_extra else Extra.forbid)

            @pre_load
            def _pre_load(data: dict) -> dict:
                data["contractor"] = int(data["contractor"])

                try:
                    data["last_updated"] = datetime.strptime(data["last_updated"], '%Y-%m-%dT%H:%M:%S')
                    data["last_updated"] = data["last_updated"].isoformat()
                except (ValueError, KeyError) as e:
                    raise ValidationError(e)

                return data

        self.model = Model

    def validate(self, data):
        try:
            serializer = Serializer(self.model)
            return True, serializer.load(data)
        except (ValidationError, TypeError) as e:
            return False, e

    def to_json(self, model):
        serializer = Serializer(self.model)
        return serializer.dump(model)
