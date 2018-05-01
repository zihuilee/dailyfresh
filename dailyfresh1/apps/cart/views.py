'''

from django.views.generic import View
from django.http import JsonResponse
from goods.models import GoodsSKU
from django_redis import get_redis_connection
import json
# Create your views here.

class AddCartView(View):
    #  属于post请求
    def post(self, request):
        # # # 提示：无论是否登陆状态，都需要获取suk_id,count,校验参数。。。
        # # 所以等待参数校验结束后，再来判断用户是否登陆
        # # if not request.user.is_authenticated():
        # #     return JsonResponse({'code': 1, 'message': '用户未登录'})
        # 2.收集购物车参数 sku_id,conut
        # sku_id = request.POST.get('sku_id')
        # count = request.POST.get('count')
        # # 3.校验购物车参数 all（）
        # if not all([sku_id,count]):
        #     return JsonResponse({'code':2,'message':'缺少参数'})
        # #4.判断sku_id是否合法，放在try中
        # try:
        #     sku = GoodsSKU.objects.get(id=sku_id)
        # except GoodsSKU.DoesNotExist:
        #     return JsonResponse({'code':3,'message':'sku_id错误'})
        # #5.判断count是否合法，转int，放在try中
        # try:
        #     count = int(count)
        # except Exception:
        #     return JsonResponse({'code':4,'message':'商品count错误'})
        # #6.判断是否超出库存 sku.stock ，
        # if count > sku.stock:
        #     return JsonResponse({'code':5,'message':'库存不足'})
        # #7.判断用户是否登录
        # if request.user.is_authenticated():
        # #登录用户就获取user_id
        #     user_id = request.user.id
        # #7.加入购物车 使用django_redis
        #     #（1）创建redis_conn对象
        #     redis_conn = get_redis_connection('default')
        #     ## 8.如果商品在购物车中存在，就直接累加商品数量；反之,把新的商品和数量添加到购物车
        #     origin_count = redis_conn.hget('cart_%s'%user_id,sku_id)
        #     if origin_count is not None:
        #         count += int(origin_count)
        #     redis_conn.hset('cart_%s'%user_id,sku_id,count)
        #     # 9.为了配合前端页面,展示最终的购物车数据的总数,需要在响应json之前,查询购物车数据
        #     cart_num = 0
        #     cart_dict =  redis_conn.hgetall('cart_%s' % user_id)
        #     for val in cart_dict.values():
        #         cart_num += int(val)
        #     #10.返回json数据
        #     return JsonResponse({'code':0,'message':'加入购物车成功','cart_num':cart_num})
        # else:
        #     #没有登录，就将购物车数据保存到cookie中
        #     #先从cookie的购物车信息中，获取当前商品的记录，json字符串购物车数据
        #     cart_json = request.COOKIES.get('cart')
        #     #判断 cart_json是否为空，不为空就转json字典，空就给一个空字典，后面需要使用
        #     if cart_json:
        #         cart_dict = json.loads(cart_json)
        #     else:
        #         cart_dict = {}
        #     #判断商品 sku_id 是否在cookie中，在就累加count，不在就赋值
        #     if sku_id in cart_dict:
        #         origin_count = cart_dict[sku_id]
        #         count += origin_count
        #     #判断是否超出库存
        #     if count > sku.stock:
        #         return JsonResponse({'code':5,'message':'库存不足'})
        #     #设置最终的商品数量到购物车
        #     cart_dict[sku_id] = count
        #     #查询购物车数量
        #     cart_num = 0
        #     for val in cart_dict.values():
        #         cart_num += val
        #     #将json字典转成json字符串
        #     cart_str = json.dumps(cart_dict)
        #     response = JsonResponse({'code':0,'message':'加入购物车成功','cart_num':cart_num})
        #     response.set_cookie('cart',cart_str)
        #     return response


       # 无论登录还是未登录都需要获取参数
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 检验参数 --  sku_id,count，是否缺少参数
        if not all([sku_id,count]):
            return JsonResponse({'code':2,'message':'缺少参数'})
        #判断商品是否合法
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code':3,'message':'商品不存在'})
        #判断数量count 是否是整型
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code':4,'messqge':'数量有误'})

        #判断用户是否登录，登录就查询redis中的数据，未登录就查询cookie信息
        if request.user.is_authenticated():
            user_id = request.user.id
            redis_conn = get_redis_connection('default')

            #先尝试从用户的购物车中获取商品sku_id 的原始数量，有就累加，没有就赋值
            origin_count = redis_conn.hget('cart_%s'%user_id,sku_id)#商品原有数量
            if origin_count is not None:
                count += int(origin_count)
            #还需要判断库存
            if count > sku.stock:
                return JsonResponse({'code':5,'message':'库存不足'})
            #存储到redis
            redis_conn.hset('cart_%s'%user_id,sku_id,count)
            #为了方便前端查看购物车数量，需要查询购物车总数
            cart_num = 0
            cart =redis_conn.hgetall('cart_%s'%user_id)
            for val in cart.values():
                cart_num += int(val)
            #响应结果
            return JsonResponse({'code':0,'message':'添加到购物车成功','cart_num':cart_num})
        else:
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
            #如果cookie有这个商品的购物车记录就累加，没有就赋值
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]
                count += origin_count
            #判断是否超过库存
            if count > sku.stock:
                return JsonResponse({'code':4,'message':'库存不足'})
            #设置最终的商品数量到购物车
            cart_dict[sku_id]=count
            #为了方便前端查看购物车，需要查询购物车总数
            cart_num = 0
            for val in cart_dict.values():
                cart_num += int(val)
            #将新字典转成json字符串
            cart_str = json.dumps(cart_dict)
            response = JsonResponse({'code':0,'message':'添加到购物车成功','cart_num':cart_num})
            response.set_cookie('cart',cart_str)
            return response
# class CartInfoView(View):
#     """购物车页面"""
#     def get(self,request):
#         """get请求--提供购物车页面，不需要传参数"""
#         #查询登录和未登录的购物车页面并渲染
#         #用户登录从redis查询数据
#         if request.user.is_authenticated():
#             redis_conn = get_redis_connection('default')
#             user_id = request.user.id
#             cart_dict = redis_conn.hgetall('cart_%s'%user_id)
#         #用户未登录从cookie查询数据
#         else:
#             cart_json = request.COOKIES.get('cart')
#             if cart_json:
#                 cart_dict = json.loads(cart_json)
#             else:
#                 cart_dict = {}
#         #保存遍历出来的sku对象
#         #定义一个新列表存储
#         skus = []
#         #定义两个变量用来表示总金额和总数量
#         total_amount = 0
#         total_count = 0
#         #遍历cart_dict,得到模板所需要的数据
#         for sku_id,count in cart_dict.items():
#             #查询商品sku是否合法，放在try中，商品不存在就跳过这个商品。
#             try:
#                 sku = GoodsSKU.objects.get(id=sku_id)
#             except GoodsSKU.DoesNotExist:
#                 continue
#         #从redis查出来的count是字节类型，需要转成int类型--- 无论从哪里得到的count，都转成int类型
#             count = int(count)
#             #计算小计
#             amount = sku.price * count
#             #将需要展示的数据保存到对象中
#             sku.amount = amount
#             sku.count = count
#             skus.append(sku)
#             #计算总金额
#             total_amount += amount
#             #计算商品总数量
#             total_count += count
#         #2.构造上下文
#         context = {
#             'skus':skus,
#             'total_amount':total_amount,
#             'total_count':total_count
#         }
#         #3.渲染模板
#         return render(request,'cart.html',context)


# --
class CartInfoView(View):
    """购物车页面"""
    #get 请求
    def get(self,request):
        #1.查询购物车数据
        #判断用户是否登录，登录用户就从redis查询数据，未登录就从cookie查询信息
        if request.user.is_authenticated():
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            cart_dict = redis_conn.hgetall('cart_%s'%user_id)
        else:
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
        #定义一个空列表用来保存遍历出来的sku
        skus = []
        #定义两个变量
        #总数量
        total_count = 0
        #总金额
        total_amount = 0
        for sku_id,count in cart_dict.items():
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                continue
            count = int(count)
            #计算小计
            amount = sku.price * count
            #将需要展示的数据保存在对象中，防止遍历覆盖
            sku.count = count
            sku.amount = amount
            #生成模型列表
            skus.append(sku)
            #累加得总金额，总数量
            total_count += count
            total_amount += amount
        #2.构造上下文
        context = {
            'skus':skus,
            'total_count':total_count,
            'total_amount':total_amount
        }
        #渲染模板
        return render(request,'cart.html',context)


class UpdateCartView(View):
    """更新购物车 + - 编辑"""
    def post(self,request):
        #获取参数 -- sku_id,count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 校验参数
        # 判断all()
        if not all([sku_id,count]):
            return JsonResponse({'code':1,'message':'参数不完整'})
        # 判断商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code':2,'message':'商品不存在'})
        #判断count是否是整数
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code':3,'message':'数量有误'})
        #判断是否超过库存
        if count > sku.stock:
            return JsonResponse({'code':4,'message':'库存不足'})
        #判断用户是否登录，登录就将修改存储到redis数据库，未登录就将修改存入cookie中
        if request.user.is_authenticated():
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            cart_dict = redis_conn.hset('cart_%s'%user_id,sku_id,count)
            return JsonResponse({'code':0,'message':'更新购物车成功'})
        else:
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
            cart_dict[sku_id] = count
        #将字典转成json字符串
        new_cart_json = json.dumps(cart_dict)
        #响应结果
        response = JsonResponse({'code':0,'message':'更新购物车成功'})
        # 写入cookie
        response.set_cookie('cart',new_cart_json)
        return response


#-- 更新购物车数量视图
class UpdateCartView(View):
    """更新购物车商品 +- 编辑框"""
    # 这是post请求
    def post(self,request):
    # 获取参数 sku_id,count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
    #校验参数是否为空
        if not all([sku_id,count]):
            return JsonResponse({'code':1,'message':'参数不完整'})
    #判断商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code':2,'message':'商品不存在'})
    #判断数量
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code':3,'message':'数量有误'})
    #判断库存
        if count > sku.stock:
            return JsonResponse({'code':4,'message':'库存不足'})
    #判断是否登录，登录就修改redis，未登录就修改cookie
        if request.user.is_authenticated():
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
        # 如果设计成幂等的，count就是最终要保存的商品的数量，不需要累加
            redis_conn.hset('cart_%s'%user_id,sku_id,count)
            return JsonResponse({'code':0,'message':'更新购物车成功'})
        else:
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
            #因为是设计成幂等的，count就是最终要保存的商品的数量，不需要累加
            cart_dict[sku_id] = count
            new_cart_json = json.dumps(cart_dict)
            #响应结果
            response = JsonResponse({'code':0,'message':'更新购物车成功'})
            #设置新的cookie
            response.set_cookie('cart',new_cart_json)
            return response







# class DeleteCartView(View):
#     """删除购物车记录"""
#     def post(self,request):
#         #获取参数 -- sku_id
#         sku_id = request.POST.get('sku_id')
#         #校验参数
#         # 判断是否缺少参数
#         if not sku_id:
#             return JsonResponse({'code':1,'message':'参数错误'})
#         #判断用户是否登录，用户登录就删除redis数据库中的购物车数据，未登录就删除cookie
#         if request.user.is_authenticated():
#             redis_conn = get_redis_connection('default')
#             user_id = request.user.id
#             redis_conn.hdel('cart_%s'%user_id,sku_id)
#         else:
#             cart_json = request.COOKIES.get('cart')
#             if cart_json:
#                 cart_dict = json.loads(cart_json)
#                 #判断要删除的商品是否存在
#                 if sku_id in cart_dict:
#                     del cart_dict[sku_id]
#                 response = JsonResponse({'code':0,'message':'删除购物车记录成功'})
#                 response.set_cookie('cart',json.dumps(cart_dict))
#                 return response
#         #当删除成功或没有要删除的都要提示用户删除成功
#         return JsonResponse({'code':0,'message':'删除成功'})

# -- 删除购物车记录
class DeleteCartView(View):
    """删除购物车记录"""
    #这个是post请求
    def post(self,request):
    #获取参数sku_id
        sku_id = request.POST.get('sku_id')
    #校验参数是否缺少
        if not sku_id:
            return JsonResponse({'code':1,'message':'缺少参数'})
    #判断用户是否登录，登录用户就删除redis的数据，未登录就删除cookie的记录
        if request.user.is_authenticated():
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            redis_conn.hdel('cart_%s'%user_id,sku_id)
        else:
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                cart_dict = json.loads(cart_json)
                if sku_id in cart_dict:#判断要删除的商品是否存在
                    del cart_dict[sku_id]#字典删除key对应的value
                #响应中重新写入cookie
                response = JsonResponse({'code':0,'message':'删除成功'})
                response.set_cookie('cart',json.dumps(cart_dict))
                return response
         # 当删除成功或者没有要删除的都提示用户成功
        return JsonResponse({'code': 0, 'message': '删除成功'})
'''
from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse,JsonResponse
from goods.models import GoodsSKU
import json
from django_redis import get_redis_connection


