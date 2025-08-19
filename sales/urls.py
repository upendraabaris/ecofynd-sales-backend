from django.urls import path
from . import views
from .views import TopProfitableProductsAPIView
from .views import TopLossProductsAPIView
from .views import TopSellingByUnitsAPIView
from .views import SalesSummaryAPIView

urlpatterns = [
    path('top-profit/', views.top_profit_products),
    path('top-loss/', views.top_loss_products),
    path('sku-profit/', TopProfitableProductsAPIView.as_view(), name='sku-profit-api'),
    path('sku-loss/', TopLossProductsAPIView.as_view(), name='sku-loss-api'),
    path('top-units/', TopSellingByUnitsAPIView.as_view(), name='sku-top-units-api'),
    path('sales-summary/', SalesSummaryAPIView.as_view(), name='sales-summary')
]
