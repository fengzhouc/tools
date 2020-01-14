# encoding=utf-8

import requests
from bs4 import BeautifulSoup


def getStatusAndTitle(url, redirect=False):
    """
    发送请求，获取状态码及title
    :param redirect: 是否跟进重定向
    :param url: 请求的url
    :return: list [url，status，title]
    """
    # 结果保存
    result = [url, ]
    if not url:
        raise ValueError("url is none.")

    try:
        # 默认是遇到重定向会跟进,allow_redirects控制是否跟进，这里不跟进主要是因为，如果协议不对的话，跟进后就进入的主页
        resp = requests.get(url, allow_redirects=redirect)
        # print(resp.is_redirect)
        result.append(resp.url)
        status = resp.status_code
        result.append(status)
        # 获取title
        title = getTitle(resp.content)
        result.append(title)
    # python异常 https://blog.csdn.net/polyhedronx/article/details/81589196
    except (OSError) as e:
        # 连接失败的时候，信息设置为None
        result.append(None)
        result.append(None)
        result.append(None)

    print(result)
    return result


def getTitle(resp):
    """
    获取响应中的title内容
    :param resp: 响应正文，request.get.content
    :return: title文本
    """
    soup = BeautifulSoup(resp, "html.parser")
    titleS = soup.find("title")
    # print("[debug] ", titleS)
    if not titleS:
        return None
    else:
        # print("[debug] %s", titleS.text)
        return titleS.text
    pass


if __name__ == "__main__":
    getStatusAndTitle("http://www.vip.com/sdfas", redirect=False)
