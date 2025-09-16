from django.db import models

class Place(models.Model):
    address = models.CharField(
        'адрес',
        max_length=200,
        unique=True,
        db_index=True,
    )
    latitude = models.FloatField('широта', null=True, blank=True)
    longitude = models.FloatField('долгота', null=True, blank=True)
    updated_at = models.DateTimeField('обновлено', auto_now=True)

    class Meta:
        verbose_name = 'место на карте'
        verbose_name_plural = 'места на карте'

    def __str__(self):
        return self.address
