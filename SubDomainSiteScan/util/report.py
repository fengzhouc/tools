# encoding = utf-8
import xlwt


def report(filename, message):
    """
    把数据写到excel中
    :param message: list [url，status，title]
    :return: none
    """

    wb = xlwt.Workbook()
    ws = wb.add_sheet("result")

    reportpath = "./report/"
    if "" == filename:
        nfilename = reportpath + "report"
    else:
        nfilename = reportpath + filename

    print("report writting........")
    for row, ms in enumerate(message):
        # print("[writting] data -> {} ".format(ms))
        for column, m in enumerate(ms):
            ws.write(row, column, m)

    wb.save("{}.xls".format(nfilename))

    print("report save success,filename is {}.xls".format(nfilename))


if __name__ == "__main__":
    report("", [[1, 2, 3], [4, 5, 6]])
