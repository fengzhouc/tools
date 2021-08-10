# encoding=utf-8

import gevent
# from gevent import monkey
# gevent需要修改Python自带的一些标准库，这一过程在启动时通过monkey patch完成
# monkey.patch_socket()

import _queue
import multiprocessing

from gevent.pool import Pool
from scapy.all import *
from scapy.layers.inet import IP, TCP
from lib.config import processes, ports, yellow, end, red, blue




# 主逻辑
def main(port, scan_ip=None, pqueue=None):
    print(scan_ip, port, sep=":")
    try:
        packet = IP(dst=scan_ip) / TCP(dport=port, flags='S')  # 构造一个 flags 的值为 S 的报文
        send = sr1(packet, timeout=2, verbose=0)
        if send.haslayer('TCP'):
            if send['TCP'].flags == 'SA':  # 判断目标主机是否返回 SYN+ACK
                send_1 = sr1(IP(dst=scan_ip) / TCP(dport=port, flags='R'), timeout=2, verbose=0)  # 只向目标主机发送 RST
                # print('{}[PortScan] [+] {} is open{}'.format(yellow, port, end))
                pqueue.put(port)
            elif send['TCP'].flags == 'RA':
                # 端口未开放
                pass
    except Exception as e:
        pass


# 进度
def schedule(queue):
    total = queue.qsize()
    while not queue.empty():
        print("{}[Schedule] {}/{} | {:.0%}{}".format(yellow, total - queue.qsize(), total,
                                                     (total - queue.qsize()) / total, end), end="\r")


# 入口
def port_scan(rqueue=None):
    """

    :param rqueue:  {dm: [ip]}
    :return:  [{dm:[ip:port,dm:port]}]
    """
    ip_re = re.compile('[A-Za-z]', re.S)  # 判断是否非ip
    _pool = multiprocessing.Pool(processes=processes)
    result = []  # [{dm:[ip:port,dm:port]}]
    dm = ""  # 域名
    total = rqueue.qsize()
    # 端口扫描的进度条线程
    # threading.Thread(target=schedule, args=(rqueue,)).start()
    print("{}[PortScan] Start portScan......{}".format(blue, end))
    start_dns = time.time()
    while True:
        try:
            queue_ip = rqueue.get_nowait()
            dm = list(queue_ip.keys())[0]  # domain
            ips = list(queue_ip.values())[0]  # 对应域名的所有ip
            ipps = []  # 域名/ip组合端口的所有数据
            for index, ip in enumerate(ips):
                # ip = ip.strip()
                if len(ip_re.findall(ip)) > 0:
                    # 这里因为dnsquery在查询不到的时候,返回域名,所以这里相应的处理,直接添加
                    ipps.append(ip)
                    continue
                print("{}[PortScan] {:.0%} | '{}/{}', #dm:{}/{}, ip:{}/{}{}".format(yellow,
                                                                                    (total - rqueue.qsize()) / total,
                                                                                    dm, ip,
                                                                                    total - rqueue.qsize(), total,
                                                                                    index + 1, len(ips),
                                                                                    end))
                pqueue = multiprocessing.Manager().Queue()
                _pool.map(functools.partial(async_main, scan_ip=ip, pqueue=pqueue), ports)  # 常见端口
                # TODO 整理结果的数据格式 {dm, [ip:port,dm:port]}
                while True:
                    try:
                        port = pqueue.get_nowait()
                        ipp = "{}:{}".format(ip, port)
                        dmp = "{}:{}".format(dm, port)
                        if ipp not in ipps:
                            ipps.append(ipp)
                        if dmp not in ipps:
                            ipps.append(dmp)
                    except _queue.Empty:  # on python 2 use Queue.Empty
                        break
            result.append({dm: ipps})
        except _queue.Empty:  # on python 2 use Queue.Empty
            break
    _pool.close()
    _pool.join()
    print("{}[PortScan] PortScan Over, time: {}{}".format(blue, time.time() - start_dns, end))
    return result

# 主逻辑
def async_main(port, scan_ip=None, pqueue=None):
    addr = (scan_ip, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建TCP对象
    sock.settimeout(2)  # 设置超时
    try:
        sock.connect(addr)  # 建立完整连接 和telnet相同
        # print(f'{str(str(addr[0]))} :{str(str(addr[1]))} is open')
        pqueue.put(port)
    except:
        pass
    finally:
        sock.close()


# TODO 端口扫描优化
# 背景：原来的设计性能太差了,参考masscan及zmap,将发包跟收包分开,在控制端口数量
# 扫描状态表，记录每个端口扫描的情况，{obj,dm,ip,port,send_time,retry,status}
# 思路
# 符合协程的工作模式: 尽管发包,不等待响应
def async_port_scan(rqueue=None, pros=None):
    """
    :param rqueue:  {dm: [ip,ip1,ip2], dm1: [ip,ip1,ip2]}
    :return:  [{dm:[ip:port,dm:port]}]
    """
    result = []  # [{dm:[ip:port,dm:port]}]
    # 协程任务池
    threads = []
    if pros:
        pool = Pool(pros)
    else:
        pool = Pool(processes)

    ip_re = re.compile('[A-Za-z]', re.S)  # 判断是否非ip
    result = []  # [{dm:[ip:port,dm:port]}]
    dm = ""  # 域名
    total = rqueue.qsize()
    # 端口扫描的进度条线程
    # threading.Thread(target=schedule, args=(rqueue,)).start()
    print("{}[PortScan] Start portScan......{}".format(blue, end))
    start_dns = time.time()
    while True:
        try:
            queue_ip = rqueue.get_nowait()
            dm = list(queue_ip.keys())[0]  # domain
            ips = list(queue_ip.values())[0]  # 对应域名的所有ip
            ipps = []  # 域名/ip组合端口的所有数据
            for index, ip in enumerate(ips):
                # ip = ip.strip()
                if len(ip_re.findall(ip)) > 0:
                    # 这里因为dnsquery在查询不到的时候,返回域名,所以这里相应的处理,直接添加
                    ipps.append(ip)
                    continue
                print("{}[PortScan] {:.0%} | '{}/{}', #dm:{}/{}, ip:{}/{}{}".format(yellow,
                                                                                    (total - rqueue.qsize()) / total,
                                                                                    dm, ip,
                                                                                    total - rqueue.qsize(), total,
                                                                                    index + 1, len(ips),
                                                                                    end))
                pqueue = multiprocessing.Manager().Queue()
                for port in ports:
                    threads.append(pool.spawn(async_main, port, scan_ip=ip, pqueue=pqueue))
                gevent.joinall(threads)
                # TODO 整理结果的数据格式 {dm, [ip:port,dm:port]}
                while True:
                    try:
                        port = pqueue.get_nowait()
                        ipp = "{}:{}".format(ip, port)
                        dmp = "{}:{}".format(dm, port)
                        if ipp not in ipps:
                            ipps.append(ipp)
                        if dmp not in ipps:
                            ipps.append(dmp)
                    except _queue.Empty:  # on python 2 use Queue.Empty
                        break
            result.append({dm: ipps})
        except _queue.Empty:  # on python 2 use Queue.Empty
            break
    print("{}[PortScan] PortScan Over, time: {}{}".format(blue, time.time() - start_dns, end))
    return result


if __name__ == '__main__':
    ip = {"dm": ["121.8.148.87"]}
    rqueue = multiprocessing.Manager().Queue()
    rqueue.put(ip)
    start_time = time.time()
    async_port_scan(rqueue)
    # port_scan(rqueue)
    end_time = time.time()
    print('[time cost] : ' + str(end_time - start_time))
