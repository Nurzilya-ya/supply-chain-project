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
        low_stock_items = Stock.objects.filter(quantity__lte=10).select_related('material', 'warehouse')

    context = {
        'total_materials': total_materials,
        'active_requests': active_requests,
        'total_orders': total_orders,
        'low_stock_items': low_stock_items,
    }

    return render(request, 'core/home.html', context)