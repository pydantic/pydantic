from datetime import datetime
from typing import List, Optional

import attr

#
# Benchmark against attr. Slightly involved to get nested structuring without
# any third party library like cattrs
#


class TestAttr:
    package = 'attr'

    def __init__(self, allow_extra):

        def not_none(self, attribute, value):
            # Test that value is not None
            if value is None:
                raise ValueError()

        def str_len_val(max_len: int, min_len: int = 0, required: bool = False):
            # validate the max len of a string and optionally its min len and whether None is
            # an acceptable value
            def _check_str_len(self, attribute, value):
                if value is None:
                    if required:
                        raise ValueError("")
                    else:
                        return
                if len(value) > max_len:
                    raise ValueError("")
                if min_len and len(value) < min_len:
                    raise ValueError("")
            return _check_str_len

        def pos_int(self, attribute, value):
            # Validate that value is a positive >0 integer; None is allowed
            if value is None:
                return
            if value <= 0:
                raise ValueError("")

        def dtconv(ts):
            # Helper to convert strings to datettime
            return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S')

        def skill_list_converter(in_list):
            # helper to convert a list of Skills
            return [Skill(**skill) for skill in in_list]

        @attr.s(auto_attribs=True, frozen=True, kw_only=True)
        class Skill:
            subject: str = attr.ib(validator=not_none)
            subject_id: int = attr.ib(converter=int, validator=not_none)
            category: str = attr.ib(validator=not_none)
            qual_level: str = attr.ib(validator=not_none)
            qual_level_id: int = attr.ib(converter=int, validator=not_none)
            qual_level_ranking: float = attr.ib(converter=int, default=0)

        @attr.s(auto_attribs=True, frozen=True, kw_only=True)
        class Location:
            latitude: float = None
            longitude: float = None

        @attr.s(auto_attribs=True, frozen=True, kw_only=True)
        class Model:
            id: int = attr.ib(validator=not_none)
            sort_index: float = attr.ib(validator=not_none)
            client_name: str = attr.ib(validator=str_len_val(255, min_len=5, required=True))
            # client_email: EmailStr = None
            client_phone: Optional[str] = attr.ib(default=None, validator=str_len_val(255))
            location: Optional[Location] = None

            contractor: Optional[int] = attr.ib(default=None, validator=pos_int, convert=int)
            upstream_http_referrer: Optional[str] = attr.ib(default=None, validator=str_len_val(1023))
            grecaptcha_response: str = attr.ib(validator=str_len_val(1000, 20, required=True))
            last_updated: Optional[datetime] = attr.ib(default=None, converter=dtconv)
            skills: List[Skill] = attr.ib(default=[], convert=skill_list_converter)

        self.model = Model

    def validate(self, data):
        try:
            return True, self.model(**data)
        except Exception as e:
            return False, str(e)
