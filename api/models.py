from django.db import models

# Create your models here.

# class IpAvailable(models.Model):
#     """
#     可用IP列表
#     """
#     ip = models.CharField(max_length=32,verbose_name="可用ip")
#
#     def __str__(self):
#         return self.ip
#
#     class Meta:
#         db_table = "ip_available"
#
# class IpUsed(models.Model):
#     """
#     已用IP列表
#     """
#     ip = models.CharField(max_length=32,verbose_name="已用ip")
#     expri_time = models.DateTimeField(verbose_name="过期时间")
#     publickey = models.CharField(max_length=32,blank=True,null=True,verbose_name="客户端公钥")
#
#     def __str__(self):
#         return self.ip
#
#     class Meta:
#         db_table = "ip_used"