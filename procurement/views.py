from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import MaterialRequest


class MyRequestsListView(LoginRequiredMixin, ListView):
    model = MaterialRequest
    template_name = 'procurement/my_requests.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return MaterialRequest.objects.filter(created_by=self.request.user).order_by('-created_at')


class SupplyRequestsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = MaterialRequest
    template_name = 'procurement/supply_requests.html'
    context_object_name = 'requests'

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def get_queryset(self):
        return MaterialRequest.objects.filter(status__in=['submitted', 'need_clarification']).order_by('required_date')