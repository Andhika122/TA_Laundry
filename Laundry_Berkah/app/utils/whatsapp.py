import re
from urllib.parse import quote


def normalize_phone(phone):
    if not phone:
        return None

    phone_str = re.sub(r'[^0-9]', '', str(phone))
    if not phone_str:
        return None

    if phone_str.startswith('0'):
        return '62' + phone_str[1:]
    if phone_str.startswith('8'):
        return '62' + phone_str
    return phone_str


def build_whatsapp_chat_url(phone, message=None):
    normalized = normalize_phone(phone)
    if not normalized:
        return None

    if message:
        return f'https://wa.me/{normalized}?text={quote(message)}'
    return f'https://wa.me/{normalized}'
