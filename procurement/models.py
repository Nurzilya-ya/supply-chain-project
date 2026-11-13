from django.db import models

class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название поставщика')
    contact_person = models.CharField(max_length=150, blank=True, verbose_name='Контактное лицо')
    phone = models.CharField(max_length=30, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Электронная почта')
    address = models.CharField(max_length=255, blank=True, verbose_name='Адрес')
    is_active = models.BooleanField(default=True, verbose_name='Действующий поставщик')

    def __str__(self):
        return self.name
