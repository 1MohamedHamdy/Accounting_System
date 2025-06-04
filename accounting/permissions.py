from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Invoice, Product

def create_custom_permissions():
    content_type = ContentType.objects.get_for_model(Invoice)
    Permission.objects.get_or_create(
        codename='export_invoices',
        name='Can export invoices',
        content_type=content_type,
    )
    Permission.objects.get_or_create(
        codename='mark_invoices_paid',
        name='Can mark invoices as paid',
        content_type=content_type,
    )
    Permission.objects.get_or_create(
        codename='mark_invoices_unpaid',
        name='Can mark invoices as unpaid',
        content_type=content_type,
    )
    Permission.objects.get_or_create(
        codename='export_sales_report',
        name='Can export sales report',
        content_type=content_type,
    )
    Permission.objects.get_or_create(
        codename='export_purchases_report',
        name='Can export purchases report',
        content_type=content_type,
    )

    content_type = ContentType.objects.get_for_model(Product)
    Permission.objects.get_or_create(
        codename='export_products',
        name='Can export products',
        content_type=content_type,
    )