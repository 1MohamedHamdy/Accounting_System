# # core/custom_admin.py

# from django.contrib.admin import AdminSite
# from django.utils.translation import gettext_lazy as _
# from django.utils.safestring import mark_safe
# from django.utils import timezone
# from django.db.models.functions import TruncMonth
# from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q

# from .models import Invoice, Client, InvoiceItem

# class CustomAdminSite(AdminSite):
#     site_header = _("Accounting Admin")
#     index_template = "admin/index.html"

#     def each_context(self, request):
#         context = super().each_context(request)

#         today = timezone.now().date()

#         # Calculate today's total sales from InvoiceLines of sales invoices with today's date
#         today_sales = InvoiceLine.objects.filter(
#             invoice__invoice_date=today,
#             invoice__invoice_type=Invoice.SALES
#         ).annotate(
#             line_total=ExpressionWrapper(
#                 (F('price') * F('quantity') - F('discount')) + 
#                 (  # tax calculation based on tax_type
#                     (F('product__tax_value') * F('quantity')) if F('product__tax_type') == 'amount' else 
#                     ((F('price') * F('quantity') - F('discount')) * (F('product__tax_value') / 100))
#                 ),
#                 output_field=DecimalField(max_digits=20, decimal_places=2)
#             )
#         ).aggregate(total=Sum('line_total'))['total'] or 0

#         context['today_sales'] = f"{today_sales:.2f} EGP"

#         # Calculate top clients by total sales amount
#         # Sum InvoiceLine totals for invoices of type sales, grouped by client
#         top_clients = (
#             Client.objects.annotate(
#                 total=Sum(
#                     ExpressionWrapper(
#                         (F('invoice__lines__price') * F('invoice__lines__quantity') - F('invoice__lines__discount')) +
#                         # tax logic (same as above)
#                         ((F('invoice__lines__product__tax_value') * F('invoice__lines__quantity')) if F('invoice__lines__product__tax_type') == 'amount' else
#                          ((F('invoice__lines__price') * F('invoice__lines__quantity') - F('invoice__lines__discount')) * (F('invoice__lines__product__tax_value') / 100))),
#                         output_field=DecimalField(max_digits=20, decimal_places=2)
#                     ),
#                     filter=Q(invoice__invoice_type=Invoice.SALES),
#                 )
#             )
#             .order_by('-total')[:5]
#         )

#         rows = "".join(
#             f"<tr><td>{client.name}</td><td>{client.total or 0:.2f} EGP</td></tr>" for client in top_clients
#         )
#         context['top_clients'] = mark_safe(f"""
#             <table style="width:100%; border-collapse: collapse;" border="1">
#                 <thead><tr><th>Client</th><th>Total</th></tr></thead>
#                 <tbody>{rows}</tbody>
#             </table>
#         """)

#         # Monthly sales aggregation for chart
#         sales = (
#             InvoiceLine.objects
#             .filter(invoice__invoice_type=Invoice.SALES)
#             .annotate(month=TruncMonth('invoice__invoice_date'))
#             .values('month')
#             .annotate(
#                 total=Sum(
#                     ExpressionWrapper(
#                         (F('price') * F('quantity') - F('discount')) +
#                         ((F('product__tax_value') * F('quantity')) if F('product__tax_type') == 'amount' else
#                          ((F('price') * F('quantity') - F('discount')) * (F('product__tax_value') / 100))),
#                         output_field=DecimalField(max_digits=20, decimal_places=2)
#                     )
#                 )
#             )
#             .order_by('month')
#         )

#         labels = [s['month'].strftime('%b %Y') for s in sales if s['month'] is not None]
#         data = [float(s['total']) for s in sales if s['month'] is not None]

#         context['sales_chart'] = mark_safe(f"""
#             <canvas id="salesChart" width="400" height="200"></canvas>
#             <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
#             <script>
#             new Chart(document.getElementById('salesChart').getContext('2d'), {{
#                 type: 'bar',
#                 data: {{
#                     labels: {labels},
#                     datasets: [{{
#                         label: 'Monthly Sales',
#                         data: {data},
#                         backgroundColor: 'rgba(75, 192, 192, 0.6)'
#                     }}]
#                 }},
#                 options: {{
#                     responsive: true,
#                     scales: {{
#                         y: {{
#                             beginAtZero: true
#                         }}
#                     }}
#                 }}
#             }});
#             </script>
#         """)

#         return context
