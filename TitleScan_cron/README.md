# TitleScan 

Note: python 3.6

## 功能

对收集的子域名站点进行筛查，并进行分类

##使用的方式
asyncio + aiomultiprocess

## 主逻辑

流程：访问不存在的资源，响应正常，再请求根目录，根据每个分支不同的状态码进行分类

分类：正常网站、受限网站、非正常网站、不是网站


## 代码结构

- TitleScan.py        主逻辑

- lib/core.py         主要函数：getStatusAndTitle，获取相应数据，整理返回dict

- lib/cmdline.py      解析命令行参数

- report              报告目录