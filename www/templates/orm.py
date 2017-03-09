#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Zheng Wantong'
'''
unction:   封装的ORM工具类
Version:    1.0
选择MySQL作为网站的后台数据库 
执行SQL语句进行操作，并将常用的SELECT、INSERT等语句进行函数封装 
在异步框架的基础上，采用aiomysql作为数据库的异步IO驱动 
将数据库中表的操作，映射成一个类的操作，也就是数据库表的一行映射成一个对象(ORM) 
整个ORM也是异步操作 
# -*- -----  思路  ----- -*-
    如何定义一个user类，这个类和数据库中的表User构成映射关系，二者应该关联起来，
 user可以操作表User  
    通过Field类将user类的属性映射到User表的列中，其中每一列的字段又有自己的一些
 属性，包括数据类型，列名，主键和默认值 
'''
# 一次使用异步 处处使用异步 
import aiomysql
import asyncio, logging

# 打印SQL查询语句
def log(sql, args=()):
	logging.info('SQL: %s' % sql)

# 创建一个全局的连接池，每个HTTP请求都从池中获得数据库连接
async def create_pool(loop, **kw):#这里的**kw是一个dict  
	logging.info('create database connection pool...')
	# 全局变量__pool用于存储整个连接池
	global __pool
	__pool = await aiomysql.create_pool(
		# **kw参数可以包含所有连接需要用到的关键字参数
		host=kw.get('host', 'localhost'),#默认值localhost
		port=kw.get('port', 3306),
		user=kw['user'],
		password=kw['password'],
		db=kw['db'],
		charset=kw.get('charset', 'utf-8'),
		autocommit=kw.get('autocommit', True),#默认自动提交事务，不用手动去提交事务
		maxsize=kw.get('maxsize', 10),# 默认最大连接数为10
		minsize=kw.get('minsize', 1),
		loop=loop # 接收一个event_loop实例
	)

# 原版没有destroy方法	
async def destroy_pool():
    global __pool
    if __pool is not None :
        __pool.close()
        await __pool.wait_closed()

# 封装SQL SELECT语句为select函数
async def select(sql, args,size=None):
	log(sql, args)
	global __pool
	# async从连接池中返回一个连接
	async with __pool.get() as conn:
		# DictCursor is a cursor which returns results as a dictionary
		# async 将会调用一个子协程，并直接返回调用的结果
		async with conn.cursor(aiomysql.DictCursor) as cur:
			# 执行SQL语句,SQL语句的占位符为?，MySQL的占位符为%s
			await cur.execute(sql.replace('?', '%s'), args or ())
			 # 根据指定返回的size，返回查询的结果
			if size:
				 # 返回size条查询结果
				rs = await cur.fetchmany(size)
			else:
				# 返回所有查询结果
				rs = await cur.fetchall()
		logging.info('rows returned: %s' % len(rs))
		return rs

# 封装INSERT、UPDATE、DELETE语句,语句操作参数一样，
# 所以定义一个通用的执行函数，返回操作影响的行号
async def execute(sql, args, autocommit=True):
	log(sql)
	async with __pool.get() as conn:
		if not autocommit:
			await conn.begin()
		try:
			#aiomysql.DictCursor因为execute类型sql操作返回结果只有行号，不需要dict
			async with conn.cursor() as cur:
				await cur.execute(sql.replace('?', '%s'), args)
				affected_line = cur.rowcount
			if not autocommit:
				await conn.commit()
		except BaseException as e:
			if not autocommit:
				await conn.rollback()
			raise
		return affected_line

# 根据输入的参数生成占位符列表
# 比如说：insert into  `User` (`password`, `email`, `name`, `id`) values (?,?,?,?)  看到了么 后面这四个问号  
def create_args_string(num):  
    L = []  
    for n in range(num):  
        L.append('?')  
    return ', '.join(L) # 以','为分隔符，将列表合成字符串

# 定义Field类，负责保存(数据库)表的字段名和字段类型
class Field(object):
	# 表的字段包含名字、类型、是否为表的主键和默认值
	def __init__(self, name, column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default
	# 当打印(数据库)表时，输出(数据库)表的信息:类名，字段类型和名字
	def __str__(self):
		return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)

