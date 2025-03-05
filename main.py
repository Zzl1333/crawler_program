from tasks import queue_url
import repo
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from urllib.request import urlopen, Request
import redis  # 新增导入
import threading  # 新增导入
from datetime import datetime  # 新增导入
import time  # 新增导入
#要访问的url
starting_url = 'https://scrapeme.live/shop/page/1/'

# Redis连接配置（与原有repo模块保持一致）
REDIS_CLIENT = redis.Redis(host='localhost', port=6379, db=1)  # 新增
NODE_NAME = 'node1'  # 新增
HEARTBEAT_INTERVAL = 10  # 新增

# ========== 心跳线程函数 ==========
def send_heartbeat():
    """定期发送心跳信号到Redis"""
    while True:
        REDIS_CLIENT.set(
            f'node:{NODE_NAME}:heartbeat',
            datetime.now().isoformat()
        )
        time.sleep(HEARTBEAT_INTERVAL)

# ========== 主程序初始化 ==========
# 启动心跳守护线程（在程序开始时执行）
heartbeat_thread = threading.Thread(target=send_heartbeat)
heartbeat_thread.daemon = True  # 设为守护线程，主程序退出时自动终止
heartbeat_thread.start()
def check_robots_allowed(url, user_agent="MyCrawler/1.0"):
    """检查目标URL是否允许爬取"""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.hostname}/robots.txt"

    rp = RobotFileParser()
    rp.set_url(robots_url)

    try:
        # 使用 urlopen 手动抓取 robots.txt 并设置超时
        req = Request(robots_url)
        with urlopen(req, timeout=5) as response:
            robots_content = response.read().decode()

        # 解析 robots.txt
        rp.parse(robots_content.split('\n'))
        print(f"✅ 成功获取robots.txt: {robots_url}")
        repo.connection.rpush('robots_allow_url',robots_url)
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        print(f"⚠️ robots.txt检查失败: {str(e)}")
        # 根据保守策略：无法验证时默认禁止爬取
        return False


if check_robots_allowed(starting_url):
    # 将要访问的url加入redis待访问队列中（仅当允许时）
    repo.add_to_visit(starting_url)
    print(f"已添加初始URL到队列: {starting_url}")
else:
    print(f"🚫 根据robots协议禁止爬取初始URL: {starting_url}")
    exit(1)  # 直接终止程序

page = 1
maximum_items = 30

while True:
    #检查任务总数：已爬取和正在处理
    total = repo.count_visited() + repo.count_queued()
    if total >= maximum_items:
        print('超出最大限制 :', total)
        break

    # timeout after 1 minute
    #从redis的to_visit队列取出一个url
    item = repo.pop_to_visit_blocking(60)
    if item is None:
        print('超时！队列中无待访问Url')
        break

    url = item[1].decode('utf-8')
    print('从redis中提取出的url为 ：', url)



    #将url分发给celery的异步任务，限制为maximum_items
    queue_url.delay(url, maximum_items)







