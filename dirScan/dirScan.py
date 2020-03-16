# encoding=utf-8
import asyncio
import csv
import functools
import os
import random
import string
import time

import threadpool
import xlrd
from aiomultiprocess import Pool

from lib.core import get
from lib.cmdline import parse_args
from lib.config import path_dict, filename_dict, threads

# 这里是状态码200的错误页面的关键字，后续需要更新以保证正确性
_key404 = ["404", "找不到", "Not Found", "很抱歉"]
# 缺少参数的关键字
_key_lost_param = ["required", "parameter"]


# 主逻辑函数
async def scan(url):
    is404 = False
    islost_param = False

    resp_text, status, error = await get(url)
    if str(status).startswith("50"):
        resp_text, status, error = await get(url)
        if str(status).startswith("50"):
            return ["c", status, url, error]
    elif status == 200:
        # 状态码200的错误页面相似度比较
        for key in _key404:
            if key in resp_text:
                is404 = True
                break
        if is404:
            return ["c", status, url, error]
        else:
            print("[命中] {} {}".format(status, url))
            return ["a", status, url, error]
    elif status in [400, 403]:
        # 状态码200的错误页面相似度比较
        for key in _key_lost_param:
            if key in resp_text:
                islost_param = True
                break
        if islost_param:
            print("[命中] {} {}".format(status, url))
            return ["a", status, url, error]
        else:
            random_url = get_r_url(url)
            resp_404, status_404, error_404 = await get(random_url)
            # print(status_404,random_url)
            if status == status_404:
                return ["c", status, url, error]
            else:
                print("[可能] {} {}".format(status, url))
                return ["b", status, url, error]
    elif status == 405:
        print("[命中] {} {}".format(status, url))
        return ["a", status, url, error]
    else:
        return ["c", status, url, error]


# 获取随机url，集不存在的目录url
def get_r_url(url):
    flag = string.ascii_letters + string.digits
    return url + "".join(random.sample(flag, random.randint(3, 10)))


# 写报告
def report(url, results):
    r_temp = []
    c_result = []
    file = "report/{}.csv".format(url.split("/")[2].replace(":", "-"))
    c_file = "report/c.csv"
    for result in results:
        if result[0] in ["a", "b"]:
            r_temp.append(result)
        else:
            c_result.append(result)
    if len(r_temp) == 0:
        return
    # A,B类的结果
    with open(file, 'w', newline="\n") as f:
        w = csv.writer(f)
        for result in r_temp:
            w.writerow(result)
            # f.write("{} {}\n".format(*result))
    # C类结果
    with open(c_file, "a", newline="\n") as f:
        w = csv.writer(f)
        for result in c_result:
            w.writerow(result)
            # f.write("{} {}\n".format(*result))

# 主函数，注入爆破目标url，根据字典生成请求，并使用多进程协程进行验证
async def main(url):
    # 加载字典
    dicts = open("dicts/{}".format(path_dict)).readlines()
    # 根据字典生成验证请求
    targets = ["{}/{}".format(url, d.strip()) for d in dicts]
    start = time.time()
    # 多进程协程并发进行验证
    async with Pool(childconcurrency=500) as pool:
        results = await pool.map(scan, targets)
    print("over scan {}, time:{}s".format(url, time.time() - start))
    report(url, results)


# 每个线程设置新的事件循环对象
def thread_loop(url):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = asyncio.ensure_future(main(url))
    loop.run_until_complete(task)


# 入口，传入需要爆破的url集
def run(urls):
    print("target total : {}, starting scan........".format(len(urls)))
    pool = threadpool.ThreadPool(threads)
    reqs = threadpool.makeRequests(thread_loop, urls)
    for req in reqs:
        pool.putRequest(req)
    pool.wait()



if __name__ == '__main__':
    start = time.time()
    try:
        args = parse_args()
        data = xlrd.open_workbook(args.file, encoding_override='utf-8')
        urls = []
        sheet_list = [int(_) for _ in args.sheets.split(",")]  # 选定表
        for sheet in sheet_list:
            table = data.sheets()[sheet]
            urls.extend(table.col_values(1)[1:])
        run(urls)
    except KeyboardInterrupt as e:
        print('You aborted the scan.')
        exit(1)
    except Exception as e:
        print('[__main__.exception] %s %s' % (type(e), str(e)))
    finally:
        print("all done, times:{}".format(time.time() - start))
