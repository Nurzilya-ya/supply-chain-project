from django.contrib import admin
from .models import (
    Supplier,
    MaterialRequest,
    RequestItem,
    ProcurementOrder,
    ProcurementOrderItem,
)


admin.site.register(Supplier)


class RequestItemInline(admin.TabularInline):
    model = RequestItem
    extra = 1


@admin.register(MaterialRequest)
class MaterialRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by', 'production_site', 'status', 'required_date', 'created_at')
    list_filter = ('status', 'production_site')
    search_fields = ('created_by__username', 'purpose')
    inlines = [RequestItemInline]


class ProcurementOrderItemInline(admin.TabularInline):
    model = ProcurementOrderItem
    extra = 1


@admin.register(ProcurementOrder)
class ProcurementOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'warehouse', 'status', 'order_date', 'expected_delivery_date')
    list_filter = ('status', 'supplier', 'warehouse')
    search_fields = ('order_number', 'supplier__name')
    inlines = [ProcurementOrderItemInline]
