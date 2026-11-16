from django import forms
from django.forms import inlineformset_factory
from .models import MaterialRequest, RequestItem

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