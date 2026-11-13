from django.db import models


class Warehouse(models.Model):

    WAREHOUSE_TYPES = [
        ('central', 'Центральный склад'),
        ('local', 'Локальный склад'),
    ]

    name = models.CharField(
        max_length=150,
        verbose_name='Название склада'
    )

    warehouse_type = models.CharField(
        max_length=20,
        choices=WAREHOUSE_TYPES,
        verbose_name='Тип склада'
    )

    production_site = models.ForeignKey(
        'organization.ProductionSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouses',
        verbose_name='Производственный объект'
    )

    address = models.CharField(
        max_length=255,
        verbose_name='Адрес'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Действующий склад'
    )

    def __str__(self):
        return self.name