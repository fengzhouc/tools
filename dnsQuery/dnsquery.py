# encoding=utf-8
import csv

import xlrd
from dns import resolver
from dns.resolver import NXDOMAIN

from cmdline import parse_args


def query(domain, type):
    result = []
    try:
        ans = resolver.query(domain, type)
        for i in ans:
            result.append([domain, i.address])
    except NXDOMAIN as e:
        report([[domain, str(e)], ], "dna_error")
    finally:
        report(result, "dnsquery")

# 写报告
def report(data, filename):
    file = "{}.csv".format(filename)

    with open(file, 'a', newline="\n") as f:
        w = csv.writer(f)
        for _ in data:
            w.writerow(_)

def get_urls():
    urls = []
    args = parse_args()
    f = args.f
    # 读取excel的url，主要是titlescan的扫描结果
    if f.endswith("xls") or f.endswith("xlxs"):
        data = xlrd.open_workbook(f, encoding_override='utf-8')
        sheet_list = [int(_) for _ in args.s.split(",")]  # 选定表
        for sheet in sheet_list:
            table = data.sheets()[sheet]
            urls.extend(table.col_values(args.c)[1:])
        return list(set(urls))
    # 读取txt中的url
    if f.endswith("txt"):
        with open(f, encoding="utf-8") as file:
            for url in file:
                urls.append(url.strip())
        return list(set(urls))


if __name__ == '__main__':
    domains = get_urls()
    for domain in domains:
        query(domain, parse_args().t)
