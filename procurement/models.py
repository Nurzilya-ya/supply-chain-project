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