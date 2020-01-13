# encoding=utf-8

"""
google hack  site:domain
use selenuim webdriver
"""
import random
from time import sleep
import tools.SubDomainSpider.util.report as reportWrite

from selenium import webdriver
import xlwt


def mapfunc(tg):
    """
    处理element列表得到每个element的文件，方便后续写报告
    :param tg:
    :return: list [文本1，文本2]
    """
    return [t.text for t in tg]

def googlehack_domain(*args):
    """
    google hack search subdomain
    :param args: [search, filename, nextxpath, othermessagexpath..]
    :return list like [(d1,x1,y1),(d2,x2,y2)]
    """
    search = args[0]
    filename = args[1]
    nextxpath = args[2]
    other = args[3:]
    print("[args] search={}, filename={}, nextxpath={}, other={}".format(search, filename, nextxpath, other))
    chromeOptions = webdriver.ChromeOptions()
    # 设置代理
    chromeOptions.add_argument('--proxy-server=http://127.0.0.1:1080')
    # 设置无界面模式
    chromeOptions.add_argument('--headless')
    chromeOptions.add_argument('--disable-gpu')
    wd = webdriver.Chrome(options=chromeOptions)
    # 设置隐式等待时间
    wd.implicitly_wait(10)
    # 发送请求
    wd.get("https://www.google.com/search?q={}".format(search))
    message = []

    while True:
        # 查找目标
        wblist = [wd.find_elements_by_xpath(xpath=xp) for xp in other]
        tglist = list(zip(*wblist))
        result = list(map(mapfunc, tglist))
        print("[searching] {} ".format(result))
        message.extend(result)
        try:
            if nextxpath is None:
                break
            n = wd.find_element_by_xpath(nextxpath)
            sleep(random.randint(2, 9))# 睡眠随机，防止被检测出爬虫
            n.click()
            # print(n.text)
        except Exception as e:
            print(e.__doc__)
            break
        # print(message)
    reportWrite(filename, message)




# def reportWrite(filename, message):
#
#     """
#     write report to xls file
#     :param filename: report name, xls type
#     :param message:  data for write, datatype like [(d1,x1,y1),(d2,x2,y2)]
#     """
#     wb = xlwt.Workbook()
#     ws = wb.add_sheet(filename)
#
#     for row, ms in enumerate(message):
#         print("[writting] {} ".format(", ".join(ms)))
#         for column, m in enumerate(ms):
#             ws.write(row, column, m)
#
#     wb.save("{}.xls".format(filename))
#
#     print("report save success,filename is {}.xls".format(filename))



if __name__ == "__main__":
    googlehack_domain("site:vpal.com", "vpal.com", "//*[@id=\"pnnext\"]/span[2]", "//*[@class=\"TbwUpd\"]/cite", "//*/span[@class=\"S3Uucc\"]")
    # mess = [('d1','x1','y1'),('d2','x2','y2')]
    # reportWrite("test", mess)
