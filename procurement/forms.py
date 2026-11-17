from django import forms
from django.forms import inlineformset_factory
from .models import MaterialRequest, RequestItem
from .models import ProcurementOrder, ProcurementOrderItem

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
ProcurementOrderItemFormSet = inlineformset_factory(
    ProcurementOrder,
    ProcurementOrderItem,
    fields=('material', 'quantity', 'unit_price', 'request_item'),
    extra=5,
    widgets={
        'material': forms.Select(attrs={'class': 'form-select'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
        'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        'request_item': forms.Select(attrs={'class': 'form-select'}),
    }
)