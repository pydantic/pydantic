from pydantic import BaseModel, ValidationError
from pydantic.fields import ModelField
from typing import TypeVar, Generic

OldType = TypeVar('OldType')
GradeType = TypeVar('GradeType')

# This is not a pydantic model, it's an arbitrary generic class
class Assessment(Generic[OldType, GradeType]):
    def __init__(self, name: str, old: OldType, grade: GradeType):
        self.name = name
        self.old = old
        self.grade = grade

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    # You don't need to add the "ModelField", but it will help your
    # editor give you completion and catch errors
    def validate(cls, v, field: ModelField):
        if not isinstance(v, cls):
            # The value is not even an Assessment
            raise ValueError('Invalid value')
        if not field.sub_fields:
            # Generic parameters were not provided so we don't try to validate
            # them and just return the value as is
            return v
        sub_field_old = field.sub_fields[0]
        sub_field_grade = field.sub_fields[1]
        errors = []
        # Here we don't need the validated value, but we want the errors
        value_old, error = sub_field_old.validate(v.old, {}, loc='old')
        if error:
            errors.append(error)
        # Here we don't need the validated value, but we want the errors
        value_grade, error = sub_field_grade.validate(v.grade, {}, loc='grade')
        if error:
            errors.append(error)
        if errors:
            raise ValidationError(errors, cls)
        # Validation passed without errors, return the same instance received
        return v

class Model(BaseModel):
    student: Assessment[int, float]  # old is an int, grade a float
    cheese: Assessment[bool, str]  # old is a bool, grade a str
    thing: Assessment  # old is Any, grade is Any

model = Model(
    student=Assessment(name='Harry', old=15, grade=87),
    cheese=Assessment(name='Gouda', old=True, grade='Good'),
    thing=Assessment(name='Python', old='Nah', grade='Awesome')
    )
print(model)
print(model.student)
print(model.student.name)
print(model.student.old)
print(model.student.grade)
print(model.cheese)
print(model.cheese.name)
print(model.cheese.old)
print(model.cheese.grade)
print(model.thing)
print(model.thing.name)
print(model.thing.old)
print(model.thing.grade)
try:
    # If the values of the sub-types are invalid, we get an error
    Model(
        # For student, old should be an int, and grade a float
        student=Assessment(name='Harry', old=True, grade='Fail'),
        # For cheese, old should be a bool, and grade a str
        cheese=Assessment(name='Gouda', old='yeah', grade=5),
        # For thing, no type parameters are declared, and we skipped validation
        # in those cases in the Assessment.validate() function
        thing=Assessment(name='Python', old='Nah', grade='Awesome')
    )
except ValidationError as e:
    print(e)
