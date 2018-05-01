from django.shortcuts import render,redirect
from django.views.generic import View
from django.core.cache import cache
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django_redis import get_redis_connection
from orders.models import OrderGoods
import json
from django.core.paginator import Paginator,EmptyPage
from goods.models import GoodsCategory,Goods,GoodsSKU,IndexCategoryGoodsBanner,IndexPromotionBanner,IndexGoodsBanner
# Create your views here.

# class BaseCartView(View):
#     """购物车逻辑基类-- 购物车商品数量"""
#     def get_cart_num(self,request):
#         cart_num = 0
#         #用户登录的情况，从redis获取数据
#         if request.user.is_authenticated():
#
#             #创建redis_conn 对象
#             redis_conn = get_redis_connection('default')
#             #获取user_id
#             user_id = request.user.id
#             #从数据库中获取购物车数据 -- 得到一个字典
#             cart_dict = redis_conn.hgetall('cart_%s'%user_id)
#             #遍历这个字典，累加购物车的值
#             for val in cart_dict.values():
#                 cart_num += int(val)
#         else:
#             #用户未登录需要查询cookie
#             cart_json = request.COOKIES.get('cart')
#             #判断 cart_json 是否为空
#             if cart_json:
#                 cart_dict = json.loads(cart_json)
#             else:
#                 cart_dict = {}
#             for val in cart_dict.values():
#                 cart_num += val
#         return cart_num


# # 第二遍 ：购物车逻辑封装到基类BaseCartView中
# class BaseCartView(View):
#     """封装购物车逻辑的基类---提供购物车数据统计功能"""
#     #主页 ， 详情页， 列表页需要展示购物车
#     def get_cart_num(self,request):
#         cart_num = 0
#         #判断用户是否登录，登录就查询redis，未登录就查询cookie
#         if request.user.is_authenticated():
#             redis_conn = get_redis_connection('default')
#             user_id = request.user.id
#             cart_dict = redis_conn.hgetall('cart_%s'%user_id)
#             #遍历字典，累加购物车的值
#             for val in cart_dict.values():
#                 cart_num += int(val)
#         else:
#             cart_json = request.COOKIES.get('cart')
#             if cart_json:
#                 cart_dict = json.loads(cart_json)
#             else:
#                 cart_dict = {}
#             for val in cart_dict.values():
#                 cart_num += val
#         return cart_num

class BaseCartView(View):
    """展示各页面购物车商品数量"""
    def get_cart_num(self,request):
        cart_num = 0
        #如果用户登录
        if request.user.is_authenticated():
        #获取user_id
            user_id = request.user.id
        #创建redis连接对象
            redis_conn = get_redis_connection('default')
        #从redis中获取购物车数据
            cart = redis_conn.hgetall('cart_%s'%user_id)
        #累加商品数量
            for val in cart.values():
                cart_num += int(val)
        #返回cart_num
        #如果用户未登录
        else:
            #从cookie中获取购物车数据是json字符串
            cart_json = request.COOKIES.get('cart')
            #判断是否获取到，有就转json字典，没有就给空字典
            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
            #遍历字典的值，累加商品数量
            for val in cart_dict.values():
                cart_num += int(val)
        #返回cart_num
        return cart_num












class IndexView(BaseCartView):
    """主页"""
    # def get(self,request):
    #     # （1）查询用户个人信息 --- request.user
    #     #先从缓存中读取数据，如果有就获取缓存数据，没有就查询
    #     context = cache.get('index_page_data')
    #     if context is None:
    #         print('没有缓存')
    #         # (2)查询商品分类信息
    #         categorys = GoodsCategory.objects.all()
    #         #(3)查询图片轮播信息：注意按照index排序
    #         banners =  IndexGoodsBanner.objects.all().order_by('index')
    #         #（4）查询活动信息 -- 注意顺序
    #         promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
    #         #（5）查询分类列表信息，注意有两种展示类型
    #           #遍历 商品分类列表取出一种类别的商品
    #         for category in categorys:
    #             image_banners = IndexCategoryGoodsBanner.objects.filter(category=category,display_type=1)
    #             category.image_banners = image_banners
    #             title_banners = IndexCategoryGoodsBanner.objects.filter(category=category,display_type=0)
    #             category.title_banners = title_banners
    #         #2.构造上下文
    #         context = {
    #             'categorys':categorys,
    #             'banners':banners,
    #             'promotion_banners':promotion_banners,
    #
    #         }
    #         #设置存储缓存数据，名字，内容，有效期
    #         cache.set('index_page_data',context,3600)
    #     #查询购物车信息 ，不能被缓存，因为经常变化
    #     cart_num = 0
    #
    #     # 如果用户登录，就获取购物车信息
    #     #1.判断用户是否登录
    #     if request.user.is_authenticated():
    #         #(1)创建redis_conn对象
    #         redis_conn = get_redis_connection('default')
    #         #（2）获取用户id
    #         user_id = request.user.id
    #         # （3）从redis中获取购物车数据，返回字典
    #         cart_dict = redis_conn.hgetall('cart_%s'%user_id)
    #         #（4）遍历 字典，取值累加
    #         for val in cart_dict.values():
    #             cart_num += int(val)
    #         # 补充购物车数据
    #     context.update(cart_num=cart_num)
    #     #3.渲染模板
    #     return render(request,'index.html',context)

       #第二遍
    def get(self,request):
        #1.查询信息
        #尝试从缓存中读取
        context = cache.get('index_page_data')
        #判断是否有缓存
        if context is None:
            print("没有缓存")
        #查询用户信息--- request.user
        #(1)查询商品类别信息
            categorys = GoodsCategory.objects.all()
            #（2）查询图片轮播信息,注意按照index排序
            banners = IndexGoodsBanner.objects.all().order_by('index')
            #（3）查询活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
            #（4）查询分类列表信息
            for category in categorys:
                image_banners = IndexCategoryGoodsBanner.objects.filter(category = category,display_type=1)
                category.image_banners = image_banners
                title_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0)
                category.title_banners = title_banners
            #2.构造上下文
            context = {
                'categorys':categorys,
                'banners':banners,
                'promotion_banners':promotion_banners,
            }
            #设置缓存
            cache.set('index_page_data',context,3600)
        #查询购物车信息，不定时更新，不能缓存
        cart_num = self.get_cart_num(request)
        #补充购物车数据
        context.update(cart_num=cart_num)
            #3.渲染模板
        return render(request,'index.html',context)
