from pydantic import BaseModel
from typing import Any, Optional
from pydantic.utils import GetterDict
from xml.etree.ElementTree import fromstring


xmlstring = """
<User Id="2138">
    <FirstName />
    <LoggedIn Value="true" />
</User>
"""


class UserGetter(GetterDict):

    def get(self, key: str, default: Any) -> Any:

        # element attributes
        if key in {'Id', 'Status'}:
            return self._obj.attrib.get(key, default)

        # element children
        else:
            try:
                return self._obj.find(key).attrib['Value']
            except (AttributeError, KeyError):
                return default


class User(BaseModel):
    Id: int
    Status: Optional[str]
    FirstName: Optional[str]
    LastName: Optional[str]
    LoggedIn: bool

    class Config:
        orm_mode = True
        getter_dict = UserGetter


user = User.from_orm(fromstring(xmlstring))
