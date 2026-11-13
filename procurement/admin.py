from django.contrib import admin
from .models import Supplier, MaterialRequest, RequestItem


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
