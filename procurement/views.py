from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib import messages
from .forms import MaterialRequestForm, RequestItemFormSet
from .forms import ProcurementOrderForm, ProcurementOrderItemFormSet
from .models import MaterialRequest
from django.shortcuts import redirect
from django.views import View
from warehouse.models import Warehouse
from django.shortcuts import get_object_or_404
from .models import ProcurementOrder


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


class MaterialRequestCreateView(LoginRequiredMixin, CreateView):
    model = MaterialRequest
    form_class = MaterialRequestForm
    template_name = 'procurement/request_form.html'
    success_url = reverse_lazy('my_requests')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = RequestItemFormSet()
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = RequestItemFormSet(self.request.POST)

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        # Заполняем скрытые поля заявки
        form.instance.created_by = self.request.user
        if self.request.user.production_site:
            form.instance.production_site = self.request.user.production_site
        else:
            form.add_error(None, "У вашего профиля не указан производственный объект.")
            return self.form_invalid(form, formset)

        # Статус при создании — Черновик!
        form.instance.status = 'draft'

        # Сохраняем саму заявку
        self.object = form.save()

        # Привязываем материалы к сохраненной заявке и сохраняем их
        formset.instance = self.object
        formset.save()

        messages.success(self.request, 'Заявка сохранена как черновик. Не забудьте отправить её в снабжение!')
        return super().form_valid(form)

    def form_invalid(self, form, formset):
        # Если есть ошибки (например, не выбрана дата или материал), возвращаем форму с ошибками
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )


class MaterialRequestDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = MaterialRequest
    template_name = 'procurement/request_detail.html'
    context_object_name = 'request_obj'

    def test_func(self):
        # Смотреть заявку может автор, снабженец или админ
        req = self.get_object()
        user = self.request.user
        if user.is_superuser or req.created_by == user:
            return True
        return user.groups.filter(name='Supply Specialists').exists()

# 2. Отправка заявки в снабжение (смена статуса)
class SubmitRequestView(LoginRequiredMixin, View):
    def post(self, request, pk):
        # Берем заявку из базы
        req = MaterialRequest.objects.get(pk=pk, created_by=request.user)
        # Меняем статус, если это черновик
        if req.status == 'draft':
            req.status = 'submitted'
            req.save()
            messages.success(request, f'Заявка №{req.id} успешно отправлена в снабжение!')

        return redirect('request_detail', pk=req.pk)

#Supplier
# 1. Просмотр заявки снабженцем (с выбором склада)
class SupplyRequestDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = MaterialRequest
    template_name = 'procurement/supply_request_detail.html'
    context_object_name = 'request_obj'

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаем список всех складов для выпадающего списка
        context['warehouses'] = Warehouse.objects.filter(is_active=True)
        return context


# 2. Согласование заявки
class ApproveRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def post(self, request, pk):
        req = get_object_or_404(MaterialRequest, pk=pk)

        if req.status not in ['submitted', 'need_clarification']:
            messages.error(request, 'Эту заявку нельзя согласовать в текущем статусе.')
            return redirect('supply_requests')

        warehouse_id = request.POST.get('warehouse')
        if not warehouse_id:
            messages.error(request, 'Пожалуйста, выберите склад для обеспечения заявки.')
            return redirect('supply_request_detail', pk=req.pk)

        req.warehouse = get_object_or_404(Warehouse, pk=warehouse_id)
        req.status = 'approved'
        req.save()

        # ВЫЗЫВАЕМ НАШУ БИЗНЕС-ЛОГИКУ РЕЗЕРВИРОВАНИЯ!
        deficits = req.reserve_stock()

        if deficits:
            msg = 'Заявка согласована, но обнаружился дефицит: '
            for item, shortage in deficits:
                msg += f'{item.material.name} (не хватает {shortage}), '
            messages.warning(request, msg)
        else:
            messages.success(request, 'Заявка успешно согласована и полностью зарезервирована!')

        return redirect('supply_requests')

class ApprovedRequestsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = MaterialRequest
    template_name = 'procurement/approved_requests.html'
    context_object_name = 'requests'

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def get_queryset(self):
        # Показываем только согласованные заявки
        return MaterialRequest.objects.filter(status='approved').order_by('-updated_at')

