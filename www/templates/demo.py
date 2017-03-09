#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code is far away from bugs with the god animal protecting
             ┏┓      ┏┓
            ┏┛┻━━━━━━┛┻┓
            ┃      ☃   ┃
            ┃  ┳┛  ┗┳  ┃
            ┃    ┻     ┃
            ┗━━━┓    ┏━┛
                ┃    ┗━━━━━━━━┓
                ┃  神兽保佑   ┣┓
                ┃　永无BUG！  ┏┛
                ┗━┓ ┓ ┏━━┳ ┓ ┏┛
                  ┃ ┫ ┫  ┃ ┫ ┫
                  ┗━┻━┛  ┗━┻━┛

-------------------------------------------------------------------------------
"""

import orm, asyncio
from models import User, Blog, Comment
loop = asyncio.get_event_loop()

@asyncio.coroutine
def test(loop):
	yield from orm.create_pool(user='www-data', password='www-data', database='awesome', charset='utf-8')
	u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')
	yield from u.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.run_forever()