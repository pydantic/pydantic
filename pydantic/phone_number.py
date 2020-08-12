try:
    import phonenumbers
except ImportError as e:
    raise ImportError('phonenumbers is not installed, run `pip install phonenumbers`') from e


class PhoneNumber:
    def __init__(self, number):
        if not isinstance(number, phonenumbers.PhoneNumber):
            number = phonenumbers.parse(number)

        self._number: phonenumbers.PhoneNumber = number

    @classmethod
    def __get_validators__(cls):
        yield cls
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not isinstance(value, cls):
            value = cls(value)

        if not phonenumbers.is_valid_number(value):
            raise TypeError('Invalid Phone Number')

        return value

    @classmethod
    def __modify_schema__(cls, field_schema: dict):
        field_schema.update(
            type='string', example='+4 31 23 4567',
        )

    @property
    def formated(self):
        return phonenumbers.format_number(self._number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
