from bs4 import BeautifulSoup
from urllib.parse import urljoin
import repo


def crawl(url, queued_count, maximum_items, get_html, extract_content):
    # 防御空URL攻击/无效输入
    if not url:
        print('URL not provided', url)
        return
    # 通过布隆过滤器或Redis进行O(1)查重
    already_seen = _seen(url)
    if already_seen:
        print('URL already seen ', already_seen)
        return
    #流量控制模块
    total = queued_count + repo.count_visited() + repo.count_queued()
    if total >= maximum_items:
        print('Exiting! queued + visited over maximum:', queued_count, total)
        return
    # 原子操作标记URL为处理中
    repo.add_to_queue(url)
    # 实际爬取操作
    links, content = _crawl(url, get_html, extract_content)
    #将提取的 links 添加到待爬取队列中，并使用 parser.allow_url_filter 过滤不符合条件的链接
    repo.move_from_queued_to_visited(url)

    return links, content


def add_results_to_queue(urls, allow_url_filter):
    if not urls:
        return

    for url in urls:
        if allow_url_filter(url) and not _seen(url):
            print('Add URL to visit queue', url)
            repo.add_to_visit(url)


def _crawl(url, get_html, extract_content):
    print('Crawl ->', url)

    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    links = _extract_links(url, soup)
    content = extract_content(url, soup)

    return links, content


def _extract_links(url, soup):
    return list({
        urljoin(url, a.get('href'))
        for a in soup.find_all('a')
        if a.get('href') and not(a.get('rel') and 'nofollow' in a.get('rel'))
    })


def _seen(url):
    return repo.is_visited(url) or repo.is_queued(url)
