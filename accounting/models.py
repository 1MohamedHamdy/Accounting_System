from django.db import models, transaction, IntegrityError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum, F
import qrcode
from io import BytesIO
from django.core.files import File
import uuid
from django.core.cache import cache
from django.contrib import admin
from django.utils.html import format_html, escape
from django.urls import reverse
from django.http import HttpResponse
from datetime import timedelta
from django.utils import timezone
import csv
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib import messages
from django.urls import path

from django.utils.translation import gettext_lazy as _

# Models
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        abstract = True

class PhoneNumber(models.Model):
    number = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("Phone Number"))
    description = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Description"))

    class Meta:
        abstract = True

class ClientPhoneNumber(PhoneNumber):
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='phone_numbers', verbose_name=_("Client"))

class SupplierPhoneNumber(PhoneNumber):
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE, related_name='phone_numbers', verbose_name=_("Supplier"))
    is_main = models.BooleanField(default=False, verbose_name=_("Is Main"))

class Client(TimeStampedModel):
    INDIVIDUAL = 'individual'
    COMPANY = 'company'
    BUSINESS_TYPE_CHOICES = [
        (INDIVIDUAL, _("Individual")),
        (COMPANY, _("Company")),
    ]

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, verbose_name=_("Business Type"))
    national_id = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("National ID"))
    tax_number = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Tax Number"))
    address = models.TextField(verbose_name=_("Address"))
    num_of_invoices = models.PositiveIntegerField(default=0, verbose_name=_("Number of Invoices"))

    def clean(self):
        if self.business_type == self.INDIVIDUAL and not self.national_id:
            raise ValidationError(_("National ID is required for individual clients"))
        if self.business_type == self.COMPANY and not self.tax_number:
            raise ValidationError(_("Tax number is required for company clients"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        indexes = [
            models.Index(fields=['name'], name='client_name_idx'),
            models.Index(fields=['national_id'], name='client_national_id_idx'),
            models.Index(fields=['tax_number'], name='client_tax_number_idx'),
        ]

class Supplier(TimeStampedModel):
    INDIVIDUAL = 'individual'
    COMPANY = 'company'
    BUSINESS_TYPE_CHOICES = [
        (INDIVIDUAL, _("Individual")),
        (COMPANY, _("Company")),
    ]

    PAYMENT_30_DAYS = '30_days'
    PAYMENT_60_DAYS = '60_days'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_30_DAYS, _("30 Days")),
        (PAYMENT_60_DAYS, _("60 Days")),
    ]

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    tax_number = models.CharField(max_length=50, verbose_name=_("Tax Number"))
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, default=COMPANY, verbose_name=_("Business Type"))
    address = models.TextField(verbose_name=_("Address"))
    supplier_code = models.CharField(max_length=50, unique=True, verbose_name=_("Supplier Code"))
    cooperation_start_date = models.DateField(null=True, blank=True, verbose_name=_("Cooperation Start Date"))
    cooperation_end_date = models.DateField(blank=True, null=True, verbose_name=_("Cooperation End Date"))
    website = models.URLField(blank=True, null=True, verbose_name=_("Website"))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_30_DAYS, verbose_name=_("Payment Method"))
    total_orders = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total Orders"))
    terms_and_conditions = models.TextField(blank=True, null=True, verbose_name=_("Terms and Conditions"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        indexes = [
            models.Index(fields=['name'], name='supplier_name_idx'),
            models.Index(fields=['supplier_code'], name='supplier_code_idx'),
            models.Index(fields=['tax_number'], name='supplier_tax_number_idx'),
        ]

class Product(TimeStampedModel):
    AMOUNT = 'amount'
    PERCENT = 'percent'
    TAX_TYPE_CHOICES = [
        (AMOUNT, _("Amount")),
        (PERCENT, _("Percent")),
    ]

    WHOLESALE = 'wholesale'
    RETAIL = 'retail'
    PRICE_TYPE_CHOICES = [
        (WHOLESALE, _("Wholesale")),
        (RETAIL, _("Retail")),
    ]

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Code"))
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name=_("QR Code"))
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Wholesale Price"))
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Retail Price"))
    tax_type = models.CharField(max_length=10, choices=TAX_TYPE_CHOICES, verbose_name=_("Tax Type"))
    tax_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Tax Value"))
    reorder_level = models.PositiveIntegerField(verbose_name=_("Reorder Level"))
    quantity_in_stock = models.PositiveIntegerField(default=0, verbose_name=_("Quantity in Stock"))
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name=_("Image"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name=_("Supplier"))

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        try:
            with transaction.atomic():
                if not self._state.adding:
                    old_instance = self.__class__.objects.get(pk=self.pk)
                    if not self.qr_code or self.name != old_instance.name or self.code != old_instance.code:
                        self.generate_qr_code()
                else:
                    if not self.qr_code:
                        self.generate_qr_code()
                super().save(*args, **kwargs)
        except IntegrityError as e:
            raise ValidationError(f"Error saving Product: {str(e)}")

    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"Product: {self.name}\nCode: {self.code}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer)
        filename = f'qr_code_{self.code}.png'
        self.qr_code.save(filename, File(buffer), save=False)

    @property
    def current_stock_status(self):
        if self.quantity_in_stock <= self.reorder_level:
            return _("Low Stock")
        return _("In Stock")

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        indexes = [
            models.Index(fields=['name'], name='product_name_idx'),
            models.Index(fields=['code'], name='product_code_idx'),
            models.Index(fields=['quantity_in_stock'], name='product_stock_idx'),
        ]

class Invoice(TimeStampedModel):
    PURCHASE = 'purchase'
    SALE = 'sale'
    INVOICE_TYPE_CHOICES = [
        (PURCHASE, _("Purchase")),
        (SALE, _("Sale")),
    ]

    PAID = 'paid'
    UNPAID = 'unpaid'
    PENDING = 'pending'
    PAYMENT_STATUS_CHOICES = [
        (PAID, _("Paid")),
        (UNPAID, _("Unpaid")),
        (PENDING, _("Pending")),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, verbose_name=_("Invoice Number"))
    invoice_date = models.DateField(default=timezone.now, verbose_name=_("Invoice Date"))
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPE_CHOICES, verbose_name=_("Invoice Type"))
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default=UNPAID, verbose_name=_("Payment Status"))
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name=_("Client"))
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name=_("Supplier"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False, verbose_name=_("Total Amount"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))

    def clean(self):
        if self.invoice_type == self.SALE and not self.client:
            raise ValidationError(_("Client is required for sales invoices"))
        if self.invoice_type == self.PURCHASE and not self.supplier:
            raise ValidationError(_("Supplier is required for purchase invoices"))

    def generate_invoice_number(self, prefix):
        max_attempts = 10
        for _ in range(max_attempts):
            invoice_number = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
            if not Invoice.objects.filter(invoice_number=invoice_number).exists():
                return invoice_number
        raise ValidationError(_("Could not generate a unique invoice number"))

    def save(self, *args, **kwargs):
        try:
            with transaction.atomic():
                if not self.invoice_number:
                    prefix = 'PUR' if self.invoice_type == self.PURCHASE else 'SAL'
                    self.invoice_number = self.generate_invoice_number(prefix)
                
                super().save(*args, **kwargs)

                if self.invoice_type == self.SALE and self.client:
                    self.client.num_of_invoices = self.client.invoices.count()
                    self.client.save()
                elif self.invoice_type == self.PURCHASE and self.supplier:
                    self.supplier.total_orders = self.supplier.invoices.aggregate(
                        total=Sum('total_amount')
                    )['total'] or 0
                    self.supplier.save()
        except IntegrityError as e:
            raise ValidationError(f"Error saving Invoice: {str(e)}")

    def __str__(self):
        return f"{self.invoice_number} - {self.get_invoice_type_display()}"

    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        indexes = [
            models.Index(fields=['invoice_number'], name='invoice_number_idx'),
            models.Index(fields=['invoice_date'], name='invoice_date_idx'),
        ]

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name=_("Invoice"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name=_("Quantity"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Price"))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Tax Amount"))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Discount"))
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name=_("Total"))

    def save(self, *args, **kwargs):
        try:
            with transaction.atomic():
                product = Product.objects.select_for_update().get(pk=self.product.pk)
                self.total = (self.price * self.quantity) + self.tax_amount - self.discount
                super().save(*args, **kwargs)

                if self.invoice.invoice_type == Invoice.PURCHASE:
                    product.quantity_in_stock += self.quantity
                elif self.invoice.invoice_type == Invoice.SALE:
                    product.quantity_in_stock -= self.quantity
                product.save()

                self.invoice.total_amount = self.invoice.items.aggregate(
                    total=Sum('total')
                )['total'] or 0
                self.invoice.save()
        except IntegrityError as e:
            raise ValidationError(f"Error saving InvoiceItem: {str(e)}")

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")