class AddCartView(View):
    """添加购物车,属于post请求"""
    def post(self,request):
        #获取参数sku_id,count,从POST请求中获取
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        #检验参数完整性
        if not all([sku_id,count]):
            return JsonResponse({'code':2,'message':'参数不完整'})
        #查询数据库，判断商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code':3,'message':'商品不存在'})
        #判断count是int类型,转成Int
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code':4,'message':'数量有误'})
        #当需要存储数据，需要考虑用户是否登录，未登录需要保存到cookie，
        #登录用户需要将购物车数据保存到redis中
        #如果用户未登录
        if not request.user.is_authenticated():
        #从cookie的购物车信息中获取商品记录,是json字符串
            cart_json = request.COOKIES.get('cart')
        #如果获取到了就转成json字典，没有就给一个空字典
            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
        #如果字典中有sku_id，就累加该商品数量，没有就赋值,设置到cookie中
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]
                count += origin_count
        #判断库存：计算最终的count和库存比较
            if count > sku.stock:
                return JsonResponse({'code':5,'message':'超出库存'})
        #设置最终的商品数量到购物车
            cart_dict[sku_id] = count
        #计算购物车总数
            cart_num = 0
            for val in cart_dict.values():
                cart_num += val
        #将json字典转成json字符串
            cart_str = json.dumps(cart_dict)
        #将购物车数据写入到cookie中，构造响应体，传入购物车商品总数
            response = JsonResponse({'code':0,'message':'添加购物车成功','cart_num':cart_num})
        #设置这个json字符串到cookie
            response.set_cookie('cart',cart_str)
        #返回结果
            return response
        #如果用户登录就存储购物车数据到redis
        elif request.user.is_authenticated():
            #获取user_id
            user_id = request.user.id
            #创建redis连接对象
            redis_conn = get_redis_connection('default')
            #从redis的购物车信息中获取商品记录，如果有就累加该商品数量，没有就设置
            origin_count = redis_conn.hget('cart_%s'%user_id,sku_id)
            if origin_count is not None:
                count += int(origin_count)
            #判断库存
            if count > sku.stock:
                return JsonResponse({'code':5,'message':'超出库存'})
            #存储到redis
            redis_conn.hset('cart_%s'%user_id,sku_id,count)
            #查询购物车总数
            cart_num = 0
            cart = redis_conn.hgetall('cart_%s'% user_id)
            for val in cart.values():
                cart_num += int(val)
            #返回结果
            return JsonResponse({'code':0,'message':'添加购物车成功','cart_num':cart_num})


