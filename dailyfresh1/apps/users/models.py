from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from utils.models import BaseModel


# Create your models here.
# user中的应用模型类User是使用django自带的用户认证系统维护的。
class User(AbstractUser,BaseModel): #可以迁移出第一张表 关于用户的
    """用户"""
    class Meta:
        db_table = 'df1_users'
    # 下面预留空白 需要 生成激活令牌
    def generate_active_token(self):
        """生成激活token"""
        serializer = Serializer(settings.SECRET_KEY,3600) # 生成序列化器
        token = serializer.dumps({"confirm":self.id})
       # 返回bytes类型
        # 括号中的编码？--- 需要解码成字符串类型---还是加密的。
        return token.decode()



class Address(BaseModel):# 可以迁移出第二张表。 关于地址信息的
    """地址"""
    user = models.ForeignKey(User,verbose_name="所属用户")
    receiver_name = models.CharField(max_length=20,verbose_name="收件人")
    receiver_mobile = models.CharField(max_length=11, verbose_name="联系电话")
    detail_addr = models.CharField(max_length=256, verbose_name="详细地址")
    zip_code = models.CharField(max_length=6, verbose_name="邮政编码")
    class Meta:
        db_table= 'df1_address'

















