from datetime import datetime, timedelta
from pydantic import BaseModel
from pydantic.json import timedelta_isoformat


class CustomChildModel(BaseModel):
    dt: datetime
    diff: timedelta

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp(),
            timedelta: timedelta_isoformat,
        }


class ParentModel(BaseModel):
    diff: timedelta
    child: CustomChildModel

    class Config:
        json_encoders = {
            timedelta: lambda v: v.total_seconds(),
            CustomChildModel: lambda _: 'using parent encoder',
        }


child = CustomChildModel(dt=datetime(2032, 6, 1), diff=timedelta(hours=100))
parent = ParentModel(diff=timedelta(hours=3), child=child)

# default encoder uses total_seconds() for diff
print(parent.json())

# nested encoder uses isoformat
print(parent.json(use_nested_encoders=True))

# turning off models_as_dict only uses the top-level formatter, however

print(parent.json(models_as_dict=False, use_nested_encoders=True))

print(parent.json(models_as_dict=False, use_nested_encoders=False))
