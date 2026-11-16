from django.urls import path
from . import views

urlpatterns = [
    path('my-requests/', views.MyRequestsListView.as_view(), name='my_requests'),
    path('supply-requests/', views.SupplyRequestsListView.as_view(), name='supply_requests'),
]