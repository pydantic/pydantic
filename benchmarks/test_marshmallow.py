from marshmallow import Schema, ValidationError, __version__, fields, validate


class TestMarshmallow:
    package = 'marshmallow'
    version = __version__

    def __init__(self, allow_extra):
        class LocationSchema(Schema):
            latitude = fields.Float(allow_none=True)
            longitude = fields.Float(allow_none=True)

        class SkillSchema(Schema):
            subject = fields.Str(required=True)
            subject_id = fields.Integer(required=True)
            category = fields.Str(required=True)
            qual_level = fields.Str(required=True)
            qual_level_id = fields.Integer(required=True)
            qual_level_ranking = fields.Float(default=0)

        class Model(Schema):
            id = fields.Integer(required=True)
            client_name = fields.Str(validate=validate.Length(max=255), required=True)
            sort_index = fields.Float(required=True)
            # client_email = fields.Email()
            client_phone = fields.Str(validate=validate.Length(max=255), allow_none=True)

            location = fields.Nested(LocationSchema)

            contractor = fields.Integer(validate=validate.Range(min=0), allow_none=True)
            upstream_http_referrer = fields.Str(validate=validate.Length(max=1023), allow_none=True)
            grecaptcha_response = fields.Str(validate=validate.Length(min=20, max=1000), required=True)
            last_updated = fields.DateTime(allow_none=True)
            skills = fields.Nested(SkillSchema, many=True)

        self.allow_extra = allow_extra  # unused
        self.schema = Model()

    def validate(self, data):
        try:
            result = self.schema.load(data)
        except ValidationError as e:
            return False, e.normalized_messages()
        else:
            return True, result
