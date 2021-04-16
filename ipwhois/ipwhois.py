# encoding=utf-8
import asyncio
import csv
import functools
import os
import re
import time

import aiohttp
import aiomultiprocess
import xlrd

from cmdline import parse_args

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/59.0.3071.104 Safari/537.36',
}


async def whois(ip, file="", queryOption="ipv4"):
    for _ip in ip.split(","):
        # target_ip,target_ip_range,netname,company_description,netname_ip_range
        url = "http://ipwhois.cnnic.cn/bns/query/Query/ipwhoisQuery.do?txtquery={}&queryOption={}".format(_ip,
                                                                                                          queryOption)
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False),
                                             conn_timeout=1000) as session:
                async with session.get(url, headers=headers, timeout=5) as resp:
                    resp_str = await resp.text(errors="ignore")
                    # print(resp_str)
                    data = parse_resp(_ip, resp_str)

                # 搜网络名称，得到ip段
                name = ""
                if data["netname"] != "" or data["netname"] is not None:
                    name = data["netname"]
                url = "http://ipwhois.cnnic.cn/bns/query/Query/ipwhoisQuery.do?txtquery={}&queryOption={}".format(name,
                                                                                                                  "netname")
                async with session.get(url, headers=headers, timeout=5) as resp:
                    resp_str = await resp.text(errors="ignore")
                    data["netname_ip_range"] = parse_resp(_ip, resp_str, isnet=True)

                print(data)
                report(data, file)
        except (aiohttp.ClientResponseError, aiohttp.ClientConnectionError, asyncio.TimeoutError, RuntimeError) as e:
            print("[EXCEPT] {} {}".format(_ip, str(e)))


def parse_resp(ip, resp_str, isnet=False):
    # target_ip,target_ip_range,netname,company_description,netname_ip_range
    result = {}
    key1 = 'IPv4地址段:</font></td>\s*<td align="left" class="t_blue"><font size="2">(.*)&nbsp;</font></td>'  # ip范围
    key2 = '网络名称:</font></td>\s*<td align="left" class="t_blue"><font size="2">(.*)&nbsp;</font></td>'  # 网络名称
    key3 = '单位描述:</font></td>\s*<td align="left" class="t_blue"><font size="2">(.*)&nbsp;</font></td>'  # 单位名称1
    if isnet:
        ip = re.findall(key1, resp_str)
        return ip

    result["target_ip"] = ip
    """解析resp，获取IP信息及网络名称"""
    data1 = re.findall(key1, resp_str)
    data2 = re.findall(key2, resp_str)
    data3 = re.findall(key3, resp_str)

    result["target_ip_range"] = data1[0]
    result["netname"] = data2[0]
    result["company_description"] = data3[0]

    return result


# TODO 将IP段转成CIDR格式
def handler_ip():
    pass


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

# 写报告
def report(data, file):
    fieldnames = ["target_ip", "target_ip_range", "netname", "company_description", "netname_ip_range"]
    with open(file, 'a', newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        # w.writeheader()
        netname_ip_range = data["netname_ip_range"]
        if len(netname_ip_range) == 0:
            w.writerow(data)
        else:
            for d in netname_ip_range:
                data["netname_ip_range"] = d
                w.writerow(data)


async def run(urls):
    file = "{}-{}.csv".format("ipwhois", time.time())
    # 多进程协程并发爆破每个url
    async with aiomultiprocess.Pool() as pool:
        await pool.map(functools.partial(whois, file=file), urls)


if __name__ == '__main__':
    urls = get_urls()
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(run(urls))
    # task = asyncio.ensure_future(whois("14.215.177.39"))
    loop.run_until_complete(task)
    print("all done.")
