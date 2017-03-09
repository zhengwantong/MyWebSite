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

import asyncio, aiomysql
from models import User, Blog, Comment

loop = asyncio.get_event_loop()

async def test():
	conn = await aiomysql.connect(host='127.0.0.1', port=3306,
                                       user='root', password='1234', db='awesome',
                                       loop=loop)
	cur = await conn.cursor()
	await cur.execute("SELECT * FROM users")
	print(cur.description)
	r = await cur.fetchall()
	print(r)
	await cur.close()
	conn.close()

loop.run_until_complete(test())
