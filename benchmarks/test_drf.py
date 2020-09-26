import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes']
)
django.setup()

from rest_framework import __version__, serializers


class TestDRF:
    package = 'django-rest-framework'
    version = __version__

    def __init__(self, allow_extra):
        class Model(serializers.Serializer):
            id = serializers.IntegerField()
            client_name = serializers.CharField(max_length=255, trim_whitespace=False)
            sort_index = serializers.FloatField()
            # client_email = serializers.EmailField(required=False, allow_null=True)
            client_phone = serializers.CharField(max_length=255, trim_whitespace=False, required=False, allow_null=True)

            class Location(serializers.Serializer):
                latitude = serializers.FloatField(required=False, allow_null=True)
                longitude = serializers.FloatField(required=False, allow_null=True)
            location = Location(required=False, allow_null=True)

            contractor = serializers.IntegerField(required=False, allow_null=True, min_value=0)
            upstream_http_referrer = serializers.CharField(
                max_length=1023, trim_whitespace=False, required=False, allow_null=True
            )
            grecaptcha_response = serializers.CharField(min_length=20, max_length=1000, trim_whitespace=False)
            last_updated = serializers.DateTimeField(required=False, allow_null=True)

            class Skill(serializers.Serializer):
                subject = serializers.CharField()
                subject_id = serializers.IntegerField()
                category = serializers.CharField()
                qual_level = serializers.CharField()
                qual_level_id = serializers.IntegerField()
                qual_level_ranking = serializers.FloatField(default=0)
            skills = serializers.ListField(child=Skill())

        self.allow_extra = allow_extra  # unused
        self.serializer = Model

    def validate(self, data):
        s = self.serializer(data=data)
        if s.is_valid():
            return True, dict(s.data)
        else:
            return False, dict(s.errors)
