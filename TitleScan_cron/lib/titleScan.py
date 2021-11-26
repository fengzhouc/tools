# encoding=utf-8

from gevent.pool import Pool
from gevent.queue import Queue

from lib.core import getStatusAndTitle
from lib.config import processes
from lib import glo


# 这里是状态码200的错误页面的关键字，后续需要更新以保证正确性
_key404 = ["404", "找不到", "Not Found"]
# 标题关键字，识别特殊错误，这个以后需要持续完善的，太多定制的错误我们需要每次持续的更新
keyworkd = ["访问拦截",
            "网站访问报错", ]


def async_scan_process(targets, pros=None):
    """

   :param targets: [{dm:[ip:port,dm:port]}]
   :param pros:os.spu_count()
   :return:
   """
    if pros:
        pool = Pool(pros)
    else:
        pool = Pool(processes)
    for target in targets:
        pool.spawn(scan_process, target)


def scan_process(target):
    """
    主逻辑
    :param target: 扫描目标 {domain, [ip:port,dm:port]}
    :param result_queue: 每类结果的队列
    :return:
    """
    print("scan_process")
    # 不同分类的结果队列
    # all_results, a_results, b_results, c_results, d_results, e_results = result_queue
    all_results, a_results, b_results, c_results, d_results, e_results = glo.get_all().values()
    domain = list(target.keys())[0]  # 域名
    ips = list(target.values())[0]  # 域名/ip组合端口的所有数据
    # 扫描列表，主要是http/https两种协议
    target_dict = {}
    for dm in ips:
        # 获取不存在资源的响应信息，不跟进重定向，getStatusAndTitle函数已处理
        http_mess = getStatusAndTitle(domain, dm)
        # http状态码400 或者请求失败时尝试https
        if http_mess.get("status") == 400 or http_mess.get("status") is None:
            https_mess = getStatusAndTitle(domain, dm, https=True)
            target_dict[https_mess["index_url"]] = https_mess
        elif str(http_mess.get("status")).startswith("30"):
            https_mess = getStatusAndTitle(domain, dm, https=True)
            # 请求失败时,则只支持http
            if https_mess.get("status") is None:
                target_dict[http_mess["index_url"]] = http_mess
            # https状态码20x，而且重定向是同一个域，则认为是同样的网站，支持http/https
            elif str(https_mess.get("status")).startswith("20") and http_mess["original_domain"] == http_mess["Location"]:
                target_dict[http_mess["index_url"]] = http_mess
            # https状态码30x，如果跳转同一个页面，则认为是同样的网站，支持http/https
            elif str(https_mess.get("status")).startswith("30") and https_mess["Location"] == http_mess["Location"]:
                target_dict[http_mess["index_url"]] = http_mess
            else:
                target_dict[http_mess["index_url"]] = http_mess
                target_dict[https_mess["index_url"]] = https_mess
        else:
            https_mess = getStatusAndTitle(domain, dm, https=True)
            # 如果状态码即title都相同，则认为是同一个站点，支持http/https
            if http_mess.get("status") == https_mess.get("status") and http_mess.get("title") == https_mess.get("title"):
                target_dict[http_mess["index_url"]] = http_mess
            else:
                target_dict[http_mess["index_url"]] = http_mess
                target_dict[https_mess["index_url"]] = https_mess

    # print(target_dict)
    # 循环扫描target_dict里的目标，这样就包含了http、https
    for pro in target_dict.keys():
        _https = True if "https" in pro.split("://") else False
        _mess = target_dict[pro]
        dm = _mess["original_domain"]

        # 这里不会有http 400的情况，上面做了过滤，如果http 400 ，则target_dict中只有https
        if _mess.get("status") == 400 and _https:
            c_results.put(_mess)
            all_results.put(_mess)
            continue

        # 不存在目录请求状态码200，进行分支访问主页继续判断
        _is404 = False
        if _mess.get("status") == 200:
            for i in _key404:
                _is404 = True if i in _mess.get("title") else False
                if _is404:
                    break
            # 如果包含关键字，则是状态码为200的错误页面，这种情况错误处理是自定义的，基本可以判断是正常网站，直接存入A类
            if _is404:
                a_results.put(_mess)
                all_results.put(_mess)  # 添加到汇总队列
            # 如果不包含，则需要进一步确认主页
            else:
                # _checkcentent=True, 不存在目录跟主页状态码都在200的情况下进行相似度比较
                r, index_mess = getindexmess(domain, dm, _mess, _https, a_results, b_results, c_results,
                                                   d_results, e_results, _checkcentent=True)
                all_results.put(index_mess)  # 添加到汇总队列
                # 主页如果属于D类，即状态码501/502/503/504/请求失败，则重新请求请求再确认一次
                if r is d_results:
                    # 以第二次访问的结果为准保存
                    r, index_mess = getindexmess(domain, dm, _mess, _https, a_results, b_results, c_results,
                                                       d_results, e_results, _checkcentent=True)
                    r.put(index_mess)
                # 其他类的结果
                else:
                    r.put(index_mess)
        # 不存在目录请求状态码30x，A类
        elif str(_mess.get("status")).startswith("30"):
            i_mess = getStatusAndTitle(domain, dm, index=True, redirect=True, https=_https)
            all_results.put(i_mess)  # 添加到汇总队列
            # 这里可能会出现协议转换的302,跟进302,看是否访问正常，确定是协议转换则抛弃
            if _mess.get("index_url").split("://")[0] != i_mess.get("index_url").split("://")[0]:
                pass
            elif i_mess.get("status") in [200, 302]:
                a_results.put(i_mess)
            elif i_mess.get("status") in [404, ]:
                c_results.put(i_mess)
            elif i_mess.get("status") in [401, 407, 415]:
                b_results.put(i_mess)
            elif (i_mess.get("status") is None) or (i_mess.get("status") in [501, 502, 503, 504]):
                d_results.put(i_mess)
            # 预料之外的情况，需要关注，以完善工具
            else:
                e_results.put(_mess)
        # 不存在目录请求状态码404，进行分支访问主页继续判断
        elif _mess.get("status") == 404:
            r, index_mess = getindexmess(domain, dm, _mess, _https, a_results, b_results, c_results, d_results, e_results)
            all_results.put(index_mess)  # 添加到汇总队列
            # 如果是D类，则重新请求再确认一次
            if r is d_results:
                # 以第二次访问的结果为准保存
                r, index_mess = getindexmess(domain, dm, _mess, _https, a_results, b_results, c_results,
                                                   d_results, e_results)
                r.put(index_mess)
            # 其他类的结果
            else:
                r.put(index_mess)

        # 不存在目录请求状态码是否401,407,415，都是需要认证的,大概率正常网站，因为做了认证
        elif _mess.get("status") in [401, 407, 415]:
            b_results.put(_mess)
            all_results.put(_mess)  # 添加到汇总队列
        # 不存在目录请求状态码403，500，小概率正常网站
        elif _mess.get("status") in [403, 500]:
            c_results.put(_mess)
            all_results.put(_mess)  # 添加到汇总队列
        # 不存在目录请求状态码是否501，502，503，504及没有，不存在目录返回这些状态码，说明不是正常网站
        elif (_mess.get("status") is None) or (_mess.get("status") in [501, 502, 503, 504]):
            d_results.put(_mess)
            all_results.put(_mess)  # 添加到汇总队列
        # 预料之外的情况，需要关注，以完善工具
        else:
            e_results.put(_mess)
            all_results.put(_mess)  # 添加到汇总队列


