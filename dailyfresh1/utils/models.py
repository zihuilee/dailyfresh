from django.db import models

# Create your models here.

#定义BaseModel
class BaseModel(models.Model):
    """为模型类都补充的字段"""
    create_time = models.DateField(auto_now_add=True,verbose_name="创建时间")
    update_time = models.DateField(auto_now=True,verbose_name="修改时间")
    class Meta:
        abstract = True #这句话说明是抽象基类，不会创建任何数据表
