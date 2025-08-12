Pydantic is quite helpful for validating data that goes into and comes out of queues. Below,
we'll explore how to validate / serialize data with various queue systems.

## Redis queue

Redis is a popular in-memory data structure store.

In order to run this example locally, you'll first need to [install Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)
and start your server up locally.

Here's a simple example of how you can use Pydantic to:
1. Serialize data to push to the queue
2. Deserialize and validate data when it's popped from the queue

```python {test="skip"}
import redis

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


r = redis.Redis(host='localhost', port=6379, db=0)
QUEUE_NAME = 'user_queue'


def push_to_queue(user_data: User) -> None:
    serialized_data = user_data.model_dump_json()
    r.rpush(QUEUE_NAME, user_data.model_dump_json())
    print(f'Added to queue: {serialized_data}')


user1 = User(id=1, name='John Doe', email='john@example.com')
user2 = User(id=2, name='Jane Doe', email='jane@example.com')

push_to_queue(user1)
#> Added to queue: {"id":1,"name":"John Doe","email":"john@example.com"}

push_to_queue(user2)
#> Added to queue: {"id":2,"name":"Jane Doe","email":"jane@example.com"}


def pop_from_queue() -> None:
    data = r.lpop(QUEUE_NAME)

    if data:
        user = User.model_validate_json(data)
        print(f'Validated user: {repr(user)}')
    else:
        print('Queue is empty')


pop_from_queue()
#> Validated user: User(id=1, name='John Doe', email='john@example.com')

pop_from_queue()
#> Validated user: User(id=2, name='Jane Doe', email='jane@example.com')

pop_from_queue()
#> Queue is empty
```

<!-- TODO: kafka, rabbitMQ, celery, arq, etc - better for SEO, great for new contributors! -->
