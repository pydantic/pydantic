from pydantic_core import SchemaValidator, ValidationError

v = SchemaValidator(
    {
        'title': 'MyModel',
        'type': 'model',
        'fields': {
            'name': {'type': 'str'},
            'age': {'type': 'int-constrained', 'ge': 18},
            'is_developer': {'type': 'bool', 'default': True},
        },
    }
)
print(v)
"""
SchemaValidator(title="MyModel", validator=ModelValidator ...
"""

r1 = v.validate_python({'name': 'Samuel', 'age': 35})
print(r1)
"""
(
  {'name': 'Samuel', 'age': 35, 'is_developer': True}, <- validated data
  {'age', 'name'} <- fields set
)
"""

# pydantic-core can also validate JSON directly
r2 = v.validate_json('{"name": "Samuel", "age": 35}')
assert r1 == r2

try:
    v.validate_python({'name': 'Samuel', 'age': 11})
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    age
      Value must be greater than or equal to 18
      [kind=int_greater_than_equal, context={ge: 18}, input_value=11, input_type=int]
    """
