# encodingutf-8
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


async def ip138(ip):
    url = "https://site.ip138.com/{}/".format(ip)
    #发起请求获取响应
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False),
                                         conn_timeout=1000) as session:
            async with session.get(url, headers=headers, timeout=5) as resp:
                resp_str = await resp.text(errors="ignore")
                #解析响应获取域名
                data = parse_resp(ip, resp_str)
                report(data)


    except (aiohttp.ClientResponseError, aiohttp.ClientConnectionError, asyncio.TimeoutError, RuntimeError) as e:
        print("[EXCEPT] {} {}".format(ip, str(e)))


def parse_resp(ip, resp_str):
    key = '<li><span class="date">.*</span><a href="/(.*)/" target="_blank">\\1</a></li>'
    #解析响应，获取域名,返回[ip, [domain list]]
    r = re.findall(key, resp_str)
    result = [[domain, ip] for domain in r]
    return result

def get_urls():
    urls = []
    args = parse_args()
    # if len(args) < 2:
    #     print("python ip138.py -f target.txt -d domian")
    #     exit(-1)
    f = args.f
    # 读取excel的url，主要是titlescan的扫描结果
    if f.endswith("xls") or f.endswith("xlxs"):
        data = xlrd.open_workbook(f, encoding_override='utf-8')
        sheet_list = [int(_) for _ in args.s.split(",")]  # 选定表
        for sheet in sheet_list:
            table = data.sheets()[sheet]
            urls.extend(table.col_values(args.c)[1:])
        return urls
    # 读取txt中的url
    if f.endswith("txt"):
        with open(f, encoding="utf-8") as file:
            for url in file:
                urls.append(url.strip())
        return urls


# 写报告
def report(data):
    file = "{}.csv".format("result")

    with open(file, 'a', newline="\n") as f:
        w = csv.writer(f)
        for _ in data:
            w.writerow(_)


async def run(urls):
    # 多进程协程并发爆破每个url
    async with aiomultiprocess.Pool() as pool:
        await pool.map(ip138, urls)


if __name__ == '__main__':
    urls = get_urls()
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(run(urls))
    # task = asyncio.ensure_future(ip138("14.215.177.39"))
    loop.run_until_complete(task)
