from typing import List

from pydantic import BaseModel, parse_as_type

class Item(BaseModel):
    id: int
    name: str

# `item_data` could come from an API call, eg., via something like:
# >>> import requests
# >>> item_data = requests.get('https://my-api.com/items').json()
item_data = [{'id': 1, 'name': 'My Item'}]

items = parse_as_type(item_data, List[Item])
print(items)