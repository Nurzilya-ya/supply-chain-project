from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    production_site = models.ForeignKey(
        'organization.ProductionSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name='Производственный объект'
    )

    warehouse = models.ForeignKey(
        'warehouse.Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name='Склад (для кладовщика)'
    )
    def __str__(self):
        return self.username