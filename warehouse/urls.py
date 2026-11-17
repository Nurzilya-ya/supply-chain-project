from django.urls import path
from . import views

urlpatterns = [
    path('stocks/', views.WarehouseStockListView.as_view(), name='warehouse_stocks'),
    path('orders-to-receive/', views.OrdersToReceiveListView.as_view(), name='orders_to_receive'),
    path('orders-to-receive/<int:pk>/', views.ReceiveOrderView.as_view(), name='receive_order'),
]