# encoding=utf-8

import asyncio
import csv
import re

import aiohttp
import aiomultiprocess
import xlrd

from cmdline import parse_args

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/59.0.3071.104 Safari/537.36',
    }


async def whois(domain):
    url = "http://whois.chinaz.com/{}".format(domain)
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), conn_timeout=1000) as session:
            async with session.get(url, headers=headers, timeout=5) as resp:
                resp_str = await resp.text(errors="ignore")
                data = parse_resp(domain, resp_str)
                report(data)
    except (aiohttp.ClientResponseError, aiohttp.ClientConnectionError, asyncio.TimeoutError, RuntimeError) as e:
        print("[EXCEPT] {} {}".format(domain, str(e)))


def parse_resp(domain, resp_str):
    result = [domain, ]
    key1 = '注册商</div><div class="fr WhLeList-right"><div class="block ball"><span>(.*)</span></div></div>'  # 注册商
    key2 = '联系邮箱</div><div class="fr WhLeList-right block ball lh24"><span>([^\d]*)</span>'  # 联系邮箱
    key3 = '联系电话</div><div class="fr WhLeList-right block ball lh24"><span>([0-9-\*]*)</span>'  # 联系电话
    key4 = '域名服务器</div><div class="fr WhLeList-right"><span>(.*)</span></div></li><li class="clearfix bor-b1s "><div class="fl WhLeList-left">DNS'  # 域名服务器
    key5 = 'DNS</div><div class="fr WhLeList-right">(.*)</div></li><li class="clearfix bor-b1s bg-list"><div class="fl WhLeList-left">状态'  # DNS
    """解析resp，获取IP信息及网络名称"""
    data1 = re.findall(key1, resp_str)
    data2 = re.findall(key2, resp_str)
    data3 = re.findall(key3, resp_str)
    data4 = re.findall(key4, resp_str)
    data5 = re.findall(key5, resp_str)
    if data5:
        data5 = [ns.strip() for ns in data5[0].split("<br/>")]

    result.extend(data1)
    result.extend(data2)
    result.extend(data3)
    result.extend(data4)
    result.append(data5)
    return result


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
                urls.append(".".join(url.strip().split(".")[-2:]))
        return list(set(urls))


# 写报告
def report(data):
    file = "{}.csv".format("dnswhois")

    with open(file, 'a', newline="\n") as f:
        w = csv.writer(f)
        w.writerow(data)

async def run(urls):
    # 多进程协程并发爆破每个url
    async with aiomultiprocess.Pool() as pool:
        await pool.map(whois, urls)


if __name__ == '__main__':
    # urls = get_urls()
    loop = asyncio.get_event_loop()
    # task = asyncio.ensure_future(run(urls))
    task = asyncio.ensure_future(whois("www.baifu-tech.net"))
    loop.run_until_complete(task)
