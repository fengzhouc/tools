# encoding=utf-8
import os
import sqlite3
from lib.config import yellow, green, end


# 功能：
# （1）将命中的字典存入数据库，并次数+1
# （2）导出数据库的的字典到文件中（根据次数排序），目录dicts
# 使用splite3数据库
# 表 DICTS
# 字段：
#   ID    主键
#   TYPE  字典类型，api/js/do/action/backup/php
#   DICT  字典
#   COUNT 命中次数


class Dbcontroller:

    def __init__(self):
        # print("[DB] Connect DB, please wait.")
        # self.db = sqlite3.connect("./db/dicts.db")
        self.db = sqlite3.connect("D:\\code\\github\\tools\\dirScan\\db\\dicts.db")
        self.cursor = self.db.cursor()
        self.create_table()

    def create_table(self):
        try:
            self.cursor.execute('''CREATE TABLE DICTS
                           (ID INTEGER PRIMARY KEY  AUTOINCREMENT,
                           TYPE           TEXT  NOT NULL,
                           DICT           TEXT  NOT NULL,
                           COUNT          INT   NOT NULL);''')
            # print("Table created successfully")
            self.db.commit()
        except sqlite3.OperationalError as e:
            # print(str(e))
            pass

    def drop_table(self, table_name):
        self.cursor.execute("DROP TABLE {};".format(table_name))
        self.db.commit()
        print("DROP TABLE successfully")

    # 将命中的字典存入数据库，并次数+1
    def update(self, d_str):
        if self.select(d_str) is None:
            self.insert(d_str, "path")
            return
        sql = "UPDATE DICTS set COUNT = '{}' where DICT='{}'".format(self.select(d_str) + 1, d_str)
        self.cursor.execute(sql)
        self.db.commit()
        # print("UPDATE COUNT successfully")

    # 导出数据库字典
    # 导出两份, 1、all.txt  2、top3000.txt
    def export_3000(self, type="api", d="3000"):
        print("{}[Export] get top{} '{}' dict{}".format(green, d, type, end))
        top_path_sql = "SELECT (a.DICT) FROM (SELECT * FROM DICTS WHERE TYPE='{}' ORDER BY COUNT DESC)a LIMIT {};".format(type.strip(), d.strip())
        top_path_c = self.cursor.execute(top_path_sql)
        return [data[0] for data in list(top_path_c)]

    def export_all(self, type="api"):
        print("{}[Export] get all '{}' dict{}".format(green, type, end))
        all_sql = "SELECT DICT FROM DICTS WHERE TYPE='{}';".format(type.strip())
        all_c = self.cursor.execute(all_sql)
        # print(list(all_c))
        return [data[0] for data in list(all_c)]

    def export_10000_all(self):
        print("{}[Export] get top10000 dict{}".format(green, end))
        top_path_sql = "SELECT (a.DICT) FROM (SELECT * FROM DICTS ORDER BY COUNT DESC)a LIMIT 10000;"
        top_path_c = self.cursor.execute(top_path_sql)
        return [data[0] for data in list(top_path_c)]

    # 导入字典到数据库
    def import_dicts(self, d_file, d_type):
        print("{}start insert, type: {}".format(green, d_type, end))
        index = 0
        with open(d_file, encoding="utf-8") as f:
            for d in f:
                data = d.strip()
                # 已经存在了就不添加了
                if self.select(data) is not None:
                    continue
                index += self.insert(data, d_type)
                print("{}[Schedule] Inserting, total:{}{}".format(yellow, index, end), end="\r")
        print("Data import Over")

    def select(self, d_str):
        sql = "SELECT COUNT FROM DICTS WHERE DICT='{}';".format(d_str)
        try:
            c = self.cursor.execute(sql)
            count = list(c)[0][0]
        except (IndexError, sqlite3.OperationalError) as e:
            count = None

        return count

    def insert(self, d, d_type):
        if self.select(d) is not None:
            print("Data was exists")
            return
        sql = "INSERT INTO DICTS (TYPE, DICT, COUNT) VALUES ('{}','{}',{});".format(d_type, d, 0)
        try:  # 如果数据导致语法异常则不添加
            self.cursor.execute(sql)
            self.db.commit()
            return 1
        except sqlite3.OperationalError:
            return 0

        # print("INSERT data successfully")

    # 查询数据
    def select_data(self, sql):
        try:
            c = self.cursor.execute(sql)
            for data in list(c):
                print(data)
        except (IndexError, sqlite3.OperationalError) as e:
            print(e)

    # 导出字典到文件
    def exportToFile(self):
        all_sql = "SELECT DICT FROM DICTS;"
        top_path_sql = "SELECT (a.DICT) FROM (SELECT * FROM DICTS WHERE TYPE='path' ORDER BY COUNT DESC)a LIMIT 3000;"
        allpath = "{}/../dicts/all.txt".format(os.getcwd())
        all_c = self.cursor.execute(all_sql)
        with open(allpath, "w", encoding="utf-8") as all:
            for d in list(all_c):
                print("all ", d[0])
                all.write(d[0] + "\n")


db = Dbcontroller()

if __name__ == '__main__':
    # 导入数据,字典类型: path/js
    # db.import_dicts("D:\\code\\github\\myDicts\\04dirDict\\all.txt", "path")
    # db.import_dicts("D:\\code\\github\\myDicts\\05fileDict\\all.txt", "path")
    # db.import_dicts("D:\\code\github\\myDicts\\05fileDict\\s\\all.txt", "js")
    # 查询
    print(db.select_data("SELECT * FROM DICTS;"))
    # 删除表
    # db.drop_table("DICTS")
    # 导出字典到文件
    # db.exportToFile()
    pass
