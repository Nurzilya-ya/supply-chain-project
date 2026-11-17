from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal
from procurement.models import ProcurementOrder, ProcurementOrderItem
from .models import Stock, StockTransaction


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

class OrdersToReceiveListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ProcurementOrder
    template_name = 'warehouse/orders_to_receive.html'
    context_object_name = 'orders'

    def test_func(self):
        # Доступ только для Кладовщиков и Админов
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Warehouse Staff').exists()

    def get_queryset(self):
        # Показываем только те заказы, которые ждем (Заказано или Частично поставлено)
        return ProcurementOrder.objects.filter(
            status__in=['ordered', 'partially_delivered']
        ).order_by('expected_delivery_date')


class ReceiveOrderView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Warehouse Staff').exists()

    def get(self, request, pk):
        # Показываем страницу приемки
        order = get_object_or_404(ProcurementOrder, pk=pk)
        return render(request, 'warehouse/receive_order.html', {'order': order})

    def post(self, request, pk):
        # Обрабатываем введенные данные
        order = get_object_or_404(ProcurementOrder, pk=pk)

        for item in order.items.all():
            # Получаем количество, которое кладовщик ввел для этого материала
            received_str = request.POST.get(f'item_{item.pk}')

            if received_str:
                received_now = Decimal(received_str)

                # Проверяем, что ввели положительное число и не больше, чем осталось принять
                if received_now > 0 and (item.received_quantity + received_now) <= item.quantity:
                    # 1. Обновляем строку заказа (сколько уже принято)
                    item.received_quantity += received_now
                    item.save()

                    # 2. Обновляем физический остаток на складе
                    stock, created = Stock.objects.get_or_create(
                        warehouse=order.warehouse,
                        material=item.material,
                        defaults={'quantity': 0, 'reserved_quantity': 0}
                    )
                    stock.quantity += received_now
                    stock.save()

                    # 3. Создаем запись в журнале складских операций
                    StockTransaction.objects.create(
                        transaction_type='receipt',
                        warehouse=order.warehouse,
                        material=item.material,
                        quantity=received_now,
                        created_by=request.user,
                        procurement_order_item=item,
                        comment=f"Приемка по заказу {order.order_number}"
                    )

        # 4. Обновляем статус самого заказа
        # Перечитываем заказ, чтобы взять свежие данные по received_quantity
        all_received = True
        any_received = False

        for item in order.items.all():
            if item.received_quantity > 0:
                any_received = True
            if item.received_quantity < item.quantity:
                all_received = False

        if all_received:
            order.status = 'delivered'
        elif any_received:
            order.status = 'partially_delivered'
        order.save()

        messages.success(request, f'Приемка по заказу {order.order_number} успешно зарегистрирована.')
        return redirect('orders_to_receive')