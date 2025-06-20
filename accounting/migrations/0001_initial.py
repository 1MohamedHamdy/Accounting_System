# Generated by Django 5.2.1 on 2025-05-27 05:55

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('business_type', models.CharField(choices=[('individual', 'Individual'), ('company', 'Company')], max_length=20)),
                ('national_id', models.CharField(blank=True, max_length=50, null=True)),
                ('tax_number', models.CharField(blank=True, max_length=50, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('invoice_count', models.PositiveIntegerField(default=0, editable=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('qr_code', models.ImageField(blank=True, null=True, upload_to='qr_codes/')),
                ('price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('price_type', models.CharField(choices=[('wholesale', 'Wholesale'), ('retail', 'Retail')], default='retail', max_length=20)),
                ('tax_type', models.CharField(choices=[('amount', 'Fixed Amount'), ('percent', 'Percentage')], default='percent', max_length=20)),
                ('tax_value', models.DecimalField(decimal_places=2, max_digits=12)),
                ('reorder_level', models.PositiveIntegerField(default=10)),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/')),
                ('description', models.TextField(blank=True, null=True)),
                ('quantity_in_stock', models.PositiveIntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('tax_number', models.CharField(max_length=50)),
                ('business_type', models.CharField(choices=[('individual', 'Individual'), ('company', 'Company')], max_length=20)),
                ('address', models.TextField(blank=True, null=True)),
                ('supplier_code', models.CharField(max_length=50, unique=True)),
                ('cooperation_start_date', models.DateField()),
                ('cooperation_end_date', models.DateField(blank=True, null=True)),
                ('website', models.URLField(blank=True, null=True)),
                ('payment_terms', models.CharField(choices=[('30_days', '30 Days'), ('60_days', '60 Days')], default='30_days', max_length=20)),
                ('total_orders', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=12)),
                ('terms_and_conditions', models.TextField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ClientPhoneNumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=20)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phone_numbers', to='accounting.client')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invoice_number', models.CharField(max_length=50, unique=True)),
                ('invoice_date', models.DateField(default=django.utils.timezone.now)),
                ('invoice_type', models.CharField(choices=[('purchase', 'Purchase'), ('sales', 'Sales')], max_length=20)),
                ('payment_status', models.CharField(choices=[('paid', 'Paid'), ('unpaid', 'Unpaid'), ('pending', 'Pending')], default='unpaid', max_length=20)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=12)),
                ('notes', models.TextField(blank=True, null=True)),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounting.client')),
                ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounting.supplier')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payment_date', models.DateField(default=django.utils.timezone.now)),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('bank_transfer', 'Bank Transfer'), ('check', 'Check'), ('credit_card', 'Credit Card')], default='cash', max_length=20)),
                ('notes', models.TextField(blank=True, null=True)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounting.invoice')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('discount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('description', models.TextField(blank=True, null=True)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='accounting.invoice')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounting.product')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounting.supplier'),
        ),
        migrations.CreateModel(
            name='SupplierPhoneNumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=20)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
                ('is_main', models.BooleanField(default=False)),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phone_numbers', to='accounting.supplier')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
