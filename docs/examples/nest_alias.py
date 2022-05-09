from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(..., alias='request.user.name')


user = User.parse_obj({'request': {'user': {'name': 'aber'}, 'other_key': ''}})
print(user)
print(user.dict(by_alias=True))
