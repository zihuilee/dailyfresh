import re
from django import db
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from django_redis import get_redis_connection
from itsdangerous import SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from celery_tasks.tasks import send_active_email
from goods.models import GoodsSKU
from users.models import User, Address
from utils.views import LoginRequiredMixin
import json


# Create your views here.
# def register(request):
#     """展示注册页面的视图"""
#     if request.method == 'GET':
#         return render(request,'register.html')
#     else:
#         return HttpResponse('这里是注册逻辑实现')

#  使用类视图 处理注册逻辑
class RegisterView(View):
    """定义注册类视图"""
    def get(self,request):
        return render(request, 'register.html')
    def post(self,request):

    #获取注册请求参数
        user_name = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
    ##校验注册请求参数 --- 注册逻辑不涉及查重
        # 判断是否缺少参数:只要有一个为空,就返回假---返回注册页面
        if not  all([user_name,password,email]):
            return redirect(reverse('users:register'))
        # 判断邮箱格式是否正确 --- 取反
        if not re.match(r"^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$", email):
            return render(request,'register.html',{'errormsg':'邮箱格式不正确'})

    #判断是否勾选用户协议
        if allow != 'on':
            return render(request,'register.html',{'errormsg':'没有勾选用户协议'})
    #保存注册请求参数 到数据库 --- 属于隐私信息需要加密--可以使用django的用户认证系统
        try:
            user = User.objects.create_user(user_name,email,password)
        except db.IntegrityError:
            return render(request,'register.html',{'errormsg':'用户名已存在'})
        # 保存的用户默认是激活状态，需要手动设置成未激活状态
        user.is_active = False
        #保存这个用户的信息到数据库
        user.save()
        # 生成token --- 调用模型类中定义的生成token的方法。
        token = user.generate_active_token()
        # send_active_email(email, user_name, token)   # 错误写法
        # delay : 触发异步任务 --- 不然celery不认识
        send_active_email.delay(email, user_name, token)

        return redirect(reverse('goods:index'))

class ActiveView(View):
    """定义邮件激活的视图"""
    def get(self,request,token):
        """接收和处理激活请求"""
        # 逆推的思想
        # 1.创建序列化器
        serializer = Serializer(settings.SECRET_KEY,3600)
        #2.获取token，解出{'confirm':user_id},需要在签名为过期时,读取结果 --- 为防止出错，
#         放在try中 --- loads()
        try:
            result = serializer.loads(token)# 返回一个字典
        except SignatureExpired:#走这个表示链接过期
            return HttpResponse('链接已过期')
        #从字典中读取user_id
        user_id = result.get('confirm')
        #查询要激活的用户 --- 防止不存在报异常 fangzaitry中
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return HttpResponse('用户不存在')
        #重置激活状态是true
        user.is_active = True
        #保存到数据库
        user.save()
        # 响应结果:跳转到登录页面
        return redirect(reverse('users:login'))