def getindexmess(domain, dm, mess404, _https, a_results, b_results, c_results, d_results, e_results, _checkcentent=False):
    """
    主页请求判断分支函数封装
    :param dm: 域名，生成url
    :param mess404:  前面不存在资源的访问结果
    :param _checkcentent:  不存在目录跟主页状态码都在200的情况下进行相似度比较
    :param _https:  协议是否https
    :return:  站点分类，A,B,C,D,E
    """
    # 请求主页信息
    _mess_index = getStatusAndTitle(domain, dm, index=True, https=_https)
    # 特殊错误识别，相似度比较
    if _mess_index.get("title") in keyworkd or \
            (_mess_index.get("status") == mess404.get("status") and
             mess404.get("title") == _mess_index.get("title") and
             _mess_index.get("contenthash") == mess404.get("contenthash")):
        return c_results, _mess_index

    # 主页状态码200，跟不存在资源请求的响应作比较，看是否相同，相同则C类，否则A类
    if _mess_index.get("status") == 200:
        # 不存在目录跟主页状态码都在200的情况下进行相似度比较
        if _checkcentent and (mess404.get("header_count") == _mess_index.get("header_count")) \
                and (mess404.get("contenthash") == _mess_index.get("contenthash")):
            return c_results, _mess_index
        return a_results, _mess_index
    # 主页状态码30x，A类
    if str(_mess_index.get("status")).startswith("30"):
        return a_results, _mess_index
    # 主页判断状态码是否401,403,404,407,415，都是需要认证的
    if _mess_index.get("status") in [401, 403, 404, 407, 415]:
        return b_results, _mess_index
    # 主页状态码400,500，说明主页异常，可能没有设置主页，
    if _mess_index.get("status") in [400, 500]:
        return c_results, _mess_index
    # 主页是否有状态码，有则在访问主页确认，否则可能不是网站
    if (_mess_index.get("status") is None) or (_mess_index.get("status") in [501, 502, 503, 504]):
        return d_results, _mess_index
    else:
        return e_results, _mess_index


if __name__ == "__main__":
    glo._init()
    all_results = Queue()
    glo.set_value("all", all_results)
    a_results = Queue()
    glo.set_value("a", a_results)
    b_results = Queue()
    glo.set_value("b", b_results)
    c_results = Queue()
    glo.set_value("c", c_results)
    d_results = Queue()
    glo.set_value("d", d_results)
    e_results = Queue()
    glo.set_value("e", e_results)
    t = [{"a": ["3.24.119.219:443","112.53.42.125:587","112.53.42.125:995","112.53.42.125:993","120.232.22.49:25","boe.mindlinker.com:80","120.232.22.49:110","120.232.22.49:143","120.232.22.49:465","120.232.22.49:993","120.232.22.49:587","120.232.22.49:843","smtp.bytello.com:843","120.232.22.49:995","120.232.27.164:25","120.232.27.164:110","120.232.27.164:143","120.232.27.164:465","120.232.27.164:587","120.232.27.164:993","120.232.27.164:995","20.79.64.165:80","eus-azure-http-external.bytello.com:80","20.79.64.165:443"]}]
    async_scan_process(t, pros=4)
    pass
