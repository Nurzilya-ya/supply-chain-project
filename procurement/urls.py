from django.urls import path
from . import views

urlpatterns = [
    path('my-requests/', views.MyRequestsListView.as_view(), name='my_requests'),
    path('my-requests/create/', views.MaterialRequestCreateView.as_view(), name='request_create'),
    path('my-requests/<int:pk>/', views.MaterialRequestDetailView.as_view(), name='request_detail'),
    path('my-requests/<int:pk>/submit/', views.SubmitRequestView.as_view(), name='request_submit'),

    path('supply-requests/', views.SupplyRequestsListView.as_view(), name='supply_requests'),
    path('supply-requests/<int:pk>/', views.SupplyRequestDetailView.as_view(), name='supply_request_detail'),
    path('supply-requests/<int:pk>/approve/', views.ApproveRequestView.as_view(), name='request_approve'),
    path('supply-requests/approved/', views.ApprovedRequestsListView.as_view(), name='approved_requests'),
    path('supply-requests/<int:pk>/reject/', views.RejectRequestView.as_view(), name='request_reject'),
    path('procurement-orders/', views.ProcurementOrderListView.as_view(), name='procurement_orders'),
    path('procurement-orders/create/', views.ProcurementOrderCreateView.as_view(), name='procurement_order_create'),
    path('procurement-orders/<int:pk>/edit/', views.ProcurementOrderUpdateView.as_view(), name='procurement_order_edit'),
    path('procurement-orders/<int:pk>/confirm/', views.ConfirmProcurementOrderView.as_view(), name='procurement_order_confirm'),
]