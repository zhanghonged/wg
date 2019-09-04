import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wg.settings")
django.setup()
from IPy import IP, intToIp
from django_redis import get_redis_connection


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

def generate_available_ip2set(start_ip,end_ip,netmask):
    conn = get_redis_connection()
    # 删除现有的server publickey字段
    conn.delete("spublickey")
    # 删除现有的可用IP集合
    conn.delete('ip_available_set')
    # 起止IP必须在同一网段中
    network_segment = IP(start_ip + '/' + netmask, make_net=True)

    # 初始化服务器公钥
    server_publickey_file = "/etc/wireguard/spublickey"
    cmd = "cat %s" % server_publickey_file
    server_publickey = os.popen(cmd).read().strip()
    conn.set("spublickey",server_publickey)

    # 初始化可用ip
    if IP(end_ip) in network_segment:
        for ip_dec in range(IP(start_ip).int(),IP(end_ip).int()+1):
            ip = intToIp(ip_dec,4)
            if check_ip(ip):
                conn.sadd("ip_available_set",ip)

        return "success"
    else:
        return "error"

if __name__ == "__main__":
    start_ip = "10.0.0.2"
    end_ip = "10.0.3.254"
    netmask = "22"

    res = generate_available_ip2set(start_ip,end_ip,netmask)
    print(res)