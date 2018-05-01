from django.shortcuts import render,redirect
from django.views.generic import View
from utils.views import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from users.models import Address
from django.utils import timezone
from utils.views import LoginRequiredJsonMixin,TransactionAtomicMixin
from django.http import JsonResponse
from orders.models import OrderInfo,OrderGoods
from django.db import transaction
from django.core.paginator import Paginator,EmptyPage
import time
from alipay import AliPay
from django.conf import settings
from django.core.cache import cache

# Create your views here.
'''
class PlaceOrderView(LoginRequiredMixin,View):
    """订单确认页面"""
    #这个是post请求
    def post(self,request):
    # 这里必须是登录用户才能进入 -- 所有要进行用户登录的验证--LoginRequiredMiXin
    #获取参数，sku_ids，count --- 用户从详情页过来才有count -- 通过count建立逻辑分支
        sku_ids = request.POST.getlist('sku_ids')
        count = request.POST.get('count')
    #校验参数，是否缺少参数
        if not sku_ids:#如果sku_ids没有，就重定向到购物车重新选择
            return redirect(reverse('cart:info'))
    #定义临时容器
        skus = []
        total_count = 0
        total_sku_amount = 0
        trans_cost = 10
        total_amount = 0 # 实付款

    #检验count，用于区分用户从哪儿进入订单确认页面,如果没有count是从购物车页面点击去结算进来的
    #从而建立逻辑分支-- 从购物车页面点去结算 进来 和 从商品详情点击直接购买进来，商品数据从redis获取
        # 如果从购物车进来，查询商品数据，商品的数量从redis获取
        if not count:
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            cart_dict = redis_conn.hgetall('cart_%s'%user_id)
            #遍历商品 sku_ids,获取每个商品的信息
            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    return redirect(reverse('cart:info'))
                #取出的sku_id是字符串类型，需要转成bytes
                sku_id = sku_id.encode()
                #取出每个sku_id对应的商品数量
                sku_count = cart_dict[sku_id]
                #--- count转成int类型，方便后续代码的计算和比较。
                sku_count = int(sku_count)
                #计算商品小计
                amount = sku.price * sku_count
                #将商品金额和数量封装到sku对象，防止每次遍历覆盖原值
                sku.count = sku_count
                sku.amount = amount
                skus.append(sku)
                #商品总金额-不含运费，和商品总数量
                total_count += sku_count
                total_sku_amount += amount
        # 如果是从详情页进来，查询商品数据，商品的数量count从request中获取，需要try
        else:#如果从详情页过来，逻辑差不多，只是多了查询判断count和判断库存
            for sku_id in sku_ids:#只有一个sku_id
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    return redirect(reverse('cart:info'))
                #判断count,没有就重定向到详情页，传参数是不定长参数
                try:
                    sku_count = int(count)
                except Exception:
                    return redirect(reverse('goods:detail',args= sku_id ))
                #判断库存

                if sku_count > sku.stock:
                    return redirect(reverse('goods:detail',args=sku_id))

                amount = sku.price * sku_count
                #把金额和数量封装到sku对象
                sku.count = sku_count
                sku.amount = amount
                skus.append(sku)
                #商品总金额--不含运费 ，商品总数量
                total_sku_amount += amount
                total_count += sku_count
        total_amount = total_sku_amount + trans_cost
        #获取用户地址信息
        try:
            address = Address.objects.filter(user=request.user).latest('create_time')
        except Address.DoesNotExist:
            address = None
        #2.构造上下文
        context = {
            'skus':skus,
            'total_count': total_count,
            'total_sku_amount': total_sku_amount,
            'trans_cost': trans_cost,
            'total_amount': total_amount,
            'address': address,
            'sku_ids':','.join(sku_ids)
        }
        return render(request,'place_order.html',context)


class CommitOrderView(LoginRequiredJsonMixin,TransactionAtomicMixin,View):
    """订单提交"""
    #这个是post请求,接收用户提交的订单信息，存储在OrderInfo和OrderGoods表中
    # 跳转到全部订单页面
    def post(self,request):
        #获取参数 user,address_id,pay_method,sku_ids,count--登录用户，从redis获取
        user = request.user
        address_id= request.POST.get('address_id')
        pay_method = int(request.POST.get('pay_method'))
        sku_ids = request.POST.get('sku_ids')
        #检验是否缺少参数 ，all(address_id,pay_method,sku_ids) ??count
        if not all([address_id,pay_method,sku_ids]):
            return JsonResponse({'code':2,'message':'缺少参数'})
        #判断地址是否存在，放在try中
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return JsonResponse({'code':3,'message':'地址不存在'})
        #判断支付方式 --- if not in语句
        if pay_method not in OrderInfo.PAY_METHODS:
            return JsonResponse({'code':4,'message':'支付方式错误'})
        #创建redis连接对象，取出字典
        redis_conn = get_redis_connection('default')
        cart_dict = redis_conn.hgetall('cart_%s'%user.id)
        # 截取出sku_ids列表 sku_ids = [1 5] --
        sku_ids = sku_ids.split(',')
        # sku_ids = sku_ids.split(',') --- 需要在place视图中context添加 ’sku_ids‘：’，‘.join(sku_ids) -- 模板传递 sku_ids:{{sku_ids}}
        #定义临时容器
        total_count = 0
        total_amount = 0
        #手动生成order_id - timezone.now()
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        #在操作数据库之前创建事务保存点
        sid = transaction.savepoint()
        # 创建商品订单信息
        #暴力回滚
        try:
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_amount=0,
                trans_cost=10,
                pay_method=pay_method
            )
            #遍历sku_ids列表
            # 循环取出sku，判断商品是否存在
            for sku_id in sku_ids:
                for i in range(3):# 0 1 2
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        #回滚
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'code':5,'message':'商品不存在'})
                #判断商品数量count，判断库存---redis中读取
                    sku_count = cart_dict.get(sku_id.encode())
                    sku_count = int(sku_count)
                    if sku_count > sku.stock:
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'code':6,'message':'库存不足'})

                    # time.sleep(10)
                #加入乐观锁
                #减少sku库存
                    origin_stock = sku.stock
                    new_stock = origin_stock - sku_count
                #增加sku销量
                    new_sales = sku.sales + sku_count
                    result = GoodsSKU.objects.filter(id=sku_id,stock=origin_stock).update(stock=new_stock,sales = new_sales)
                    if 0 == result and i<2:
                        continue
                    elif 0 == result and i==2:
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'code':8,'message':'下单失败，请检查库存'})
                #创建订单商品信息
                    OrderGoods.objects.create(
                        order = order,
                        sku=sku,
                        count = sku_count,
                        price = sku.price
                    )
                #计算总数和总金额
                    total_count += sku_count
                    total_amount += (sku.price * sku_count)
                    break#下单成功就跳出循环
    # 修改订单信息里面的总数和总金额(OrderInfo) --- 封装到order对象中
            order.total_count = total_count
            order.total_amount = total_amount + 10
            order.save()
        except Exception:#出现任何异常都要回滚
            transaction.savepoint_rollback(sid)
            return JsonResponse({'code':7,'message':'下单失败'})
        #没有异常就手动提交
        transaction.savepoint_commit(sid)
    # 订单生成后删除购物车(hdel)
        redis_conn.hdel('cart_%s'%user.id,*sku_ids)
#     #响应结果
        return JsonResponse({'code':0,'message':'下单成功'})


class UserOrderView(LoginRequiredMixin,View):
    """用户中心全部订单页面"""
    def get(self,request,page):
        #提供订单信息页面
        #1.查询所有信息
        #查询user --
        user = request.user
        #查询所有订单
        orders = user.orderinfo_set.all().order_by('-create_time')
        #遍历所有订单
        for order in orders:
        #给订单动态绑定状态 -- 使用对象.属性的方式
            order.status_name = OrderInfo.ORDER_STATUS[order.status]
        #给订单动态绑定支付方式
            order.pay_method_name = OrderInfo.PAY_METHODS[order.pay_method]
        #定义临时变量
            order.skus = []
        #查询订单中所有商品
            order_skus = order.ordergoods_set.all()
        #遍历订单中所有商品,，得到每个商品信息
            for order_sku in order_skus:
                sku = order_sku.sku
                sku.count = order_sku.count
                sku.amount = sku.price * sku.count
                order.skus.append(sku)
    #分页
        page = int(page)
        paginator = Paginator(orders, 2)
        try:
            page_orders = paginator.page(page)
        except EmptyPage:
         #如果传入的页数不存在默认给第一页
            page_orders = paginator.page(1)
            page = 1
    #页数
        page_list = paginator.page_range
    #响应结果
        context = {
            "orders": page_orders,
            "page": page,
            "page_list": page_list,
        }

        return render(request, "user_center_order.html", context)


class PayView(LoginRequiredJsonMixin,View):
    #用户向服务器传递订单id，当做请求参数传入
    def post(self,request):
        #获取订单id
        order_id = request.POST.get('order_id')
        #校验订单
        if not order_id:
            return JsonResponse({'code':2,'message':'订单id错误'})
        #获取订单信息 -- 放在try中防止报异常
        try:
            order = OrderInfo.objects.get(
                user = request.user,
                order_id = order_id,
                status= OrderInfo.ORDER_STATUS_ENUM["UNPAID"],
                pay_method= OrderInfo.PAY_METHODS_ENUM["ALIPAY"]
            )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'code':3,'message':'订单错误'})
        # 创建用于支付宝支付的对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            # 自己生产的私钥
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False 配合沙箱模式使用
        )
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),  # 将浮点数转成字符串
            subject='天天生鲜',
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )
        # 生成url:让用户进入支付宝页面的支付网址   yyukid0458@sandbox.com
        url = settings.ALIPAY_URL + "?" + order_string
        return JsonResponse({'code':0,'message':'支付成功','url':url})

class CheckPayView(LoginRequiredJsonMixin,View):
    """检查订单状态"""
    def get(self,request):
        #获取订单id
        order_id = request.GET.get('order_id')
        #校验订单id
        if not order_id:
            return JsonResponse({'code':2,'message':'订单id错误'})
        #获取订单信息
        try:
            order = OrderInfo.objects.get(
                order_id=order_id,user=request.user,
                status=OrderInfo.ORDER_STATUS_ENUM["UNPAID"],
                pay_method=OrderInfo.PAY_METHODS_ENUM["ALIPAY"]
            )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'code':3,'message':'订单错误'})
        #创建用于支付宝支付的对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            # 自己生产的私钥
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False 配合沙箱模式使用
        )
        #查询支付结果
        while True:
            response = alipay.api_alipay_trade_query(order_id)
            #判断支付结果
            code = response.get('code')#支付宝接口调用结果的标志
            trade_status = response.get('trade_status')#用户支付状态
        #如果支付成功，设置订单的支付状态为待评论，设置支付宝对应的订单编号

            if code == '10000' and trade_status == 'TRADE_SUCCESS':
                #表示用户支付成功
                #设置订单的支付状态为待评论
                order.status = OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"]
                #设置支付宝对应的订单编号
                order.trade_id = response.get('trade_no')
                order.save()
                #返回json，告诉前端结果
                return JsonResponse({'code':0,'message':'支付成功'})
            #判断用户其他支付状态，订单支付会有延迟，有些状态只是暂时出错
            elif code == '40004' or (code=='10000' and trade_status == 'WAIT_BUYER_PAY' ):
                # 表示支付宝的接口暂时调用失败，网络延迟，订单还未生成；or 等待订单的支付
                #继续查询
                continue
            #如果用户支付失败，返回失败结果
            else:
                return JsonResponse({'code':4,'message':'支付失败'})

class CommentView(LoginRequiredMixin,View):
    """订单评论"""
    def get(self,request,order_id):
        #提供评论页面
        #获取参数 user
        user = request.user
        #查询订单，放在try中
        try:
            order = OrderInfo.objects.get(order_id=order_id,user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('orders:info'))
        #给订单动态绑定状态
        order.status_name = OrderInfo.ORDER_STATUS[order.status]
        #定义临时容器
        order.skus = []
        #查询订单中所有商品
        order_skus = order.ordergoods_set.all()
        #遍历订单中所有商品，获得每个商品的信息
        for order_sku in order_skus:
            sku = order_sku.sku
            sku.count = order_sku.count
            sku.amount = sku.price * sku.count
            #加入临时容器中
            order.skus.append(sku)
        #构造上下文
        context = {
            'order':order
        }
        #响应结果，渲染模板
        return render(request,'order_comment.html',context)
    def post(self,request,order_id):
        #处理评论内容
        #获取参数用户user
        user = request.user
        #查询订单,放在try中
        try:
            order = OrderInfo.objects.get(order_id=order_id,user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('orders:info'))
        #获取评论条数,转成int类型
        total_count = request.POST.get('total_count')
        total_count = int(total_count)
        #遍历获取sku_id和content
        for i in range(1,total_count+1):
            sku_id = request.POST.get('sku_%s'%i)
            content = request.POST.get('content_%s'%i)
        #查询出订单所有商品,没有就跳过继续
            try:
                order_goods = OrderGoods.objects.get(order=order,sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue
        #保存评论内容，封装到对象
            order_goods.comment = content
            order_goods.save()
        #清除商品详情缓存
            cache.delete('detail_%s'%sku_id)
        #设置商品状态为已完成
        order.status = OrderInfo.ORDER_STATUS_ENUM["FINISHED"]
        order.save()
        #响应结果
        #重定向到订单第一页
        return redirect(reverse('orders:info',kwargs={'page'}))
'''

