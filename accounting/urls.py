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
]