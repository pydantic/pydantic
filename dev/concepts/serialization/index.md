Beyond accessing model attributes directly via their field names (e.g. `model.foobar`), models can be converted, dumped, serialized, and exported in a number of ways. Serialization can be customized for the whole model, or on a per-field or per-type basis.

Serialize versus dump

Pydantic uses the terms "serialize" and "dump" interchangeably. Both refer to the process of converting a model to a dictionary or JSON-encoded string.

Outside of Pydantic, the word "serialize" usually refers to converting in-memory data into a string or bytes. However, in the context of Pydantic, there is a very close relationship between converting an object from a more structured form — such as a Pydantic model, a dataclass, etc. — into a less structured form comprised of Python built-ins such as dict.

While we could (and on occasion, do) distinguish between these scenarios by using the word "dump" when converting to primitives and "serialize" when converting to string, for practical purposes, we frequently use the word "serialize" to refer to both of these situations, even though it does not always imply conversion to a string or bytes.

Tip

Want to quickly jump to the relevant serializer section?

- Field serializer

  ______________________________________________________________________

  - [field *plain* serializer](#field-plain-serializer)
  - [field *wrap* serializer](#field-wrap-serializer)

- Model serializer

  ______________________________________________________________________

  - [model *plain* serializer](#model-plain-serializer)
  - [model *wrap* serializer](#model-wrap-serializer)

## Serializing data

Pydantic allows models (and any other type using [type adapters](../type_adapter/)) to be serialized in *two* modes: [Python](#python-mode) and [JSON](#json-mode). The Python output may contain non-JSON serializable data (although this can be emulated).

### Python mode

When using the Python mode, Pydantic models (and model-like types such as dataclasses) (1) will be (recursively) converted to dictionaries. This is achievable by using the model_dump() method:

1. With the exception of [root models](../models/#rootmodel-and-custom-root-types), where the root value is dumped directly.

```python
from typing import Optional

from pydantic import BaseModel, Field


class BarModel(BaseModel):
    whatever: tuple[int, ...]


class FooBarModel(BaseModel):
    banana: Optional[float] = 1.1
    foo: str = Field(serialization_alias='foo_alias')
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': (1, 2)})

# returns a dictionary:
print(m.model_dump())
#> {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': (1, 2)}}

print(m.model_dump(by_alias=True))
#> {'banana': 3.14, 'foo_alias': 'hello', 'bar': {'whatever': (1, 2)}}

```

```python
from pydantic import BaseModel, Field


class BarModel(BaseModel):
    whatever: tuple[int, ...]


class FooBarModel(BaseModel):
    banana: float | None = 1.1
    foo: str = Field(serialization_alias='foo_alias')
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': (1, 2)})

# returns a dictionary:
print(m.model_dump())
#> {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': (1, 2)}}

print(m.model_dump(by_alias=True))
#> {'banana': 3.14, 'foo_alias': 'hello', 'bar': {'whatever': (1, 2)}}

```

Notice that the value of `whatever` was dumped as tuple, which isn't a known JSON type. The `mode` argument can be set to `'json'` to ensure JSON-compatible types are used:

```python
print(m.model_dump(mode='json'))
#> {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': [1, 2]}}

```

See also

The TypeAdapter.dump_python() method, useful when *not* dealing with Pydantic models.

### JSON mode

Pydantic allows data to be serialized directly to a JSON-encoded string, by trying its best to convert Python values to valid JSON data. This is achievable by using the model_dump_json() method:

```python
from datetime import datetime

from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: tuple[int, ...]


class FooBarModel(BaseModel):
    foo: datetime
    bar: BarModel


m = FooBarModel(foo=datetime(2032, 6, 1, 12, 13, 14), bar={'whatever': (1, 2)})

print(m.model_dump_json(indent=2))
"""
{
  "foo": "2032-06-01T12:13:14",
  "bar": {
    "whatever": [
      1,
      2
    ]
  }
}
"""

```

In addition to the supported types by the standard library json module, Pydantic supports a wide variety of types (date and time types, UUID objects, sets, etc). If an unsupported type is used and can't be serialized to JSON, a PydanticSerializationError exception is raised.

See also

The TypeAdapter.dump_json() method, useful when *not* dealing with Pydantic models.

## Iterating over models

Pydantic models can also be iterated over, yielding `(field_name, field_value)` pairs. Note that field values are left as is, so sub-models will *not* be converted to dictionaries:

```python
from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

for name, value in m:
    print(f'{name}: {value}')
    #> banana: 3.14
    #> foo: hello
    #> bar: whatever=123

```

This means that calling dict() on a model can be used to construct a dictionary of the model:

```python
print(dict(m))
#> {'banana': 3.14, 'foo': 'hello', 'bar': BarModel(whatever=123)}

```

Note

[Root models](../models/#rootmodel-and-custom-root-types) *does* get converted to a dictionary with the key `'root'`.

## Pickling support

Pydantic models support efficient pickling and unpickling.

```python
import pickle

from pydantic import BaseModel


class FooBarModel(BaseModel):
    a: str
    b: int


m = FooBarModel(a='hello', b=123)
print(m)
#> a='hello' b=123
data = pickle.dumps(m)
print(data[:20])
#> b'\x80\x04\x95\x95\x00\x00\x00\x00\x00\x00\x00\x8c\x08__main_'
m2 = pickle.loads(data)
print(m2)
#> a='hello' b=123

```

## Serializers

Similar to [custom validators](../validators/), you can leverage custom serializers at the field and model levels to further control the serialization behavior.

Warning

Only *one* serializer can be defined per field/model. It is not possible to combine multiple serializers together (including *plain* and *wrap* serializers).

### Field serializers

API Documentation

pydantic.functional_serializers.PlainSerializer\
pydantic.functional_serializers.WrapSerializer\
pydantic.functional_serializers.field_serializer

In its simplest form, a field serializer is a callable taking the value to be serialized as an argument and **returning the serialized value**.

If the `return_type` argument is provided to the serializer (or if a return type annotation is available on the serializer function), it will be used to build an extra serializer, to ensure that the serialized field value complies with this return type.

**Two** different types of serializers can be used. They can all be defined using the [annotated pattern](../fields/#the-annotated-pattern) or using the @field_serializer decorator, applied on instance or static methods.

- ***Plain* serializers**: are called unconditionally to serialize a field. The serialization logic for types supported by Pydantic will *not* be called. Using such serializers is also useful to specify the logic for arbitrary types.

  ```python
  from typing import Annotated, Any

  from pydantic import BaseModel, PlainSerializer


  def ser_number(value: Any) -> Any:
      if isinstance(value, int):
          return value * 2
      else:
          return value


  class Model(BaseModel):
      number: Annotated[int, PlainSerializer(ser_number)]


  print(Model(number=4).model_dump())
  #> {'number': 8}
  m = Model(number=1)
  m.number = 'invalid'
  print(m.model_dump())  # (1)!
  #> {'number': 'invalid'}

  ```

  1. Pydantic will *not* validate that the serialized value complies with the `int` type.

  ```python
  from typing import Any

  from pydantic import BaseModel, field_serializer


  class Model(BaseModel):
      number: int

      @field_serializer('number', mode='plain')  # (1)!
      def ser_number(self, value: Any) -> Any:
          if isinstance(value, int):
              return value * 2
          else:
              return value


  print(Model(number=4).model_dump())
  #> {'number': 8}
  m = Model(number=1)
  m.number = 'invalid'
  print(m.model_dump())  # (2)!
  #> {'number': 'invalid'}

  ```

  1. `'plain'` is the default mode for the decorator, and can be omitted.
  1. Pydantic will *not* validate that the serialized value complies with the `int` type.

- ***Wrap* serializers**: give more flexibility to customize the serialization behavior. You can run code before or after the Pydantic serialization logic.

  Such serializers must be defined with a **mandatory** extra *handler* parameter: a callable taking the value to be serialized as an argument. Internally, this handler will delegate serialization of the value to Pydantic. You are free to *not* call the handler at all.

  ```python
  from typing import Annotated, Any

  from pydantic import BaseModel, SerializerFunctionWrapHandler, WrapSerializer


  def ser_number(value: Any, handler: SerializerFunctionWrapHandler) -> int:
      return handler(value) + 1


  class Model(BaseModel):
      number: Annotated[int, WrapSerializer(ser_number)]


  print(Model(number=4).model_dump())
  #> {'number': 5}

  ```

  ```python
  from typing import Any

  from pydantic import BaseModel, SerializerFunctionWrapHandler, field_serializer


  class Model(BaseModel):
      number: int

      @field_serializer('number', mode='wrap')
      def ser_number(
          self, value: Any, handler: SerializerFunctionWrapHandler
      ) -> int:
          return handler(value) + 1


  print(Model(number=4).model_dump())
  #> {'number': 5}

  ```

#### Which serializer pattern to use

While both approaches can achieve the same thing, each pattern provides different benefits.

##### Using the annotated pattern

One of the key benefits of using the [annotated pattern](../fields/#the-annotated-pattern) is to make serializers reusable:

```python
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer

DoubleNumber = Annotated[int, PlainSerializer(lambda v: v * 2)]


class Model1(BaseModel):
    my_number: DoubleNumber


class Model2(BaseModel):
    other_number: Annotated[DoubleNumber, Field(description='My other number')]


class Model3(BaseModel):
    list_of_even_numbers: list[DoubleNumber]  # (1)!

```

1. As mentioned in the [annotated pattern](../fields/#the-annotated-pattern) documentation, we can also make use of serializers for specific parts of the annotation (in this case, serialization is applied for list items, but not the whole list).

It is also easier to understand which serializers are applied to a type, by just looking at the field annotation.

##### Using the decorator pattern

One of the key benefits of using the @field_serializer decorator is to apply the function to multiple fields:

```python
from pydantic import BaseModel, field_serializer


class Model(BaseModel):
    f1: str
    f2: str

    @field_serializer('f1', 'f2', mode='plain')
    def capitalize(self, value: str) -> str:
        return value.capitalize()

```

Here are a couple additional notes about the decorator usage:

- If you want the serializer to apply to all fields (including the ones defined in subclasses), you can pass `'*'` as the field name argument.
- By default, the decorator will ensure the provided field name(s) are defined on the model. If you want to disable this check during class creation, you can do so by passing `False` to the `check_fields` argument. This is useful when the field serializer is defined on a base class, and the field is expected to exist on subclasses.

### Model serializers

API Documentation

pydantic.functional_serializers.model_serializer

Serialization can also be customized on the entire model using the @model_serializer decorator.

If the `return_type` argument is provided to the @model_serializer decorator (or if a return type annotation is available on the serializer function), it will be used to build an extra serializer, to ensure that the serialized model value complies with this return type.

As with [field serializers](#field-serializers), **two** different types of model serializers can be used:

- ***Plain* serializers**: are called unconditionally to serialize the model.

  ```python
  from pydantic import BaseModel, model_serializer


  class UserModel(BaseModel):
      username: str
      password: str

      @model_serializer(mode='plain')  # (1)!
      def serialize_model(self) -> str:  # (2)!
          return f'{self.username} - {self.password}'


  print(UserModel(username='foo', password='bar').model_dump())
  #> foo - bar

  ```

  1. `'plain'` is the default mode for the decorator, and can be omitted.
  1. You are free to return a value that *isn't* a dictionary.

- ***Wrap* serializers**: give more flexibility to customize the serialization behavior. You can run code before or after the Pydantic serialization logic.

  Such serializers must be defined with a **mandatory** extra *handler* parameter: a callable taking the instance of the model as an argument. Internally, this handler will delegate serialization of the model to Pydantic. You are free to *not* call the handler at all.

  ```python
  from pydantic import BaseModel, SerializerFunctionWrapHandler, model_serializer


  class UserModel(BaseModel):
      username: str
      password: str

      @model_serializer(mode='wrap')
      def serialize_model(
          self, handler: SerializerFunctionWrapHandler
      ) -> dict[str, object]:
          serialized = handler(self)
          serialized['fields'] = list(serialized)
          return serialized


  print(UserModel(username='foo', password='bar').model_dump())
  #> {'username': 'foo', 'password': 'bar', 'fields': ['username', 'password']}

  ```

## Serialization info

Both the field and model serializers callables (in all modes) can optionally take an extra `info` argument, providing useful extra information, such as:

- [user defined context](#serialization-context)
- the current serialization mode: either `'python'` or `'json'` (see the mode property)
- the various parameters set during serialization using the [serialization methods](#serializing-data) (e.g. exclude_unset, serialize_as_any)
- the current field name, if using a [field serializer](#field-serializers) (see the field_name property).

### Serialization context

You can pass a context object to the [serialization methods](#serializing-data), which can be accessed inside the serializer functions using the context property:

```python
from pydantic import BaseModel, FieldSerializationInfo, field_serializer


class Model(BaseModel):
    text: str

    @field_serializer('text', mode='plain')
    @classmethod
    def remove_stopwords(cls, v: str, info: FieldSerializationInfo) -> str:
        if isinstance(info.context, dict):
            stopwords = info.context.get('stopwords', set())
            v = ' '.join(w for w in v.split() if w.lower() not in stopwords)
        return v


model = Model(text='This is an example document')
print(model.model_dump())  # no context
#> {'text': 'This is an example document'}
print(model.model_dump(context={'stopwords': ['this', 'is', 'an']}))
#> {'text': 'example document'}

```

Similarly, you can [use a context for validation](../validators/#validation-context).

## Serializing subclasses

### Subclasses of supported types

Subclasses of supported types are serialized according to their super class:

```python
from datetime import date

from pydantic import BaseModel


class MyDate(date):
    @property
    def my_date_format(self) -> str:
        return self.strftime('%d/%m/%Y')


class FooModel(BaseModel):
    date: date


m = FooModel(date=MyDate(2023, 1, 1))
print(m.model_dump_json())
#> {"date":"2023-01-01"}

```

### Subclasses of model-like types

When using model-like classes (Pydantic models, dataclasses, etc.) as field annotations, the default behavior is to serializer the field value as though it was an instance of the class, even if it is a subclass. More specifically, only the fields declared on the type annotation will be included in the serialization result:

```python
from pydantic import BaseModel


class User(BaseModel):
    name: str


class UserLogin(User):
    password: str


class OuterModel(BaseModel):
    user: User


user = UserLogin(name='pydantic', password='hunter2')

m = OuterModel(user=user)
print(m)
#> user=UserLogin(name='pydantic', password='hunter2')
print(m.model_dump())  # (1)!
#> {'user': {'name': 'pydantic'}}

```

1. Note: the password field is not included

Migration Warning

This behavior is different from how things worked in Pydantic V1, where we would always include all (subclass) fields when recursively serializing models to dictionaries. The motivation behind this change in behavior is that it helps ensure that you know precisely which fields could be included when serializing, even if subclasses get passed when instantiating the object. In particular, this can help prevent surprises when adding sensitive information like secrets as fields of subclasses. To enable the old V1 behavior, refer to the next section.

### Serializing with duck typing 🦆

Duck typing serialization is the behavior of serializing a model instance based on the actual field values, rather than the field definitions. This means that for a field annotated with a model-like class, all the fields present in subclasses of such class will be included in the serialized output.

To achieve duck typing serialization, Pydantic can apply *serialize as any* behavior. In this mode, Pydantic does *not* make use of the type annotation (more precisely, the serialization schema derived from the type) to infer how the value should be serialized, but instead inspects the actual type of the value at runtime to do so.

When a subclass of a model is used as a value, Pydantic will *not* serialize it according to the schema of the parent class, but rather use the value itself and preserve all of its fields.

This behavior can be configured at the field level and at runtime, for a specific serialization call:

- Field level: use the SerializeAsAny annotation.
- Runtime level: use the `serialize_as_any` argument when calling the [serialization methods](#serializing-data).

We discuss these options below in more detail:

#### `SerializeAsAny` annotation

If you want duck typing serialization behavior, this can be done using the SerializeAsAny annotation on a type:

```python
from pydantic import BaseModel, SerializeAsAny


class User(BaseModel):
    name: str


class UserLogin(User):
    password: str


class OuterModel(BaseModel):
    as_any: SerializeAsAny[User]
    as_user: User


user = UserLogin(name='pydantic', password='password')

print(OuterModel(as_any=user, as_user=user).model_dump())
"""
{
    'as_any': {'name': 'pydantic', 'password': 'password'},
    'as_user': {'name': 'pydantic'},
}
"""

```

When a type is annotated as `SerializeAsAny[<type>]`, the validation behavior will be the same as if it was annotated as `<type>`, and static type checkers will treat the annotation as if it was simply `<type>`. When serializing, the field will be serialized as though the type hint for the field was Any, which is where the name comes from.

#### `serialize_as_any` runtime setting

The `serialize_as_any` runtime setting can be used to serialize model data with or without duck typed serialization behavior. `serialize_as_any` can be passed as a keyword argument to the various [serialization methods](#serializing-data) (such as model_dump() and model_dump_json() on Pydantic models).

```python
from pydantic import BaseModel


class User(BaseModel):
    name: str


class UserLogin(User):
    password: str


class OuterModel(BaseModel):
    user1: User
    user2: User


user = UserLogin(name='pydantic', password='password')

outer_model = OuterModel(user1=user, user2=user)
print(outer_model.model_dump(serialize_as_any=True))  # (1)!
"""
{
    'user1': {'name': 'pydantic', 'password': 'password'},
    'user2': {'name': 'pydantic', 'password': 'password'},
}
"""

print(outer_model.model_dump(serialize_as_any=False))  # (2)!
#> {'user1': {'name': 'pydantic'}, 'user2': {'name': 'pydantic'}}

```

1. With `serialize_as_any` set to `True`, the result matches that of V1.
1. With `serialize_as_any` set to `False` (the V2 default), fields present on the subclass, but not the base class, are not included in serialization.

However, do note that the *serialize as any* behavior will apply to *all* values, not only the values where duck typing is relevant. You may want to prefer using the `SerializeAsAny` annotation when required instead.

## Field inclusion and exclusion

For serialization, field inclusion and exclusion can be configured in two ways:

- at the field level, using the `exclude` and `exclude_if` parameters on [the `Field()` function](../fields/).
- using the various serialization parameters on the [serialization methods](#serializing-data).

### At the field level

At the field level, the `exclude` and `exclude_if` parameters can be used:

```python
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    id: int
    private_id: int = Field(exclude=True)
    value: int = Field(ge=0, exclude_if=lambda v: v == 0)


print(Transaction(id=1, private_id=2, value=0).model_dump())
#> {'id': 1}

```

Exclusion at the field level takes priority over the `include` serialization parameter described below.

### As parameters to the serialization methods

When using the [serialization methods](#serializing-data) (such as model_dump()), several parameters can be used to exclude or include fields.

#### Excluding and including specific fields

Consider the following models:

```python
from pydantic import BaseModel, Field, SecretStr


class User(BaseModel):
    id: int
    username: str
    password: SecretStr


class Transaction(BaseModel):
    id: str
    private_id: str = Field(exclude=True)
    user: User
    value: int


t = Transaction(
    id='1234567890',
    private_id='123',
    user=User(id=42, username='JohnDoe', password='hashedpassword'),
    value=9876543210,
)

```

The `exclude` parameter can be used to specify which fields should be excluded (including the others), and vice-versa using the `include` parameter.

```python
# using a set:
print(t.model_dump(exclude={'user', 'value'}))
#> {'id': '1234567890'}

# using a dictionary:
print(t.model_dump(exclude={'user': {'username', 'password'}, 'value': True}))
#> {'id': '1234567890', 'user': {'id': 42}}

# same configuration using `include`:
print(t.model_dump(include={'id': True, 'user': {'id'}}))
#> {'id': '1234567890', 'user': {'id': 42}}

```

Note that using `False` to *include* a field in `exclude` (or to *exclude* a field in `include`) is not supported.

It is also possible to exclude or include specific items from sequence and dictionaries:

```python
from pydantic import BaseModel


class Hobby(BaseModel):
    name: str
    info: str


class User(BaseModel):
    hobbies: list[Hobby]


user = User(
    hobbies=[
        Hobby(name='Programming', info='Writing code and stuff'),
        Hobby(name='Gaming', info='Hell Yeah!!!'),
    ],
)

print(user.model_dump(exclude={'hobbies': {-1: {'info'}}}))  # (1)!
"""
{
    'hobbies': [
        {'name': 'Programming', 'info': 'Writing code and stuff'},
        {'name': 'Gaming'},
    ]
}
"""

```

1. The equivalent call with `include` would be:

   ```python
   user.model_dump(
      include={'hobbies': {0: True, -1: {'name'}}}
   )

   ```

The special key `'__all__'` can be used to apply an exclusion/inclusion pattern to all members:

```python
print(user.model_dump(exclude={'hobbies': {'__all__': {'info'}}}))
#> {'hobbies': [{'name': 'Programming'}, {'name': 'Gaming'}]}

```

#### Excluding and including fields based on their value

When using the [serialization methods](#serializing-data), it is possible to exclude fields based on their value, using the following parameters:

- `exclude_defaults`: Exclude all fields whose value compares equal to the default value (using the equality (`==`) comparison operator).

- `exclude_none`: Exclude all fields whose value is `None`.

- `exclude_unset`: Pydantic keeps track of fields that were *explicitly* set during instantiation (using the model_fields_set property). Using `exclude_unset`, any field that was not explicitly provided will be excluded:

  ```python
  from pydantic import BaseModel


  class UserModel(BaseModel):
      name: str
      age: int = 18


  user = UserModel(name='John')
  print(user.model_fields_set)
  #> {'name'}

  print(user.model_dump(exclude_unset=True))
  #> {'name': 'John'}

  ```

  Note that altering a field *after* the instance has been created will remove it from the unset fields:

  ```python
  user.age = 21

  print(user.model_dump(exclude_unset=True))
  #> {'name': 'John', 'age': 21}

  ```

  Tip

  The experimental [`MISSING` sentinel](../experimental/#missing-sentinel) can be used as an alternative to `exclude_unset`. Any field with `MISSING` as a value is automatically excluded from the serialization output.
