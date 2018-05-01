from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.http import JsonResponse
from django.db import transaction
# Create your views here.
class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return login_required(view)

# def login_required_json(view_func):
#     @wraps(view_func)#恢复和文档相同的函数名
#     def wrapper(request,*args,**kwargs):
#         #如果用户未登录，返回json数据
#         if not request.user.is_authenticated():
#             return JsonResponse({'code':1,'message':'用户未登录'})
#         else:#若用户登录，进入到view_func中
#             return view_func()
#     return wrapper
#
# class LoginRequiredJsonMixin(object):
#     @classmethod
#     def as_view(cls,**initkwargs):
#         view = super().as_view(**initkwargs)
#         return login_required_json(view)


# def login_required_json(view_func):
#     @wraps(view_func)
#     def wrapper(request,*args,**kwargs):
#        #如果用户未登录，返回json数据
#         if not request.user.is_authenticated():
#            return JsonResponse({'code':1,'message':'用户未登录'})
#         else:
#             return view_func(request,*args,**kwargs)
#     return wrapper
#
# class LoginRequiredJsonMixin(object):
#     @classmethod
#     def as_view(cls,**initkwargs):
#         view = super().as_view()
#         return login_required_json(view)

def login_required_json(view_func):
    @wraps(view_func)
    def wrapper(request,*args,**kwargs):
        #如果用户未登录就返回json提示
        if not request.user.is_authenticated():
           return JsonResponse({'code':1,'message':'用户未登录'})
        #已登录就进入到view_func中
        else:
            return view_func(request,*args,**kwargs)
    return wrapper

class LoginRequiredJsonMixin(object):
    @classmethod
    def as_view(cls,**initkwargs):
        view = super().as_view()
        return login_required_json(view)



class TransactionAtomicMixin(object):
    @classmethod
    def as_view(cls,**initkwargs):
        view = super(TransactionAtomicMixin,cls).as_view(**initkwargs)
        return transaction.atomic()















#
# class TransactionAtomicMixin(object):
#     @classmethod
#     def as_view(cls,**initkwargs):
#         view = super(TransactionAtomicMixin,cls).as_view(**initkwargs)
#         return transaction.atomic(view)










