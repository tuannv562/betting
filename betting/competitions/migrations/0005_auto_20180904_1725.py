# Generated by Django 2.0.8 on 2018-09-04 10:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('competitions', '0004_auto_20180904_1641'),
    ]

    operations = [
        migrations.AlterField(
            model_name='season',
            name='end_date',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='season',
            name='start_date',
            field=models.DateField(null=True),
        ),
    ]
