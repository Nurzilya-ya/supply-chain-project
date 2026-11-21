from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal
from procurement.models import ProcurementOrder, MaterialRequest, ProcurementOrderItem
from .models import Stock, StockTransaction, Material
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import StockTransactionForm, MaterialForm


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
        user = self.request.user
        queryset = Stock.objects.filter(quantity__gt=0)
        # Если это кладовщик и у него указан склад, показываем только его
        if user.groups.filter(name='Warehouse Staff').exists() and user.warehouse:
            queryset = queryset.filter(warehouse=user.warehouse)

        return queryset.select_related('warehouse', 'material')

class OrdersToReceiveListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ProcurementOrder
    template_name = 'warehouse/orders_to_receive.html'
    context_object_name = 'orders'

    def test_func(self):
        # Доступ только для Кладовщиков и Админов
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Warehouse Staff').exists()

    def get_queryset(self):
        user = self.request.user
        queryset = ProcurementOrder.objects.filter(status__in=['ordered', 'partially_delivered'])

        if user.groups.filter(name='Warehouse Staff').exists() and user.warehouse:
            queryset = queryset.filter(warehouse=user.warehouse)

        return queryset.order_by('expected_delivery_date')


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
        if request.user.groups.filter(name='Warehouse Staff').exists() and request.user.warehouse:
            if order.warehouse != request.user.warehouse:
                messages.error(request, 'У вас нет прав на операции с этим складом.')
                return redirect('orders_to_receive')
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


# 1. Список согласованных заявок для выдачи
class RequestsToIssueListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = MaterialRequest
    template_name = 'warehouse/requests_to_issue.html'
    context_object_name = 'requests'

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Warehouse Staff').exists()

    def get_queryset(self):
        user = self.request.user
        # Берем только согласованные заявки
        queryset = MaterialRequest.objects.filter(status='approved')

        # Если это кладовщик с назначенным складом - фильтруем
        if user.groups.filter(name='Warehouse Staff').exists() and user.warehouse:
            queryset = queryset.filter(warehouse=user.warehouse)

        return queryset.order_by('required_date')


# 2. Обработка выдачи
class IssueRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Warehouse Staff').exists()

    def post(self, request, pk):
        req = get_object_or_404(MaterialRequest, pk=pk)
        if request.user.groups.filter(name='Warehouse Staff').exists() and request.user.warehouse:
            if req.warehouse != request.user.warehouse:
                messages.error(request, 'У вас нет прав на выдачу с этого склада.')
                return redirect('requests_to_issue')
        if req.status != 'approved':
            messages.error(request, 'Эту заявку нельзя выдать (она не согласована).')
            return redirect('requests_to_issue')

        if req.has_deficit:
            messages.error(request,
                           'ОШИБКА: В заявке есть дефицит материалов. Дождитесь, пока снабженец закупит и довыделит их.')
            return redirect('requests_to_issue')

        if not req.warehouse:
            messages.error(request, 'У заявки не выбран склад обеспечения.')
            return redirect('requests_to_issue')

        # Проходим по всем строкам заявки
        for item in req.items.all():
            if item.reserved_quantity > 0:
                # 1. Находим остаток на складе
                stock = Stock.objects.filter(warehouse=req.warehouse, material=item.material).first()

                if stock:
                    # 2. Уменьшаем физический остаток и резерв
                    stock.quantity -= item.reserved_quantity
                    stock.reserved_quantity -= item.reserved_quantity
                    stock.save()

                    # 3. Создаем запись в журнале операций
                    StockTransaction.objects.create(
                        transaction_type='issue',
                        warehouse=req.warehouse,
                        material=item.material,
                        quantity=item.reserved_quantity,
                        created_by=request.user,
                        request_item=item,
                        comment=f"Выдача по заявке №{req.pk}"
                    )

                    # 4. Обнуляем резерв в строке заявки (товар ушел)
                    item.reserved_quantity = 0
                    item.save()

        # 5. Закрываем заявку
        req.status = 'fulfilled'
        req.save()

        messages.success(request, f'Материалы по заявке №{req.pk} успешно выданы со склада!')
        return redirect('requests_to_issue')

class StockTransactionCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'warehouse/transaction_form.html'
    form_class = StockTransactionForm
    success_url = reverse_lazy('warehouse_stocks') # После сохранения кидаем на страницу остатков

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Warehouse Staff').exists()

    def form_valid(self, form):
        # Получаем данные из формы, но пока не сохраняем в базу
        transaction = form.save(commit=False)
        transaction.created_by = self.request.user

        source_stock = Stock.objects.filter(
            warehouse=transaction.warehouse,
            material=transaction.material
        ).first()

        # Проверка: есть ли вообще такой материал на этом складе и хватает ли его (с учетом резерва)
        if not source_stock or source_stock.available_quantity < transaction.quantity:
            form.add_error('quantity', 'На выбранном складе недостаточно доступного материала для этой операции.')
            return self.form_invalid(form)

        # --- ЛОГИКА СПИСАНИЯ ---
        if transaction.transaction_type == 'write_off':
            source_stock.quantity -= transaction.quantity
            source_stock.save()
            transaction.save() # Сохраняем запись в журнале
            messages.success(self.request, f'Материал "{transaction.material.name}" списан в количестве {transaction.quantity}.')

        # --- ЛОГИКА ПЕРЕМЕЩЕНИЯ ---
        elif transaction.transaction_type == 'transfer':
            if not transaction.destination_warehouse:
                form.add_error('destination_warehouse', 'Для перемещения нужно выбрать склад-получатель.')
                return self.form_invalid(form)
            if transaction.warehouse == transaction.destination_warehouse:
                form.add_error('destination_warehouse', 'Склады отправки и получения должны различаться.')
                return self.form_invalid(form)

            # 1. Списываем с исходного склада
            source_stock.quantity -= transaction.quantity
            source_stock.save()

            # 2. Добавляем на склад-получатель (если там еще нет этого материала, создаем запись)
            dest_stock, created = Stock.objects.get_or_create(
                warehouse=transaction.destination_warehouse,
                material=transaction.material,
                defaults={'quantity': 0, 'reserved_quantity': 0}
            )
            dest_stock.quantity += transaction.quantity
            dest_stock.save()

            transaction.save() # Сохраняем запись в журнале
            messages.success(self.request, f'Материал "{transaction.material.name}" перемещен.')

        return super().form_valid(form)

# Справочник материалов
class MaterialListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Material
    template_name = 'warehouse/material_list.html'
    context_object_name = 'materials'
    paginate_by = 20

    def test_func(self):
        user = self.request.user
        # ТОЛЬКО снабженцы и админ
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def get_queryset(self):
        return Material.objects.all().order_by('category', 'name')

# Создание материала
class MaterialCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Material
    form_class = MaterialForm
    template_name = 'warehouse/material_form.html'
    success_url = reverse_lazy('material_list')

    def test_func(self):
        user = self.request.user
        # ТОЛЬКО снабженцы и админ
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def form_valid(self, form):
        messages.success(self.request, f'Материал "{form.instance.name}" успешно добавлен в справочник.')
        return super().form_valid(form)