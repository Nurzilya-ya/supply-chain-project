from django.db import models
from django.db.models import Q

class Warehouse(models.Model):

    WAREHOUSE_TYPES = [
        ('central', 'Центральный склад'),
        ('local', 'Локальный склад'),
    ]

    name = models.CharField(max_length=150, verbose_name='Название склада')
    warehouse_type = models.CharField(max_length=20, choices=WAREHOUSE_TYPES, verbose_name='Тип склада')
    production_site = models.ForeignKey(
        'organization.ProductionSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouses',
        verbose_name='Производственный объект'
    )
    address = models.CharField(  max_length=255, verbose_name='Адрес')
    is_active = models.BooleanField(default=True, verbose_name='Действующий склад')

    def __str__(self):
        return self.name

class Material(models.Model):
    UNIT_CHOICES = [
        ('pcs', 'шт.'),
        ('kg', 'кг'),
        ('l', 'л'),
        ('m', 'м'),
        ('m2', 'м²'),
        ('m3', 'м³'),
        ('set', 'компл.'),
    ]
    CATEGORY_CHOICES = [
        ('spare_parts', 'Запасные части'),
        ('consumables', 'Расходные материалы'),
        ('tools', 'Инструменты'),
        ('equipment', 'Оборудование'),
        ('fuel', 'ГСМ'),
        ('clothing', 'Спецодежда'),
        ('other', 'Прочее'),
    ]
    name = models.CharField( max_length=200, verbose_name='Наименование')
    code = models.CharField(max_length=50,unique=True, verbose_name='Код материала')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='Категория')
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, verbose_name='Единица измерения')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активный материал')

    class Meta:
        ordering = ['name']
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'

    def __str__(self):
        return f"{self.name} ({self.code})"

class Stock(models.Model):
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name='Склад',
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name='Материал',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name='Физический остаток',
    )
    reserved_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name='Зарезервировано',
    )

    class Meta:
        verbose_name = 'Складской остаток'
        verbose_name_plural = 'Складские остатки'
        constraints = [
            models.UniqueConstraint(
                fields=['warehouse', 'material'],
                name='unique_stock_per_warehouse_material',
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name='stock_quantity_non_negative',
            ),
            models.CheckConstraint(
                condition=Q(reserved_quantity__gte=0),
                name='stock_reserved_non_negative',
            ),
            models.CheckConstraint(
                condition=Q(reserved_quantity__lte=models.F('quantity')),
                name='stock_reserved_not_greater_than_quantity',
            ),
        ]

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    def __str__(self):
        return f"{self.material.name} @ {self.warehouse.name}: {self.quantity}"