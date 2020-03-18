# encoding=utf-8
import csv
import os
import time
from urllib import parse


# 写报告
def report(url, r_queue, report_dir):
    # 根据时间创建目录
    os.mkdir("{}/report/{}".format(os.getcwd(), report_dir))
    r_temp = []
    c_result = []
    url_info = parse.urlparse(url)
    report_file = url_info[1].replace(":", "#")  # windows文件不允许出现：
    file = "report/{}/{}.csv".format(report_dir, report_file)
    c_file = "report/{}/c.csv".format(report_dir)
    while not r_queue.empty():
        result = r_queue.get_nowait()
        if result[0] in ["a", "b"]:
            r_temp.append(result)
        else:
            c_result.append(result)

    # C类结果
    with open(c_file, "a", newline="\n") as f:
        w = csv.writer(f)
        for result in c_result:
            w.writerow(result)

    if len(r_temp) == 0:
        return
    # A,B类的结果
    with open(file, 'w', newline="\n") as f:
        w = csv.writer(f)
        for result in r_temp:
            w.writerow(result)


if __name__ == "report":
    print("report init")
    report_dir = time.strftime("%Y%m%d%H%M%S", time.localtime())