class LoginView(View):
    # def get(self,request):
    #     """提供登录页面"""
    #     return render(request,'login.html')
    # def post(self,request):
    #     """处理登录逻辑"""
    #     #1.获取用户名和密码
    #     user_name = request.POST.get('user_name')
    #     pwd = request.POST.get('pwd')
    #     #2.进行参数校验,先判断是否是空
    #     if not all([user_name,pwd]):
    #         return redirect(reverse('users:login'))
    #     #（2）然后可以使用django认证系统判断是否登录成功
    #     user = authenticate(username=user_name,password=pwd)
    #     #登录失败的情况
    #     if user is None:
    #         return render(request,'login.html',{'mistake':"用户名或密码错误"})
    #     #验证登陆成功，并判断是否是激活用户
    #     if user.is_active is False:
    #         return render(request, 'login.html', {'mistake': "用户未激活"})
    #     # 能够执行到这里，说明没有异常，可以登入一个用户，登入用户的同时需要向服务器写入状态保持信息
    #     # django认证系统的login()默认会把用户状态保持信息存储到django_session中
    #     #如果我们选择使用django_redis作为缓存后端，需要进行配置
    #     # 使用django的用户认证系统，在session中保存用户的登陆状态
    #     login(request,user)
    #     # 登录记住用户---勾选就设置成没有活动后十天过期，没有勾选就在会话结束后立马过期
    #     remembered = request.POST.get('remembered')
    #     if remembered != 'on':
    #         request.session.set_expiry(0)
    #     else:
    #         request.session.set_expiry(60*60*24*10)
    #     #根据next参数后面的内容来确定登录成功后要跳转到的页面
    #     next = request.GET.get('next')
    #     if next is None:
    #         return redirect(reverse('goods:index'))
    #     else:
    #         return redirect(next)

        # 第二遍
    def get(self,request):
        """展示登录页面"""
        return render(request,'login.html')
    def post(self,request):
        """处理登录逻辑"""
        #1.接收从表单输入的内容
        user_name = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        #2.对参数校验
        if not all([user_name,pwd]):
            return redirect(reverse('users:login'))
        #3.当内容都不为空，使用django用户认证系统进行验证是否登陆成功 -
        user = authenticate(username = user_name,password =pwd)
        #判断 是否存在这个用户
        if user is None:
            return render(request,'login.html',{'mistake':"用户名或密码错误"})
        #判断此用户是否激活
        if user.is_active is False:
            return render(request,'login.html',{'mistake':'用户未激活'})
        #使用django认证系统，在session中保存用户的登录状态
        login(request,user)
        #登录记住用户,勾选就设置一个过期时间，不勾选就在会话结束后立马过期
        remembered = request.POST.get('remembered')
        if remembered != 'on':
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(60*60*24*10)
        #根据next参数后面内容跳转到对应页面，没有内容就跳转到主页，有内容就跳转到对应页
        #在界面跳转之前，需要将cookie的数据加到redis中
        #获取cookie中的购物车数据
        # cart_json = request.COOKIES.get('cart')
        # if cart_json:
        #     cart_dict_cookie = json.loads(cart_json)
        # else:
        #     cart_dict_cookie = {}
        # #获取redis中的购物车数据
        # redis_conn = get_redis_connection('default')
        # user_id = request.user.id
        # cart_dict_redis = redis_conn.hgetall('cart_%s'%user_id)
        # #遍历cookie中的购物车数据，判断商品是否在reids中存在，需要把cookie中的sku_id转成字节类型
        # for sku_id,count in cart_dict_cookie.items():
        #     sku_id = sku_id.encode()
        # #存在就累加count有一个原始count --origin_count
        #     if sku_id in cart_dict_redis:
        #         origin_count = cart_dict_redis[sku_id]
        #         #origin_count是字节类型，需要转成int类型才能累加
        #         count += int(origin_count)
        #     cart_dict_redis[sku_id] = count
        # #将合并后的redis数据，保存到redis中，
        # redis_conn.hmset('cart_%s'%user_id,cart_dict_redis)
        # #获取next参数，用于判断登录界面是哪里来的，还需要清除cookie
        # --以下是实现登录跳转时把未登录的购物车数据合并到redis的逻辑
        # #从cookie中获取购物车数据
        # cart_json = request.COOKIES.get('cart')
        # if cart_json:
        #     cart_dict_cookie = json.loads(cart_json)
        # else:
        #     cart_dict_cookie = {}
        # #从redis中获取购物车数据
        # redis_conn = get_redis_connection('default')
        # user_id = request.user.id
        # cart_dict_redis = redis_conn.hgetall('cart_%s'%user_id)
        # #进行购物车商品数量合并，将cookie中的购物车数据合并到redis中
        # for sku_id,count in cart_dict_cookie.items():
        #     #需要把sku_id转成bytes类型，才能判断redis是否存在
        #     sku_id = sku_id.encode()
        #     if sku_id in cart_dict_redis:#存在就累加，不存在就赋值
        #         origin_count = cart_dict_redis[sku_id]
        #         count += int(origin_count)
        #     cart_dict_redis[sku_id] = count
        # #将合并后的数据写入到redis
        # if cart_dict_redis:
        #     redis_conn.hmset('cart_%s'%user_id,cart_dict_redis)#hmset（）括号中不能穿入空字典
        # #响应结果 -- next参数，从哪儿来回哪儿去，没有就登陆到主页
        # #获取next参数，用于判断登录是从哪儿来的
        # next = request.GET.get('next')
        # if next is None:
        #     response = redirect(reverse('goods:index'))
        # else:
        #     if next == '/orders/place':
        #         response=redirect('cart:info')
        #     else:
        #         response=redirect(next)
        # #需要清除cookie
        # response.delete_cookie('cart')
        # return response

        #获取cookie中的购物车数据，有就转json字典，没有就给一个空字典
        cart_json = request.COOKIES.get('cart')
        if cart_json:
            cart_dict_cookie = json.loads(cart_json)
        else:
            cart_dict_cookie = {}
        #从redis中获取购物车数据
        #获取user_id
        user_id = request.user.id
        #创建连接redis的客户端对象
        redis_conn = get_redis_connection('default')
        #查询购物车数据---获取字典
        cart_dict_redis = redis_conn.hgetall('cart_%s'% user_id)
        #遍历cookie中的购物车数据，取出sku_id，商品数量
        for sku_id,count in cart_dict_cookie.items():
        #把sku_id转成bytes类型
            sku_id = sku_id.encode()
        #判断sku_id是否在redis的字典中
            if sku_id in cart_dict_redis:
        #有就累加商品数量
                origin_count = cart_dict_redis[sku_id]
                count += int(origin_count)
        #没有就生成新的购物车数据
            cart_dict_redis[sku_id] = count
    #将新生成的redis字典设置到redis，不能传入空字典，需要判断
        if cart_dict_redis:
            redis_conn.hmset('cart_%s'% user_id,cart_dict_redis)
        #获取next参数，确认从哪儿来回哪儿去
        next = request.GET.get('cart')
        if next is None:
            response = redirect(reverse('goods:index'))
        else:
            if next == '/orders/place':
                response=redirect('cart:info')
            else:
                response=redirect(next)
        #清除cookie中的购物车数据
        response.delete_cookie('cart')
        #返回结果
        return response

