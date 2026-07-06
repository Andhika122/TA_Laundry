from io import BytesIO
from fpdf import FPDF


def _format_currency(value):
    try:
        return f"Rp {int(value):,}".replace(',', '.')
    except Exception:
        return f"Rp {value}"


def generate_receipt_pdf(receipt_data):
    pdf = FPDF('P', 'mm', 'A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, receipt_data.get('merchant_name', 'Laundry Berkah'), ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, f"{receipt_data.get('merchant_address', '')} | Telp: {receipt_data.get('merchant_phone', '')}")
    pdf.ln(4)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Struk Pembayaran', ln=True)
    pdf.ln(2)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(55, 6, 'No. Struk:', border=0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, receipt_data.get('nomor_struk', '-'), ln=True)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(55, 6, 'Order ID:', border=0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, receipt_data.get('nomor_transaksi', '-'), ln=True)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(55, 6, 'Nama Pelanggan:', border=0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, receipt_data.get('pelanggan_nama', '-'), ln=True)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(55, 6, 'Telepon:', border=0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, receipt_data.get('pelanggan_telepon', '-'), ln=True)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(55, 6, 'Tanggal Masuk:', border=0)
    pdf.set_font('Arial', '', 10)
    tanggal_masuk = receipt_data.get('tanggal_masuk')
    pdf.cell(0, 6, tanggal_masuk.strftime('%d %B %Y %H:%M') if tanggal_masuk else '-', ln=True)
    pdf.ln(4)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(75, 8, 'Layanan', border=1)
    pdf.cell(25, 8, 'Qty', border=1, align='C')
    pdf.cell(45, 8, 'Harga', border=1, align='R')
    pdf.cell(45, 8, 'Subtotal', border=1, align='R', ln=True)
    pdf.set_font('Arial', '', 10)

    for item in receipt_data.get('detail_items', []):
        pdf.cell(75, 7, str(item.get('nama', '-'))[:30], border=1)
        pdf.cell(25, 7, str(item.get('kuantitas', 0)), border=1, align='C')
        pdf.cell(45, 7, _format_currency(item.get('harga', 0)), border=1, align='R')
        pdf.cell(45, 7, _format_currency(item.get('subtotal', 0)), border=1, align='R', ln=True)

    pdf.ln(6)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(100, 7, 'Ringkasan Pembayaran', ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 6, 'Total Harga', border=0)
    pdf.cell(0, 6, _format_currency(receipt_data.get('total_harga', 0)), ln=True, align='R')
    pdf.cell(90, 6, 'Bayar Sekarang', border=0)
    pdf.cell(0, 6, _format_currency(receipt_data.get('jumlah_bayar', 0)), ln=True, align='R')
    pdf.cell(90, 6, 'Sudah Dibayar', border=0)
    pdf.cell(0, 6, _format_currency(receipt_data.get('total_paid', 0)), ln=True, align='R')
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(90, 7, 'Sisa / Kurang', border=0)
    pdf.cell(0, 7, _format_currency(receipt_data.get('kurang', 0)), ln=True, align='R')

    pdf.ln(6)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, 'Catatan:', ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, receipt_data.get('catatan', 'Tidak ada catatan tambahan.'))

    tracking_url = receipt_data.get('tracking_url')
    if tracking_url:
        pdf.ln(4)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 6, 'Lacak Laundry:', ln=True)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, tracking_url)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return pdf_bytes
