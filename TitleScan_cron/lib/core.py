# encoding=utf-8
import aiohttp
import requests
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

    try:
        # 获取请求响应
        resp = await getResp(_url, redirect=redirect)

        result["redirect_url"] = resp.url
        status = resp.status_code
        result["status"] = status
        # 获取title
        title = getTitle(resp.text)
        result["title"] = title if title else "without title"
        # headers
        _headers = len(resp.headers)
        result["header_count"] = _headers
        # 有些可能没有content-length头部
        # content_length = resp.headers.get("content-length")
        result["content_length"] = len(resp.content)
    # python异常 https://blog.csdn.net/polyhedronx/article/details/81589196
    except OSError as e:
        # 连接失败的时候，信息设置为None
        result["redirect_url"] = None
        result["status"] = None
        result["title"] = "without title"
        result["header_count"] = None
        result["content_length"] = None

    # print(result)
    return result


async def getResp(url, redirect=False):
    """
    获取响应，不过对状态码判断是否重定向，若重定向则递归获取最后的请求响应
    :param url: 请求的url
    :param redirect: 是否跟进重定向
    :return: 请求响应
    """
    # 默认是遇到重定向会跟进, allow_redirects控制是否跟进，这里不跟进主要是因为，如果协议不对的话，跟进后就进入的主页
    resp = await asyncio.get_event_loop().run_in_executor(None, requests.get, url)
    if resp.is_redirect:
        location = resp.headers.get("Location")
        # 默认是发起http请求，如果使用的是https，出现302重定向是到主页的，对于随机url就丢失了，这里做下处理
        if not url.endswith("/") and str(location).endswith("/"):
            location += url.split("/").pop()
        # print(location)
        resp = getResp(location)
    return resp
    # async with aiohttp.ClientSession() as session:
    #     async with session.get(url, allow_redirects=redirect, timeout=5) as resp:
    #         if str(resp.status).startswith("3"):
    #             location = resp.headers.get("Location")
    #             # 默认是发起http请求，如果使用的是https，出现302重定向是到主页的，对于随机url就丢失了，这里做下处理
    #             if not url.endswith("/") and str(location).endswith("/"):
    #                 location += url.split("/").pop()
    #             # print(location)
    #             resp = getResp(location)
    #         return resp


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
    if (len(_domain.split(":")) > 1) and _domain.split(":").pop() in ["443", "8443"]:
        https = True
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


if __name__ == "__main__":
    getStatusAndTitle("vip.com:443", redirect=False)
    getUrl("sdfasd", https=True)
