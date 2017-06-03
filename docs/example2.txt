UserModel(signup_ts='broken') >
pydantic.exceptions.ValidationError: 2 errors validating input
user_id:
  field required (error_type=Missing)
signup_ts:
  Invalid datetime format (error_type=ValueError track=datetime)
