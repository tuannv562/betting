# Generated by Django 2.0.8 on 2018-09-04 09:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('competitions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='team',
            field=models.ManyToManyField(null=True, related_name='members', to='competitions.Team'),
        ),
    ]
