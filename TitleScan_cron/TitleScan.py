# encoding=utf-8
import csv

from gevent import monkey
# gevent需要修改Python自带的一些标准库，这一过程在启动时通过monkey patch完成
# 这个需要放置在最前。虽然实际使用是在子模块，不然会有告警，影响程序执行
monkey.patch_socket()
monkey.patch_ssl()
monkey.patch_queue()

import functools
import multiprocessing
import os
import threading
import time

# import xlwt
from lib.cmdline import parse_args

from lib.config import yellow, green, red, blue, end, processes
from lib.dnsQuery import dns_query
from lib.portScan import async_port_scan
from lib.titleScan import async_scan_process
from gevent.queue import Queue
from lib import glo


# 将结果写入文件
# 废弃，xlwt最多写入65535条数据，不然会报错
# def disable_getresult(target_num):
#     """
#     从队列中获取结果写到excel
#     queue: dict {'target_domain', 'original_domain', 'index_url', "Location", 'status', 'title', 'contenthash'}
#     :return:
#     """
#     # TODO 做一个汇总页
#     wb = xlwt.Workbook()
#     column_keys = ['target_domain', 'original_domain', 'index_url', "Location", 'status', 'title', 'contenthash']
#     all = wb.add_sheet("汇总")
#     for column, m in enumerate(column_keys):
#         all.write(0, column, m)
#     a = wb.add_sheet("A类 正常网站（重点关注）")
#     for column, m in enumerate(column_keys):
#         a.write(0, column, m)
#     b = wb.add_sheet("B类 大概率正常网站（重点关注）")
#     for column, m in enumerate(column_keys):
#         b.write(0, column, m)
#     c = wb.add_sheet("C类 小概率正常网站")
#     for column, m in enumerate(column_keys):
#         c.write(0, column, m)
#     d = wb.add_sheet("D类 非正常网站")
#     for column, m in enumerate(column_keys):
#         d.write(0, column, m)
#     e = wb.add_sheet("E类 意外情况（需要关注）")
#     for column, m in enumerate(column_keys):
#         e.write(0, column, m)
#     # 报告文件名以时间
#     report_filename = time.strftime("%Y%m%d%H%M%S", time.localtime())
#
#     global STOP_ME
#     global all_results
#     global a_results
#     global b_results
#     global c_results
#     global d_results
#     global e_results
#     # 报告行数记录
#     allline = 0
#     aline = 0
#     bline = 0
#     cline = 0
#     dline = 0
#     eline = 0
#     while not STOP_ME:
#         print("{}[Schedule] A:{} B:{} C:{} D:{} E:{} ,total:{} | {:.2%} {}".format(yellow, aline, bline, cline, dline, eline,
#                                                                           aline + bline + cline + dline + eline,
#                                                                           (aline + bline + cline + dline + eline)/target_num, end),
#               end="\r")
#         if all_results.qsize() > 0:
#             allline = writerdata(all, all_results.get_nowait(), allline)
#         if a_results.qsize() > 0:
#             aline = writerdata(a, a_results.get_nowait(), aline)
#         if b_results.qsize() > 0:
#             bline = writerdata(b, b_results.get_nowait(), bline)
#         if c_results.qsize() > 0:
#             cline = writerdata(c, c_results.get_nowait(), cline)
#         if d_results.qsize() > 0:
#             dline = writerdata(d, d_results.get_nowait(), dline)
#         if e_results.qsize() > 0:
#             eline = writerdata(e, e_results.get_nowait(), eline)
#     wb.save("./report/{}.xls".format(report_filename))
#     print("{}[Report] save success, file name: {}.xls{}".format(green, report_filename, end))
#
#
# def writerdata(worksheet, message, row):
#     """
#
#     :param worksheet:  excel sheet 对象
#     :param message:  写入的数据，dict
#     :param row:  当前sheet已写了多少行，在+1行继续写入
#     :return: 返回写完后的行数
#     """
#     # print(message)
#     row += 1
#     for column, m in enumerate(message.values()):
#         worksheet.write(row, column, m)
#     return row

#################################################
########以上是废弃代码，只是觉得思路不错，保留下来########
#################################################