class PlaceOrderView(LoginRequiredMixin,View):
    """订单确认页面"""
    def post(self,request):
        #从post请求中获取sku_ids,count
        sku_ids = request.POST.getlist('sku_ids')
        count = request.POST.get('count')
        #校验参数sku_ids是否存在，不存在就重定向到购物车
        if not sku_ids:
            return redirect(reverse('cart:info'))
        #定义临时容器，定义所需变量
        skus= []
        total_count = 0
        total_amount = 0#实付款
        trans_cost = 10
        total_sku_amount = 0 #商品总金额
        #查询商品数据，需要分情况
        #如果从购物车页面点击提交订单进入，获取不到count参数,需要从redis中获取
        if count is None:
            #创建连接redis的对象
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            cart_dict = redis_conn.hgetall('cart_%s'% user_id)
            #遍历sku_ids，取出每个sku_id得到sku，获取不到就重定向到购物车
            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    return redirect(reverse('cart:info'))
                #取出sku_id对应的商品数量转成int类型
                sku_count = cart_dict.get(sku_id.encode())
                sku_count = int(sku_count)
                #计算商品小计
                amount = sku.price * sku_count
                #把商品小计和商品数量封装到sku对象中
                sku.count = sku_count
                sku.amount = amount
                #把sku对象添加到空列表中
                skus.append(sku)
                #累加小计得到商品总金额
                total_sku_amount += amount
                #累加商品数量得到商品总数量
                total_count += sku_count
        else:
            #如果从商品详情页进入，count从POST请求中获取

            #遍历sku_ids，根据sku_id查询sku，没有就重定向到购物车页面
            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    return redirect(reverse('cart:info'))
                # 商品数量转成int类型，不对就重定向到详情页
                try:
                    sku_count = int(count)
                except Exception:
                    return redirect(reverse('goods:detail',args=sku_id))
                #判断库存，出错就重定向到详情页
                if sku_count > sku.stock:
                    return redirect(reverse('goods:detail',args=sku_id))
                #计算商品小计
                amount = sku.price * sku_count
                #将需要保存的数据封装到sku对象中
                sku.amount = amount
                sku.count = sku_count
                #添加到skus列表中
                skus.append(sku)
                #累加商品小计得商品总金额
                total_sku_amount += amount
                # 累加商品数量得商品总数量
                total_count += sku_count
        #计算实付款
        total_amount = total_sku_amount + trans_cost
        #根据user_id查询最新的地址
        try:
            address = Address.objects.filter(user=request.user).latest('create_time')
        except Address.DoesNotExist:
            address = None
        #构造上下文
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_sku_amount': total_sku_amount,
            'trans_cost': trans_cost,
            'total_amount': total_amount,
            'address': address,
            'sku_ids':','.join(sku_ids)#'1,2,3'
        }
        #渲染模板
        return render(request,'place_order.html',context)


