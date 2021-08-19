# encoding=utf-8

import re
import string
import random
import requests
import socket

from requests.packages.urllib3.exceptions import InsecureRequestWarning
# 关闭安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def getTitle(resp):
    """
    获取响应中的title内容
    :param resp: 响应正文，request.get.content
    :return: title文本
    """
    # print("getTitle: ", resp)
    key = "<title.*?>(.*)</title>"
    title = re.findall(key, resp)
    if title:
        return title[0]
    return None


def getStatusAndTitle(domain, target, index=False, https=False, redirect=False):
    """
    发送请求，获取状态码及title
    :param https: 是否使用https协议发送请求
    :param redirect: 是否跟进重定向
    :param domain: 域名
    :return: dict [target_domain, original_domain, rediect_url, status，title, header_count, content-length]
    """
    _url = getUrl(target, index=index, https=https)
    # 结果保存
    result = {"target_domain": domain, "original_domain": target, }
    # print(_url)
    if not _url:
        raise ValueError("url is none.")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/59.0.3071.104 Safari/537.36',
        'Referer': _url,
    }
    try:
        # 获取请求响应, timeout=10
        resp = requests.get(_url, headers=headers, verify=False, allow_redirects=redirect, timeout=10)
        result["index_url"] = _url
        result["Location"] = resp.headers.get("Location")
        result["status"] = resp.status_code
        # 获取title, content获取的是bytes类型
        text = resp.content
        title = getTitle(text.decode("utf-8", "ignore"))
        result["title"] = title if title else ""
        result["contenthash"] = hash(text)
        result["headers"] = resp.headers
    # python异常 https://blog.csdn.net/polyhedronx/article/details/81589196
    except RuntimeError as e:
        # print("{}[EXCEPT] {} {} {}".format(red, _url, "connect error", end))
        # 连接失败的时候，信息设置为None
        result["index_url"] = _url
        result["Location"] = None
        result["status"] = None
        result["title"] = str(e)
        result["contenthash"] = None
        result["headers"] = None
    except UnicodeDecodeError as e:
        # 编码不一致的情况，或者响应不是文本，而是二进制流
        result["title"] = str(e)
        result["contenthash"] = None
        result["headers"] = None
    except socket.error as e:
        # winerror 10054 连接重置,可能还是个站点，但出现了某种去情况，手动试试
        result["index_url"] = _url
        result["Location"] = None
        result["status"] = None
        result["title"] = str(e)
        result["contenthash"] = None
        result["headers"] = None
    finally:
        pass
    # print(result)
    return result


def getUrl(domain, index=False, https=False):
    """
    根据域名生成随机的url，指向不存在的资源;；返回随机url
    :param index: boolean 默认获取不存在url
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


if __name__ == "__main__":
    print(getStatusAndTitle("a", "boe.minnker.com:80"))
    l = []
    ts = []
    # pool = Pool(os.cpu_count())
    # for i in l:
    #     # r = gevent.spawn(getStatusAndTitle, "a", i)
    #     # ts.append(r)
    #     ts.append(pool.spawn(getStatusAndTitle, "a", i))
    #
    # gevent.joinall(ts)
    # for r in ts:
    #     print(r.get())
