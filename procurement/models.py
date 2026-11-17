from django.db import models
from django.conf import settings

class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название поставщика')
    contact_person = models.CharField(max_length=150, blank=True, verbose_name='Контактное лицо')
    phone = models.CharField(max_length=30, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Электронная почта')
    address = models.CharField(max_length=255, blank=True, verbose_name='Адрес')
    is_active = models.BooleanField(default=True, verbose_name='Действующий поставщик')

    def __str__(self):
        return self.name

class MaterialRequest(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('submitted', 'На рассмотрении'),
        ('approved', 'Согласована'),
        ('rejected', 'Отклонена'),
        ('need_clarification', 'На уточнении'),
        ('fulfilled', 'Выполнена'),
    ]

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='material_requests',
        verbose_name='Автор заявки',
    )
    production_site = models.ForeignKey(
        'organization.ProductionSite',
        on_delete=models.PROTECT,
        related_name='material_requests',
        verbose_name='Производственный объект',
    )
    warehouse = models.ForeignKey(
        'warehouse.Warehouse',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='assigned_requests',
        verbose_name='Склад обеспечения',
        help_text='Выбирается специалистом снабжения при согласовании',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Статус',
    )
    purpose = models.TextField(
        verbose_name='Назначение заявки',
        help_text='Например: плановый ремонт насосной станции, причина заявки и т.п.',
    )
    required_date = models.DateField(
        verbose_name='Требуемая дата поставки',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )

    class Meta:
        verbose_name = 'Заявка на материалы'
        verbose_name_plural = 'Заявки на материалы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка №{self.pk} от {self.created_by.username}"

    @property
    def has_deficit(self):
        return any(item.reserved_quantity < item.quantity for item in self.items.all())

    def reserve_stock(self):
        if not self.warehouse:
            raise ValueError('Не выбран склад для обеспечения заявки')

        if self.status != 'approved':
            raise ValueError('Резервирование возможно только для согласованной заявки')

        from warehouse.models import Stock

        deficits = []

        for item in self.items.all():
            still_needed = item.quantity - item.reserved_quantity
            if still_needed <= 0:
                continue

            try:
                stock = Stock.objects.get(warehouse=self.warehouse, material=item.material)
            except Stock.DoesNotExist:
                deficits.append((item, still_needed))
                continue

            available = stock.quantity - stock.reserved_quantity
            to_reserve = min(available, still_needed)

            if to_reserve > 0:
                stock.reserved_quantity += to_reserve
                stock.save()
                item.reserved_quantity += to_reserve
                item.save()

            shortage = still_needed - to_reserve
            if shortage > 0:
                deficits.append((item, shortage))

        return deficits


class RequestItem(models.Model):
    request = models.ForeignKey(
        MaterialRequest,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заявка',
    )
    material = models.ForeignKey(
        'warehouse.Material',
        on_delete=models.PROTECT,
        related_name='request_items',
        verbose_name='Материал',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        verbose_name='Количество',
    )
    reserved_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name='Зарезервировано',
    )
    comment = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Комментарий',
    )

    class Meta:
        verbose_name = 'Строка заявки'
        verbose_name_plural = 'Строки заявки'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='request_item_quantity_positive',
            ),
        ]

    def __str__(self):
        return f"{self.material.name} × {self.quantity}"


class ProcurementOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('ordered', 'Заказано поставщику'),
        ('partially_delivered', 'Частично поставлено'),
        ('delivered', 'Поставлено'),
        ('cancelled', 'Отменён'),
    ]

    order_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Номер заказа',
        help_text='Можно не заполнять — будет присвоен автоматически',
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Поставщик',
    )
    warehouse = models.ForeignKey(
        'warehouse.Warehouse',
        on_delete=models.PROTECT,
        related_name='procurement_orders',
        verbose_name='Склад назначения',
        help_text='Куда привезти заказанные материалы',
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Статус',
    )
    order_date = models.DateField(
        auto_now_add=True,
        verbose_name='Дата заказа',
    )
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ожидаемая дата поставки',
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='procurement_orders',
        verbose_name='Автор заказа',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )

    class Meta:
        verbose_name = 'Заказ на закупку'
        verbose_name_plural = 'Заказы на закупку'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ {self.order_number} — {self.supplier.name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            super().save(*args, **kwargs)
            self.order_number = f"ПО-{self.pk:04d}"
            super().save(update_fields=['order_number'])
        else:
            super().save(*args, **kwargs)


class ProcurementOrderItem(models.Model):
    order = models.ForeignKey(
        ProcurementOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ',
    )
    material = models.ForeignKey(
        'warehouse.Material',
        on_delete=models.PROTECT,
        related_name='procurement_items',
        verbose_name='Материал',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        verbose_name='Количество',
    )
    received_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name='Принято на склад',
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Цена за единицу',
    )
    request_item = models.ForeignKey(
        'RequestItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='procurement_items',
        verbose_name='Строка заявки',
        help_text='Если закупка закрывает дефицит по заявке',
    )

    class Meta:
        verbose_name = 'Строка заказа'
        verbose_name_plural = 'Строки заказа'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='procurement_item_quantity_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(received_quantity__gte=0),
                name='procurement_item_received_non_negative',
            ),
            models.CheckConstraint(
                condition=models.Q(received_quantity__lte=models.F('quantity')),
                name='procurement_item_received_not_greater',
            ),
        ]

    def __str__(self):
        return f"{self.material.name} × {self.quantity}"

class PlannedRequirement(models.Model):
    STATUS_CHOICES = [
        ('open', 'Открыта'),
        ('in_progress', 'В работе (закупка)'),
        ('closed', 'Закрыта'),
    ]

    production_site = models.ForeignKey(
        'organization.ProductionSite',
        on_delete=models.PROTECT,
        related_name='planned_requirements',
        verbose_name='Производственный объект',
    )
    material = models.ForeignKey(
        'warehouse.Material',
        on_delete=models.PROTECT,
        related_name='planned_requirements',
        verbose_name='Материал',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        verbose_name='Требуемое количество',
    )
    target_date = models.DateField(
        verbose_name='Планируемая дата потребления',
        help_text='Например, дата начала планового ремонта'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name='Статус',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='planned_requirements',
        verbose_name='Автор',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий',
    )

    class Meta:
        verbose_name = 'Плановая потребность'
        verbose_name_plural = 'Плановые потребности'
        ordering = ['target_date']

    def __str__(self):
        return f"{self.material.name} — {self.quantity} (к {self.target_date})"

