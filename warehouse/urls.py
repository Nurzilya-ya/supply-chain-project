from django.urls import path
from . import views

urlpatterns = [
    path('stocks/', views.WarehouseStockListView.as_view(), name='warehouse_stocks'),
]