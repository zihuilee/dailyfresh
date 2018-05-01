# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0002_auto_20180227_2010'),
    ]

    operations = [
        migrations.CreateModel(
            name='IndexCategoryGoodsBanner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('create_time', models.DateField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateField(verbose_name='修改时间', auto_now=True)),
                ('display_type', models.SmallIntegerField(verbose_name='展示类型', choices=[(0, '标题'), (1, '图片')])),
                ('index', models.SmallIntegerField(verbose_name='顺序', default=0)),
                ('category', models.ForeignKey(verbose_name='商品类别', to='goods.GoodsCategory')),
                ('sku', models.ForeignKey(verbose_name='商品SKU', to='goods.GoodsSKU')),
            ],
            options={
                'verbose_name': '主页分类展示商品',
                'db_table': 'df1_index_category_goods',
                'verbose_name_plural': '主页分类展示商品',
            },
        ),
        migrations.CreateModel(
            name='IndexGoodsBanner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('create_time', models.DateField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateField(verbose_name='修改时间', auto_now=True)),
                ('image', models.ImageField(verbose_name='图片', upload_to='banner')),
                ('index', models.SmallIntegerField(verbose_name='顺序', default=0)),
                ('sku', models.ForeignKey(verbose_name='商品SKU', to='goods.GoodsSKU')),
            ],
            options={
                'verbose_name': '主页轮播商品',
                'db_table': 'df1_index_goods',
                'verbose_name_plural': '主页轮播商品',
            },
        ),
        migrations.RemoveField(
            model_name='indexcategorygoodsbaner',
            name='category',
        ),
        migrations.RemoveField(
            model_name='indexcategorygoodsbaner',
            name='sku',
        ),
        migrations.RemoveField(
            model_name='indexgoodsbaner',
            name='sku',
        ),
        migrations.DeleteModel(
            name='IndexCategoryGoodsBaner',
        ),
        migrations.DeleteModel(
            name='IndexGoodsBaner',
        ),
    ]
