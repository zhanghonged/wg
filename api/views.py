from django.http import JsonResponse
from django_redis import get_redis_connection
from django.views.decorators.csrf import csrf_exempt
from wg.settings import SPUBLICKEY as spublickey
import json
import os

# spublickey = "server_public_key"

def call_resource(conn,c_publickey):
    """
    资源分配
    """
    result = {"code":500,"spublickey":"","cip":""}
    ip_available_count = conn.scard("ip_available_set")
    if ip_available_count > 0:
        client_ip = conn.spop("ip_available_set")
        c = client_ip.decode() + " " + c_publickey
        conn.sadd("ip_used_set", c)
        # 动态添加配置文件
        add_peer = "wg set wg0 peer %s allowed-ips %s/32" %(c_publickey,client_ip.decode())
        add_save = "wg-quick save wg0"
        status = os.system(add_peer)
        if status == 0:
            os.system(add_save)
            result["code"] = 200
            result["cip"] = client_ip.decode()
            result["spublickey"] = spublickey
        else:
            # 如果配置文件处理失败，撤销redis操作
            if conn.srem("ip_used_set",c):
                conn.sadd("ip_available_set",client_ip.decode())
    else:
        result["code"] = 400

    return result

@csrf_exempt
def demand(request):
    """
    请求资源
    """
    result = {"code":500,"spublickey":"","cip":""}
    if request.method == "POST":
        data = json.loads(request.body.decode())
        c_ip = data.get("cip")
        c_publickey = data.get("cpublickey")

        conn = get_redis_connection()
        if c_ip and c_publickey:
            # c_ip不为空，客户端非第一次请求，需要判断此ip是否可用
            is_available = conn.sismember("ip_available_set",c_ip)
            if is_available:
                # 此ip已释放，重新分配
                result = call_resource(conn,c_publickey)
            else:
                # 此ip正在使用，判断c_publickey 和 配置文件里的是否一致
                c_used = c_ip + " " + c_publickey
                is_c_used = conn.sismember("ip_used_set",c_used)
                if is_c_used:
                    # 公钥相同，表面这个客户端在用，原样返回
                    result["code"] = 200
                    result["spublickey"] = spublickey
                    result["cip"] = c_ip
                else:
                    # 公钥不同，表面此ip别人在用，重新分配
                    result = call_resource(conn,c_publickey)
        elif c_publickey:
            # c_ip为空，表示客户端第一次请求，从资源池中给客户端分配ip
            result = call_resource(conn,c_publickey)
    return JsonResponse(result)

@csrf_exempt
def release(request):
    """
    释放资源
    """
    result = {"code":500}
    if request.method == "POST":
        data = json.loads(request.body.decode())
        c_ip = data.get("cip")
        c_publickey = data.get("cpublickey")
        if c_ip and c_publickey:
            conn = get_redis_connection()
            c_used = c_ip + " " + c_publickey
            if conn.srem("ip_used_set", c_used):
                conn.sadd("ip_available_set", c_ip)
                # 动态删除配置文件
                remove_peer = "wg set wg0 peer %s remove" % (c_publickey)
                save = "wg-quick save wg0"
                status = os.system(remove_peer)
                if status == 0:
                    os.system(save)
                    result["code"] = 200
                else:
                    # 如果配置文件修改失败，恢复redis配置
                    if conn.srem("ip_available_set",c_ip):
                        conn.sadd("ip_used_set", c_used)
            else:
                result["code"] = 400

    return JsonResponse(result)