class CommitOrderView(LoginRequiredJsonMixin,View):
    """订单提交"""
    def post(self,request):
        #获取参数--address_id,pay_method,sku_ids,user
        address_id = request.POST.get('address_id')
        user = request.user
        pay_method = int(request.POST.get('pay_method'))
        sku_ids= request.POST.get('sku_ids')
        #校验参数完整性(address_id,paymethod,sku_ids)
        if not all([address_id,pay_method,sku_ids]):
            return JsonResponse({'code':2,'message':'缺少参数'})
        #判断地址,查询数据库
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return JsonResponse({'code':3,'message':'地址不存在'})
        #判断支付方式,是否在模型类的四种支付方式中
        if pay_method not in OrderInfo.PAY_METHODS:
            return JsonResponse({'code':4,'message':'支付方式错误'})
        #创建redis连接对象
        redis_conn = get_redis_connection('default')
        #取出购物车字典
        cart_dict = redis_conn.hgetall('cart_%s'% user.id)
        # 截取sku_ids列表
        sku_ids = sku_ids.split(',')
        #定义两个临时变量来表示商品总数量和总金额
        total_count = 0
        total_amount = 0
        #手动生成order_id
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        #在操作数据库前创建事务保持点，出错就回滚
        save_point = transaction.savepoint()
        #在创建订单商品信息前，先创建商品订单信息，商品订单和订单商品是一对多的关系
        try:
            order = OrderInfo.objects.create(
                order_id= order_id,
                user = user,
                address = address,
                total_amount = 0,
                trans_cost = 10,
                pay_method = pay_method,
            )
            #遍历sku_ids,根据sku_id查询sku
            for sku_id in sku_ids:
                #添加乐观锁
                for i in range(3):
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        transaction.savepoint_rollback(save_point)
                        return JsonResponse({'code':5,'message':'商品不存在'})
                    #从字典中获取商品数量需要sku_id是字符串类型，再把商品数量转成int类型
                    sku_count = cart_dict.get(sku_id.encode())
                    sku_count = int(sku_count)
                    #判断库存
                    if sku_count > sku.stock:
                        transaction.savepoint_rollback(save_point)
                        return JsonResponse({'code':6,'message':'库存不足'})
                    #原始库存
                    origin_stock = sku.stock
                    #减少sku库存 --新库存
                    new_stock = origin_stock - sku_count
                    #增加sku销量--新销量
                    new_sales = sku.sales + sku_count
                    #更新库存和销量，需要判断
                    result = GoodsSKU.objects.filter(id=sku_id,stock=origin_stock).update(sales=new_sales,stock=new_stock)
                    if 0 == result and i < 2:
                        continue #还有机会重新下单
                    elif 0 == result and i == 2:
                        transaction.savepoint_rollback(save_point)
                        return JsonResponse({'code':8,'message':'下单失败'})
                #保存订单商品数据
                OrderGoods.objects.create(
                    order= order,
                    sku = sku,
                    count = sku_count,
                    price = sku.price
                )
                #计算商品总数量和总金额
                total_count += sku_count
                total_amount += (sku.price * sku_count)
            #修改订单信息里面的商品总数和总金额
            order.total_amount = total_amount
            order.total_count = total_count + 10
            order.save()
            #出现任何异常都回滚
        except Exception:
            transaction.savepoint_rollback(save_point)
            return JsonResponse({'code':7,'message':'下单失败'})
        #确认没有异常就手动提交
        transaction.savepoint_commit(save_point)
        #订单生成后删除购物车
        redis_conn.hdel('cart_%s'% user.id,*sku_ids)
        #响应结果
        return JsonResponse({'code':0,'message':'下单成功'})

