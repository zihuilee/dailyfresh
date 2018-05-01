from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
from goods.models import GoodsCategory,IndexGoodsBanner,IndexPromotionBanner,IndexCategoryGoodsBanner
from django.template import loader
import os
#创建Celery客户端就是创建celery应用对象
#
app = Celery('celery_tasks.tasks',broker='redis://192.168.24.129:6379/1')

@app.task
def send_active_email(to_email,user_name,token):
    """使用celery异步发送激活邮件"""
    subject = "天天生鲜用户激活"  # 标题
    body = ""  # 文本邮件体
    sender = settings.EMAIL_FROM  # 发件人
    receiver = [to_email]  # 接收人
    html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
    send_mail(subject, body, sender, receiver, html_message=html_body)

@app.task
def generate_static_index_html():
    """生成静态的html页面"""
    #1.查询主页相关信息
    #查询用户信息 --- user = request.user
    #（1）查询商品类别信息
    categorys = GoodsCategory.objects.all()
    #（2）查询图片轮播信息,按照index排序
    banners = IndexGoodsBanner.objects.all().order_by('index')
    #（3）查询活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
    #（4）查询商品分类列表信息
    for category in categorys:
        image_banners = IndexCategoryGoodsBanner.objects.filter(category=category,display_type=1)
        category.image_banners = image_banners
        title_banners = IndexCategoryGoodsBanner.objects.filter(category=category,display_type=0)
        category.title_banners = title_banners
    #（5）查询 购物车信息,默认是0，不是真实查到的数据
    cart_num = 0
    #2.构造上下文
    context = {
         'categorys' :categorys,
         'banners':banners,
         'promotion_banners':promotion_banners,
        'cart_num':cart_num
        }
    #得到静态模板-loader 方法
    template = loader.get_template('static_index.html')
    html_data = template.render(context)
    #保存成html文件：放到静态文件中
    file_path = os.path.join(settings.STATICFILES_DIRS[0],'index.html')
    #写入数据
    with open(file_path,'w') as file:
        file.write(html_data)
# @app.task
# def generate_static_index_html():
#     """生成静态的html页面"""
#     # (1)查询商品类别信息
#     categorys = GoodsCategory.objects.all()
#     # （2）查询图片轮播信息,注意按照index排序
#     banners = IndexGoodsBanner.objects.all().order_by('index')
#     # （3）查询活动信息
#     promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
#     # （4）查询分类列表信息
#     for category in categorys:
#         image_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1)
#         category.image_banners = image_banners
#         title_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0)
#         category.title_banners = title_banners
#     # （5）查询购物车信息
#     cart_num = 0
#     # 2.构造上下文
#     context = {
#         'categorys': categorys,
#         'banners': banners,
#         'promotion_banners': promotion_banners,
#         'cart_num': cart_num
#     }
#     #加载出模板
#     template = loader.get_template('static_index.html')
#     html_data = template.render(context)
#     #保存成html文件，放到静态文件中
#     file_path = os.path.join(settings.STATICFILES_DIRS[0],'index.html')
#     with open(file_path,'w') as file:
#         file.write(html_data)