# 3. Отклонение заявки
class RejectRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def post(self, request, pk):
        req = get_object_or_404(MaterialRequest, pk=pk)
        if req.status in ['submitted', 'need_clarification']:
            req.status = 'rejected'
            req.save()
            messages.info(request, f'Заявка №{req.pk} отклонена.')
        return redirect('supply_requests')

class ProcurementOrderListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ProcurementOrder
    template_name = 'procurement/procurement_orders.html'
    context_object_name = 'orders'

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def get_queryset(self):
        return ProcurementOrder.objects.all().select_related('supplier', 'warehouse').order_by('-created_at')


class ProcurementOrderCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ProcurementOrder
    form_class = ProcurementOrderForm
    template_name = 'procurement/procurement_order_form.html'
    success_url = reverse_lazy('procurement_orders')

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def get_initial(self):
        initial = super().get_initial()
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            initial['warehouse'] = warehouse_id
        return initial

    # ПЕРЕДАЧА НАЧАЛЬНЫХ ДАННЫХ ДЛЯ ТАБЛИЦЫ (ФОРМСЕТА)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.method == 'GET':
            material_id = self.request.GET.get('material')
            qty = self.request.GET.get('quantity')

            formset_initial = [{}]
            if material_id:
                formset_initial = [{'material': material_id, 'quantity': qty}]

            context['formset'] = ProcurementOrderItemFormSet(initial=formset_initial)
        else:
            context['formset'] = ProcurementOrderItemFormSet()

        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = ProcurementOrderItemFormSet(self.request.POST)

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        form.instance.created_by = self.request.user
        form.instance.status = 'draft'

        self.object = form.save()

        formset.instance = self.object
        formset.save()

        messages.success(self.request, f'Заказ {self.object.order_number} сохранен как черновик.')
        return super().form_valid(form)

    def form_invalid(self, form, formset):
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )

class ConfirmProcurementOrderView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def post(self, request, pk):
        order = get_object_or_404(ProcurementOrder, pk=pk)
        if order.status == 'draft':
            # ПРОВЕРКА 1: Заполнены ли поставщик и склад?
            if not order.supplier or not order.warehouse:
                messages.error(request,
                               f'Нельзя отправить заказ {order.order_number}. Выберите поставщика и склад назначения (нажмите "Редактировать").')
                return redirect('procurement_orders')

            # ПРОВЕРКА 2: Есть ли в заказе материалы?
            if order.items.count() == 0:
                messages.error(request,
                               f'Нельзя отправить пустой заказ {order.order_number}. Добавьте хотя бы один материал.')
                return redirect('procurement_orders')

            # Если проверки пройдены — отправляем
            order.status = 'ordered'
            order.save()
            messages.success(request, f'Заказ {order.order_number} отправлен поставщику!')

        return redirect('procurement_orders')

class ProcurementOrderUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ProcurementOrder
    form_class = ProcurementOrderForm
    template_name = 'procurement/procurement_order_form.html' # Используем тот же шаблон!
    success_url = reverse_lazy('procurement_orders')

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаем формсет, привязанный к текущему заказу
        if self.request.POST:
            context['formset'] = ProcurementOrderItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = ProcurementOrderItemFormSet(instance=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = ProcurementOrderItemFormSet(self.request.POST, instance=self.object)

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        self.object = form.save()
        formset.instance = self.object
        formset.save()
        messages.success(self.request, f'Заказ {self.object.order_number} обновлен.')
        return super().form_valid(form)

    def form_invalid(self, form, formset):
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )


class ReReserveRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Supply Specialists').exists()

    def post(self, request, pk):
        req = get_object_or_404(MaterialRequest, pk=pk)

        if req.status != 'approved':
            messages.error(request, 'Эта заявка не находится в статусе согласования.')
            return redirect('approved_requests')

        if not req.warehouse:
            messages.error(request, 'У заявки не выбран склад обеспечения.')
            return redirect('approved_requests')

        # Вызываем нашу бизнес-логику довыделения!
        deficits = req.reserve_stock()

        if deficits:
            msg = 'Удалось довыделить материалы, но остался дефицит: '
            for item, shortage in deficits:
                msg += f'{item.material.name} (не хватает {shortage}), '
            messages.warning(request, msg)
        else:
            messages.success(request, 'Все материалы по заявке полностью зарезервированы!')

        return redirect('approved_requests')