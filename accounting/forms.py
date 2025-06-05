from django import forms
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from .models import Client, ClientPhoneNumber, Supplier, SupplierPhoneNumber, Product, Invoice, Payment, InvoiceItem

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'business_type', 'address', 'national_id', 'tax_number', 'num_of_invoices']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('Enter client name')}),
            'business_type': forms.Select(attrs={'class': 'filter-input'}),
            'address': forms.Textarea(attrs={'class': 'filter-input', 'rows': 4, 'placeholder': _('Enter address')}),
            'national_id': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('Enter national ID')}),
            'tax_number': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('Enter tax number')}),
            'num_of_invoices': forms.NumberInput(attrs={'class': 'filter-input', 'placeholder': _('Enter number of invoices')}),
        }

    def clean(self):
        cleaned_data = super().clean()
        business_type = cleaned_data.get('business_type')
        national_id = cleaned_data.get('national_id')
        tax_number = cleaned_data.get('tax_number')

        if business_type == Client.INDIVIDUAL and not national_id:
            raise forms.ValidationError(_("National ID is required for individual clients"))
        if business_type == Client.COMPANY and not tax_number:
            raise forms.ValidationError(_("Tax number is required for company clients"))
        return cleaned_data

class ClientPhoneNumberForm(forms.ModelForm):
    class Meta:
        model = ClientPhoneNumber
        fields = ['number', 'description']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('Enter phone number')}),
            'description': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('e.g., Main contact')}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'supplier_code', 'business_type', 'tax_number', 'address', 'cooperation_start_date', 'cooperation_end_date', 'website', 'payment_method', 'terms_and_conditions', 'total_orders']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('Enter supplier name')}),
            'supplier_code': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('Enter supplier code')}),
            'business_type': forms.Select(attrs={'class': 'filter-input'}),
            'tax_number': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('Enter tax number')}),
            'address': forms.Textarea(attrs={'class': 'filter-input', 'rows': 4, 'placeholder': _('Enter address')}),
            'cooperation_start_date': forms.DateInput(attrs={'class': 'filter-input', 'type': 'date'}),
            'cooperation_end_date': forms.DateInput(attrs={'class': 'filter-input', 'type': 'date'}),
            'website': forms.URLInput(attrs={'class': 'filter-input', 'placeholder': _('Enter website URL')}),
            'payment_method': forms.Select(attrs={'class': 'filter-input'}),
            'terms_and_conditions': forms.Textarea(attrs={'class': 'filter-input', 'rows': 4, 'placeholder': _('Enter terms and conditions')}),
            'total_orders': forms.NumberInput(attrs={'class': 'filter-input', 'placeholder': _('Enter total orders')}),  # Corrected line
        }

class SupplierPhoneNumberForm(forms.ModelForm):
    class Meta:
        model = SupplierPhoneNumber
        fields = ['number', 'description', 'is_main']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('Enter phone number')}),
            'description': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('e.g., Main contact')}),
            'is_main': forms.CheckboxInput(attrs={'class': 'filter-input'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'code', 'wholesale_price', 'retail_price', 'tax_type', 'tax_value', 'reorder_level', 'quantity_in_stock', 'image', 'description', 'supplier', 'qr_code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('Enter product name')}),
            'code': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('Enter product code')}),
            'wholesale_price': forms.NumberInput(attrs={'class': 'filter-input', 'placeholder': _('Enter wholesale price'), 'step': '0.01'}),
            'retail_price': forms.NumberInput(attrs={'class': 'filter-input', 'placeholder': _('Enter retail price'), 'step': '0.01'}),
            'tax_type': forms.Select(attrs={'class': 'filter-input'}),
            'tax_value': forms.NumberInput(attrs={'class': 'filter-input', 'placeholder': _('Enter tax value'), 'step': '0.01'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'filter-input', 'placeholder': _('Enter reorder level')}),
            'quantity_in_stock': forms.NumberInput(attrs={'class': 'filter-input', 'placeholder': _('Enter quantity in stock')}),
            'image': forms.FileInput(attrs={'class': 'filter-input'}),
            'description': forms.Textarea(attrs={'class': 'filter-input', 'rows': 4, 'placeholder': _('Enter description')}),
            'supplier': forms.Select(attrs={'class': 'filter-input'}),
            'qr_code': forms.FileInput(attrs={'class': 'filter-input'}),
        }

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'invoice_date', 'invoice_type', 'payment_status', 'client', 'supplier', 'notes']
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'filter-input', 'placeholder': _('Enter invoice number')}),
            'invoice_date': forms.DateInput(attrs={'class': 'filter-input', 'type': 'date'}),
            'invoice_type': forms.Select(attrs={'class': 'filter-input'}),
            'payment_status': forms.Select(attrs={'class': 'filter-input'}),
            'client': forms.Select(attrs={'class': 'filter-input'}),
            'supplier': forms.Select(attrs={'class': 'filter-input'}),
            'notes': forms.Textarea(attrs={'class': 'filter-input', 'rows': 4, 'placeholder': _('Enter notes')}),
        }

    def clean(self):
        cleaned_data = super().clean()
        invoice_type = cleaned_data.get('invoice_type')
        client = cleaned_data.get('client')
        supplier = cleaned_data.get('supplier')

        if invoice_type == Invoice.SALE and not client:
            raise forms.ValidationError(_("Client is required for sales invoices"))
        if invoice_type == Invoice.PURCHASE and not supplier:
            raise forms.ValidationError(_("Supplier is required for purchase invoices"))
        return cleaned_data

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'price', 'tax_amount', 'discount']
        widgets = {
            'product': forms.Select(attrs={'class': 'filter-input'}),
            'quantity': forms.NumberInput(attrs={'class': 'filter-input', 'min': 1}),
            'price': forms.NumberInput(attrs={'class': 'filter-input', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'filter-input', 'step': '0.01'}),
            'discount': forms.NumberInput(attrs={'class': 'filter-input', 'step': '0.01'}),
        }

class PaymentForm(forms.ModelForm):
    # Add remaining_amount as a form field, not a model field
    remaining_amount = forms.DecimalField(
        label=_("Remaining Amount"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'filter-input', 'readonly': 'readonly'}),
    )

    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'payment_date', 'payment_method', 'notes']  # Remove remaining_amount
        widgets = {
            'invoice': forms.Select(attrs={'class': 'filter-input'}),
            'amount': forms.NumberInput(attrs={'class': 'filter-input', 'placeholder': _('Enter amount'), 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'filter-input', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'filter-input'}),
            'notes': forms.Textarea(attrs={'class': 'filter-input', 'rows': 4, 'placeholder': _('Enter notes')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value for remaining_amount based on invoice and existing payments
        if self.instance and self.instance.pk:
            self.fields['remaining_amount'].initial = self.instance.remaining_amount
        elif self.data.get('invoice'):
            try:
                invoice = Payment._meta.get_field('invoice').remote_field.model.objects.get(pk=self.data.get('invoice'))
                total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or 0
                self.fields['remaining_amount'].initial = invoice.total_amount - total_paid
            except (ValueError, Payment._meta.get_field('invoice').remote_field.model.DoesNotExist):
                self.fields['remaining_amount'].initial = 0

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Since remaining_amount is a property, we don't need to set it on the instance
        if commit:
            instance.save()
        return instance