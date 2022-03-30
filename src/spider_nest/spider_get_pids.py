"""
模块功能：
1. 采集批改网所有在库作文数据
2. 清洗，预处理
3. 入库信息键：pid作文号、title作文标题、abstract简介、refer参考答案{可能为空}、
spider_time采集时间、source_href答题页面访问链接
"""
from gevent import monkey

monkey.patch_all()
import json

import requests
from lxml import etree
import gevent
from gevent.queue import Queue
from fake_useragent import UserAgent

work_q = Queue()
pids = dict()
session = requests.session()
with open("../database/cookies.txt", "r") as f:
    # cookies_dict = json.loads(f.read())
    # cookies = ';'.join(['{}:{}'.format(i['name'], i['value']) for i in json.loads(f.read())])
    data = json.loads(f.read())
    cookies_dict = dict(zip([i["name"] for i in data], [i["value"] for i in data]))
    cookies = requests.utils.cookiejar_from_dict(cookies_dict)
    session.cookies = cookies
print(session.cookies)


def handle_html(url):
    headers = {
        "User-Agent": UserAgent().random,
        "Host": "tiku.pigai.org",
        "DNT": "1",
        # 'Cookie': cookies,
    }

    res = session.get(url, headers=headers)
    if res.status_code == 200:
        print(">>> 访问成功")
        tree = etree.HTML(res.text)
        # print(res.text)
        titles = tree.xpath("//li[@class='title']/text()")
        for title in titles:
            print(title)


def coroutine_engine():
    while not work_q.empty():
        url = work_q.get_nowait()
        handle_html(url)


def coroutine_speed_up(power: int = 4):
    task_list = []
    for x in range(power):
        task = gevent.spawn(coroutine_engine)
        task_list.append(task)
    gevent.joinall(task_list)


def run():
    pass


if __name__ == "__main__":
    handle_html(
        "http://tiku.pigai.org/Home/Index/essayNormal/tp/0/yycd/1/grade/%E5%A4%A7%E5%AD%A6%E8%8B%B1%E8%AF%AD"
    )