class Payment(TimeStampedModel):
    CASH = 'cash'
    CHECK = 'check'
    BANK_TRANSFER = 'bank_transfer'
    CREDIT_CARD = 'credit_card'
    PAYMENT_METHOD_CHOICES = [
        (CASH, _("Cash")),
        (CHECK, _("Check")),
        (BANK_TRANSFER, _("Bank Transfer")),
        (CREDIT_CARD, _("Credit Card")),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name=_("Invoice"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Amount"))
    payment_date = models.DateField(default=timezone.now, verbose_name=_("Payment Date"))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name=_("Payment Method"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))

    @property
    def remaining_amount(self):
        total_paid = self.invoice.payments.aggregate(total=Sum('amount'))['total'] or 0
        return self.invoice.total_amount - total_paid

    def save(self, *args, **kwargs):
        try:
            with transaction.atomic():
                super().save(*args, **kwargs)
                
                remaining = self.remaining_amount
                if remaining <= 0:
                    self.invoice.payment_status = Invoice.PAID
                elif self.invoice.payments.count() > 0:
                    self.invoice.payment_status = Invoice.PENDING
                else:
                    self.invoice.payment_status = Invoice.UNPAID
                self.invoice.save()
        except IntegrityError as e:
            raise ValidationError(f"Error saving Payment: {str(e)}")

    def __str__(self):
        return f"Payment of {self.amount} for {self.invoice}"

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        indexes = [
            models.Index(fields=['payment_date'], name='payment_date_idx'),
        ]

class DashboardStats(models.Model):
    class Meta:
        managed = False
        verbose_name = _("Dashboard Statistics")
        verbose_name_plural = _("Dashboard Statistics")