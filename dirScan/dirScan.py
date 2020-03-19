# encoding=utf-8
import asyncio
import functools
import time
from urllib import parse

import aiohttp
import aiomultiprocess
import xlrd

from lib.core import get, get_r_url
from lib.cmdline import parse_args
from lib.config import path_dict, filename_dict, processes, crons, childconcurrency
from lib.report import report
from lib.db import Dbcontroller


db = Dbcontroller()

# 这里是状态码200的错误页面的关键字，后续需要更新以保证正确性
_key404 = ["404", "找不到", "Not Found", "很抱歉"]
# 缺少参数的关键字
_key_lost_param = ["required", "parameter"]


# 主逻辑函数
async def scan(queue, r_queue, session):
    while not queue.empty():
        url = queue.get_nowait()
        url_info = parse.urlparse(url)
        await asyncio.sleep(0.5)  # 防止访问过快，导致大量socket连接失败
        is404 = False
        islost_param = False

        resp_text, status, error = await get(url, session)
        if str(status).startswith("50"):
            resp_text, status, error = await get(url, session)
            if str(status).startswith("50"):
                r_queue.put_nowait(["c", status, url, error])
                pass
        elif status == 200:
            # 状态码200的错误页面相似度比较
            for key in _key404:
                if key in resp_text:
                    is404 = True
                    break
            if is404:
                r_queue.put_nowait(["c", status, url, error])
                pass
            else:
                print("[命中] {} {}".format(status, url))
                r_queue.put_nowait(["a", status, url, error])
                # 更新数据库字典信息
                db.update(url_info.path[1:])
        elif status in [400, 403]:
            # 状态码200的错误页面相似度比较
            for key in _key_lost_param:
                if key in resp_text:
                    islost_param = True
                    break
            if islost_param:
                print("[命中] {} {}".format(status, url))
                r_queue.put_nowait(["a", status, url, error])
                # 更新数据库字典信息
                db.update(url_info.path[1:])
            else:
                random_url = get_r_url(url)
                resp_404, status_404, error_404 = await get(random_url, session)
                # print(status_404,random_url)
                if status == status_404:
                    r_queue.put_nowait(["c", status, url, error])
                    pass
                else:
                    print("[可能] {} {}".format(status, url))
                    r_queue.put_nowait(["b", status, url, error])
                    # 更新数据库字典信息
                    db.update(url_info.path[1:])
        elif status == 405:
            print("[命中] {} {}".format(status, url))
            r_queue.put_nowait(["a", status, url, error])
            # 更新数据库字典信息
            db.update(url_info.path[1:])
        else:
            r_queue.put_nowait(["c", status, url, error])

async def schedule(url, queue):
    total = queue.qsize()
    while not queue.empty():
        await asyncio.sleep(1)
        print("[schedule] bruting {} done:{} | {:.0%}".format(url,
                                                              total-queue.qsize(),
                                                              (total-queue.qsize())/total), end="\r")
    print()

# 主函数，注入爆破目标url，根据字典生成请求，并使用多进程协程进行验证
async def main(url, report_dir):
    print("start brute {}".format(url))
    # 加载字典
    dicts = open("dicts/{}".format(path_dict)).readlines()
    # 根据字典生成验证请求
    targets = ["{}/{}".format(url, d.strip()) for d in dicts]
    # 爆破任务队列
    q = asyncio.Queue()
    # 爆破结果队列
    r_q = asyncio.Queue()
    for target in targets:
        q.put_nowait(target)
    # 协程任务列表
    tasks = []
    # 多协程并发进行验证
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False),
                                     conn_timeout=1000) as session:
        # 进度条的协程
        tasks.append(schedule(url, q))
        for _ in range(crons):
            task = scan(q, r_q, session)
            tasks.append(task)
        start = time.time()
        await asyncio.wait(tasks)
    print("over brute {}, time:{}s".format(url, time.time() - start))
    # 写报告
    report(url, r_q, report_dir)


async def run(urls):
    print("target total : {}, starting scan........".format(len(urls)))
    report_dir = time.strftime("%Y%m%d%H%M%S", time.localtime())
    # 多进程协程并发爆破每个url
    async with aiomultiprocess.Pool(processes=processes, childconcurrency=childconcurrency) as pool:
        await pool.map(functools.partial(main, report_dir=report_dir), urls)


if __name__ == '__main__':
    start = time.time()
    try:
        args = parse_args()
        data = xlrd.open_workbook(args.f, encoding_override='utf-8')
        urls = []
        sheet_list = [int(_) for _ in args.s.split(",")]  # 选定表
        for sheet in sheet_list:
            table = data.sheets()[sheet]
            urls.extend(table.col_values(1)[1:])
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(urls))
    except KeyboardInterrupt as e:
        print('You aborted the scan.')
        exit(1)
    except Exception as e:
        print('[__main__.exception] %s %s' % (type(e), str(e)))
    finally:
        print("all done, times:{}".format(time.time() - start))
