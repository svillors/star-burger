# Generated by Django 4.2.20 on 2025-04-09 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0046_order_delivered_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('CARD', 'Электронно'), ('CASH', 'Наличностью')], default='CASH', max_length=4, verbose_name='Способ оплаты'),
        ),
    ]
