#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
如果要部署到服务器时，通常需要修改数据库的host等信息
config_override.py，用来覆盖某些默认设置：
生产环境的标准配置
'''
__author__ = 'Zheng Wantong'

configs = {
	'db': {
		'host': '127.0.0.1'
	}
}