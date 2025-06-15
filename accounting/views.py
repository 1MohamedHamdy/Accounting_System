from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import (
    Client, ClientPhoneNumber, Supplier, SupplierPhoneNumber,
    Product, Invoice, InvoiceItem, Payment
)
from .serializers import (
    ClientSerializer, SupplierSerializer, ProductSerializer,
    InvoiceSerializer, PaymentSerializer
)

from .forms import (
    ClientForm, ClientPhoneNumberForm, SupplierForm,
    SupplierPhoneNumberForm, ProductForm, InvoiceForm, PaymentForm,
    InvoiceItemForm
)
from .reports import generate_sales_report, generate_purchases_report
import openpyxl
from datetime import datetime, timedelta
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all().order_by('-created_at')
    serializer_class = ClientSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by('-created_at')
    serializer_class = SupplierSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        low_stock_products = self.queryset.filter(
            quantity_in_stock__lte=F('reorder_level'))
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-invoice_date')
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        invoice_type = self.request.query_params.get('type')
        if invoice_type:
            queryset = queryset.filter(invoice_type=invoice_type)
        return queryset


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by('-payment_date')
    serializer_class = PaymentSerializer


class SalesReportView(generics.GenericAPIView):
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        client_id = request.query_params.get('client_id')

        if not start_date or not end_date:
            return Response(
                {'error': 'Both start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Dates must be in YYYY-MM-DD format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        report_data = generate_sales_report(start_date, end_date, client_id)
        
        format = request.query_params.get('format', 'json')
        if format == 'excel':
            return self._generate_excel_response(report_data, 'sales_report')
        
        return Response(report_data)

    def _generate_excel_response(self, data, report_name):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = report_name

        # Add headers
        headers = [
            'Invoice Number', 'Date', 'Client', 'Product', 'Quantity',
            'Unit Price', 'Tax', 'Discount', 'Total'
        ]
        ws.append(headers)

        # Add data
        for invoice in data['invoices']:
            for item in invoice['items']:
                ws.append([
                    invoice['invoice_number'],
                    invoice['invoice_date'],
                    invoice['client_name'],
                    item['product_name'],
                    item['quantity'],
                    item['unit_price'],
                    item['tax_amount'],
                    item['discount'],
                    item['total']
                ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={report_name}.xlsx'
        wb.save(response)
        return response


class PurchasesReportView(generics.GenericAPIView):
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        supplier_id = request.query_params.get('supplier_id')

        if not start_date or not end_date:
            return Response(
                {'error': 'Both start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Dates must be in YYYY-MM-DD format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        report_data = generate_purchases_report(start_date, end_date, supplier_id)
        
        format = request.query_params.get('format', 'json')
        if format == 'excel':
            return self._generate_excel_response(report_data, 'purchases_report')
        
        return Response(report_data)

    def _generate_excel_response(self, data, report_name):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = report_name

        # Add headers
        headers = [
            'Invoice Number', 'Date', 'Supplier', 'Product', 'Quantity',
            'Unit Price', 'Tax', 'Discount', 'Total'
        ]
        ws.append(headers)

        # Add data
        for invoice in data['invoices']:
            for item in invoice['items']:
                ws.append([
                    invoice['invoice_number'],
                    invoice['invoice_date'],
                    invoice['supplier_name'],
                    item['product_name'],
                    item['quantity'],
                    item['unit_price'],
                    item['tax_amount'],
                    item['discount'],
                    item['total']
                ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={report_name}.xlsx'
        wb.save(response)
        return response
    
    
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from .models import Client, ClientPhoneNumber, Supplier, SupplierPhoneNumber, Product, Invoice, Payment
from .forms import ClientForm, ClientPhoneNumberForm, SupplierForm, SupplierPhoneNumberForm, ProductForm, InvoiceForm, PaymentForm
from django.forms import formset_factory
from django.views.decorators.http import require_GET

@login_required
def add_client(request):
    PhoneNumberFormSet = formset_factory(ClientPhoneNumberForm, extra=1, can_delete=True)
    
    if request.method == 'POST':
        client_form = ClientForm(request.POST)
        phone_formset = PhoneNumberFormSet(request.POST, prefix='phones')
        
        if client_form.is_valid() and phone_formset.is_valid():
            try:
                client = client_form.save()
                for phone_form in phone_formset:
                    if phone_form.cleaned_data and not phone_form.cleaned_data.get('DELETE', False):
                        if phone_form.cleaned_data.get('number'):
                            phone = phone_form.save(commit=False)
                            phone.client = client
                            phone.save()
                messages.success(request, _("Client added successfully!"))
                if '_addanother' in request.POST:
                    return redirect('admin:accounting_add_client')
                elif '_continue' in request.POST:
                    return redirect('admin:accounting_client_change', client.id)
                return redirect('admin:accounting_dashboardstats')
            except Exception as e:
                messages.error(request, _("Error adding client: ") + str(e))
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        client_form = ClientForm()
        phone_formset = PhoneNumberFormSet(prefix='phones')

    context = {
        'client_form': client_form,
        'phone_formset': phone_formset,
        'app_label': 'accounting',
    }
    return render(request, 'admin/add_client.html', context)

@login_required
def add_supplier(request):
    PhoneNumberFormSet = formset_factory(SupplierPhoneNumberForm, extra=1, can_delete=True)
    
    if request.method == 'POST':
        supplier_form = SupplierForm(request.POST)
        phone_formset = PhoneNumberFormSet(request.POST, prefix='phones')
        
        if supplier_form.is_valid() and phone_formset.is_valid():
            try:
                supplier = supplier_form.save()
                for phone_form in phone_formset:
                    if phone_form.cleaned_data and not phone_form.cleaned_data.get('DELETE', False):
                        if phone_form.cleaned_data.get('number'):
                            phone = phone_form.save(commit=False)
                            phone.supplier = supplier
                            phone.save()
                messages.success(request, _("Supplier added successfully!"))
                if '_addanother' in request.POST:
                    return redirect('admin:accounting_add_supplier')
                elif '_continue' in request.POST:
                    return redirect('admin:accounting_supplier_change', supplier.id)
                return redirect('admin:accounting_dashboardstats')
            except Exception as e:
                messages.error(request, _("Error adding supplier: ") + str(e))
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        supplier_form = SupplierForm()
        phone_formset = PhoneNumberFormSet(prefix='phones')

    context = {
        'supplier_form': supplier_form,
        'phone_formset': phone_formset,
        'app_label': 'accounting',
    }
    return render(request, 'admin/add_supplier.html', context)

@login_required
def add_product(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES)
        
        if product_form.is_valid():
            try:
                product = product_form.save()
                messages.success(request, _("Product added successfully!"))
                if '_addanother' in request.POST:
                    return redirect('admin:accounting_add_product')
                elif '_continue' in request.POST:
                    return redirect('admin:accounting_product_change', product.id)
                return redirect('admin:accounting_dashboardstats')
            except Exception as e:
                messages.error(request, _("Error adding product: ") + str(e))
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        product_form = ProductForm()

    context = {
        'product_form': product_form,
        'app_label': 'accounting',
    }
    return render(request, 'admin/add_product.html', context)

@login_required
def add_invoice(request):
    InvoiceItemFormSet = formset_factory(InvoiceItemForm, extra=1, can_delete=True)
    
    if request.method == 'POST':
        invoice_form = InvoiceForm(request.POST)
        item_formset = InvoiceItemFormSet(request.POST, prefix='items')
        
        if invoice_form.is_valid() and item_formset.is_valid():
            try:
                with transaction.atomic():
                    invoice = invoice_form.save()
                    total_amount = 0
                    for item_form in item_formset:
                        if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                            item = item_form.save(commit=False)
                            item.invoice = invoice
                            item.total = (item.price * item.quantity) + item.tax_amount - item.discount
                            item.save()
                            total_amount += item.total
                    invoice.total_amount = total_amount
                    invoice.save()
                    messages.success(request, _("Invoice added successfully!"))
                    if '_addanother' in request.POST:
                        return redirect('admin:accounting_add_invoice')
                    elif '_continue' in request.POST:
                        return redirect('admin:accounting_invoice_change', invoice.id)
                    return redirect('admin:accounting_dashboardstats')
            except Exception as e:
                messages.error(request, _("Error adding invoice: ") + str(e))
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        invoice_type = request.GET.get('invoice_type', 'sale')
        initial = {'invoice_type': invoice_type}
        invoice_form = InvoiceForm(initial=initial)
        item_formset = InvoiceItemFormSet(prefix='items')

    context = {
        'invoice_form': invoice_form,
        'item_formset': item_formset,
        'app_label': 'accounting',
    }
    return render(request, 'admin/add_invoice.html', context)

@login_required
def add_payment(request):
    if request.method == 'POST':
        payment_form = PaymentForm(request.POST)
        if payment_form.is_valid():
            try:
                payment = payment_form.save()
                messages.success(request, _("Payment added successfully!"))
                if '_addanother' in request.POST:
                    return redirect('admin:accounting_add_payment')
                elif '_continue' in request.POST:
                    return redirect('admin:accounting_payment_change', payment.id)
                return redirect('admin:accounting_dashboardstats')
            except Exception as e:
                messages.error(request, _("Error adding payment: ") + str(e))
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        payment_form = PaymentForm()

    context = {
        'payment_form': payment_form,
        'app_label': 'accounting',
    }
    return render(request, 'admin/add_payment.html', context)


@login_required
def view_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'name': client.name,
            'business_type': client.get_business_type_display(),
            'address': client.address,
            'national_id': client.national_id,
            'tax_number': client.tax_number,
            'num_of_invoices': client.num_of_invoices,
            'phone_numbers': [f"{p.number} ({p.description or 'N/A'})" for p in client.clientphonenumber_set.all()]
        }
        return JsonResponse(data)
    paid_invoices_count = client.invoices.filter(payment_status='paid').count()
    unpaid_invoices_count = client.invoices.filter(payment_status='unpaid').count()
    return render(request, 'admin/view_client.html', {
        'client': client,
        'paid_invoices_count': paid_invoices_count,
        'unpaid_invoices_count': unpaid_invoices_count,
    })

@login_required
def view_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'name': supplier.name,
            'business_type': supplier.get_business_type_display(),
            'address': supplier.address,
            'national_id': supplier.national_id,
            'tax_number': supplier.tax_number,
            'num_of_invoices': supplier.num_of_invoices,
            'phone_numbers': [f"{p.number} ({p.description or 'N/A'})" for p in supplier.supplierphonenumber_set.all()]
        }
        return JsonResponse(data)
    paid_invoices_count = supplier.invoices.filter(payment_status='paid').count()
    unpaid_invoices_count = supplier.invoices.filter(payment_status='unpaid').count()
    context = {
        'supplier': supplier,
        'paid_invoices_count': paid_invoices_count,
        'unpaid_invoices_count': unpaid_invoices_count,
    }
    return render(request, 'admin/view_supplier.html', context)

@login_required
def view_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'name': product.name,
            'description': product.description,
            'quantity_in_stock': product.quantity_in_stock,
            'unit_price': product.unit_price,
            'reorder_level': product.reorder_level
        }
        return JsonResponse(data)
    return render(request, 'admin/view_product.html', {'product': product})

@login_required
def view_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date,
            'client_name': invoice.client.name if invoice.client else 'N/A',
            'total_amount': invoice.total_amount,
            'invoice_type': invoice.get_invoice_type_display()
        }
        return JsonResponse(data)
    return render(request, 'admin/view_invoice.html', {'invoice': invoice})

@login_required
def view_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'payment_date': payment.payment_date,
            'amount': payment.amount,
            'payment_method': payment.get_payment_method_display(),
            'invoice': payment.invoice.invoice_number if payment.invoice else 'N/A'
        }
        return JsonResponse(data)
    return render(request, 'admin/view_payment.html', {'payment': payment})

@require_GET
def get_model_options(request, model_name):
    model_map = {
        'clients': Client,
        'suppliers': Supplier,
        'products': Product,
        'invoices': Invoice,
        'payments': Payment,
    }
    if model_name not in model_map:
        return JsonResponse({'error': 'Invalid model name'}, status=400)
    model = model_map[model_name]
    options = [{'id': obj.id, 'name': str(obj)} for obj in model.objects.all()]
    return JsonResponse({'options': options})

@login_required
def list_clients(request):
    query = request.GET.get('q', '').strip()
    business_type = request.GET.get('business_type', '')
    page_number = request.GET.get('page', 1)
    clients = Client.objects.all().order_by('-created_at')
    if query:
        clients = clients.filter(
            Q(name__icontains=query) |
            Q(national_id__icontains=query) |
            Q(tax_number__icontains=query)
        )
    if business_type:
        clients = clients.filter(business_type=business_type)
    paginator = Paginator(clients, 15)
    page_obj = paginator.get_page(page_number)
    # For pagination links with filters
    filter_querystring = ''
    if query:
        filter_querystring += f'&q={query}'
    if business_type:
        filter_querystring += f'&business_type={business_type}'
    context = {
        'clients': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'filter_querystring': filter_querystring,
        'request': request,
    }
    return render(request, 'admin/client_list.html', context)

@login_required
def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('accounting:view_client', client_id=client.id)
    else:
        form = ClientForm(instance=client)
    return render(request, 'admin/edit_client.html', {'form': form, 'client': client})

@login_required
def list_suppliers(request):
    query = request.GET.get('q', '').strip()
    business_type = request.GET.get('business_type', '')
    page_number = request.GET.get('page', 1)
    suppliers = Supplier.objects.all().order_by('-created_at')
    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query) |
            Q(supplier_code__icontains=query) |
            Q(tax_number__icontains=query)
        )
    if business_type:
        suppliers = suppliers.filter(business_type=business_type)
    paginator = Paginator(suppliers, 15)
    page_obj = paginator.get_page(page_number)
    filter_querystring = ''
    if query:
        filter_querystring += f'&q={query}'
    if business_type:
        filter_querystring += f'&business_type={business_type}'
    context = {
        'suppliers': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'filter_querystring': filter_querystring,
        'request': request,
    }
    return render(request, 'admin/supplier_list.html', context)

@login_required
def edit_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('accounting:view_supplier', supplier_id=supplier.id)
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'admin/edit_supplier.html', {'form': form, 'supplier': supplier})

