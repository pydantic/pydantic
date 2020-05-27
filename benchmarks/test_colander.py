import pkg_resources
import colander as c


class TestColander:
    package = "colander"
    version = pkg_resources.get_distribution(package).version

    def __init__(self, allow_extra):
        class LocationSchema(c.MappingSchema):
            latitude = c.SchemaNode(c.Float(), missing=None)
            longitude = c.SchemaNode(c.Float(), missing=None)

        class SkillSchema(c.MappingSchema):
            subject = c.SchemaNode(c.Str())
            subject_id = c.SchemaNode(c.Int())
            category = c.SchemaNode(c.Str())
            qual_level = c.SchemaNode(c.Str())
            qual_level_id = c.SchemaNode(c.Int())
            qual_level_ranking = c.SchemaNode(c.Float(), missing=0)

        class SkillsSchema(c.SequenceSchema):
            skill = SkillSchema()

        class Model(c.MappingSchema):
            id = c.SchemaNode(c.Int())
            client_name = c.SchemaNode(c.Str(), validator=c.Length(max=255))
            sort_index = c.SchemaNode(c.Float())
            # client_email = fields.Email()
            client_phone = c.SchemaNode(
                c.Str(), validator=c.Length(max=255), missing=None
            )
            location = LocationSchema()
            contractor = c.SchemaNode(c.Int(), validator=c.Range(min=0), missing=None)
            upstream_http_referrer = c.SchemaNode(
                c.Str(), validator=c.Length(max=1023), missing=None
            )
            grecaptcha_response = c.SchemaNode(
                c.Str(), validator=c.Length(min=20, max=1000)
            )
            last_updated = c.SchemaNode(
                c.DateTime(format="%Y-%m-%dT%H:%M:%S"), missing=None
            )
            skills = SkillsSchema()

        self.allow_extra = allow_extra  # unused
        self.schema = Model()

    def validate(self, data):
        try:
            result = self.schema.deserialize(data)
        except c.Invalid as e:
            return False, e.asdict()
        else:
            return True, result
