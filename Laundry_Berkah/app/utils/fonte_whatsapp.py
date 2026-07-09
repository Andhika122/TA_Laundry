import os
import re
from urllib.parse import urlparse

import requests


def normalize_phone(phone):
    if not phone:
        return None
    phone = re.sub(r'[^0-9]', '', str(phone))
    if phone.startswith('0'):
        return '62' + phone[1:]
    if phone.startswith('8'):
        return '62' + phone
    return phone


def get_fonte_api_url():
    return os.getenv('FONTE_API_URL', os.getenv('FONTE_URL', 'https://api.fonnte.com/send'))


def get_fonte_token():
    return os.getenv('FONTE_TOKEN') or os.getenv('Token')


def get_fonte_sender_number():
    return os.getenv('FONTE_PHONE') or os.getenv('nowa')


def is_fonte_configured():
    return bool(get_fonte_api_url() and get_fonte_token() and get_fonte_sender_number())


def build_fonte_payload(receipt_data, image_url=None, to_phone=None):
    phone = normalize_phone(to_phone or receipt_data.get('pelanggan_telepon'))
    if not phone:
        return None

    message_lines = [
        'Laundry Berkah - Struk Pembayaran',
        f"Order ID: {receipt_data.get('nomor_transaksi', '-')}",
        f"Pelanggan: {receipt_data.get('pelanggan_nama', '-')}",
        f"Total: Rp {int(receipt_data.get('total_harga', 0)):,}".replace(',', '.'),
        f"Dibayar: Rp {int(receipt_data.get('jumlah_bayar', 0)):,}".replace(',', '.'),
        f"Kurang: Rp {int(receipt_data.get('kurang', 0)):,}".replace(',', '.'),
    ]

    if image_url:
        message_lines.extend(['', 'Lihat Struk:', image_url])

    message_lines.append('')
    message_lines.append('Terima kasih telah menggunakan Laundry Berkah.')

    payload = {
        'token': get_fonte_token(),
        'to': phone,
        'sender': get_fonte_sender_number(),
        'message': '\n'.join(message_lines),
    }
    if image_url:
        payload['image'] = image_url
        payload['caption'] = 'Struk Pembayaran Laundry Berkah'
    return payload


def is_fonnte_endpoint(api_url):
    hostname = urlparse(api_url).hostname or ''
    return hostname.endswith('fonnte.com')


def build_fonnte_form_payload(receipt_data, image_url=None, to_phone=None):
    phone = normalize_phone(to_phone or receipt_data.get('pelanggan_telepon'))
    if not phone:
        return None

    message_lines = [
        'Laundry Berkah - Struk Pembayaran',
        f"Order ID: {receipt_data.get('nomor_transaksi', '-')}",
        f"Pelanggan: {receipt_data.get('pelanggan_nama', '-')}",
        f"Total: Rp {int(receipt_data.get('total_harga', 0)):,}".replace(',', '.'),
        f"Dibayar: Rp {int(receipt_data.get('jumlah_bayar', 0)):,}".replace(',', '.'),
        f"Kurang: Rp {int(receipt_data.get('kurang', 0)):,}".replace(',', '.'),
        '',
        'Terima kasih telah menggunakan Laundry Berkah.',
    ]

    payload = {
        'target': phone,
        'message': '\n'.join(message_lines),
    }
    if image_url:
        payload['url'] = image_url
        payload['filename'] = f"struk-{receipt_data.get('nomor_transaksi', 'laundry')}.png"
    return payload


def send_whatsapp_via_fonte(receipt_data, image_url=None, to_phone=None):
    if not is_fonte_configured():
        return False, 'Fonte WA API belum dikonfigurasi.'

    api_url = get_fonte_api_url()
    try:
        if is_fonnte_endpoint(api_url):
            payload = build_fonnte_form_payload(receipt_data, image_url=image_url, to_phone=to_phone)
            if payload is None:
                return False, 'Nomor WA pelanggan tidak valid.'
            response = requests.post(
                api_url,
                data=payload,
                headers={'Authorization': get_fonte_token()},
                timeout=20,
            )
        else:
            payload = build_fonte_payload(receipt_data, image_url=image_url, to_phone=to_phone)
            if payload is None:
                return False, 'Nomor WA pelanggan tidak valid.'
            response = requests.post(
                api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=20,
            )

        if response.status_code in {200, 201}:
            return True, response.text
        return False, f'Fonte API error: {response.status_code} {response.text}'
    except Exception as exc:
        return False, str(exc)
