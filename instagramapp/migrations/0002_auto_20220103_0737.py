# Generated by Django 2.2 on 2022-01-03 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instagramapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='users',
            name='email',
            field=models.EmailField(help_text='Email address', max_length=254),
        ),
    ]