@login_required
def list_products(request):
    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    products = Product.objects.all().order_by('-created_at')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query)
        )
    paginator = Paginator(products, 15)
    page_obj = paginator.get_page(page_number)
    filter_querystring = ''
    if query:
        filter_querystring += f'&q={query}'
    context = {
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'filter_querystring': filter_querystring,
        'request': request,
    }
    return render(request, 'admin/product_list.html', context)

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('accounting:view_product', product_id=product.id)
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin/edit_product.html', {'form': form, 'product': product})

@login_required
def list_invoices(request):
    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    invoices = Invoice.objects.all().order_by('-invoice_date')
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query)
        )
    paginator = Paginator(invoices, 15)
    page_obj = paginator.get_page(page_number)
    filter_querystring = ''
    if query:
        filter_querystring += f'&q={query}'
    context = {
        'invoices': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'filter_querystring': filter_querystring,
        'request': request,
    }
    return render(request, 'admin/invoice_list.html', context)

@login_required
def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            return redirect('accounting:view_invoice', invoice_id=invoice.id)
    else:
        form = InvoiceForm(instance=invoice)
    return render(request, 'admin/edit_invoice.html', {'form': form, 'invoice': invoice})

@login_required
def list_payments(request):
    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    payments = Payment.objects.all().order_by('-payment_date')
    if query:
        payments = payments.filter(
            Q(notes__icontains=query)
        )
    paginator = Paginator(payments, 15)
    page_obj = paginator.get_page(page_number)
    filter_querystring = ''
    if query:
        filter_querystring += f'&q={query}'
    context = {
        'payments': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'filter_querystring': filter_querystring,
        'request': request,
    }
    return render(request, 'admin/payment_list.html', context)

@login_required
def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return redirect('accounting:view_payment', payment_id=payment.id)
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'admin/edit_payment.html', {'form': form, 'payment': payment})