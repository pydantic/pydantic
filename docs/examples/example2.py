from pydantic import ValidationError
try:
    User(signup_ts='broken', friends=[1, 2, 'not number'])
except ValidationError as e:
    print(e.json())

"""
{
  "friends": [
    {
      "error_msg": "invalid literal for int() with base 10: 'not number'",
      "error_type": "ValueError",
      "index": 2,
      "track": "int"
    }
  ],
  "id": {
    "error_msg": "field required",
    "error_type": "Missing"
  },
  "signup_ts": {
    "error_msg": "Invalid datetime format",
    "error_type": "ValueError",
    "track": "datetime"
  }
}
"""