class DetailView(BaseCartView):
    """商品详情页视图"""

    def get(self, request, sku_id):
        """查询详情信息,渲染模板"""
        # 查询商品SKU信息
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 查询商品分类信息
        categorys = GoodsCategory.objects.all()

        # 从订单中获取评论信息
        sku_orders = sku.ordergoods_set.all().order_by('-create_time')[:30]
        if sku_orders:
            for sku_order in sku_orders:
                sku_order.ctime = sku_order.create_time.strftime('%Y-%m-%d %H:%M:%S')
                sku_order.username = sku_order.order.user.username
        else:
            sku_orders = []

        # 查询新品推荐信息:查询最新发布的两件商品
        new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[:2]

        # 查询其他规格商品:当前商品是500g规格的, exclude()
        other_skus = sku.goods.goodssku_set.exclude(id=sku_id)

        """
        500g规格草莓  盒装草莓 

        sku = 500g规格草莓
        sku.goods = 草莓
        sku.goods.goodssku_set() == 500g规格草莓  盒装草莓
        sku.goods.goodssku_set().exclude(id=500g规格草莓_id)
        """

        # 查询购物车信息:目前没有实现,暂时设置成0,不能被缓存
        cart_num = self.get_cart_num(request)

        # 如果是登录用户,需要查询保存在redis中的购物车数据
        if request.user.is_authenticated():

            # 创建连接到redis的对象
            redis_conn = get_redis_connection('default')

            # 调用hgetall(),查询hash对象中所有的数据,返回字典(说明,字典的key和value是字节类型(bytes))
            user_id = request.user.id
            cart_dict = redis_conn.hgetall('cart_%s' % user_id)
            # 需要先去重
            redis_conn.lrem('history_%s' % user_id, 0, sku_id)
            # 记录用户浏览信息
            redis_conn.lpush('history_%s' % user_id, sku_id)
            # 最多存储5个
            redis_conn.ltrim('history_%s' % user_id, 0, 4)

        # 构造上下文
        context = {
            'sku': sku,
            'categorys': categorys,
            'sku_orders': sku_orders,
            'new_skus': new_skus,
            'other_skus': other_skus,
            'cart_num': cart_num
        }

        # 渲染模板
        return render(request, 'detail.html', context)
    # def get(self,request):
    #     #1.尝试读取缓存数据
    #     #没有缓存数据就查询
    #     #2.从数据库查询信息
    #     #（1）查询用户--- request.user
    #     #(2)查询商品类别信息
    #     #（3）查询商品信息
    #     #（4）查询其他规格信息
    #     #（5）查询新品推荐信息
    #     #（6）查询商品评论信息
    #     #（7）查询商品详情页购物车数量
    #     #（8）记住用户浏览记录，需要是登录用户
    #     #3.构造上下文
    #         pass


class ListView(BaseCartView):
    """商品列表类视图"""
    def get(self,request,category_id,page_num):
        #1.查询多种信息
        # （1）sort用于排序，如果用户不传，就是默认的排序规则
        sort = request.GET.get('sort','default')
        #（2）检验参数，判断传入的category_id是否正确,放在try中，不正确就重定向到首页
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return redirect(reverse('goods:index'))
        #（3）查询全部商品分类
        categorys = GoodsCategory.objects.all()
        #（4）查询新品推荐信息
        new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[:2]
        #（5）查询所有的category关联的sku，并按sort进行排序--- 分三种情况排序
        if sort == 'price':
            skus = GoodsSKU.objects.filter(category=category).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(category=category).order_by('-sales')
        else:
            skus = GoodsSKU.objects.filter(category=category)
            sort = 'default'
        #（6）实现分页功能，对skus分页.每页2个GoodsSKU模型对象
        paginator = Paginator(skus,2)
        # 获取用户要看的那一页数据,先把传入的page_num转成整型,防止报错，防止try中
        page_num = int(page_num)
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            page_skus = paginator.page(1)
        #获取分页列表
        page_list = paginator.page_range
        #查询购物车数据
        cart_num = self.get_cart_num(request)
        #2.构造上下文
        context = {
            'sort':sort,
            'categorys':categorys,
            'new_skus':new_skus,
            'page_skus':page_skus,
            'page_list':page_list,
            'category':category,
            'cart_num':cart_num
        }
        # 3.渲染模板
        return render(request,'list.html',context)


