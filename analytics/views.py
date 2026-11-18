import json
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Sum, F
from procurement.models import MaterialRequest, ProcurementOrderItem
from warehouse.models import Stock


class AnalyticsDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'analytics/dashboard.html'

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Managers').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Данные для круговой диаграммы "Заявки по статусам"
        status_counts = MaterialRequest.objects.values('status').annotate(count=Count('id'))
        status_names = {
            'draft': 'Черновик',
            'submitted': 'На рассмотрении',
            'approved': 'Согласована',
            'fulfilled': 'Выполнена',
            'rejected': 'Отклонена'
        }
        labels = []
        data = []
        for item in status_counts:
            labels.append(status_names.get(item['status'], item['status']))
            data.append(item['count'])

        context['requests_labels'] = json.dumps(labels)
        context['requests_data'] = json.dumps(data)

        # 2. Общая сумма закупок (считаем количество * цену по всем заказам)
        total_procurement = ProcurementOrderItem.objects.aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total'] or 0
        context['total_procurement'] = total_procurement

        # 3. Количество позиций с дефицитом (где резерв занимает почти весь остаток)
        # Условно: если доступно меньше 5 штук, считаем это критическим остатком
        low_stock_count = Stock.objects.filter(quantity__lte=F('reserved_quantity') + 5).count()
        context['low_stock_count'] = low_stock_count

        # 4. Общее количество заявок
        context['total_requests'] = MaterialRequest.objects.count()

        return context