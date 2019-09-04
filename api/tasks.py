from __future__ import absolute_import
from celery import shared_task
from django_redis import get_redis_connection
import subprocess
import datetime
import logging
import re
import os

logger = logging.getLogger(__name__)

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
    result=result.decode("utf-8")
    regex = re.findall('100% packet loss', result)
    if len(regex) == 0:
        logging.info("%s:up"%ip)
        return True
    else:
        logging.info("%s:down"%ip)
        return False


@shared_task
def checkUsedIp():
    """
    定时任务，回收redis集合ip_used_set中可用ip
    """
    logger.info("开始定期回收IP检测:%s" % datetime.datetime.now())
    conn = get_redis_connection()
    ip_list = []
    for c_used in conn.sscan_iter("ip_used_set",match=None,count=None):
        c_used = c_used.decode()
        ip,c_publickey = c_used.split(" ")
        logging.info("开始检测IP: %s,cpublickey: %s"% (ip,c_publickey))
        # 如果ip无法ping通，则回收该IP
        if not check_alive(ip):
            logging.info("回收ip: %s"%ip)
            # redis集合ip回收
            if conn.srem("ip_used_set", c_used):
                conn.sadd("ip_available_set", ip)
                # 动态删除配置文件
                remove_peer = "wg set wg0 peer %s remove" % (c_publickey)
                save = "wg-quick save wg0"
                status = os.system(remove_peer)
                if status == 0:
                    os.system(save)
                    ip_list.append(ip)
                else:
                    #如果配置文件修改失败，恢复redis操作
                    logger.error("wg删除客户端配置错误")
                    if conn.srem("ip_available_set",ip):
                        conn.sadd("ip_used_set", c_used)
    return ip_list