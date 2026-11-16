from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Stock


class WarehouseStockListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Stock
    template_name = 'warehouse/stock_list.html'
    context_object_name = 'stocks'

    def test_func(self):
        user = self.request.user
        # Пускаем и кладовщиков, и снабженцев!
        if user.is_superuser:
            return True
        return user.groups.filter(name__in=['Warehouse Staff', 'Supply Specialists']).exists()

    def get_queryset(self):
        return Stock.objects.filter(quantity__gt=0).select_related('warehouse', 'material')