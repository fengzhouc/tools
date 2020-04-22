# encoding=utf-8

import csv
import multiprocessing
import threading
import time

import dns
from dns import resolver
from dns.exception import Timeout
from dns.resolver import NXDOMAIN, NoAnswer

from cmdline import parse_args


def query(domain, rqueue, equeue):
    result = []
    cname = ""
    for t in ["CNAME", "A"]:
        try:
            ans = resolver.query(domain, t)
            for i in ans:
                if i.rdtype == dns.rdatatype.A:
                    result.append([domain, i, cname])
                else:
                    cname = i

        except (NXDOMAIN, Timeout, NoAnswer) as e:
            equeue.put([[domain, str(e)], ])
        for r in result:
            rqueue.put(r)


# 写报告
def report():
    global rqueue
    global equeue
    global STOP
    file = "{}.csv".format("dnsquery-all")
    efile = "{}.csv".format("dnsquery-error")
    with open(file, 'a', newline="\n") as f:
        w = csv.writer(f)
        while not STOP:
            w.writerow(rqueue.get())
    with open(efile, 'a', newline="\n") as f:
        w = csv.writer(f)
        while not equeue.empty():
            w.writerow(equeue.get())


def get_urls():
    urls = []
    args = parse_args()
    f = args.f
    if f.endswith("txt"):
        with open(f, encoding="utf-8") as file:
            for url in file:
                urls.append(url.strip())
        return list(set(urls))


if __name__ == '__main__':
    STOP = False
    try:
        domains = get_urls()
        rqueue = multiprocessing.Manager().Queue()
        equeue = multiprocessing.Manager().Queue()
        start = time.time()
        threading.Thread(target=report).start()
        pool = multiprocessing.Pool()
        for domain in domains:
            pool.apply_async(func=query, args=(domain, rqueue, equeue))  # 维持执行的进程总数为processes，当一个进程执行完毕后会添加新的进程进去
        print('Waiting for all subprocesses done...')
        pool.close()
        pool.join()  # 调用join之前，先调用close函数，否则会出错。执行完close后不会有新的进程加入到pool,join函数等待所有子进程结束
        time.sleep(5)
        STOP = True
        print("all done. tile: {}".format(time.time() - start))

    except KeyboardInterrupt as e:
        print('You aborted the scan.')
        exit(-1)
    except Exception as e:
        print('\n[__main__.exception] %s %s' % (type(e), str(e)))
    finally:
        STOP = True
