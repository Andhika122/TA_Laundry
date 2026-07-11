import os
import base64
from io import BytesIO

import cloudinary
import cloudinary.uploader


class CloudinaryUploadError(RuntimeError):
    """Raised when a receipt image cannot be uploaded to Cloudinary."""


def missing_cloudinary_config():
    required = [
        'CLOUDINARY_CLOUD_NAME',
        'CLOUDINARY_API_KEY',
        'CLOUDINARY_API_SECRET',
    ]
    return [name for name in required if not os.getenv(name)]


def is_cloudinary_configured():
    return not missing_cloudinary_config()


def configure_cloudinary():
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        secure=True,
    )


def upload_image_bytes_or_raise(image_bytes, public_id=None, folder='laundry_struk'):
    """Upload PNG bytes to Cloudinary and return secure URL, or raise a clear error."""
    if not is_cloudinary_configured():
        missing = ', '.join(missing_cloudinary_config())
        raise CloudinaryUploadError(f'Konfigurasi Cloudinary belum lengkap: {missing}.')

    if not image_bytes:
        raise CloudinaryUploadError('Data gambar struk kosong.')

    configure_cloudinary()

    upload_options = {
        'resource_type': 'image',
        'public_id': public_id,
        'folder': folder,
        'overwrite': True,
        'invalidate': True,
        'format': 'png',
    }

    try:
        fileobj = BytesIO(image_bytes)
        fileobj.name = 'struk.png'
        fileobj.seek(0)
        result = cloudinary.uploader.upload(
            fileobj,
            **upload_options,
        )
    except Exception as first_error:
        try:
            encoded = base64.b64encode(image_bytes).decode('ascii')
            result = cloudinary.uploader.upload(
                f'data:image/png;base64,{encoded}',
                **upload_options,
            )
        except Exception as second_error:
            raise CloudinaryUploadError(
                f'Upload ke Cloudinary gagal: {first_error}. Fallback base64 juga gagal: {second_error}.'
            ) from second_error

    secure_url = result.get('secure_url')
    if not secure_url:
        raise CloudinaryUploadError('Cloudinary tidak mengembalikan secure_url.')

    return secure_url


def upload_image_bytes(image_bytes, public_id=None, folder='laundry_struk'):
    """Upload PNG bytes to Cloudinary and return secure URL."""
    try:
        return upload_image_bytes_or_raise(image_bytes, public_id=public_id, folder=folder)
    except CloudinaryUploadError:
        return None
