# encoding = utf-8
import string
import random


def getRandomUrl(domain, index=False):
    """
    根据域名生成随机的url，指向不存在的资源;；返回随机url
    :param index: boolean 默认获取主页url，即/
    :param domain: 域名
    :return: random url
    """
    # 主页url
    _url = "http://{}/".format(domain.strip())
    # 字典
    flag = string.ascii_letters + string.digits
    if not index:
        _url += "".join(random.sample(flag, random.randint(3, 10)))
    # print(_url)
    return _url

if __name__ == "__main__":
    getRandomUrl("sdfasd")