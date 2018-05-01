# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_auto_20180214_1910'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='ordergoods',
            table='df1_order_goods',
        ),
        migrations.AlterModelTable(
            name='orderinfo',
            table='df1_order_info',
        ),
    ]
