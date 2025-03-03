from redis import Redis


connection = Redis(db=1)

to_visit_key = 'crawling:to_visit'#待爬取的url队列
visited_key = 'crawling:visited'#已爬取的url集合
queued_key = 'crawling:queued'#正在处理的url结合
content_key = 'crawling:content'#正在爬取内容的哈希表


# To Visit
def add_to_visit(value):
    # LPOS 要求redis版本为6以上
    if connection.execute_command('LPOS', to_visit_key, value) is None:
        # add URL to the end of the list
        connection.rpush(to_visit_key, value)


def pop_to_visit_blocking(timeout=0):
    #BLPOP 命令用于移出并获取列表的第一个元素。如果列表没有元素，命令会阻塞列表直到等待超时或发现可弹出元素为止
    # pop URL from the beginning of the list
    return connection.blpop(to_visit_key, timeout)


# Visited
def count_visited():
    #scard返回集合中元素的数量
    return connection.scard(visited_key)


def add_visited(value):
    #sadd向集合中添加元素
    connection.sadd(visited_key, value)


def is_visited(value):
    return connection.sismember(visited_key, value)


# Queued
def count_queued():
    return connection.scard(queued_key)


def add_to_queue(value):
    connection.sadd(queued_key, value)


def is_queued(value):
    return connection.sismember(queued_key, value)


def move_from_queued_to_visited(value):
    # atomically move a URL from queued to visited
    connection.smove(queued_key, visited_key, value)


# Content
def set_content(key, value):
    connection.hset(content_key, key=key, value=value)


def add_to_list(list, value):
    connection.rpush(list, value)
