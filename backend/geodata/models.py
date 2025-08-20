from django.db import models


class Place(models.Model):
    address = models.CharField(
        'Адресс',
        max_length=150,
        unique=True
    )
    longitude = models.DecimalField(
        'Долгота',
        max_digits=20,
        decimal_places=17
    )
    latitude = models.DecimalField(
        'Широта',
        max_digits=20,
        decimal_places=17
    )
    updated_at = models.DateTimeField(
        'Последнее обновление',
        auto_now=True
    )

    def __str__(self):
        return f'место по адресу: {self.address}'
