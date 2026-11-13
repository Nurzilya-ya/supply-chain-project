from django.contrib import admin
from .models import Warehouse, Material


admin.site.register(Warehouse)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'unit', 'is_active')
    list_filter = ('category', 'unit', 'is_active')
    search_fields = ('name', 'code')
