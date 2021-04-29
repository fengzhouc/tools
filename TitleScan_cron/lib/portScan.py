# encoding=utf-8

import _queue
import multiprocessing
from scapy.all import *
from scapy.layers.inet import IP, ICMP, TCP
from lib.config import processes, ports, yellow, end, red


# 主逻辑
def main(port, scan_ip=None, pqueue=None):
    try:
        packet = IP(dst=scan_ip)/TCP(dport=port, flags='S')  # 构造一个 flags 的值为 S 的报文
        send = sr1(packet, timeout=2, verbose=0)
        if send.haslayer('TCP'):
            if send['TCP'].flags == 'SA':   # 判断目标主机是否返回 SYN+ACK
                send_1 = sr1(IP(dst=scan_ip)/TCP(dport=port, flags='R'), timeout=2, verbose=0)  # 只向目标主机发送 RST
                print('{}[PortScan] [+] {} is open{}'.format(yellow, port, end))
                pqueue.put(port)
            elif send['TCP'].flags == 'RA':
                # 端口未开放
                pass
    except Exception as e:
        pass


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
    while True:
        try:
            queue_ip = rqueue.get_nowait()
            dm = list(queue_ip.keys())[0]  # domain
            ips = list(queue_ip.values())[0]  # 对应域名的所有ip
            ipps = []  # 域名/ip组合端口的所有数据
            for ip in ips:
                # ip = ip.strip()
                if len(ip_re.findall(ip)) > 0:
                    # 这里因为dnsquery在查询不到的时候,返回域名,所以这里相应的处理,直接添加
                    ipps.append(ip)
                    continue
                print('{}[PortScan] Start scan {}{}'.format(yellow, ip, end))
                packet_ping = IP(dst=ip) / ICMP()  # 在扫描端口之前先用 ICMP 协议探测一下主机是否存活
                ping = sr1(packet_ping, timeout=2, verbose=0)
                if ping is not None:
                    pqueue = multiprocessing.Manager().Queue()
                    _pool.map(functools.partial(main, scan_ip=ip, pqueue=pqueue), ports)  # 常见端口
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
                elif ping is None:
                    print("{}[PortScan] {}无法ping通{}".format(red, ip, end))
            result.append({dm: ipps})
        except _queue.Empty:  # on python 2 use Queue.Empty
            break
    _pool.close()
    _pool.join()
    return result


if __name__ == '__main__':
    ip = "121.8.148.87"
    start_time = time.time()
    main(ip)
    end_time = time.time()
    print('[time cost] : ' + str(end_time-start_time))
