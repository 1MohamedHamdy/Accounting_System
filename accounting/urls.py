from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientViewSet, SupplierViewSet, ProductViewSet,
    InvoiceViewSet, PaymentViewSet, SalesReportView,
    PurchasesReportView
)

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
]