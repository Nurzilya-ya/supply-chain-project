from django.contrib import admin
from .models import Warehouse, Material, Stock, StockTransaction


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

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'transaction_type', 'material', 'quantity', 'warehouse', 'created_by')
    list_filter = ('transaction_type', 'warehouse', 'created_at')
    search_fields = ('material__name', 'material__code', 'comment')
    readonly_fields = ('created_at',)