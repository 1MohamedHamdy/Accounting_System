import io
import pandas as pd
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from .models import Invoice, MonthlyReportExport
import qrcode
from io import BytesIO
from django.core.files.base import Conte

def generate_invoice_report(report_type='sales'):
    invoices = Invoice.objects.filter(type=report_type)
    data = []
    for invoice in invoices:
        for line in invoice.lines.all():
            data.append({
                "Invoice No": invoice.invoice_number,
                "Date": invoice.invoice_date,
                "Status": invoice.status,
                "Product": line.product.item_name,
                "Quantity": line.quantity,
                "Price": line.price,
                "Total": line.total_line_amount
            })

    df = pd.DataFrame(data)
    file_buffer = io.BytesIO()
    df.to_excel(file_buffer, index=False)
    file_buffer.seek(0)

    filename = f"reports/{report_type}_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    saved_path = default_storage.save(filename, ContentFile(file_buffer.read()))

    return MonthlyReportExport.objects.create(
        export_type=report_type,
        file=saved_path
    )
    
def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return ContentFile(buffer.read())

