# encoding=utf-8

import sys
from util import getRandomUrl, getStatusAndTtile, report
from lib.cmdline import parse_args

# 命令行获取domain file
argv = parse_args()
args_file = argv.f

# 结果分类
nList = []  # 正常
n_file = "n_file"
eList = []  # 死站
e_file = "e_file"
oList = []  # 其他
o_file = "o_file"

with open(args_file) as f:
    for dm in f:
        # 获取不存在的url
        rurl = getRandomUrl.getRandomUrl(dm)
        # 获取信息，跟进重定向
        rmess = getStatusAndTtile.getStatusAndTitle(rurl, redirect=True)
        # 获取主页url
        indexurl = getRandomUrl.getRandomUrl(dm, index=True)
        # 获取主页信息，跟进重定向
        imess = getStatusAndTtile.getStatusAndTitle(indexurl, redirect=True)

        # 请求失败的情况
        if (imess[1] is None) or (rmess[2] is None):
            eList.append(imess)
            continue
        # 状态码5xx，且主页状态码相同
        if str(rmess[2]).startswith("5") and rmess[2] == imess[2]:  
            eList.append(imess)
        # 因为请求的时候都是跟进重定向的，所以不会有3xx状态码
        # 状态码2xx、4xx,主页状态码2xx，有种可能都是2xx不正常的页面，但是没想到很好的识别方法，后期补充
        elif (str(rmess[2]).startswith("2") or rmess[2] == 404) and imess[2] == 200:  
            nList.append(imess)
        else:
            oList.append(imess)

    # 写报告
    report.report(n_file, nList)
    report.report(e_file, eList)
    report.report(o_file, oList)
