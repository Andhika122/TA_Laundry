import os
from io import BytesIO

import cloudinary
import cloudinary.uploader


def is_cloudinary_configured():
    return all([
        os.getenv('CLOUDINARY_CLOUD_NAME'),
        os.getenv('CLOUDINARY_API_KEY'),
        os.getenv('CLOUDINARY_API_SECRET'),
    ])


def configure_cloudinary():
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        secure=True,
    )


def upload_image_bytes(image_bytes, public_id=None, folder='laundry_struk'):
    """Upload PNG bytes to Cloudinary and return secure URL."""
    if not is_cloudinary_configured():
        return None

    configure_cloudinary()
    try:
        fileobj = BytesIO(image_bytes)
        result = cloudinary.uploader.upload(
            fileobj,
            resource_type='image',
            public_id=public_id,
            folder=folder,
            overwrite=True,
            format='png',
        )
        return result.get('secure_url')
    except Exception:
        return None
