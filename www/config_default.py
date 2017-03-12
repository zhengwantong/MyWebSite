#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Default configurations.开发环境的标准配置
'''

__author__ = 'Zheng Wantong'

configs = {
	'db': {
		'host': '127.0.0.1',
		#'host': '10.134.126.60',
		'port': 3306,
		'user': 'www-data',
		'password': 'www-data',
		'db': 'awesome'
	},
	'session': {
		'secret': 'AwEsOmE'
	}
}