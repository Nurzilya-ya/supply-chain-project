from django.urls import path
from . import views

urlpatterns = [
    path('stocks/', views.WarehouseStockListView.as_view(), name='warehouse_stocks'),
    path('orders-to-receive/', views.OrdersToReceiveListView.as_view(), name='orders_to_receive'),
    path('orders-to-receive/<int:pk>/', views.ReceiveOrderView.as_view(), name='receive_order'),
    path('requests-to-issue/', views.RequestsToIssueListView.as_view(), name='requests_to_issue'),
    path('requests-to-issue/<int:pk>/', views.IssueRequestView.as_view(), name='issue_request'),
    path('transactions/create/', views.StockTransactionCreateView.as_view(), name='transaction_create'),
]