# encoding=utf-8
import sqlite3


# 功能：
# （1）将命中的字典存入数据库，并次数+1
# （2）导出数据库的的字典到文件中（根据次数排序），目录dicts
# 使用splite3数据库
# 表 DICTS
# 字段：
#   ID    主键
#   TYPE  字典类型，path、file
#   DICT  字典
#   COUNT 命中次数


class Dbcontroller:

    def __init__(self):
        self.db = sqlite3.connect("./db/dicts.db")
        print("Opened database successfully")
        self.cursor = self.db.cursor()
        self.create_table()

    def create_table(self):
        try:
            self.cursor.execute('''CREATE TABLE DICTS
                           (ID INTEGER PRIMARY KEY  AUTOINCREMENT,
                           TYPE           TEXT  NOT NULL,
                           DICT           TEXT  NOT NULL,
                           COUNT          INT   NOT NULL);''')
            print("Table created successfully")
        except sqlite3.OperationalError as e:
            print(str(e))

    def drop_table(self, table_name):
        self.cursor.execute("DROP TABLE {};", format(table_name))
        print("DROP TABLE successfully")

    # 将命中的字典存入数据库，并次数+1
    def update(self, d_str):
        if self.select(d_str) is None:
            self.insert(d_str, "path")
            return
        sql = "UPDATE DICTS set COUNT = '{}' where DICT='{}'".format(self.select(d_str) + 1, d_str)
        self.cursor.execute(sql)
        self.db.commit()
        print("UPDATE COUNT successfully")

    # 导出数据库字典
    def export_dict(self):
        pass

    # 导入字典到数据库
    def import_dicts(self, d_file, d_type):
        with open(d_file, encoding="utf-8") as f:
            for d in f:
                self.insert(d, d_type)
        print("Data import successfully")

    def select(self, d_str):
        sql = "SELECT COUNT FROM DICTS WHERE DICT='{}';".format(d_str)
        c = self.cursor.execute(sql)
        try:
            count = list(c)[0][0]
        except IndexError as e:
            count = None

        return count

    def insert(self, d, d_type):
        if self.select(d) is not None:
            print("Data was exists")
            return
        sql = "INSERT INTO DICTS (TYPE, DICT, COUNT) VALUES ('{}','{}',{});".format(d_type, d, 0)
        self.cursor.execute(sql)
        self.db.commit()
        print("INSERT data successfully")


if __name__ == '__main__':
    db = Dbcontroller()
    # db.import_dicts("./../dicts/all.txt", "path")
    print(db.select("profs"))
