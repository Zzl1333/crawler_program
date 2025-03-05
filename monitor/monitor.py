import redis
from celery import Celery
from datetime import datetime, time
import time

# Redis连接
redis_client = redis.Redis(host='localhost', port=6379, db=1)

# Celery应用
app = Celery(
    'monitor',
    broker_url='redis://localhost:6379/1',
    result_backend='redis://localhost:6379/1'
)

# 爬虫节点心跳间隔（秒）
HEARTBEAT_INTERVAL = 10

# 爬虫节点超时时间（秒）
NODE_TIMEOUT = 30


def monitor_nodes():
    """
    监测爬虫节点运行状态
    """
    while True:
        # 获取所有爬虫节点
        nodes = get_nodes()

        # 检查每个节点的状态
        for node in nodes:
            # 获取节点最后心跳时间
            last_heartbeat = redis_client.get(f'node:{node}:heartbeat')
            status_key = f'node:{node}:status'
            if not last_heartbeat:
                # 如果没有心跳记录，初始化为当前时间
                redis_client.set(f'node:{node}:heartbeat', datetime.now().isoformat())
                continue

            # 计算节点是否超时
            last_heartbeat = datetime.fromisoformat(last_heartbeat.decode())
            if (datetime.now() - last_heartbeat).seconds > NODE_TIMEOUT:
                # 如果超时，标记为离线
                redis_client.set(f'node:{node}:status', 'offline')
                print(f'Node {node} is offline')
            else:
                # 如果未超时，标记为在线
                redis_client.set(f'node:{node}:status', 'online')

        # 检查任务状态
        task_status = check_task_status()
        redis_client.hset('system:status', 'tasks', str(task_status))
        print(f'任务状态已更新: {task_status}')
        # 等待下一个心跳周期
        time.sleep(HEARTBEAT_INTERVAL)


def get_nodes():
    """
    获取所有爬虫节点
    """
    # 从Redis中获取所有节点
    nodes = redis_client.keys('node:*:heartbeat')
    return [node.decode().split(':')[1] for node in nodes]


def check_task_status():
    """
    检查任务状态
    """
    # 获取所有任务
    tasks = app.events.State().tasks.values()

    # 统计任务状态
    task_status = {
        'total': 0,
        'pending': 0,
        'started': 0,
        'success': 0,
        'failed': 0
    }

    for task in tasks:
        task_status['total'] += 1
        if task.state == 'PENDING':
            task_status['pending'] += 1
        elif task.state == 'STARTED':
            task_status['started'] += 1
        elif task.state == 'SUCCESS':
            task_status['success'] += 1
        elif task.state == 'FAILURE':
            task_status['failed'] += 1

    # 打印任务状态
    print(f'Task status: {task_status}')


if __name__ == '__main__':
    monitor_nodes()