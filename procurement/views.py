from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages
from .forms import MaterialRequestForm, RequestItemFormSet
from .models import MaterialRequest
from django.shortcuts import redirect
from django.views import View

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