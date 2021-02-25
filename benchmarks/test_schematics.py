from schematics import __version__
from schematics.exceptions import DataError, ValidationError
from schematics.models import Model as PModel
from schematics.types import IntType, StringType
from schematics.types.base import DateType, FloatType
from schematics.types.compound import ListType, ModelType


class TestSchematics:
    package = 'schematics'
    version = __version__

    def __init__(self, allow_extra):
        class Model(PModel):
            id = IntType(required=True)
            client_name = StringType(max_length=255, required=True)
            sort_index = FloatType(required=True)
            client_phone = StringType(max_length=255, default=None)

            class Location(PModel):
                latitude = FloatType(default=None)
                longitude = FloatType(default=None)

            location = ModelType(model_spec=Location, default=None)

            contractor = IntType(min_value=1, default=None)
            upstream_http_referrer = StringType(max_length=1023, default=None)
            grecaptcha_response = StringType(min_length=20, max_length=1000, required=True)
            last_updated = DateType(formats='%Y-%m-%dT%H:%M:%S')

            class Skill(PModel):
                subject = StringType(required=True)
                subject_id = IntType(required=True)
                category = StringType(required=True)
                qual_level = StringType(required=True)
                qual_level_id = IntType(required=True)
                qual_level_ranking = FloatType(default=0, required=True)

            skills = ListType(ModelType(Skill), default=[])

        self.model = Model

    def validate(self, data):
        try:
            obj = self.model(data)
            return True, obj.validate()
        except DataError as e:
            return False, e
        except ValidationError as e:
            return False, e