# 定义不同类型的衍生Field,定义数据库中五个存储类型
# 表的不同列的字段的类型不一样
# 映射varchar的StringField：
class StringField(Field):

	def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
		super().__init__(name, primary_key, default, ddl)

# 布尔类型不可以作为主键 
class BooleanField(Field):

    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)

class IntegerField(Field):

    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):

    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)

class TextField(Field):

    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)

# -*-定义Model的元类
 
# 所有的元类都继承自type
# ModelMetaclass元类定义了所有Model基类(继承ModelMetaclass)的子类实现的操作
 
# -*-ModelMetaclass的工作主要是为一个数据库表映射成一个封装的类做准备：
# ***读取具体子类(user)的映射信息
# 创造类的时候，排除对Model类的修改
# 在当前类中查找所有的类属性(attrs)，如果找到Field属性，就将其保存到__mappings__的dict中，
# 同时从类属性中删除Field(防止实例属性遮住类的同名属性)
# 将数据库表名保存到__table__中
 
# 完成这些工作就可以在Model中定义各种数据库的操作方法
# metaclass是类的模板，所以必须从`type`类型派生：
class ModelMetaclass(type):
	# __new__控制__init__的执行，所以在其执行之前
	# cls:代表要__init__的类，此参数在实例化时由Python解释器自动提供(例如下文的User和Model)  
	# bases：代表继承父类的集合 attrs：类的方法集合
	def __new__(cls, name, bases, attrs):
		# 排除model 是因为要排除对model类的修改  
		if name=='Model':
			return type.__new__(cls, name, bases, attrs)
		# 获取table名称 为啥获取table名称 至于在哪里我也是不明白握草 
		tableName = attrs.get('__table__', None) or name
		logging.info('found model: %s (table: %s)' % (name, tableName))#r如果存在表名，则返回表名，否则返回 name
		mappings = dict() # 获取Field所有主键名和Field  
		fields = []#field保存的是除主键外的属性名  
		primaryKey = None
		for k, v in attrs.items():# 这个k是表示字段名  
			if isinstance(v, Field):
				logging.info('  found mapping: %s ==> %s' % (k, v))
				mappings[k] = v
				if v.primary_key:# 找到主键
					# 如果此时类实例的以存在主键，说明主键重复
					if primaryKey:
						#一个表只能有一个主键，当再出现一个主键的时候就报错  
						raise StandardError('Duplicate primary key for field: %s' % k)
					primaryKey = k# 也就是说主键只能被设置一次  
				else:
					fields.append(k)
		if not primaryKey:#如果主键不存在也将会报错
			raise StandardError('Primary key not found.')
		for k in mappings.keys():
			attrs.pop(k)# 保存除主键外的属性为''列表形式
		# 将除主键外的其他属性变成`id`, `name`这种形式
		escaped_fields = list(map(lambda f: '`%s`' % f, fields))
		attrs['__mappings__'] = mappings # 保存属性和列的映射关系
		attrs['__table__'] = tableName # 保存表名
		attrs['__primary_key__'] = primaryKey
		attrs['__fields__'] = fields # 除主键外的属性名
		# 构造默认的SELECT、INSERT、UPDATE、DELETE语句
        # ``反引号功能同repr()
		attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
		attrs['__insert__'] = 'insert into  `%s` (%s, `%s`) values(%s)' %(tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
		attrs['__update__'] = 'update `%s` set `%s` where `%s` = ?' %(tableName, ', '.join(map(lambda f:'`%s`=?' %(mappings.get(f).name or f), fields)), primaryKey)
		attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
		return type.__new__(cls, name, bases, attrs)        

# 定义ORM所有映射的基类：Model
# Model类的任意子类可以映射一个数据库表
# Model类可以看作是对所有数据库表操作的基本定义的映射
 
# 基于字典查询形式
# Model从dict继承，拥有字典的所有功能，同时实现特殊方法__getattr__和__setattr__，能够实现属性操作
# 实现数据库操作的所有方法，定义为class方法，所有继承自Model都具有数据库操作方法
class Model(dict, metaclass=ModelMetaclass):

	def __init__(self, **kw):
		super(Model, self).__init__(**kw)

	def __getattr__(self,key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'" % key)

	def __setattr__(self, key, value):
		self[key] = value

	def getValue(self, key):# 这个是默认内置函数实现的  
		return getattr(self, key, None)

	def getValueOrDefault(self, key):
		value = getattr(self, key, None)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s: %s' % (key,str(value)))
				setattr(self, key, value)
		return value

	# findAll() - 根据WHERE条件查找
	# 类方法有类变量cls传入，从而可以用cls做一些相关的处理。并且有
	# 子类继承时，调用该类方法时，传入的类变量cls是子类，而非父类。 
	@classmethod
	async def findAll(cls, where=None, args=None, **kw):
		' find objects by where clause. '
		sql = [cls.__select__]
		if where:
			sql.append('where')
			sql.append(where)
		if args is None:
			args = []
		orderBy = kw.get('orderBy', None)
		if orderBy:
			sql.append('order by')
			sql.append(orderBy)
		limit = kw.get('limit', None)
		if limit is not None:
			sql.append('limit')
			if isinstance(limit, int):
				sql.append('?')
				args.append(limit)
			elif isinstance(limit, tuple) and len(limit) == 2:
				sql.append('?, ?')
				args.extend(limit)
			else:
				raise ValueError('Invalid limit value: %s' % str(limit))
		rs = await select(' '.join(sql), args)#返回的rs是一个元素是tuple的list
		return [cls(**r) for r in rs]# **r 是关键字参数，构成了一个cls类的列表，
		                             # 其实就是每一条记录对应的类实例  

# findNumber()-根据WHERE条件查找，但返回的是整数，
	# 适用于select count(*)类型的SQL。
	@classmethod
	async def findNumber(cls, selectField, where=None, args=None):
		' find number by select and where. '
		sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
		if where:
			sql.append('where')
			sql.append(where)
		rs = await select(' '.join(sql), args, 1)
		if len(rs) == 0:
			return None
		return rs[0]['_num_']

	# 往Model类添加class方法，就可以让所有子类调用class方法：
	@classmethod	
	async def find(cls, pk):
		' find object by primary key. '
		rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
		if len(rs) == 0:
			return None
		return cls(**rs[0])

	# 往Model类添加实例方法，就可以让所有子类调用实例方法：
	async def save(self):
		args = list(map(self.getValueOrDefault, self.__fields__))
		args.append(self.getValueOrDefault(self.__primary_key__))
		rows = await execute(self.__insert__, args)
		if rows != 1:
			logging.warn('failed to insert record: affected rows: %s' % rows)


	async def update(self):
		args = list(map(self.getValue, self.__fields__))
		args.append(self.getValue(self.__primary_key__))
		rows = await execute(self.__update__, args)
		if rows != 1:
			logging.warn('failed to update by primary key: affected rows: %s' % rows)

	async def remove(self):
		args = [self.getValue(self.__primary_key__)]
		rows = await execute(self.__delete__, args)
		if rows != 1:
			logging.warn('failed to remove by primary key: affected rows: %s' % rows)

#一个类自带前后都有双下划线的方法，在子类继承该类的时候，
# 这些方法会自动调用，比如__init__  
if __name__ == '__main__':
    # 虽然User类乍看没有参数传入，但实际上，User类继承Model类，
    # Model类又继承dict类，所以User类的实例可以传入关键字参数  
	class User(Model):
		# 定义类的属性到列的映射：
		id = IntegerField('id',primary_key=True)#主键为id， tablename为User，即类名  
		name = StringField('username')
		email = StringField('email')
		password = StringField('password')
	#创建异步事件的句柄
	loop = asyncio.get_event_loop()
	#创建实例
	async def test():
		await create_pool(loop=loop,host='localhost', port=3306, user='root', password='1324', db='test')
		user = User(id=8, name='sly', email='slysly759@gmail.com', password='fuckblog')
		await user.save()
		r = await User.find('11')
		print(r)
		r = await User.findAll()
		print(1, r)
		r = await User.findAll(id='12')
		print(2, r)
		await destroy_pool()
 
	loop.run_until_complete(test())
	loop.close()
	if loop.is_closed():
		sys.exit(0)