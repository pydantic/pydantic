Pydantic serves as a great tool for defining models for ORM (object relational mapping) libraries.
ORMs are used to map objects to database tables, and vice versa.

Pydantic allows you to create models from arbitrary class instances (like ORM objects) by setting `from_attributes=True` in the model configuration.

## SQLAlchemy

Pydantic works seamlessly with SQLAlchemy to define schemas for your database models.

!!! warning "Code Duplication"
    If you use Pydantic with SQLAlchemy, you might experience some frustration with code duplication (defining the schema in both SQLAlchemy and Pydantic).
    If this is a concern, you might also consider [`SQLModel`](https://sqlmodel.tiangolo.com/), which integrates Pydantic with SQLAlchemy such that much of the code duplication is eliminated.

### Basic Usage with Relationships

You can use Pydantic to validate and serialize SQLAlchemy models, including nested relationships.

```python
from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel, ConfigDict

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    author = relationship("User", back_populates="posts")

class PostBase(BaseModel):
    title: str

class PostSchema(PostBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    posts: List[PostSchema] = []

# Example Usage
user = User(id=1, name="John Doe")
post = Post(id=1, title="Hello World", author=user)

user_schema = UserSchema.model_validate(user)
print(user_schema.model_dump())
#> {'id': 1, 'name': 'John Doe', 'posts': [{'title': 'Hello World', 'id': 1}]}
```

### Handling Field Conflicts with Aliases

Sometimes ORM fields conflict with Pydantic or Python reserved words. You can use Pydantic's aliases to resolve this.

In the example below, we name a `Column` `metadata_` to avoid conflict with the reserved `metadata` attribute in SQLAlchemy, but we map it back to `metadata` in the Pydantic model using an alias.

```python
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, ConfigDict, Field

class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metadata: dict[str, str] = Field(alias='metadata_')

Base = declarative_base()

class MyTableModel(Base):
    __tablename__ = 'my_table'
    id = sa.Column('id', sa.Integer, primary_key=True)
    # 'metadata' is reserved by SQLAlchemy, hence the '_'
    metadata_ = sa.Column('metadata', sa.JSON)

sql_model = MyTableModel(metadata_={'key': 'val'}, id=1)
pydantic_model = MyModel.model_validate(sql_model)

print(pydantic_model.model_dump())
#> {'metadata': {'key': 'val'}}
print(pydantic_model.model_dump(by_alias=True))
#> {'metadata_': {'key': 'val'}}
```

!!! note
    The example above works because aliases have priority over field names for
    field population. Accessing `SQLModel`'s `metadata` attribute would lead to a `ValidationError`.

## Django

Pydantic can be used to validate Django models, which is particularly useful for creating API schemas or exporting data.

```python
# Note: usage of Django requires setup (settings.configure) not shown here
from django.db import models
from pydantic import BaseModel, ConfigDict

class DjangoUser(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()

    class Meta:
        app_label = 'auth'

class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    email: str

# Creating a dummy Django object for demonstration
django_user = DjangoUser(username='user1', email='user@example.com')

pydantic_user = UserSchema.model_validate(django_user)
print(pydantic_user.model_dump())
#> {'username': 'user1', 'email': 'user@example.com'}
```

## Peewee

Here is an example using Peewee ORM.

```python
import peewee
from pydantic import BaseModel, ConfigDict

db = peewee.SqliteDatabase(":memory:")

class Person(peewee.Model):
    name = peewee.CharField()
    age = peewee.IntegerField()

    class Meta:
        database = db

class PersonSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    age: int

db.connect()
db.create_tables([Person])

person = Person.create(name="Jane", age=25)
schema = PersonSchema.model_validate(person)

print(schema.model_dump())
#> {'id': 1, 'name': 'Jane', 'age': 25}
```

## Performance Warning: The "N+1" Problem

!!! warning "Lazy Loading & Performance"
    When you set `from_attributes=True`, Pydantic will access the attributes of your ORM object to validate them.
    
    For simple fields, this is efficient. However, accessing related fields (like `user.posts` in the SQLAlchemy example above) often triggers **lazy loading** (executing a separate database query) if the data wasn't pre-fetched.
    
    If you convert a list of 100 users to Pydantic models, and each user validates their posts list, your ORM might execute 100 extra database queries (one per user). This is known as the **N+1 problem**.
    
    **Solution:** Always use your ORM's "eager loading" features (e.g., `joinedload` in SQLAlchemy, `select_related`/`prefetch_related` in Django) to fetch all necessary data in a single query before passing objects to Pydantic.
