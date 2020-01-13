# encoding =utf-8
import xlwt


def reportWrite(filename, message):

    """
    write report to xls file
    :param filename: report name, xls type
    :param message:  data for write, datatype like [(d1,x1,y1),(d2,x2,y2)]
    """
    wb = xlwt.Workbook()
    ws = wb.add_sheet(filename)

    for row, ms in enumerate(message):
        print("[writting] {} ".format(", ".join(ms)))
        for column, m in enumerate(ms):
            ws.write(row, column, m)

    wb.save("{}.xls".format(filename))

    print("report save success,filename is {}.xls".format(filename))