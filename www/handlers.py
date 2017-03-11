
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Zheng Wantong'

' url handlers '

from coroweb import get, post
from aiohttp import web

@get('/blog')
async def handler_url_blog(request):
    return web.Response(body=b'<h1>Awesome: /blog</h1>', content_type='text/html', charset='UTF-8')

@get('/index')
async def handler_url_index(request):
    return web.Response(body=b'<h1>Awesome: /index</h1>', content_type='text/html', charset='UTF-8')

@get('/create_comment')
async def handler_url_create_comment(request):
    return web.Response(body=b'<h1>Awesome>: /create_comment</h1', content_type='text/html', charset='UTF-8')