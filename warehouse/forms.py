from django import forms
from .models import StockTransaction


class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        # Пользователь сам выбирает тип операции: перемещение или списание
        fields = ['transaction_type', 'warehouse', 'destination_warehouse', 'material', 'quantity', 'comment']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'destination_warehouse': forms.Select(attrs={'class': 'form-select'}),
            'material': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0.001'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                             'placeholder': 'Причина списания или комментарий к перемещению'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор типов только перемещением и списанием
        # (Приход и выдачу мы делаем через другие формы)
        self.fields['transaction_type'].choices = [
            ('transfer', 'Перемещение между складами'),
            ('write_off', 'Списание (порча, утиль)')
        ]
        self.fields['destination_warehouse'].required = False