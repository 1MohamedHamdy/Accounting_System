from rest_framework import serializers
from .models import (
    Client, ClientPhoneNumber, Supplier, SupplierPhoneNumber,
    Product, Invoice, InvoiceItem, Payment
)


class ClientPhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientPhoneNumber
        fields = ['id', 'number', 'description']


class ClientSerializer(serializers.ModelSerializer):
    phone_numbers = ClientPhoneNumberSerializer(many=True, required=False)
    business_type_display = serializers.CharField(
        source='get_business_type_display', read_only=True)

    class Meta:
        model = Client
        fields = [
            'id', 'name', 'business_type', 'business_type_display',
            'national_id', 'tax_number', 'address', 'num_of_invoices',
            'phone_numbers', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        phone_numbers_data = validated_data.pop('phone_numbers', [])
        client = Client.objects.create(**validated_data)
        for phone_data in phone_numbers_data:
            ClientPhoneNumber.objects.create(client=client, **phone_data)
        return client

    def update(self, instance, validated_data):
        phone_numbers_data = validated_data.pop('phone_numbers', [])
        
        # Update client fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle phone numbers
        if phone_numbers_data is not None:
            current_phones = instance.phone_numbers.all()
            current_phones.delete()
            for phone_data in phone_numbers_data:
                ClientPhoneNumber.objects.create(client=instance, **phone_data)
        
        return instance


class SupplierPhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPhoneNumber
        fields = ['id', 'number', 'description', 'is_main']


class SupplierSerializer(serializers.ModelSerializer):
    phone_numbers = SupplierPhoneNumberSerializer(many=True, required=False)
    business_type_display = serializers.CharField(
        source='get_business_type_display', read_only=True)
    payment_terms_display = serializers.CharField(
        source='get_payment_terms_display', read_only=True)

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'tax_number', 'business_type', 'business_type_display',
            'address', 'supplier_code', 'cooperation_start_date',
            'cooperation_end_date', 'website', 'payment_terms',
            'payment_terms_display', 'total_orders', 'terms_and_conditions',
            'phone_numbers', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        phone_numbers_data = validated_data.pop('phone_numbers', [])
        supplier = Supplier.objects.create(**validated_data)
        for phone_data in phone_numbers_data:
            SupplierPhoneNumber.objects.create(supplier=supplier, **phone_data)
        return supplier

    def update(self, instance, validated_data):
        phone_numbers_data = validated_data.pop('phone_numbers', [])
        
        # Update supplier fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle phone numbers
        if phone_numbers_data is not None:
            current_phones = instance.phone_numbers.all()
            current_phones.delete()
            for phone_data in phone_numbers_data:
                SupplierPhoneNumber.objects.create(supplier=instance, **phone_data)
        
        return instance


class ProductSerializer(serializers.ModelSerializer):
    tax_type_display = serializers.CharField(
        source='get_tax_type_display', read_only=True)
    price_type_display = serializers.CharField(
        source='get_price_type_display', read_only=True)
    supplier_name = serializers.CharField(
        source='supplier.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'code', 'qr_code', 'price', 'price_type',
            'price_type_display', 'tax_type', 'tax_type_display', 'tax_value',
            'reorder_level', 'image', 'description', 'supplier', 'supplier_name',
            'quantity_in_stock', 'created_at', 'updated_at'
        ]


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'product', 'product_name', 'product_code', 'quantity',
            'unit_price', 'tax_amount', 'discount', 'description', 'total'
        ]

    def get_total(self, obj):
        return (obj.quantity * obj.unit_price) + obj.tax_amount - obj.discount


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, required=False)
    invoice_type_display = serializers.CharField(
        source='get_invoice_type_display', read_only=True)
    payment_status_display = serializers.CharField(
        source='get_payment_status_display', read_only=True)
    client_name = serializers.CharField(
        source='client.name', read_only=True)
    supplier_name = serializers.CharField(
        source='supplier.name', read_only=True)
    payments = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'invoice_date', 'invoice_type',
            'invoice_type_display', 'payment_status', 'payment_status_display',
            'supplier', 'supplier_name', 'client', 'client_name', 'total_amount',
            'notes', 'items', 'payments', 'created_at', 'updated_at'
        ]

    def get_payments(self, obj):
        payments = obj.payment_set.all()
        return PaymentSerializer(payments, many=True).data

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        invoice = Invoice.objects.create(**validated_data)
        
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        
        invoice.calculate_total()
        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        
        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle items
        if items_data is not None:
            current_items = instance.items.all()
            current_items.delete()
            for item_data in items_data:
                InvoiceItem.objects.create(invoice=instance, **item_data)
        
        instance.calculate_total()
        return instance


class PaymentSerializer(serializers.ModelSerializer):
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True)
    remaining_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'amount', 'payment_date', 'payment_method',
            'payment_method_display', 'notes', 'remaining_amount',
            'created_at', 'updated_at'
        ]