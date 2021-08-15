import related

from test_cattrs import TestCAttrs


class TestRelated:
    """
    Tests the performance of related.
    related is based on attrs and is an alternative take than cattrs.
    """
    package = 'related'
    version = related.__version__

    def __init__(self, allow_extra):
        def str_len_val(value, max_len: int, min_len: int = 0, required: bool = False):
            if value is None:
                if required:
                    raise ValueError("")
                else:
                    return
            if len(value) > max_len:
                raise ValueError("")
            if min_len and len(value) < min_len:
                raise ValueError("")

        def pos_int(i):
            if not isinstance(i, int):
                raise ValueError()
            if i <= 0:
                raise ValueError()
            return i

        @related.immutable(strict=True)
        class Skill:
            subject = related.StringField()
            subject_id = related.IntegerField()
            category = related.StringField()
            qual_level = related.StringField()
            qual_level_id = related.IntegerField()
            qual_level_ranking = related.FloatField(default=0)

        @related.immutable(strict=True)
        class Location:
            latitude: float = related.FloatField(default=None)
            longitude: float = related.FloatField(default=None)

        @related.immutable(strict=True)
        class Model:
            id = related.IntegerField()
            sort_index = related.FloatField()
            client_name = related.StringField()
            grecaptcha_response = related.StringField()
            client_phone = related.StringField(required=False)
            location = related.ChildField(cls=Location, required=False)

            contractor = related.IntegerField(required=False)
            upstream_http_referrer = related.StringField(required=False)
            last_updated = related.DateTimeField(required=False)
            skills = related.SequenceField(cls=Skill, default=[])

            def __attrs_post_init__(self):
                # Validate client_name
                str_len_val(self.client_name, 255)

                # Validate captcha
                str_len_val(self.grecaptcha_response, 1000, 20, required=True)

                # Validate phone
                str_len_val(self.client_phone, 255)

                # Validate http referrer
                str_len_val(self.upstream_http_referrer, 1023)

                # Validate contractor
                pos_int(self.contractor)


        self.model = Model

    def validate(self, data):
        try:
            return True, related.to_model(self.model, data)
        except (ValueError, TypeError, KeyError) as e:
            # print(str(e))
            return False, str(e)
