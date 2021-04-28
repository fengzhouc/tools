# encoding=utf-8

from dns.resolver import Resolver
from lib.config import resolver_nameservers, resolver_timeout, resolver_lifetime, blue, end, red

def dns_resolver():
    """
    dns解析器
    """
    resolver = Resolver()
    resolver.nameservers = resolver_nameservers
    resolver.timeout = resolver_timeout
    resolver.lifetime = resolver_lifetime
    return resolver


def dns_query(qname, qtype="A", rqueue=None):
    """
    查询域名DNS记录

    :param str qname: 待查域名
    :param str qtype: 查询类型
    :return: 查询结果,数据格式 {qname, [answer]}
    """
    result = {}
    resolver = dns_resolver()
    qname = qname.strip()
    try:
        answer = resolver.resolve(qname, qtype)
        answer_list = []
        for aw in answer:
            answer_list.append(str(aw))
        print("{}[DnsQuery] {} record of {}, answer: {}{}".format(blue, qname, qtype, answer_list, end))
        result[qname] = answer_list
    except Exception as e:
        print("{}[DnsQuery] Query '{}' record of {} failed{}".format(red, qname, qtype, end))
        rqueue.put({qname: [qname]})
    else:
        rqueue.put(result)


if __name__ == "__main__":
    answer = dns_query("kk.cvte.com")
    print(answer)
