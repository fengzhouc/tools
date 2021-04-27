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
from lib.config import processes, crons, childconcurrency, yellow, green, red, blue, end
from lib.report import report
from lib.db import db

# TODO 这里是状态码200的错误页面的关键字，后续需要更新以保证正确性
_key404 = ["404", "找不到", "Not Found", "很抱歉"]
# 缺少参数的关键字
_key_lost_param = ["required", "parameter", "param"]


# 主逻辑函数
async def scan(queue, r_queue, session):
    while not queue.empty():
        url = queue.get_nowait()
        url_info = parse.urlparse(url)
        # await asyncio.sleep(0.5)  # 防止访问过快，导致大量socket连接失败
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
                print("{}[Hit] {} {}{}".format(blue, status, url, end))
                r_queue.put_nowait(["a", status, url, error])
                # 更新数据库字典信息
                db.update(url_info.path[1:])
        elif status == 405:
            print("{}[Hit] {} {}{}".format(blue, status, url, end))
            r_queue.put_nowait(["a", status, url, error])
            # 更新数据库字典信息
            db.update(url_info.path[1:])
        elif status in ["400", "403"]:
            # 错误页面相似度比较,判断是否参数缺失异常
            for key in _key_lost_param:
                if key in resp_text:
                    islost_param = True
                    break
            if islost_param:
                print("{}[Hit] {} {}{}".format(blue, status, url, end))
                r_queue.put_nowait(["a", status, url, error])
                # 更新数据库字典信息
                db.update(url_info.path[1:])
            else:
                # 生成一个随机url,即不存在的资源,这里是判断是都404的页面也是返回400/403
                random_url = get_r_url(url)
                resp_404, status_404, error_404 = await get(random_url, session)
                # print(status_404,random_url)
                # 404资源也返回403则大概率不是api
                if status == status_404:
                    r_queue.put_nowait(["c", status, url, error])
                    pass
                # 其他情况,避免定制的响应码而错过
                else:
                    print("{}[Maybe] {} {}{}".format(blue, status, url, end))
                    r_queue.put_nowait(["b", status, url, error])
                    # 更新数据库字典信息
                    db.update(url_info.path[1:])
        else:
            r_queue.put_nowait(["c", status, url, error])


async def schedule(url, queue):
    total = queue.qsize()
    while not queue.empty():
        await asyncio.sleep(2)
        print("{}[Schedule] Bruting {} done:{} | {:.0%}{}".format(yellow,
                                                                  url,
                                                                  total - queue.qsize(),
                                                                  (total - queue.qsize()) / total,
                                                                  end), end="\r")
    print()


# 主函数，注入爆破目标url，根据字典生成请求，并使用多进程协程进行验证
async def main(url, report_dir, dicts):
    """
    :param url: 爆破的url
    :param report_dir: 报告目录
    :param dicts: 字典
    :return:
    """
    print("{}[Start] start brute {}.{}".format(green, url, end))
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
    print("{}[Report] Over brute {}, time:{}s.{}".format(green, url, time.time() - start, end))
    # 写报告
    report(url, r_q, report_dir)


async def run(urls, dicts):
    """
    :param urls: 爆破的url集
    :param dicts: 字典
    :return:
    """
    print("{}[Start] target total: {}, dict total: {} {}".format(green, len(urls), len(dicts), end))
    report_dir = time.strftime("%Y%m%d%H%M%S", time.localtime())
    # 多进程协程并发爆破每个url
    async with aiomultiprocess.Pool(processes=processes, childconcurrency=childconcurrency) as pool:
        await pool.map(functools.partial(main, report_dir=report_dir, dicts=dicts), urls)


def get_urls():
    urls = []
    dicts = {}
    args = parse_args()
    f = args.f
    u = args.u
    d = args.d
    t = args.t
    _import = args.i
    # 导入字典
    if _import:
        db.import_dicts(_import, t)
        print("INSERT OVER.")
        return urls, dicts
    # 加载字典
    if t:
        if d:
            if d == "all":
                dicts = db.export_all(t)
            else:
                dicts = db.export_3000(t, d)
        else:
            dicts = db.export_3000
    else:
        # 没有指定范围，则默认加载全字典的top10000
        print("{}[Init] without -t, loading top10000 dicts....{}".format(green, end))
        dicts = db.export_10000_all()

    if u:
        urls.append(u)
        return urls, dicts
    elif f:
        # 读取excel的url，主要是titlescan的扫描结果
        if f.lower().endswith("xls") or f.endswith("xlxs"):
            data = xlrd.open_workbook(f, encoding_override='utf-8')
            sheet_list = [int(_) for _ in args.s.split(",")]  # 选定表
            for sheet in sheet_list:
                table = data.sheets()[sheet]
                # titlescan结果的index_url的结果, 第二列第二行的值
                urls.extend(table.col_values(1)[1:])
            return urls, dicts
        # 读取txt中的url
        if f.lower().endswith("txt"):
            with open(f, encoding="utf-8") as file:
                for url in file:
                    urls.append(url.strip())
            return urls, dicts


if __name__ == '__main__':
    start = time.time()
    try:
        urls, dicts = get_urls()
        # print(urls)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(urls, dicts))
    except KeyboardInterrupt as e:
        print('{}[Error] You aborted the scan.{}'.format(red, end))
        exit(1)
    except Exception as e:
        print('{}[__main__.exception] {} {}.{}'.format(red, type(e), str(e), end))
    finally:
        print("{}[End] all done, times:{}.{}".format(green, time.time() - start, end))
