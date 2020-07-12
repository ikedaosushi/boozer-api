from django.db import models

# Create your models here.

class Station(models.Model):
    station_id = models.IntegerField(unique=True)
    station_name = models.CharField(max_length=30)
    lon = models.FloatField()
    lat = models.FloatField()
    tabelog_url = models.URLField(null=True)
    top10_avarage_score = models.FloatField(null=True)
    num_shop = models.IntegerField(null=True)