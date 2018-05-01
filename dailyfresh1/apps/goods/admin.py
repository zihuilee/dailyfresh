# from django.contrib import admin
# from goods.models import GoodsSKU,GoodsCategory,Goods,IndexPromotionBanner,IndexCategoryGoodsBanner
# from celery_tasks.tasks import generate_static_index_html
# from django.core.cache import cache
# # Register your models here.
# # 缓存需要设置有效期，不然数据永远无法得到更新，具体的有效期时间根据公司需求而定
# # 缓存需要在修改内容时删除，不然内容修改了，但还是缓存的旧数据
# class BaseAdmin(admin.ModelAdmin):
#     """商品信息的管理类，运营人员在后台发布内容时，异步生成静态页面"""
#     #1.重写save_model方法
#     def save_model(self, request, obj, form, change):
#         #obj表示要保存的对象，调用save（），将对象保存到数据库中
#         obj.save()
#         #调用celery触发异步生成静态文件方法
#         generate_static_index_html.delay()
#         cache.delete('index_page_data')
#
#     #2.重写 delete_model方法
#     def delete_model(self, request, obj):
#         obj.delete()
#         generate_static_index_html.delay()
#         cache.delete('index_page_data')
# class IndexPromotionBannerAdmin(BaseAdmin):
#     """商品活动站点管理，如果有自己的新的逻辑也是写在这里"""
#     # list_display = []
#     pass
#
# class GoodsCategoryAdmin(BaseAdmin):
#     pass
#
# class GoodsAdmin(BaseAdmin):
#     pass
#
# class GoodsSKUAdmin(BaseAdmin):
#     pass
#
# class IndexCategoryGoodsBannerAdmin(BaseAdmin):
#     pass
#
# # Register your models here.
# admin.site.register(GoodsCategory,GoodsCategoryAdmin)
# admin.site.register(Goods,GoodsAdmin)
# admin.site.register(GoodsSKU,GoodsSKUAdmin)
# admin.site.register(IndexPromotionBanner,IndexPromotionBannerAdmin)
# admin.site.register(IndexCategoryGoodsBanner,IndexCategoryGoodsBannerAdmin)

from django.contrib import admin
from goods.models import GoodsSKU,Goods,GoodsCategory,IndexPromotionBanner,IndexCategoryGoodsBanner
from celery_tasks.tasks import generate_static_index_html
from django.core.cache import cache
class BaseAdmin(admin.ModelAdmin):
    """商品活动信息的管理类，"""
    def save_model(self, request, obj, form, change):
        obj.save()
        generate_static_index_html.delay()
        # 修改了数据库数据就需要删除缓存
        cache.delete('index_page_data')
    def delete_model(self, request, obj):
        obj.delete()
        generate_static_index_html.delay()
        cache.delete('index_page_data')


class IndexPromotionBannerAdmin(BaseAdmin):
    """商品活动站点管理，如果有自己的新的逻辑也是写在这里"""
    # list_display = []
    pass

class GoodsCategoryAdmin(BaseAdmin):
    pass

class GoodsAdmin(BaseAdmin):
    pass

class GoodsSKUAdmin(BaseAdmin):
    pass

class IndexCategoryGoodsBannerAdmin(BaseAdmin):
    pass

# Register your models here.
admin.site.register(GoodsCategory,GoodsCategoryAdmin)
admin.site.register(Goods,GoodsAdmin)
admin.site.register(GoodsSKU,GoodsSKUAdmin)
admin.site.register(IndexPromotionBanner,IndexPromotionBannerAdmin)
admin.site.register(IndexCategoryGoodsBanner,IndexCategoryGoodsBannerAdmin)




















