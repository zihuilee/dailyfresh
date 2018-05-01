from django.conf.urls import url
from orders import views

urlpatterns = [
    url(r'^place$',views.PlaceOrderView.as_view(),name='place'),
    url(r'^commit$',views.CommitOrderView.as_view(),name='commit'),
    url(r'^(?P<page>\d+)$',views.UserOrdersView.as_view(),name='info')
]