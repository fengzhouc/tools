# encoding=utf-8
import csv

import dns
import xlrd
from dns import resolver
from dns.exception import Timeout
from dns.resolver import NXDOMAIN, NoAnswer

from cmdline import parse_args


def query(domain):
    for t in ['A', "CNAME"]:
        result = []
        try:
            ans = resolver.query(domain, t)
            for i in ans:
                result.append([domain, i])
            report(result, "dnsquery-{}".format(t))
        except (NXDOMAIN, Timeout, NoAnswer) as e:
            report([[domain, str(e)], ], "dna_error")


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
    if f.endswith("txt"):
        with open(f, encoding="utf-8") as file:
            for url in file:
                urls.append(url.strip())
        return list(set(urls))


if __name__ == '__main__':
    domains = get_urls()
    for domain in domains:
        query(domain)
