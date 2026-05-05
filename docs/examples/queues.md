---
title: "Pydantic Validation Queues: Redis, RabbitMQ & ARQ"
description: Integrate Pydantic with Celery or Redis to enforce strict validation on task schemas and message payloads.
---
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
    r.rpush(QUEUE_NAME, serialized_data)
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

## RabbitMQ

RabbitMQ is a popular message broker that implements the AMQP protocol.

In order to run this example locally, you'll first need to [install RabbitMQ](https://www.rabbitmq.com/download.html) and start your server.

Here's a simple example of how you can use Pydantic to:

1. Serialize data to push to the queue
2. Deserialize and validate data when it's popped from the queue

First, let's create a sender script.

```python {test="skip"}
import pika

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
QUEUE_NAME = 'user_queue'
channel.queue_declare(queue=QUEUE_NAME)


def push_to_queue(user_data: User) -> None:
    serialized_data = user_data.model_dump_json()
    channel.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=serialized_data,
    )
    print(f'Added to queue: {serialized_data}')


user1 = User(id=1, name='John Doe', email='john@example.com')
user2 = User(id=2, name='Jane Doe', email='jane@example.com')

push_to_queue(user1)
#> Added to queue: {"id":1,"name":"John Doe","email":"john@example.com"}

push_to_queue(user2)
#> Added to queue: {"id":2,"name":"Jane Doe","email":"jane@example.com"}

connection.close()
```

And here's the receiver script.

```python {test="skip"}
import pika

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    QUEUE_NAME = 'user_queue'
    channel.queue_declare(queue=QUEUE_NAME)

    def process_message(
        ch: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ):
        user = User.model_validate_json(body)
        print(f'Validated user: {repr(user)}')
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_message)
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
```

To test this example:

1. Run the receiver script in one terminal to start the consumer.
2. Run the sender script in another terminal to send messages.

## ARQ

ARQ is a fast Redis-based job queue for Python.
It's built on top of Redis and provides a simple way to handle background tasks.

In order to run this example locally, you’ll need to [Install Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/) and start your server.

Here's a simple example of how you can use Pydantic with ARQ to:

1. Define a model for your job data
2. Serialize data when enqueueing jobs
3. Validate and deserialize data when processing jobs

```python {test="skip"}
import asyncio
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


REDIS_SETTINGS = RedisSettings()


async def process_user(ctx: dict[str, Any], user_data: dict[str, Any]) -> None:
    user = User.model_validate(user_data)
    print(f'Processing user: {repr(user)}')


async def enqueue_jobs(redis):
    user1 = User(id=1, name='John Doe', email='john@example.com')
    user2 = User(id=2, name='Jane Doe', email='jane@example.com')

    await redis.enqueue_job('process_user', user1.model_dump())
    print(f'Enqueued user: {repr(user1)}')

    await redis.enqueue_job('process_user', user2.model_dump())
    print(f'Enqueued user: {repr(user2)}')


class WorkerSettings:
    functions = [process_user]
    redis_settings = REDIS_SETTINGS


async def main():
    redis = await create_pool(REDIS_SETTINGS)
    await enqueue_jobs(redis)


if __name__ == '__main__':
    asyncio.run(main())
```

This script is complete.
It should run "as is" both to enqueue jobs and to process them.
<!-- TODO: kafka, celery, etc - better for SEO, great for new contributors! -->