class UserOrdersView(LoginRequiredMixin,View):
    """我的订单页面"""
    def get(self,request,page):
        #获取user
        user = request.user
        #查出该user的所有订单 --按最新创建时间排序
        orders = user.orderinfo_set.all().order_by('-create_time')
        #遍历这些订单
        for order in orders:
            #给订单动态绑定订单状态，支付方式 --- 使用对象.属性的方式
            order.status_name = OrderInfo.ORDER_STATUS[order.status]
            order.pay_methods_name = OrderInfo.PAY_METHODS[order.pay_method]
            #定义订单商品的空列表，来存放订单遍历的商品
            order.skus = []
            #查询订单中所有商品
            order_skus = order.ordergoods_set.all()
            #遍历订单中所有商品
            for order_sku in order_skus:
            #获取需要的商品信息
                sku = order_sku.sku
                #商品数量和商品总价
                sku.count = order_sku.count
                sku.amount = sku.price * sku.count
                # 添加到空列表
                order.skus.append(sku)

        #分页，如果传入的页数不存在，默认给第一页
        #先转成int类型
        page = int(page)
        # 构造Paginator对象
        paginator = Paginator(orders,2)#对查询出的订单进行分页，每页显示两个订单信息
        try:
            page_orders = paginator.page(page) #返回指定页码的page对象，若不存在则抛出错误
        except EmptyPage:
            page_orders = paginator.page(1)
            page = 1
        #页数 --页码范围，返回一个列表，从1开始，如[1,2,3,4]
        page_list = paginator.page_range
        #构造上下文
        context = {
            'orders':page_orders,
            'page':page,
            'page_list':page_list
        }
        #渲染模板
        return render(request,'user_center_info.html',context)






