# 使用csv格式
def getresult(target_num):
    """
    从队列中获取结果写到csv
    queue: dict {'target_domain', 'original_domain', 'index_url', "Location", 'status', 'title', 'contenthash', 'headers'}
    :return:
    """
    column_keys = ['target_domain', 'original_domain', 'index_url', "Location", 'status', 'title', 'contenthash', 'headers']
    # 报告文件名以时间
    report_dir = time.strftime("%Y%m%d%H%M%S", time.localtime())
    # 根据时间创建目录
    path = "{}/report/{}".format(os.getcwd(), report_dir)
    if not os.path.exists(path):
        os.makedirs(path)
    # 创建各类型结果的csv对象
    all_f = "report/{}/{}.csv".format(report_dir, "0All_message")
    f1 = open(all_f, "a", encoding="utf-8", newline="\n")
    all = csv.DictWriter(f1, column_keys)
    all.writeheader()
    a_f = "report/{}/{}.csv".format(report_dir, "A_normal(Focus)")
    f2 = open(a_f, "a", encoding="utf-8", newline="\n")
    a = csv.DictWriter(f2, column_keys)
    a.writeheader()
    b_f = "report/{}/{}.csv".format(report_dir, "B_needAuth(Focus)")
    f3 = open(b_f, "a", encoding="utf-8", newline="\n")
    b = csv.DictWriter(f3, column_keys)
    b.writeheader()
    c_f = "report/{}/{}.csv".format(report_dir, "C_smallProbability(Focus)")
    f4 = open(c_f, "a", encoding="utf-8", newline="\n")
    c = csv.DictWriter(f4, column_keys)
    c.writeheader()
    d_f = "report/{}/{}.csv".format(report_dir, "D_unavailable")
    f5 = open(d_f, "a", encoding="utf-8", newline="\n")
    d = csv.DictWriter(f5, column_keys)
    d.writeheader()
    e_f = "report/{}/{}.csv".format(report_dir, "E_outOfExpectation(Focus)")
    f6 = open(e_f, "a", encoding="utf-8", newline="\n")
    e = csv.DictWriter(f6, column_keys)
    e.writeheader()

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
        print("{}[Schedule] A:{} B:{} C:{} D:{} E:{}, total:{} | {:.2%} {}".format(yellow, aline, bline, cline, dline, eline,
                                                                          aline + bline + cline + dline + eline,
                                                                          (aline + bline + cline + dline + eline)/target_num, end),
              end="\r")
        try:
            if all_results.qsize() > 0:
                all.writerow(all_results.get_nowait())
                allline += 1
            if a_results.qsize() > 0:
                a.writerow(a_results.get_nowait())
                aline += 1
            if b_results.qsize() > 0:
                b.writerow(b_results.get_nowait())
                bline += 1
            if c_results.qsize() > 0:
                c.writerow(c_results.get_nowait())
                cline += 1
            if d_results.qsize() > 0:
                d.writerow(d_results.get_nowait())
                dline += 1
            if e_results.qsize() > 0:
                e.writerow(e_results.get_nowait())
                eline += 1
        except Exception as e:
            print("{}[Report] {} {}".format(red, e, end))
    print("\n{}[Report] save success, report_dir: {} {}".format(green, report_dir, end))
    f1.close()
    f2.close()
    f3.close()
    f4.close()
    f5.close()
    f6.close()


def main():
    # 命令行获取domain file
    argv = parse_args()
    args_file = argv.f
    # 默认根据cpu数量
    _pool = os.cpu_count()
    if argv.p:
        _pool = int(argv.p)
    # 读取所有域名，并去重
    dm_list = [tg.strip() for tg in list(set(open(args_file).readlines())) if tg.strip() != ""]
    print("{}[TitleScan] all domain total: {}{}".format(blue, len(dm_list), end))
    # 查询每个域名的ip
    print("{}[DnsQuery] Start dnsQuery......{}".format(blue, end))
    # rqueue是结果队列, {dm: [ip,ip1,ip2], dm1: [ip,ip1,ip2]}
    rqueue = multiprocessing.Manager().Queue()
    start_dns = time.time()
    dns_pool = multiprocessing.Pool(processes=os.cpu_count())
    dns_pool.map(functools.partial(dns_query, rqueue=rqueue), dm_list)
    dns_pool.close()
    dns_pool.join()
    print("{}[DnsQuery] DnsQuery Over, times: {}.{}".format(blue, time.time() - start_dns, end))

    time.sleep(1)
    # 端口扫描，返回端口跟域名/ip组合的列表
    # 预期返回: [{dm:[ip:port,dm:port]}]
    targets = async_port_scan(rqueue, pros=processes)

    # targets = [{dm.strip(): [dm.strip(), ]} for dm in dm_list]
    time.sleep(1)
    target_num = 0
    for i in targets:
        target_num += len(list(i.values())[0])
    print("{}[TiltleScan] Start ScanProcess...., total: {} {}".format(blue, target_num, end))
    # 处理队列中结果的线程
    threading.Thread(target=getresult, args=(target_num,)).start()
    # titlescan
    async_scan_process(targets, pros=_pool)

if __name__ == "__main__":

    STOP_ME = False
    glo._init()
    start = time.time()
    try:
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

        main()
        # 主线程阻塞，为了让写报告的线程再继续写入，防止丢失结果
        time.sleep(5)

    except KeyboardInterrupt as e:
        print('\n{}You aborted the scan.{}'.format(yellow, end))
        exit(1)
    except Exception as e:
        print('\n{}[__main__.exception] {} {}{}'.format(red, type(e), str(e), end))
    finally:
        STOP_ME = True
        time.sleep(1)
        print("\n{}[TiltleScan] All done, times:{}{}".format(green, time.time() - start,
                                                                                            end))
