from io import BytesIO
import os
import textwrap

try:
    import qrcode
except ImportError:
    qrcode = None


def format_rupiah(amount):
    try:
        value = float(amount)
    except (TypeError, ValueError):
        value = 0.0
    return f"Rp {int(value):,}".replace(',', '.')


def _wrap_text(text, width=40):
    if not text:
        return ['']
    return textwrap.wrap(str(text), width=width)


def _load_font(name, size):
    try:
        from PIL import ImageFont
        return ImageFont.truetype(name, size)
    except Exception:
        from PIL import ImageFont
        return ImageFont.load_default()


def _draw_dashed_line(draw, x1, y, x2, dash_length=8, gap=6, fill='gray'):
    x = x1
    while x < x2:
        x_end = min(x + dash_length, x2)
        draw.line((x, y, x_end, y), fill=fill, width=1)
        x += dash_length + gap


def _draw_qr_placeholder(draw, x, y, size, block=12, fill='black'):
    step = size // block
    for row in range(block):
        for col in range(block):
            if (row + col) % 2 == 0:
                draw.rectangle([
                    x + col * step,
                    y + row * step,
                    x + (col + 1) * step - 2,
                    y + (row + 1) * step - 2,
                ], fill=fill)


def render_receipt_image(receipt_data):
    """Generate PNG bytes for a receipt image."""
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError('Pillow is required to render receipt images. Install Pillow in the virtual environment.') from exc

    merchant_name = receipt_data.get('merchant_name', os.getenv('MERCHANT_NAME', 'Laundry Berkah'))
    merchant_address = receipt_data.get('merchant_address', os.getenv('MERCHANT_ADDRESS', 'MFWQ+JW5, Sidorejo Lor, Sidorejo, Salatiga City, Central Java 50715'))
    merchant_phone = receipt_data.get('merchant_phone', os.getenv('MERCHANT_PHONE', '087786181427'))

    title_font = _load_font('arial.ttf', 36)
    subtitle_font = _load_font('arial.ttf', 18)
    label_font = _load_font('arial.ttf', 16)
    body_font = _load_font('arial.ttf', 16)
    small_font = _load_font('arial.ttf', 14)
    tiny_font = _load_font('arial.ttf', 12)

    padding = 32
    max_width = 820
    section_gap = 26

    detail_fields = [
        ('Order ID', receipt_data.get('nomor_transaksi', '-')),
        ('Nama Pelanggan', receipt_data.get('pelanggan_nama', '-')),
        ('Telepon', receipt_data.get('pelanggan_telepon', '-')),
        ('Tanggal Masuk', receipt_data.get('tanggal_masuk').strftime('%d %B %Y %H:%M') if receipt_data.get('tanggal_masuk') else '-'),
        ('Estimasi Selesai', receipt_data.get('tanggal_selesai_estimasi').strftime('%d %B %Y %H:%M') if receipt_data.get('tanggal_selesai_estimasi') else '-'),
        ('Status Pembayaran', receipt_data.get('status_pembayaran', '-')),
    ]

    items = receipt_data.get('detail_items', [])
    item_lines = []
    for item in items:
        item_name = item.get('nama', '-')
        quantity = item.get('kuantitas', 0)
        price = format_rupiah(item.get('harga', 0))
        subtotal = format_rupiah(item.get('subtotal', 0))
        item_lines.append((item_name, quantity, price, subtotal))

    header_height = 170
    detail_height = 190
    item_height = max(180, len(item_lines) * 48 + 80)
    summary_height = 170
    note_height = 90
    track_height = 208

    image_height = (
        padding
        + header_height
        + section_gap
        + detail_height
        + section_gap
        + item_height
        + section_gap
        + summary_height
        + section_gap
        + note_height
        + section_gap
        + track_height
        + padding
    )

    image = Image.new('RGB', (max_width, image_height), '#F8FAFC')
    draw = ImageDraw.Draw(image)

    current_y = padding

    header_rect = [padding, current_y, max_width - padding, current_y + header_height]
    draw.rounded_rectangle(header_rect, radius=30, fill='#FFFFFF')
    accent_bar = [header_rect[0], header_rect[1], header_rect[2], header_rect[1] + 18]
    draw.rectangle(accent_bar, fill='#1D4ED8')

    logo_box = [header_rect[0] + 26, header_rect[1] + 30, header_rect[0] + 110, header_rect[1] + 110]
    draw.rounded_rectangle(logo_box, radius=22, fill='#2563EB')
    draw.text((logo_box[0] + 42, logo_box[1] + 40), '🧺', fill='white', font=_load_font('arial.ttf', 40), anchor='mm')

    draw.text((logo_box[2] + 24, header_rect[1] + 40), merchant_name, fill='#0F172A', font=title_font)
    draw.text((logo_box[2] + 24, header_rect[1] + 90), 'Bukti pembayaran resmi Laundry Berkah', fill='#475569', font=subtitle_font)
    draw.text((logo_box[2] + 24, header_rect[1] + 124), merchant_address, fill='#64748B', font=small_font)
    draw.text((logo_box[2] + 24, header_rect[1] + 148), f'Telp: {merchant_phone}', fill='#64748B', font=small_font)

    current_y += header_height + section_gap

    detail_rect = [padding, current_y, max_width - padding, current_y + detail_height]
    draw.rounded_rectangle(detail_rect, radius=28, fill='#FFFFFF')
    draw.text((detail_rect[0] + 28, detail_rect[1] + 22), 'Informasi Pelanggan', fill='#0F172A', font=subtitle_font)

    card_width = (max_width - padding * 2 - 30) // 2
    card_height = 56
    for index, (label, value) in enumerate(detail_fields):
        col = index % 2
        row = index // 2
        x1 = detail_rect[0] + 28 + col * (card_width + 22)
        y1 = detail_rect[1] + 62 + row * (card_height + 12)
        x2 = x1 + card_width
        y2 = y1 + card_height
        draw.rounded_rectangle([x1, y1, x2, y2], radius=16, fill='#F8FAFC', outline='#E2E8F0')
        draw.text((x1 + 16, y1 + 10), label, fill='#64748B', font=tiny_font)
        draw.text((x1 + 16, y1 + 28), str(value), fill='#0F172A', font=body_font)

    current_y += detail_height + section_gap

    table_rect = [padding, current_y, max_width - padding, current_y + item_height]
    draw.rounded_rectangle(table_rect, radius=28, fill='#FFFFFF')
    draw.text((table_rect[0] + 28, table_rect[1] + 22), 'Detail Layanan', fill='#0F172A', font=subtitle_font)
    draw.text((table_rect[0] + 28, table_rect[1] + 52), 'Layanan', fill='#64748B', font=label_font)
    draw.text((table_rect[0] + 280, table_rect[1] + 52), 'Qty', fill='#64748B', font=label_font)
    draw.text((table_rect[0] + 370, table_rect[1] + 52), 'Harga', fill='#64748B', font=label_font)
    draw.text((table_rect[2] - 28, table_rect[1] + 52), 'Subtotal', fill='#64748B', font=label_font, anchor='rm')
    draw.line((table_rect[0] + 28, table_rect[1] + 80, table_rect[2] - 28, table_rect[1] + 80), fill='#E2E8F0', width=2)

    row_y = table_rect[1] + 100
    for name, qty, price, subtotal in item_lines:
        draw.text((table_rect[0] + 28, row_y), name, fill='#0F172A', font=body_font)
        draw.text((table_rect[0] + 280, row_y), str(qty), fill='#0F172A', font=body_font)
        draw.text((table_rect[0] + 370, row_y), price, fill='#0F172A', font=body_font)
        draw.text((table_rect[2] - 28, row_y), subtotal, fill='#0F172A', font=body_font, anchor='rm')
        row_y += 44

    if not item_lines:
        draw.text((table_rect[0] + 28, row_y), 'Tidak ada item terdaftar.', fill='#64748B', font=body_font)
        row_y += 40

    current_y += item_height + section_gap

    summary_rect = [padding, current_y, max_width - padding, current_y + summary_height]
    draw.rounded_rectangle(summary_rect, radius=28, fill='#ECFDF5')
    draw.text((summary_rect[0] + 28, summary_rect[1] + 22), 'Ringkasan Pembayaran', fill='#0F172A', font=subtitle_font)

    summary_values = [
        ('Total Harga', format_rupiah(receipt_data.get('total_harga', 0))),
        ('Bayar Sekarang', format_rupiah(receipt_data.get('jumlah_bayar', 0))),
        ('Sudah Dibayar', format_rupiah(receipt_data.get('total_paid', 0))),
        ('Sisa / Kurang', format_rupiah(receipt_data.get('kurang', 0))),
    ]
    value_y = summary_rect[1] + 68
    for label, value in summary_values:
        draw.text((summary_rect[0] + 28, value_y), label, fill='#475569', font=label_font)
        draw.text((summary_rect[2] - 28, value_y), value, fill='#0F172A', font=body_font, anchor='rm')
        value_y += 32

    current_y += summary_height + section_gap

    notes_rect = [padding, current_y, max_width - padding, current_y + note_height]
    draw.rounded_rectangle(notes_rect, radius=24, fill='#FFFFFF')
    draw.text((notes_rect[0] + 28, notes_rect[1] + 22), 'Catatan', fill='#0F172A', font=subtitle_font)
    draw.text((notes_rect[0] + 28, notes_rect[1] + 56), receipt_data.get('catatan', 'Tidak ada catatan tambahan.'), fill='#475569', font=small_font)

    current_y += note_height + section_gap

    track_rect = [padding, current_y, max_width - padding, current_y + track_height]
    draw.rounded_rectangle(track_rect, radius=28, fill='#FFFFFF')
    draw.text((track_rect[0] + 28, track_rect[1] + 22), 'Lacak Laundry', fill='#0F172A', font=subtitle_font)
    draw.text((track_rect[0] + 28, track_rect[1] + 58), 'Scan QR ini untuk melihat status proses laundry secara realtime.', fill='#64748B', font=small_font)

    if receipt_data.get('tracking_url'):
        draw.text((track_rect[0] + 28, track_rect[1] + 88), receipt_data.get('tracking_url'), fill='#2563EB', font=tiny_font)

    qr_size = 156
    qr_x = track_rect[2] - qr_size - 28
    qr_y = track_rect[1] + 26
    if qrcode and receipt_data.get('tracking_url'):
        qr = qrcode.QRCode(box_size=4, border=2)
        qr.add_data(receipt_data.get('tracking_url'))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color='black', back_color='white').convert('RGB')
        qr_img = qr_img.resize((qr_size, qr_size), resample=getattr(Image, 'Resampling', Image).NEAREST)
        image.paste(qr_img, (qr_x, qr_y))
    else:
        draw.rounded_rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], radius=22, outline='#E2E8F0', width=4)
        _draw_qr_placeholder(draw, qr_x + 16, qr_y + 16, qr_size - 32)

    output = BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output.read()
