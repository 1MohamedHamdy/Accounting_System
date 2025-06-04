from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from .models import Invoice, InvoiceItem
from datetime import date


def generate_sales_report(start_date, end_date, client_id=None):
    invoices = Invoice.objects.filter(
        invoice_type='sales',
        invoice_date__gte=start_date,
        invoice_date__lte=end_date
    ).order_by('invoice_date')

    if client_id:
        invoices = invoices.filter(client_id=client_id)

    report_data = {
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': 0,
        'total_quantity': 0,
        'invoices': []
    }

    for invoice in invoices:
        items = invoice.items.annotate(
            total=ExpressionWrapper(
                F('quantity') * F('unit_price') + F('tax_amount') - F('discount'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
        
        invoice_data = {
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date,
            'client_id': invoice.client_id,
            'client_name': invoice.client.name if invoice.client else '',
            'payment_status': invoice.get_payment_status_display(),
            'total_amount': invoice.total_amount,
            'items': []
        }

        for item in items:
            invoice_data['items'].append({
                'product_id': item.product_id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'tax_amount': item.tax_amount,
                'discount': item.discount,
                'total': item.total
            })
            report_data['total_quantity'] += item.quantity

        report_data['total_sales'] += invoice.total_amount
        report_data['invoices'].append(invoice_data)

    return report_data


def generate_purchases_report(start_date, end_date, supplier_id=None):
    invoices = Invoice.objects.filter(
        invoice_type='purchase',
        invoice_date__gte=start_date,
        invoice_date__lte=end_date
    ).order_by('invoice_date')

    if supplier_id:
        invoices = invoices.filter(supplier_id=supplier_id)

    report_data = {
        'start_date': start_date,
        'end_date': end_date,
        'total_purchases': 0,
        'total_quantity': 0,
        'invoices': []
    }

    for invoice in invoices:
        items = invoice.items.annotate(
            total=ExpressionWrapper(
                F('quantity') * F('unit_price') + F('tax_amount') - F('discount'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
        
        invoice_data = {
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date,
            'supplier_id': invoice.supplier_id,
            'supplier_name': invoice.supplier.name if invoice.supplier else '',
            'payment_status': invoice.get_payment_status_display(),
            'total_amount': invoice.total_amount,
            'items': []
        }

        for item in items:
            invoice_data['items'].append({
                'product_id': item.product_id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'tax_amount': item.tax_amount,
                'discount': item.discount,
                'total': item.total
            })
            report_data['total_quantity'] += item.quantity

        report_data['total_purchases'] += invoice.total_amount
        report_data['invoices'].append(invoice_data)

    return report_data