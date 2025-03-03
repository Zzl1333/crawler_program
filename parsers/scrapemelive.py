import json
from collectors import fake
import repo
import urllib.parse
import socket
def extract_content(url, soup):
    parsed_url = urllib.parse.urlparse(url)

    # 获取域名
    domain = parsed_url.netloc
    ip_address = socket.gethostbyname(domain)

    return [{
        'id': product.find('a',
            attrs={'data-product_id': True})['data-product_id'],
        'name': product.find('h2').text,
        'price': product.find(class_='amount').text,
        'photo_url':product.find('img')['src'],
        'url' : url,
        'url->ip':ip_address
    } for product in soup.select('.product')]



def store_content(url, content):
    for item in content:
        if item['id']:
            repo.set_content(item['id'], json.dumps(item))


def allow_url_filter(url):
    return '/shop/page/' in url and '#' not in url


def get_html(url):
    return fake.get_html(url)