class CartInfoView(View):
    """购物车页面"""
    def get(self,request):
        #获取购物车所有数据
        #如果登录情况下：
        if request.user.is_authenticated():
            #创建redis连接对象
            redis_conn = get_redis_connection('default')
            #获取user_id
            user_id = request.user.id
            #查询购物车所有数据--hgetall
            cart_dict = redis_conn.hgetall('cart_%s'% user_id)
        #未登录情况下
        else:
            #从cookie中获取购物车数据 -- json字符串类型
            cart_json = request.COOKIES.get('cart')
            #有就转json字典，没有就给一个空字典
            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
        # 定义一个容器来存储商品信息
        skus = []
        # 定义总金额和总数量的变量
        total_amount = 0
        total_count = 0
        #遍历购物车数据，形成模板所需要的数据 --- sku_id，count必须有
        for sku_id,count in cart_dict.items():
            #查询商品sku信息，没有就继续循环
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                continue
            #把count转成int类型
            count = int(count)
            #计算该种商品的总价
            amount = sku.price * count
            #将需要展示的数据保存到对象中
            sku.amount = amount
            sku.count = count
            #将每个对象添加到容器中
            skus.append(sku)
            #计算总金额
            total_amount += amount
            #计算总数量
            total_count += count
        #构造上下文
        context ={
            'skus':skus,
            'total_amount':total_amount,
            'total_count':total_count
        }
        #渲染模板
        return render(request,'cart.html',context)

