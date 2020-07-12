# Generated by Django 3.0.7 on 2020-07-12 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('station_id', models.IntegerField(unique=True)),
                ('station_name', models.CharField(max_length=30)),
                ('lon', models.FloatField()),
                ('lat', models.FloatField()),
                ('tabelog_url', models.URLField(null=True)),
                ('top10_avarage_score', models.FloatField(null=True)),
                ('num_shop', models.IntegerField(null=True)),
            ],
        ),
    ]
