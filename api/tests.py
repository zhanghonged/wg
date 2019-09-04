from django.test import TestCase

# Create your tests here.




# import redis
#
# conn = redis.Redis(host="127.0.0.1", port=6379)
# conn.lpush('name_list',*['张三','李四'])
# v = conn.llen('name_list')
# print(v)

import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wg.settings")
django.setup()

from IPy import IP, intToIp
from django_redis import get_redis_connection

start_ip = "10.0.0.253"
end_ip = "10.0.1.5"
netmask = "22"

def check_ip(ipAddr):
    """
    判断IP是否合法
    """
    addr = ipAddr.strip().split('.')
    if len(addr) != 4:
        return False
    else:
        flag = True
        for i in range(4):
            try:
                addr[i] = int(addr[i])
                if addr[i] >= 0 and addr[i] < 255:
                    pass
                else:
                    flag = False
            except:
                flag = False
        # IP 第一位和最后一位不能为0
        addr_first = int(addr[0])
        addr_last = int(addr[-1])
        if addr_first == 0 or addr_last == 0:
            flag = False
        return flag
def general_ip(start_ip,end_ip,netmask):
    """
    生成IP地址段
    """
    # 起止IP必须在同一网段中
    network_segment = IP(start_ip + '/' + netmask, make_net=True)
    if IP(end_ip) in network_segment:
        ip_list = []
        for ip_dec in range(IP(start_ip).int(),IP(end_ip).int()+1):
            ip = intToIp(ip_dec,4)
            if check_ip(ip):
                ip_list.append(ip)

        return ip_list
    else:
        return "error"

def generate_available_ip2set():
    conn = get_redis_connection()
    # 删除现有的可用IP集合
    conn.delete('ip_available_set')
    # 起止IP必须在同一网段中
    network_segment = IP(start_ip + '/' + netmask, make_net=True)

    if IP(end_ip) in network_segment:
        for ip_dec in range(IP(start_ip).int(),IP(end_ip).int()+1):
            ip = intToIp(ip_dec,4)
            if check_ip(ip):
                conn.sadd("ip_available_set",ip)

        return "success"
    else:
        return "error"


import re
import subprocess


def check_alive(ip, count=2, timeout=1):
    '''
    ping网络测试,通过调用ping命令,发送一个icmp包，从结果中通过正则匹配是否有100%关键字，有则表示丢包，无则表示正常
    '''
    cmd = 'ping -c %d -w %d %s' % (count, timeout, ip)

    p = subprocess.Popen(cmd,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True
                         )

    result = p.stdout.read()
    result=result.decode("gbk")
    print(result)
    regex = re.findall('100% packet loss', result)
    if len(regex) == 0:
        print("%s:up"%ip)
    else:
        print("%s:down"%ip)


conn = get_redis_connection()
for ip in conn.sscan_iter("ip_available_set",match=None,count=None):
    check_alive(ip)