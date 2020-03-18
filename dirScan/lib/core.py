# encoding=utf-8
import functools
import random
import string
import time

import aiohttp
from aiomultiprocess import Pool
import asyncio

from bs4 import BeautifulSoup


async def get(url, session, redirect=False):
    """
    发送请求，获取状态码
    :param redirect: 是否跟进重定向
    :param url
    :return: resp
    """
    # print("get:{}".format(url))
    if not url:
        raise ValueError("url is none.")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/59.0.3071.104 Safari/537.36',
    }
    try:
        # 获取请求响应
        # async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False),
                                         # conn_timeout=1000) as session:
        async with session.get(url, allow_redirects=redirect, headers=headers, timeout=5) as resp:
            resp_text = await resp.text()
            status = resp.status
            return resp_text, status, None

    # python异常 https://blog.csdn.net/polyhedronx/article/details/81589196
    except (aiohttp.ClientResponseError, aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
        print("[Except] 请求失败 {} error_message：{}".format(url, str(e)))
        return "", "", str(e)


# 获取随机url，集不存在的目录url
def get_r_url(url):
    flag = string.ascii_letters + string.digits
    return url + "".join(random.sample(flag, random.randint(3, 10)))


async def aiomul():
    # dm_list = open("../vipshop.com_sub.txt").readlines()
    dm_list = ["legou55525ht.com", ]
    async with Pool() as pool:
        result = await pool.map(functools.partial(get, index=True), dm_list)
    # for i in result:
    #     print(i)


if __name__ == "__main__":
    start = time.time()
    task = asyncio.ensure_future(aiomul())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(task)
    print("all done, {}".format(time.time() - start))
