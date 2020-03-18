# encoding=utf-8
import os
# 注意，所有字典都放在dicts目录下

# 配置目录爆破字典文件名
path_dict = "all.txt"
# 文件名爆破字典
filename_dict = ""
# 进程数，默认cpu_count()就好
processes = os.cpu_count()
# 每个url爆破的协程数，这个数量不要太大，以免出现大量连接失败误报
crons = 100
# 每个进程中运行的协程数，这个数量不要太大，以免出现大量连接失败误报
# 这个是控制同时爆破url的数量，数量等于childconcurrency * cpu_count()
childconcurrency = 2
