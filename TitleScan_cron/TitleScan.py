# encoding=utf-8
import asyncio
import functools
import multiprocessing
import socket
import threading
import time
import xlwt
from aiomultiprocess import Pool
from lib.cmdline import parse_args
from lib.core import getStatusAndTitle

from lib.config import yellow, green, red, blue, end, processes
from lib.dnsQuery import dns_query
from lib.portScan import port_scan

# 设置超时时间，防止请求时间过长导致程序长时间停止
socket.setdefaulttimeout(5)

# 这里是状态码200的错误页面的关键字，后续需要更新以保证正确性
_key404 = ["404", "找不到", "Not Found"]
# 标题关键字，识别特殊错误，这个以后需要持续完善的，太多定制的错误我们需要每次持续的更新
keyworkd = ["访问拦截",
            "网站访问报错", ]

async def scan_process(target, result_queue=None):
    """
    主逻辑
    :param target: 扫描目标 {domain, [ip:port,dm:port]}
    :param result_queue: 每类结果的队列
    :return:
    """
    # 不同分类的结果队列
    a_results, b_results, c_results, d_results, e_results = result_queue
    domain = list(target.keys())[0]  # 域名
    ips = list(target.values())[0]  # 域名/ip组合端口的所有数据
    # 扫描列表，主要是http/https两种协议
    target_dict = {}
    for dm in ips:
        # 获取不存在资源的响应信息，不跟进重定向，getStatusAndTitle函数已处理
        http_mess = await getStatusAndTitle(domain, dm)
        # http状态码400 或者请求失败时尝试https
        if http_mess.get("status") == 400 or http_mess.get("status") is None:
            https_mess = await getStatusAndTitle(domain, dm, https=True)
            target_dict[https_mess["index_url"]] = https_mess
        elif str(http_mess.get("status")).startswith("30"):
            https_mess = await getStatusAndTitle(domain, dm, https=True)
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
            https_mess = await getStatusAndTitle(domain, dm, https=True)
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
            c_results.put(_mess.values())
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
                a_results.put(_mess.values())
            # 如果不包含，则需要进一步确认主页
            else:
                # _checkcentent=True, 不存在目录跟主页状态码都在200的情况下进行相似度比较
                r, index_mess = await getindexmess(domain, dm, _mess, _https, a_results, b_results, c_results,
                                                   d_results, e_results, _checkcentent=True)
                # 主页如果属于D类，即状态码501/502/503/504/请求失败，则重新请求请求再确认一次
                if r is d_results:
                    # 以第二次访问的结果为准保存
                    r, index_mess = await getindexmess(domain, dm, _mess, _https, a_results, b_results, c_results,
                                                       d_results, e_results, _checkcentent=True)
                    r.put(index_mess.values())
                # 其他类的结果
                else:
                    r.put(index_mess.values())
        # 不存在目录请求状态码30x，A类
        elif str(_mess.get("status")).startswith("30"):
            i_mess = await getStatusAndTitle(domain, dm, index=True, redirect=True, https=_https)
            a_results.put(i_mess.values())
        # 不存在目录请求状态码404，进行分支访问主页继续判断
        elif _mess.get("status") == 404:
            r, index_mess = await getindexmess(domain, dm, _mess, _https, a_results, b_results, c_results, d_results, e_results)
            # 如果是D类，则重新请求再确认一次
            if r is d_results:
                # 以第二次访问的结果为准保存
                r, index_mess = await getindexmess(domain, dm, _mess, _https, a_results, b_results, c_results,
                                                   d_results, e_results)
                r.put(index_mess.values())
            # 其他类的结果
            else:
                r.put(index_mess.values())

        # 不存在目录请求状态码是否401,407,415，都是需要认证的,大概率正常网站，因为做了认证
        elif _mess.get("status") in [401, 407, 415]:
            b_results.put(_mess.values())
        # 不存在目录请求状态码403，500，小概率正常网站
        elif _mess.get("status") in [403, 500]:
            c_results.put(_mess.values())
        # 不存在目录请求状态码是否501，502，503，504及没有，不存在目录返回这些状态码，说明不是正常网站
        elif (_mess.get("status") is None) or (_mess.get("status") in [501, 502, 503, 504]):
            d_results.put(_mess.values())
        # 预料之外的情况，需要关注，以完善工具
        else:
            e_results.put(_mess.values())


async def getindexmess(domain, dm, mess404, _https, a_results, b_results, c_results, d_results, e_results, _checkcentent=False):
    """
    主页请求判断分支函数封装
    :param dm: 域名，生成url
    :param mess404:  前面不存在资源的访问结果
    :param _checkcentent:  不存在目录跟主页状态码都在200的情况下进行相似度比较
    :param _https:  协议是否https
    :return:  站点分类，A,B,C,D,E
    """
    # 请求主页信息
    _mess_index = await getStatusAndTitle(domain, dm, index=True, https=_https)
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


