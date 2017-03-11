import orm,asyncio, aiomysql
from models import User, Blog, Comment

async def test(loop):
    await orm.create_pool(loop, user='www-data', password='www-data', db='awesome')
    u = User(name='Zhengwantong', email='527790840@qq.com', passwd='guessit', image='about:blank$')

    await u.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()
