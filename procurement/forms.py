from django import forms
from django.forms import inlineformset_factory
from .models import MaterialRequest, RequestItem
from .models import ProcurementOrder, ProcurementOrderItem
from django.db.models import F

# 1. Форма для самой заявки (шапка)
class MaterialRequestForm(forms.ModelForm):
    class Meta:
        model = MaterialRequest
        fields = ['purpose', 'required_date']
        widgets = {
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Например: плановый ремонт насосной станции'}),
            'required_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

# 2. Форма для строк заявки (материалы)
# inlineformset_factory создает набор форм, привязанных к главной модели
RequestItemFormSet = inlineformset_factory(
    MaterialRequest,
    RequestItem,
    fields=('material', 'quantity'),
    extra=3,
    widgets={
        'material': forms.Select(attrs={'class': 'form-select'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
    }
)

# 1. Форма для шапки заказа
class ProcurementOrderForm(forms.ModelForm):
    class Meta:
        model = ProcurementOrder
        fields = ['supplier', 'warehouse', 'expected_delivery_date', 'comment']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

# 2. Форма для строк заказа (материалы)
class ProcurementOrderItemForm(forms.ModelForm):
    class Meta:
        model = ProcurementOrderItem
        fields = ('material', 'quantity', 'unit_price', 'request_item')
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'request_item': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ФИЛЬТРАЦИЯ: показываем только те строки заявок, где есть дефицит!
        if 'request_item' in self.fields:
            self.fields['request_item'].queryset = RequestItem.objects.filter(
                request__status='approved', # Заявка согласована
                reserved_quantity__lt=F('quantity') # Резерв меньше, чем просят
            )

    # ПРОВЕРКА КОЛИЧЕСТВА
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        # Если поле пустое (например, пустая строка в формсете), просто пропускаем
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError("Количество должно быть строго больше нуля.")
        return quantity

    # ПРОВЕРКА ЦЕНЫ
    def clean_unit_price(self):
        unit_price = self.cleaned_data.get('unit_price')
        # Цена может быть 0 (например, если поставка бесплатная/гарантийная),
        # но не может быть отрицательной
        if unit_price is not None and unit_price <= 0:
            raise forms.ValidationError("Цена не может быть отрицательной.")
        return unit_price

ProcurementOrderItemFormSet = inlineformset_factory(
    ProcurementOrder,
    ProcurementOrderItem,
    form=ProcurementOrderItemForm, # Используем нашу кастомную форму
    extra=5,
)