# class LogoutView(View):
#     """定义退出登录的视图"""
#     def get(self,request):
#         """处理退出登录逻辑:需要知道谁要退出登录,也就是需要知道清理谁的状态保持数据"""
# #         如果用户已登录，Django用户认证系统会把user对象加入到request当中,没有登录就不能退出登录
#         logout(request)#这个django认证系统的方法会把cookie和session清空，request参数中有user对象
#         #返回到登录页面
#         return redirect(reverse('users:login'))


#第二遍
class LogoutView(View):
    """定义退出登录的视图"""
    def get(self,request):
        logout(request)
        #返回到登录的页面
        return redirect(reverse('users:login'))

# class LoginRequired(View):
#     #重写as_view（）类方法
#     @classmethod
#     def as_view(cls):
#         #先需要调用父类方法
#         view = super().as_view()
#         return login_required(view)
# class LoginRequired(object):
#     @classmethod
#     def as_view(cls,**initkwargs):
#         view = super().as_view()
#         return login_required(view)

#
class AddressView(LoginRequiredMixin,View):
    """定义收货地址的视图"""
    def get(self,request):
        #1.查询出该用户最近的收货地址（最新的一个） --- 一查多 再取一个
        #user对象在request中，中间件从验证请求中的用户，所以request中带有user
        user = request.user
        try:#有可能地址没有，防止报错放在try中
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None
        #2.构造上下文
        context = {
            'address':address
        }
        #3.渲染模板
        return render (request,'user_center_site.html',context)
        # 要考虑的第一点-- 没有登陆的情况下不能访问用户中心页面
        #     第一种方法： 使用不灵活，代码较多
        # if request.user.is_authenticated():
        #     return render(request,'user_center_site.html')
        # else:
        #     return redirect(reverse('users:login'))
        #
        # 第二种方法：使用login_required装饰器装饰
        #  如果用户没有登入，则重定向到settings.LOGIN_URL，并将当前访问的绝对路径传递到查询字符串中."""
#         url(r'^address$', login_required(views.AddressView.as_view()), name='address')
#         这种方法也存在问题 --- 限制页面访问是视图的逻辑，还需要交给视图完成
#         2.2 --优化（1）
#         单继承：封装一个处理限制页面访问的类LoginRequired(View)，重写as_view()方法，给该方法的结果添加装饰器@login_required
# 哪个类视图中要处理限制页面访问的逻辑，就直接继承该封装的类LoginRequired(View)即可
#     如果 这个视图继承其他类比如TemplateView，则代码不能完成对应功能
#         2.3 -优化（2）多继承 --- 自定义一个类继承object如LoginRequired
#     另一个类是View
#     2.4 --- 优化（3）
#     可以将封装的LoginRequired(object)单独定义出来，放在工具中utils使用
#       增加修改类名字为LoginRequiredMinix(object)，表示是扩展的类


    def post(self,request):
        """编辑地址"""
        #1.接收多个参数
        user = request.user
        recv_name = request.POST.get('recv_name')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        recv_mobile = request.POST.get('recv_mobile')
        #对参数是否有空的进行校验,如果有空就返回到收货地址，没有空的就把信息保存到数据库再返回
        # 收货地址页面
        if all([recv_name,addr,zip_code,recv_mobile]):
            #保存地址信息到数据库,然后返回到用户地址页面
            Address.objects.create(
                user=user,
                receiver_name= recv_name,
                detail_addr = addr,
                zip_code = zip_code,
                receiver_mobile = recv_mobile
            )
        return redirect(reverse('users:address'))

