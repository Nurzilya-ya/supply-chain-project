from django.contrib import admin
from .models import Warehouse, Material, Stock


admin.site.register(Warehouse)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'unit', 'is_active')
    list_filter = ('category', 'unit', 'is_active')
    search_fields = ('name', 'code')

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('material', 'warehouse', 'quantity', 'reserved_quantity', 'available_quantity')
    list_filter = ('warehouse', 'material__category')
    search_fields = ('material__name', 'material__code')

    def available_quantity(self, obj):
        return obj.available_quantity
    available_quantity.short_description = 'Доступно'