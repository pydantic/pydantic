import django
from django.conf import settings


django.setup()

import drf_turbo as dt

class TestDT:
    package = 'drf-turbo'
    version = dt.__version__

    def __init__(self, allow_extra):
        class Model(dt.Serializer):
            id = dt.IntField()
            client_name = dt.StrField(max_length=255, trim_whitespace=False)
            sort_index = dt.FloatField()
            # client_email = dt.EmailField(required=False, allow_null=True)
            client_phone = dt.StrField(max_length=255, trim_whitespace=False, required=False, allow_null=True)

            class Location(dt.Serializer):
                latitude = dt.FloatField(required=False, allow_null=True)
                longitude = dt.FloatField(required=False, allow_null=True)
            location = Location(required=False, allow_null=True)

            contractor = dt.IntField(required=False, allow_null=True, min_value=0)
            upstream_http_referrer = dt.StrField(
                max_length=1023, trim_whitespace=False, required=False, allow_null=True
            )
            grecaptcha_response = dt.StrField(min_length=20, max_length=1000, trim_whitespace=False)
            last_updated = dt.DateTimeField(required=False, allow_null=True)

            class Skill(dt.Serializer):
                subject = dt.StrField()
                subject_id = dt.IntField()
                category = dt.StrField()
                qual_level = dt.StrField()
                qual_level_id = dt.IntField()
                qual_level_ranking = dt.FloatField(default_value=0)
            skills = dt.ArrayField(child=Skill())

        self.allow_extra = allow_extra  # unused
        self.serializer = Model

    def validate(self, data):
        s = self.serializer(data=data)
        if s.is_valid():
            return True, dict(s.data)
        else:
            return False, dict(s.errors)
