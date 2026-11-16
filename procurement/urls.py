from django.urls import path
from . import views

urlpatterns = [
    path('my-requests/', views.MyRequestsListView.as_view(), name='my_requests'),
    path('my-requests/create/', views.MaterialRequestCreateView.as_view(), name='request_create'),
    path('my-requests/<int:pk>/', views.MaterialRequestDetailView.as_view(), name='request_detail'),
    path('my-requests/<int:pk>/submit/', views.SubmitRequestView.as_view(), name='request_submit'),

    path('supply-requests/', views.SupplyRequestsListView.as_view(), name='supply_requests'),
]