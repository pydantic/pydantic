from __future__ import annotations

from pydantic import BaseModel


# This example shows how Book and Person types reference each other.
# We will demonstrate how to suppress the undefined types warning
# when define such models.


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

# Let's create some instances of our models, to demonstrate that they work.
python_crash_course = Book(
    title='Python Crash Course',
    author=Person(name='Eric Matthes'),
)
jane_doe = Person(name='Jane Doe', books_read=[python_crash_course])

assert jane_doe.dict(exclude_unset=True) == {
    'name': 'Jane Doe',
    'books_read': [
        {
            'title': 'Python Crash Course',
            'author': {'name': 'Eric Matthes'},
        },
    ],
}
