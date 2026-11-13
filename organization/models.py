from django.db import models


class ProductionSite(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name='Название объекта'
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Адрес'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Действующий объект'
    )

    def __str__(self):
        return self.name
