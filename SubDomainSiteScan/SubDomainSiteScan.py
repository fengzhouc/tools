# encoding=utf-8

import socket
import threading, multiprocessing
from util.getRandomUrl import getRandomUrl
from util.getStatusAndTtile import getStatusAndTitle
from util.report import report
from lib.cmdline import parse_args

# 设置超时时间，防止请求时间过长导致程序长时间停止
socket.setdefaulttimeout(5)

def scan_process(dm, n_results, e_results, o_results):
    """
    线程函数
    :param dm: 域名
    :param n_results: 正常站点
    :param e_results: 死站
    :param o_results: 其他站点
    :return:
    """
    # 获取不存在的url
    rurl = getRandomUrl(dm)
    # 获取不存在资源的响应信息，不跟进重定向，getStatusAndTitle函数已处理
    rmess = getStatusAndTitle(rurl)
    # 获取主页url
    indexurl = getRandomUrl(dm, index=True)
    # 获取主页信息，不跟进重定向，getStatusAndTitle函数已处理
    imess = getStatusAndTitle(indexurl)

    # 请求失败的情况
    if (imess[1] is None) or (rmess[2] is None):
        e_results.put(imess)
        return
    # 状态码5xx，且主页状态码相同
    if str(rmess[2]).startswith("5") and rmess[2] == imess[2]:
        e_results.put(imess)
    # 因为请求的时候重定向已处理跟进，所以不会有3xx状态码
    # 状态码2xx、4xx,主页状态码2xx，有种可能都是2xx不正常的页面，但是没想到很好的识别方法，后期补充
    elif (str(rmess[2]).startswith("2") or rmess[2] == 404) and imess[2] == 200:
        n_results.put(imess)
    else:
        o_results.put(imess)
    pass

def getresult(n_results, e_results, o_results):
    """
    从队列中获取结果添加到结果序列中
    :return:
    """
    global STOP_ME
    global nList
    global eList
    global oList
    while not STOP_ME:
        while n_results.qsize() > 0:
            nList.append(n_results.get())
        while e_results.qsize() > 0:
            eList.append(e_results.get())
        while o_results.qsize() > 0:
            oList.append(o_results.get())

if __name__ == "__main__":
    # 命令行获取domain file
    argv = parse_args()
    args_file = argv.f
    _pool = 16
    if argv.p:
        _pool = argv.p

    # 结果分类
    nList = []  # 正常
    n_file = "normal_site"
    eList = []  # 死站
    e_file = "die_site"
    oList = []  # 其他
    o_file = "other_site"

    # lock = threading.Lock()
    global_lock = multiprocessing.Manager().Lock()
    n_results = multiprocessing.Manager().Queue()
    e_results = multiprocessing.Manager().Queue()
    o_results = multiprocessing.Manager().Queue()

    STOP_ME = False
    try:
        # 处理队列中结果的线程
        threading.Thread(target=getresult, args=(n_results, e_results, o_results)).start()

        p = multiprocessing.Pool(16)
        with open(args_file) as f:
            for dm in f:
                # scan_process(dm, nList, eList, oList)
                p.apply_async(scan_process, args=(dm, n_results, e_results, o_results))

            p.close()
            p.join()

            # 写报告
            report(n_file, nList)
            report(e_file, eList)
            report(o_file, oList)

    except KeyboardInterrupt as e:
        STOP_ME = True
        print('You aborted the scan.')
        exit(1)
    except Exception as e:
        print('[__main__.exception] %s %s' % (type(e), str(e)))
    STOP_ME = True
