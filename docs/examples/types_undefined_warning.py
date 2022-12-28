from __future__ import annotations
from typing import Optional

from pydantic import BaseModel


# This example shows how Book uses the Person type and Person uses the Book type.
# We will demonstrate how to suppress the undefined types warning and define all the models.

class Book(BaseModel):
    title: str
    author: Person  # note the `Person` type is not yet defined
    
    # Suppress undefined types warning so we can continue defining our models.
    class Config:
        undefined_types_warning = False

class Person(BaseModel):
    name: str
    books_read: list[Book] | None = None

# Now, we can rebuild the `Book` model, since the `Person` model is now defined.
Book.model_rebuild()

# We'll not create some instances of our models, just to demonstrate that they work.
python_crash_course = Book(title='Python Crash Course', author=Person(name='Eric Matthes'))
jane_doe = Person(name='Jane Doe', books_read=[python_crash_course])

assert jane_doe.json(indent=2, exclude_unset=True) == """
{
  "name": "Jane Doe",
  "books_read": [
    {
      "title": "Python Crash Course",
      "author": {
        "name": "Eric Matthes"
      }
    }
  ]
}
""".strip()