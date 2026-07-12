import os
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import requests
from dotenv import dotenv_values


FONTE_ENV_FILE = Path(__file__).resolve().parents[2] / '.env'


def get_fonte_setting(name, legacy_name=None, default=''):
    """Read Fonte settings, refreshing the local development .env file."""
    value = os.getenv(name) or (os.getenv(legacy_name) if legacy_name else None)
    # In development, let a newly saved .env value replace any stale value
    # inherited by the already-running editor or terminal process.
    if os.getenv('FLASK_ENV', 'development').lower() != 'production' and not os.getenv('VERCEL'):
        file_value = dotenv_values(FONTE_ENV_FILE).get(name)
        if file_value:
            value = file_value
    return str(value or default).strip()


def normalize_phone(phone):
    if not phone:
        return None
    phone = re.sub(r'[^0-9]', '', str(phone))
    if phone.startswith('0'):
        return '62' + phone[1:]
    if phone.startswith('8'):
        return '62' + phone
    return phone


def normalize_fonte_api_url(api_url):
    if not api_url:
        return api_url
    parsed = urlparse(api_url)
    hostname = parsed.hostname or ''
    if hostname.endswith('fonte.id') or hostname.endswith('api.fonte.id'):
        parsed = parsed._replace(netloc='api.fonnte.com')
        if not parsed.path or parsed.path == '/':
            parsed = parsed._replace(path='/send')
    return urlunparse(parsed)


def get_fonte_api_url():
    raw_url = get_fonte_setting('FONTE_API_URL', 'FONTE_URL', 'https://api.fonnte.com/send')
    return normalize_fonte_api_url(raw_url)


def get_fonte_token():
    token = get_fonte_setting('FONTE_TOKEN', 'Token')
    # Avoid an invalid Authorization header when a token is pasted with
    # surrounding whitespace or quotes in the environment configuration.
    return token.strip().strip('"').strip("'")


def get_fonte_sender_number():
    return get_fonte_setting('FONTE_PHONE', 'nowa')


def is_fonte_configured():
    api_url = get_fonte_api_url()
    if not api_url or not get_fonte_token():
        return False
    # Fonnte selects the connected WhatsApp device from the token.  A sender
    # number is therefore not required and should not hide the send button.
    return is_fonnte_endpoint(api_url) or bool(get_fonte_sender_number())


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


def format_fonte_error(response, api_url):
    """Return a useful API error without exposing credentials or payload."""
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return f'Fonte API error: {response.status_code} {body}. Endpoint: {api_url}'


def fonnte_response_is_rejected(response):
    try:
        response_data = response.json()
    except ValueError:
        return False, None
    return isinstance(response_data, dict) and response_data.get('status') is False, response_data


def fonte_rejection_message(response_data):
    reason = response_data.get('reason') or response_data.get('detail') or response_data
    if 'unknown token' in str(reason).lower() or 'token invalid' in str(reason).lower():
        return 'Token Fonte tidak dikenali. Pastikan token terbaru tersimpan, lalu restart aplikasi/deploy ulang.'
    return f'Fonte menolak pengiriman: {reason}'


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

        if response.status_code not in {200, 201}:
            return False, format_fonte_error(response, api_url)

        # Fonnte can return HTTP 200 for a rejected request, with the actual
        # delivery result in its JSON ``status`` field.
        rejected, response_data = fonnte_response_is_rejected(response)
        if rejected:
            # Sending media needs a qualifying Fonnte package.  Fall back to
            # the receipt text so the customer still receives the notification.
            if is_fonnte_endpoint(api_url) and image_url:
                text_payload = build_fonnte_form_payload(receipt_data, to_phone=to_phone)
                text_response = requests.post(
                    api_url,
                    data=text_payload,
                    headers={'Authorization': get_fonte_token()},
                    timeout=20,
                )
                text_rejected, _ = fonnte_response_is_rejected(text_response)
                if text_response.status_code in {200, 201} and not text_rejected:
                    return True, 'Gambar struk tidak didukung, tetapi pesan teks berhasil dikirim.'
            return False, fonte_rejection_message(response_data)
        return True, response.text
    except Exception as exc:
        return False, f'Exception saat mengirim ke Fonte: {exc}. Endpoint: {api_url}'
