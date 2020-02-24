# encoding=utf-8
import time

import aiohttp
from aiomultiprocess import Pool
from bs4 import BeautifulSoup
import string
import random
import asyncio


async def getStatusAndTitle(domain, index=False, https=False, redirect=False):
    """
    发送请求，获取状态码及title
    :param redirect: 是否跟进重定向
    :param url: 请求的url
    :return: dict [original_domain，rediect_url, status，title, header_count, content-length]
    """
    _url = getUrl(domain, index=index, https=https)
    # 结果保存
    result = {"original_domain": domain.strip(), }
    if not _url:
        raise ValueError("url is none.")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/59.0.3071.104 Safari/537.36',
    }
    try:
        # 获取请求响应
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), conn_timeout=1000) as session:
            # print("utl: ", _url)
            async with session.get(_url, allow_redirects=redirect, headers=headers, timeout=5) as resp:
                result["req_url"] = resp.url._val.geturl()
                result["Location"] = resp.headers.get("Location")
                result["status"] = resp.status
                # 获取title
                text = await resp.text(errors="ignore")
                title = getTitle(text)
                result["title"] = title if title else "without title"
                # headers
                _headers = len(resp.raw_headers)
                result["header_count"] = _headers
                # 有些可能没有content-length头部
                result["content_length"] = len(text)
    # python异常 https://blog.csdn.net/polyhedronx/article/details/81589196
    except (aiohttp.ClientResponseError, aiohttp.ClientConnectionError, asyncio.TimeoutError):
        # 连接失败的时候，信息设置为None
        result["req_url"] = None
        result["Location"] = None
        result["status"] = None
        result["title"] = "without title"
        result["header_count"] = None
        result["content_length"] = None
    finally:
        result["protocol"] = None

    # print(result)
    return result


def getTitle(resp):
    """
    获取响应中的title内容
    :param resp: 响应正文，request.get.content
    :return: title文本
    """
    # print("getTitle: ", resp)
    soup = BeautifulSoup(resp, "html.parser")
    _title = soup.find("title")
    if not _title:
        return None
    else:
        return _title.text


def getUrl(domain, index=False, https=False):
    """
    根据域名生成随机的url，指向不存在的资源;；返回随机url
    :param index: boolean 默认获取主页url，即/
    :param domain: 域名
    :return: random url
    """
    _domain = domain.strip()
    # 主页url
    if not https:
        _url = "http://{}/".format(_domain)
    else:
        _url = "https://{}/".format(_domain)
    # 字典,大小写字母及数字，用于生成随机url
    flag = string.ascii_letters + string.digits
    if not index:
        _url += "".join(random.sample(flag, random.randint(3, 10)))
    # print(_url)
    return _url

async def aiomul():
    # dm_list = open("../vipshop.com_sub.txt").readlines()
    dm_list = ["112.65.142.187:443",]
    async with Pool() as pool:
        result = await pool.map(getStatusAndTitle, dm_list)
    # for i in result:
    #     print(i)

if __name__ == "__main__":
    start = time.time()
    task = asyncio.ensure_future(aiomul())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(task)
    print("all done, {}".format(time.time() - start))
