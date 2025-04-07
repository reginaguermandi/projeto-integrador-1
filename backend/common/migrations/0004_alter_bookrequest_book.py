# Generated by Django 5.1.7 on 2025-04-07 14:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0003_alter_book_category_alter_book_classification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookrequest',
            name='book',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='book_request_rel', to='common.book'),
        ),
    ]
