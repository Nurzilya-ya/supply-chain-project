from django.shortcuts import render
from procurement.models import MaterialRequest, ProcurementOrder
from django.contrib.auth.decorators import login_required
from warehouse.models import Material, Stock

@login_required
def home(request):
    total_materials = Material.objects.filter(is_active=True).count()
    active_requests = MaterialRequest.objects.exclude(status__in=['fulfilled', 'rejected']).count()
    total_orders = ProcurementOrder.objects.count()

    # По умолчанию список предупреждений пустой
    low_stock_items = None

    # Проверяем: если это Снабженец или Админ — показываем им предупреждения
    is_supply = request.user.is_superuser or request.user.groups.filter(name='Supply Specialists').exists()

    if is_supply:
        # Берем позиции, где остаток меньше 10
        low_stock_items = list(Stock.objects.filter(quantity__lt=10).select_related('material', 'warehouse'))
        # Для каждой позиции считаем, сколько не хватает до 10 (условный минимум)
        for item in low_stock_items:
            item.recommended_qty = 10 - item.quantity
    context = {
        'total_materials': total_materials,
        'active_requests': active_requests,
        'total_orders': total_orders,
        'low_stock_items': low_stock_items,
    }

    return render(request, 'core/home.html', context)