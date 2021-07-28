# encoding=utf-8
import asyncio
import functools
import multiprocessing
import threading
import time

import xlwt
from lib.cmdline import parse_args

from lib.config import yellow, green, red, blue, end, processes
from lib.dnsQuery import dns_query
from lib.portScan import async_port_scan
from lib.titleScan import async_scan_process


# 将结果写入文件
def getresult():
    """
    从队列中获取结果写到excel
    :return:
    """
    # TODO 做一个汇总页
    wb = xlwt.Workbook()
    column_keys = ['target_domain', 'original_domain', 'index_url', "Location", 'status', 'title', 'contenthash']
    all = wb.add_sheet("汇总")
    for column, m in enumerate(column_keys):
        all.write(0, column, m)
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
    global all_results
    global a_results
    global b_results
    global c_results
    global d_results
    global e_results
    # 报告行数记录
    allline = 0
    aline = 0
    bline = 0
    cline = 0
    dline = 0
    eline = 0
    while not STOP_ME:
        print("{}[Schedule] A:{} B:{} C:{} D:{} E:{} ,total:{} {}".format(yellow, aline, bline, cline, dline, eline,
                                                                          aline + bline + cline + dline + eline, end),
              end="\r")
        if all_results.qsize() > 0:
            allline = writerdata(all, all_results.get(), allline)
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



def main(all_results, a_results, b_results, c_results, d_results, e_results):
    # 命令行获取domain file
    argv = parse_args()
    args_file = argv.f
    # 默认根据cpu数量
    _pool = processes
    if argv.p:
        _pool = int(argv.p)
    # 读取所有域名，并去重
    dm_list = list(set(open(args_file).readlines()))
    print("{}[TitleScan] all domain total: {}{}".format(blue, len(dm_list), end))
    # 查询每个域名的ip
    print("{}[DnsQuery] Start dnsQuery......{}".format(blue, end))
    # rqueue是结果队列, {dm: [ip,ip1,ip2], dm1: [ip,ip1,ip2]}
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
    targets = async_port_scan(rqueue)

    # targets = [{dm.strip(): [dm.strip(), ]} for dm in dm_list]
    time.sleep(1)
    target_num = 0
    for i in targets:
        target_num += len(i.values()[0])
    print("{}[TiltleScan] Start ScanProcess...., total: {} {}".format(blue, target_num, end))
    # 处理队列中结果的线程
    threading.Thread(target=getresult).start()
    # titlescan
    async_scan_process(targets, result_queue=(all_results, a_results, b_results, c_results, d_results, e_results))


if __name__ == "__main__":

    STOP_ME = False
    start = time.time()
    try:
        all_results = multiprocessing.Manager().Queue()
        a_results = multiprocessing.Manager().Queue()
        b_results = multiprocessing.Manager().Queue()
        c_results = multiprocessing.Manager().Queue()
        d_results = multiprocessing.Manager().Queue()
        e_results = multiprocessing.Manager().Queue()

        main(all_results, a_results, b_results, c_results, d_results, e_results)

    except KeyboardInterrupt as e:
        print('\n{}You aborted the scan.{}'.format(yellow, end))
        exit(1)
    except Exception as e:
        print('\n{}[__main__.exception] {} {}{}'.format(red, type(e), str(e), end))
    finally:
        STOP_ME = True
        print("\n{}All done, times:{}{}".format(green, time.time() - start, end))