class UpdateCartView(View):
    """更新购物车信息 + - 编辑"""
    def post(self,request):
        #获取参数sku_id,count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        #校验参数完整性
        if not all([sku_id,count]):
            return JsonResponse({'code':1,'message':'参数不完整'})
        #判断商品是否存在，查询数据库
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code':2,'message':'商品不存在'})
        #判断count是int类型
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code':3,'message':'数量有误'})
        #判断库存
        if count > sku.stock:
            return JsonResponse({'code':4,'message':'库存不足'})
        #判断用户是否登录
        # 用户未登录就将修改的数据存储到cookie中
        if not request.user.is_authenticated():
            #获取购物车数据，有就转json字典，没有就给空字典
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                cart_dict_cookie =  json.loads(cart_json)
            else:
                cart_dict_cookie = {}
            #设置字典中的购物车数据,幂等设计思想，返回最终结果，不需要累加。
            cart_dict_cookie[sku_id] = count
            #转成json字符串
            new_cart_json = json.dumps(cart_dict_cookie)
            #构造响应体
            response = JsonResponse({'code':0,'message':'更新购物车成功'})
            #写入到cookie中
            response.set_cookie('cart',new_cart_json)
            #返回结果
            return response
        #登录就将修改后的数据保存到redis中
        else:
            #获取user_id
            user_id = request.user.id
            #创建redis连接对象
            redis_conn = get_redis_connection('default')
            #设置更新后的购物车数据到redis中
            cart_dict_redis = redis_conn.hset('cart_%s' % user_id,sku_id,count)
            #返回结果
            return JsonResponse({'code':0,'message':'更新购物车成功'})

class DeletaCartView(View):
    """删除购物车商品记录"""
    def post(self,request):
        #获取参数，sku_id
        sku_id = request.POST.get('sku_id')
        #检验参数，not即可
        if not sku_id:
            return JsonResponse({'code':1,'message':'参数不对'})
        #判断用户是否登录,#已登录就删除redis中商品记录
        if request.user.is_authenticated():
            #创建连接redis的对象
            redis_conn = get_redis_connection('default')
            #获取user_id
            user_id = request.user.id
            redis_conn.hdel('cart_%s'% user_id,sku_id)
        #未登录就删除cookie中商品记录,重新写入删除后的cookie
        else:


            cart_json = request.COOKIES.get('cart')
            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
            #字典删除键对应的value
            del cart_dict[sku_id]
            #重新在响应中写入cookie
            response = JsonResponse({'code':0,'message':'删除购物车成功'})
            response.set_cookie('cart',json.dumps(cart_dict))
            return response
        return JsonResponse({'code':0,'message':'删除成功'})





