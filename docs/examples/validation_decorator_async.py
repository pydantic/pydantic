class Connection:
    async def execute(self, sql, *args):
        return 'testing@example.com'

conn = Connection()
# ignore-above
import asyncio
from pydantic import validate_arguments, PositiveInt

@validate_arguments
async def get_user_email(user_id: PositiveInt):
    # conn is some fictional connection to a database
    email = await conn.execute('select email from users where id=$1', user_id)
    if email is None:
        raise RuntimeError('user not found')
    else:
        return email

async def main():
    email = await get_user_email(123)
    print(email)

asyncio.run(main())
