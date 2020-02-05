# encoding=utf-8
import os
import socket
import threading, multiprocessing
import time

import xlwt
from lib.cmdline import parse_args
from lib.core import getUrl, getStatusAndTitle

# 设置超时时间，防止请求时间过长导致程序长时间停止
socket.setdefaulttimeout(5)


def scan_process(dm, a_results, b_results, c_results, d_results):
    """
    主逻辑
    :param dm: 域名
    :param a_results: 正常网站
    :param b_results: 访问受限网站
    :param c_results: 不正常网站
    :param d_results: 不是网站
    :return:
    """
    # print("scan_process start[{}]: {}".format(os.getpid(), dm))
    # 是否https
    _https = False
    # 获取不存在的url
    # _url = getUrl(dm)
    # 获取不存在资源的响应信息，不跟进重定向，getStatusAndTitle函数已处理
    _mess = getStatusAndTitle(dm)

    # 判断是否400， 请求错误
    if _mess.get("status") == 400:
        _https = True
        _mess = getStatusAndTitle(dm, https=True)
        if _mess.get("status") == 400:
            c_results.put(_mess.values())
            return

    # 状态码200，进行分支访问主页继续判断
    _is404 = False
    if _mess.get("status") == 200:
        # 这里是状态码200的错误页面的关键字，后续需要更新以保证正确性
        _key404 = ["404", "找不到", "not found"]
        for i in _key404:
            _is404 = True if i in _mess.get("title") else False
            if _is404:
                break
        # 如果包含关键字，则是状态码为200的错误页面，这种情况错误处理是自定义的，基本可以判断是正常网站，直接存入A类
        if _is404:
            a_results.put(_mess.values())
        # 如果不包含，则需要进一步确认主页
        else:
            r = getindexmess(dm, _mess, _is404, _https, a_results, b_results, c_results, d_results)
            # 如果是处200/401/407/415的其他状态码，则重新请求请求再确认一次
            if r is c_results:
                # 如果已经确认2次了，则直接保存结果，否则重新请求主页确认，访问次数+1，以第二次访问的结果为准保存
                r = getindexmess(dm, _mess, _is404, _https, a_results, b_results, c_results, d_results)
                r.put(_mess.values())
            else:
                r.put(_mess.values())

    # 状态码404，进行分支访问主页继续判断
    elif _mess.get("status") == 404:
        r = getindexmess(dm, _mess, _is404, _https, a_results, b_results, c_results, d_results)
        # 如果是处200/401/407/415的其他状态码，则重新请求请求再确认一次
        if r is c_results:
            # 如果已经确认2次了，则直接保存结果，否则重新请求主页确认，访问次数+1，以第二次访问的结果为准保存
            r = getindexmess(dm, _mess, _is404, _https, a_results, b_results, c_results, d_results)
            r.put(_mess.values())
        else:
            r.put(_mess.values())

    # 判断状态码是否401,407,415，都是需要认证的
    elif _mess.get("status") in [401, 403, 407, 415]:
        b_results.put(_mess.values())

    # 判断是否有状态码，有则是不正常网站，否则可能不是网站
    elif _mess.get("status") is None:
        d_results.put(_mess.values())
    else:
        c_results.put(_mess.values())
    # print("scan_process over[{}]".format(os.getpid()))

def getindexmess(dm, mess404, _is404, _https, a_results, b_results, c_results, d_results):
    """
    主页请求判断分支函数封装
    :param dm: 域名，生成url
    :param mess404:  前面不存在资源的访问结果
    :param _is404:  前面不存在资源的访问结果是否是404页面
    :param _https:  协议是否https
    :return:  站点分类，A,B,C,D
    """
    # 获取主页url
    # _indexurl = getUrl(dm, index=True)
    _mess_index = getStatusAndTitle(dm, index=True, https=_https)
    # 如果状态码200，跟不存在资源请求的响应作比较，看是否相同，相同则C类，否则A类
    if _mess_index.get("status") == 200:
        # 这里_is404的作用主要是做兼容的，不存在资源访问状态码404,200的区分兼容，只有200且不包含404关键字的时候才需要比对不存在资源响应跟主页响应是否相同
        if _is404 and (mess404.get("header_count") == _mess_index.get("header_count")) and (
                mess404.get("content_length") == _mess_index.get("content_length")):
            return c_results
        return a_results
    # 判断状态码是否401,403,407,415，都是需要认证的
    if mess404.get("status") in [401, 403, 407, 415]:
        return b_results
    # 判断是否有状态码，有则在访问主页确认，否则可能不是网站
    if mess404.get("status") is None:
        return d_results
    else:
        return c_results


def getresult():
    """
    从队列中获取结果写到excel
    :return:
    """
    wb = xlwt.Workbook()
    column_keys = ['original_domain', 'redirect_url', 'status', 'title', 'header_count', 'content_length']
    a = wb.add_sheet("A类 正常网站")
    for column, m in enumerate(column_keys):
        a.write(0, column, m)
    b = wb.add_sheet("B类 访问受限网站")
    for column, m in enumerate(column_keys):
        b.write(0, column, m)
    c = wb.add_sheet("C类 非正常网站")
    for column, m in enumerate(column_keys):
        c.write(0, column, m)
    d = wb.add_sheet("D类 不是网站")
    for column, m in enumerate(column_keys):
        d.write(0, column, m)

    global STOP_ME
    global a_results
    global b_results
    global c_results
    global d_results
    # 报告行数记录
    aline = 0
    bline = 0
    cline = 0
    dline = 0
    while not STOP_ME:
        print("[#Report_Thread] A:{} B:{} C:{} D:{} total:{} ".format(aline, bline, cline, dline, aline+bline+cline+dline), end="\r")
        if a_results.qsize() > 0:
            aline = writerdata(a, a_results.get(), aline)
        if b_results.qsize() > 0:
            bline = writerdata(b, b_results.get(), bline)
        if c_results.qsize() > 0:
            cline = writerdata(c, c_results.get(), cline)
        if d_results.qsize() > 0:
            dline = writerdata(d, d_results.get(), dline)
    wb.save("./report/{}.xls".format(str(time.time())))

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

if __name__ == "__main__":
    # 命令行获取domain file
    argv = parse_args()
    args_file = argv.f
    _pool = 8
    if argv.p:
        _pool = int(argv.p)
    # args_file = "1.txt"
    # _pool = 1

    global_lock = multiprocessing.Manager().Lock()
    a_results = multiprocessing.Manager().Queue()
    b_results = multiprocessing.Manager().Queue()
    c_results = multiprocessing.Manager().Queue()
    d_results = multiprocessing.Manager().Queue()

    STOP_ME = False
    try:
        # 处理队列中结果的线程
        threading.Thread(target=getresult).start()

        p = multiprocessing.Pool(_pool)
        with open(args_file) as f:
            for dm in f:
                p.apply_async(scan_process, args=(dm, a_results, b_results, c_results, d_results))
        p.close()
        p.join()
        # 所有进程任务执行完成后，为了保证报告线程能处理完队列中的数据
        time.sleep(5)
        STOP_ME = True
        print("\nAll done.")
    except KeyboardInterrupt as e:
        print('You aborted the scan.')
        exit(1)
    except Exception as e:
        print('[__main__.exception] %s %s' % (type(e), str(e)))
    finally:
        STOP_ME = True
