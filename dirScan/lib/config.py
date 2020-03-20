# encoding=utf-8
import os
# 注意，所有字典都放在dicts目录下

# 配置目录爆破字典文件名

path_dict = "all.txt"
# 文件名爆破字典
filename_dict = ""
# 进程数，默认cpu_count()就好
processes = os.cpu_count()
# 每个进程中运行的协程数，这个数量不要太大，以免出现大量连接失败误报
# 这个是控制同时爆破url的数量，数量等于childconcurrency * processes
childconcurrency = 1
# 每个url爆破的协程数，这个数量不要太大，以免出现大量连接失败误报
# 这个控制爆破速度，如果总的url少，可以设大一点，默认为10
crons = 40

yellow = "\033[01;33m"
white = "\033[01;37m"
green = "\033[01;32m"
blue = "\033[01;34m"
red = "\033[1;31m"
end = "\033[0m"