#第二遍
# class AddressView(LoginRequiredMixin,View):
#     """定义用户中心的收货地址的视图"""
#     # 需要确定是登录用户才能访问用户中心 --- 需要在工具包utils中重写as_view（）用login_required装饰
#     def get(self,request):
#         #1.查询最新的一个地址信息
#         user = request.user #user对象在request中，中间件从验证请求中的用户，所以request中带有user
#         #防止没有地址报错，放在try中
#         try:
#             address = user.address_set.latest('create_time')
#         except Address.DoesNotExist:
#             address = None
#         #2.构造上下文
#         context = {
#             'address':address
#         }
#         #3.渲染模板
#         return render(request,'user_center_site.html',context)
#
#     def post(self, request):
#         """编辑修改地址"""
#         # 1.接收多个参数
#         user = request.user
#         recv_name = request.POST.get('recv_name')
#         addr = request.POST.get('addr')
#         zip_code = request.POST.get('zip_code')
#         recv_mobile = request.POST.get('recv_mobile')
#         # 2.校验
#         if all([recv_name, addr, zip_code, recv_mobile]):
#             """满足条件就保存信息,返回到收货地址页面"""
#             Address.objects.create(
#                 user=user,
#                 receiver_name=recv_name,
#                 detail_addr=addr,
#                 zip_code=zip_code,
#                 receiver_mobile=recv_mobile
#             )
#         return redirect(reverse('users:address'))

# 抽离父模板
# （1）从主页抽离出最高级别的父模板
# 进入个人中心小模块
# class UserInfoView(LoginRequiredMixin,View):
#     """定义个人中心视图"""
#     def get(self,request):
#         #1.获取个人中心页面
#         #2.查询数据库，显示用户基本信息
#         #3.使用redis数据库存储浏览记录
#         user = request.user
#         try:
#             address = user.address_set.latest('create_time')
#         except Address.DoesNotExist:
#             address = None
#
#
#         #商品浏览记录设计与查询
#         #创建redis连接对象
#         redis_connection = get_redis_connection('default')
#         #从redis中获取用户浏览商品的sku_id ---返回一个列表
#         sku_ids = redis_connection.lrange('history_%s'%user.id,0,4)
#         #遍历存储多个sku_id的列表,每次遍历出一个sku_id，就查询出sku_id对应的模型类GoodsSKU的信息
#         #把查询出来的对象存在一个空列表中
#         sku_list  = []
#         for sku_id in sku_ids:
#             sku = GoodsSKU.objects.get(id=sku_id)
#             sku_list.append(sku)
#         context = {
#             'address': address,
#             'sku_list':sku_list
#         }
#         return render(request, 'user_center_info.html', context)

#第二遍 个人信息
class UserInfoView(LoginRequiredMixin,View):
    """定义用户中心的个人信息页"""
    def get(self,request):
        user = request.user
        #查出该用户的地址信息
        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None

        #1.查询最近浏览记录 -- 查skuid，再关联到GoodsSKU对象信息 -
        #(1)创建redis连接对象
        redis_connection = get_redis_connection('default')
        #(2)使用这个连接对象和redis数据库交互查询出5个sku_id--返回一个列表
        sku_ids = redis_connection.lrange('history_%s'%user.id,0,4)
        #(3)创建一个存储sku对象即GoodsSKU模型类实例化的对象的列表
        sku_list = []
        #(4)遍历 sku_ids ,每2遍历一个sku_id就实例化一个GoodsSKU对象
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id = sku_id)
            sku_list.append(sku)

        #2.构造上下文
        context = {
            'address':address,
            'sku_list':sku_list
        }
        #3.渲染模板
        return render(request,'user_center_info.html',context)