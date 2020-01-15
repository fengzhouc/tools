# encoding=utf-8

import requests
from bs4 import BeautifulSoup


def getStatusAndTitle(url, redirect=False):
    """
    发送请求，获取状态码及title
    :param redirect: 是否跟进重定向
    :param url: 请求的url
    :return: list [url，rediect_url, status，title]
    """
    # 结果保存
    result = [url, ]
    if not url:
        raise ValueError("url is none.")

    try:
        # 获取请求响应
        resp = getResp(url, redirect=redirect)

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


def getResp(url, redirect=False):
    """
    获取响应，不过对状态码判断是否重定向，若重定向则递归获取最后的请求响应
    :param url: 请求的url
    :param redirect: 是否跟进重定向
    :return: 请求响应
    """
    # 默认是遇到重定向会跟进, allow_redirects控制是否跟进，这里不跟进主要是因为，如果协议不对的话，跟进后就进入的主页
    resp = requests.get(url, allow_redirects=redirect)
    if resp.is_redirect:
        location = resp.headers.get("Location")
        # 默认是发起http请求，如果使用的是https，重定向是到主页的，对于随机url就丢失了，这里做下处理
        if not url.endswith("/") and str(location).endswith("/"):
            location += url.split("/").pop()
        # print(location)
        resp = getResp(location)
    return resp

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
    getStatusAndTitle("http://vip.com/sdfas", redirect=False)
