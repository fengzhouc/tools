# TitleScan 

Note: python 3.6

# 功能

对收集的子域名站点进行筛查，并进行分类

## 修改记录
### 20210428
新增获取域名的ip,对ip进行端口扫描，组合成域名/ip:port,加入到扫描队列中，更好的发现站点
### 20210729
重构portScan使用gevent做协程并发, 默认并发数500, 可通过config.py修改process参数进行设置
### 20210810
重构其他模块使用gevent做协程并发, titleScan默认并发数os.cpu_count(), 可通过 -p 设置并发数
### 20220113
更新数据处理，输入的taget支持domain/ip/url/urlpath

数据处理流如下
- source: domain/ip/url/urlpath
- dnsQuery处理后: {source: [ip,ip1,ip2], source: [domain,domain1,domain2]}
- portScan处理后: [{source: [ip:port,ip1:port,ip2:port]},{source: [domain:port,domain1:port,domain2:port]}]
- titleScan处理: ip:port,ip1:port,ip2:port,domain:port,domain1:port,domain2:port


## 主逻辑
流程：访问不存在的资源，响应正常，再请求根目录，根据每个分支不同的状态码进行分类

## 流程图
![img.png](img.png)

# 结果分类
## A类：正常网站
     不存在目录200,30x,404
	 主页200,30x
## B类：大概率正常网站
     不存在目录401,407,415，访问受限
	 主页401,407,415,403,404,访问受限或者没有主页
## C类：小概率正常网站
     禁止访问403
	 服务器内部错误500
## D类：非正常网站及不是网站
     501/502/503/504/请求失败
## E类：意外情况
     可能自定义了状态码
以上是一些情况比较常规的处理，预料之外的需要后期持续完善


# 代码结构

- TitleScan.py        主逻辑

- lib/cmdline.py      解析命令行参数

- lib/config.py       配置文件，主要涉及：端口列表、端扫协程数、dns解析服务器ip

- lib/core.py         主要函数：getStatusAndTitle，获取相应数据
  
- lib/dnsQuery.py     dns解析，获取域名A记录

- lib/glo.py          跨模块的全局变量存储

- lib/portScan.py     端口扫描器（全连接），通过协程以模拟masscan的快速扫描，单IP全端口扫描大概在20s

- lib/titleScan.py    web站点的探活、分类、title抓取等

- report              报告c存放目录
