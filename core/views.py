from django.shortcuts import render
from warehouse.models import Material
from procurement.models import MaterialRequest, ProcurementOrder
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    total_materials = Material.objects.filter(is_active=True).count()
    active_requests = MaterialRequest.objects.exclude(status__in=['fulfilled', 'rejected']).count()
    total_orders = ProcurementOrder.objects.count()
    context = {
        'total_materials': total_materials,
        'active_requests': active_requests,
        'total_orders': total_orders,
    }

    return render(request, 'core/home.html', context)