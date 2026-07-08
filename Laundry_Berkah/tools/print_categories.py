from app import create_app
from app.layanan.services import LayananService

app = create_app('development')
with app.app_context():
    try:
        cats = LayananService.get_kategori_list()
        print('CATEGORIES:', cats)
    except Exception as e:
        print('ERROR:', e)
