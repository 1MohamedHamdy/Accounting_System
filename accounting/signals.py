from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db.models import Sum
from .models import Invoice, Client, Supplier


# @receiver(post_save, sender=Invoice)
# def update_client_supplier_stats(sender, instance, created, **kwargs):
#     if instance.invoice_type == Invoice.SALES and instance.client:
#         instance.client.invoice_count = instance.client.invoices.count()
#         instance.client.save()
#     elif instance.invoice_type == Invoice.PURCHASE and instance.supplier:
#         total = instance.supplier.invoices.filter(
#             invoice_type=Invoice.PURCHASE).aggregate(
#                 Sum('total_amount'))['total_amount__sum'] or 0
#         instance.supplier.total_orders = total
#         instance.supplier.save()


# @receiver(pre_save, sender=Invoice)
# def validate_invoice(sender, instance, **kwargs):
#     if instance.invoice_type == Invoice.SALES:  # Use the defined constant
#         instance.update_inventory()