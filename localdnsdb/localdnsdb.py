# encoding=utf-8
import os
import sqlite3
import time

# 功能
# 1、读取数据存入数据库


import pymysql
import json

from pymysql import InternalError

config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'passwd': 'root',
    'charset': 'utf8mb4',
    'database': 'dns',
    'cursorclass': pymysql.cursors.DictCursor
    }


class Dbcontroller:

    def __init__(self):
        self.db = pymysql.connect(**config)
        self.db.autocommit(1)
        self.cursor = self.db.cursor()
        self.create_table()

    def create_table(self):
        try:
            self.cursor.execute('''create table dnsdicts(
                               id    INT      PRIMARY KEY AUTO_INCREMENT,
                               timestamp  VARCHAR(20)  NOT NULL,
                               name  VARCHAR(50)  NOT NULL,
                               type  VARCHAR(10)  NOT NULL,
                               value VARCHAR(500) NOT NULL
                            );
                            ''')
            print("Table created successfully")
        except InternalError as e:
            print(str(e))


    # 导入字典到数据库
    def import_dicts(self, d_file):
        with open(d_file, encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                d["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(d["timestamp"])))
                # insert into
                self.insert(**d)
        print("Data import successfully")

    # 检查是否重复
    def check(self, timestamp=None, name=None, type=None, value=None):
        sql = "SELECT * FROM dnsdicts WHERE timestamp='{}' and name='{}' and type='{}' and value='{}';".format(timestamp,
                                                                                                               name,
                                                                                                               type,
                                                                                                               value)
        self.cursor.execute(sql)
        if self.cursor.rowcount == 0:
            return 0
        return 1

    def insert(self, timestamp=None, name=None, type=None, value=None):
        sql = "INSERT INTO dnsdicts (timestamp, name, type, value) VALUES ('{}','{}','{}','{}');".format(timestamp,
                                                                                                         name,
                                                                                                         type,
                                                                                                         value)
        if self.check(timestamp, name, type, value):
            self.cursor.execute(sql)
            self.db.commit()
        print("INSERT data successfully")


db = Dbcontroller()


# 获取指定目录下所有同类文件名，并拼接为绝对路径
def oslistdirer(path, suffix):
    r = os.listdir(path)
    return [os.path.join(path,f) for f in r if f.endswith(suffix)]

if __name__ == '__main__':
    # db = Dbcontroller()
    # db.select("a", 'b', 'c', 'c')
    fies = oslistdirer("E:\\doc\\字典数据\\import", "json")
    for file in fies:
        db.import_dicts(file)
    pass
