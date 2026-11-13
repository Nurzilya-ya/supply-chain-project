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

    def __str__(self):
        return self.username