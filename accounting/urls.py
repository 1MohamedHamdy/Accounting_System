from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientViewSet, SupplierViewSet, ProductViewSet,
    InvoiceViewSet, PaymentViewSet, SalesReportView,
    PurchasesReportView
)
from . import views

app_name = 'accounting'

router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'products', ProductViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('reports/sales/', SalesReportView.as_view(), name='sales-report'),
    path('reports/purchases/', PurchasesReportView.as_view(), name='purchases-report'),
    path('add-client/', views.add_client, name='add_client'),
    path('add-supplier/', views.add_supplier, name='add_supplier'),
    path('add-product/', views.add_product, name='add_product'),
    path('add-invoice/', views.add_invoice, name='add_invoice'),
    path('add-payment/', views.add_payment, name='add_payment'),
    path('client/<int:client_id>/view/', views.view_client, name='view_client'),
    path('supplier/<int:supplier_id>/view/', views.view_supplier, name='view_supplier'),
    path('product/<int:product_id>/view/', views.view_product, name='view_product'),
    path('invoice/<int:invoice_id>/view/', views.view_invoice, name='view_invoice'),
    path('payment/<int:payment_id>/view/', views.view_payment, name='view_payment'),
    path('<str:model_name>/options/', views.get_model_options, name='get_model_options'),
    path('clients/options/', views.get_model_options, {'model_name': 'clients'}, name='client_options'),
    path('suppliers/options/', views.get_model_options, {'model_name': 'suppliers'}, name='supplier_options'),
    path('products/options/', views.get_model_options, {'model_name': 'products'}, name='product_options'),
    path('invoices/options/', views.get_model_options, {'model_name': 'invoices'}, name='invoice_options'),
    path('payments/options/', views.get_model_options, {'model_name': 'payments'}, name='payment_options'),   
]