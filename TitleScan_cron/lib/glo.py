

"""
跨模块的全局变量
##global仅作用在同一py文件中,跨module则没用
"""

_global_dict = {}

def _init():  # 初始化
    global _global_dict


def set_value(key, value):
    """ 定义一个全局变量 """
    _global_dict[key] = value


def get_value(key, defValue=None):
    """ 获得一个全局变量,不存在则返回默认值 """
    try:
        return _global_dict[key]
    except KeyError:
        return defValue


def get_all():
    """ 获得一个dict """
    return _global_dict

