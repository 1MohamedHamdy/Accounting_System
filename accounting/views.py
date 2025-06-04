from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import (
    Client, ClientPhoneNumber, Supplier, SupplierPhoneNumber,
    Product, Invoice, InvoiceItem, Payment
)
from .serializers import (
    ClientSerializer, SupplierSerializer, ProductSerializer,
    InvoiceSerializer, PaymentSerializer
)
from .reports import generate_sales_report, generate_purchases_report
import openpyxl
from datetime import datetime


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