def getresult():
    """
    从队列中获取结果写到excel
    :return:
    """
    wb = xlwt.Workbook()
    column_keys = ['target_domain', 'original_domain', 'index_url', "Location", 'status', 'title', 'contenthash']
    a = wb.add_sheet("A类 正常网站（重点关注）")
    for column, m in enumerate(column_keys):
        a.write(0, column, m)
    b = wb.add_sheet("B类 大概率正常网站（重点关注）")
    for column, m in enumerate(column_keys):
        b.write(0, column, m)
    c = wb.add_sheet("C类 小概率正常网站")
    for column, m in enumerate(column_keys):
        c.write(0, column, m)
    d = wb.add_sheet("D类 非正常网站")
    for column, m in enumerate(column_keys):
        d.write(0, column, m)
    e = wb.add_sheet("E类 意外情况（需要关注）")
    for column, m in enumerate(column_keys):
        e.write(0, column, m)
    # 报告文件名以时间
    report_filename = time.strftime("%Y%m%d%H%M%S", time.localtime())

    global STOP_ME
    global a_results
    global b_results
    global c_results
    global d_results
    global e_results
    # 报告行数记录
    aline = 0
    bline = 0
    cline = 0
    dline = 0
    eline = 0
    while not STOP_ME:
        print("{}[Schedule] A:{} B:{} C:{} D:{} E:{} ,total:{} {}".format(yellow, aline, bline, cline, dline, eline,
                                                                          aline + bline + cline + dline + eline, end),
              end="\r")
        if a_results.qsize() > 0:
            aline = writerdata(a, a_results.get(), aline)
        if b_results.qsize() > 0:
            bline = writerdata(b, b_results.get(), bline)
        if c_results.qsize() > 0:
            cline = writerdata(c, c_results.get(), cline)
        if d_results.qsize() > 0:
            dline = writerdata(d, d_results.get(), dline)
        if e_results.qsize() > 0:
            eline = writerdata(e, e_results.get(), eline)
    wb.save("./report/{}.xls".format(report_filename))
    print("{}report save success, file name: {}.xls{}".format(green, report_filename, end))


def writerdata(worksheet, message, row):
    """

    :param worksheet:  excel sheet 对象
    :param message:  写入的数据，list
    :param row:  当前sheet已写了多少行，在+1行继续写入
    :return: 返回写完后的行数
    """
    # print(message)
    row += 1
    for column, m in enumerate(message):
        worksheet.write(row, column, m)
    return row


async def main(a_results, b_results, c_results, d_results, e_results):
    # 命令行获取domain file
    argv = parse_args()
    args_file = argv.f
    # 默认根据cpu数量
    _pool = processes
    if argv.p:
        _pool = int(argv.p)
    # 读取所有域名，并去重
    dm_list = list(set(open(args_file).readlines()))
    # 查询每个域名的ip
    print("{}[DnsQuery] Start dnsQuery......{}".format(blue, end))
    # rqueue是结果队列, {dm: [ip]}
    rqueue = multiprocessing.Manager().Queue()
    start_dns = time.time()
    dns_pool = multiprocessing.Pool(processes=_pool)
    dns_pool.map(functools.partial(dns_query, rqueue=rqueue), dm_list)
    dns_pool.close()
    dns_pool.join()
    print("{}[DnsQuery] DnsQuery Over, time: {}.{}".format(blue, time.time() - start_dns, end))

    time.sleep(1)
    # 端口扫描，返回端口跟域名/ip组合的列表
    # 预期返回: [{dm:[ip:port,dm:port]}]
    print("{}[PortScan] Start portScan......{}".format(yellow, end))
    start_dns = time.time()
    targets = port_scan(rqueue)
    print("{}[PortScan] PortScan Over, time: {}{}".format(yellow, time.time() - start_dns, end))

    # targets = [{dm.strip(): [dm.strip(), ]} for dm in dm_list]
    time.sleep(1)
    print("{}[TiltleScan] Start ScanProcess......{}".format(blue, end))
    # 处理队列中结果的线程
    threading.Thread(target=getresult).start()
    # titlescan
    async with Pool(processes=_pool) as pool:
        result = await pool.map(
            functools.partial(scan_process, result_queue=(a_results, b_results, c_results, d_results, e_results)),
            targets)


if __name__ == "__main__":

    STOP_ME = False
    try:
        a_results = multiprocessing.Manager().Queue()
        b_results = multiprocessing.Manager().Queue()
        c_results = multiprocessing.Manager().Queue()
        d_results = multiprocessing.Manager().Queue()
        e_results = multiprocessing.Manager().Queue()

        start = time.time()
        task = asyncio.ensure_future(main(a_results, b_results, c_results, d_results, e_results))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(task)

    except KeyboardInterrupt as e:
        print('\n{}You aborted the scan.{}'.format(yellow, end))
        exit(1)
    except Exception as e:
        print('\n{}[__main__.exception] {} {}{}'.format(red, type(e), str(e), end))
    finally:
        STOP_ME = True
        print("\n{}all done, times:{}{}".format(green, time.time() - start, end))
