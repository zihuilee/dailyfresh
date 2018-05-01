# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='goods',
            table='df1_goods',
        ),
        migrations.AlterModelTable(
            name='goodscategory',
            table='df1_goods_category',
        ),
        migrations.AlterModelTable(
            name='goodsimage',
            table='df1_goods_image',
        ),
        migrations.AlterModelTable(
            name='goodssku',
            table='df1_goods_sku',
        ),
        migrations.AlterModelTable(
            name='indexcategorygoodsbaner',
            table='df1_index_category_goods',
        ),
        migrations.AlterModelTable(
            name='indexgoodsbaner',
            table='df1_index_goods',
        ),
        migrations.AlterModelTable(
            name='indexpromotionbanner',
            table='df1_index_promotion',
        ),
    ]
