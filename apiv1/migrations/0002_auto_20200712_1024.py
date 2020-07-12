# Generated by Django 3.0.7 on 2020-07-12 10:24

from django.db import migrations
import pandas as pd

def forwards_func(apps, schema_editor):
    Station = apps.get_model("apiv1", "Station")
    df = pd.read_csv("apiv1/data/stations.csv")
    for _, row in df.iterrows():
        station = Station(**row.to_dict())
        station.save()

def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]