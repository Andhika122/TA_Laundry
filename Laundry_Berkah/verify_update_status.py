import os
import sys
import importlib
os.chdir(r'C:\Users\krist\OneDrive\Documents\Tugas Kampus\Tugas PA\laundry\Laundry_Berkah')
os.environ['FLASK_ENV'] = 'testing'
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
import app as app_module
importlib.reload(app_module)
app = app_module.create_app('testing')
from app.models import Pelanggan, Layanan, db
from app.transaksi.services import TransaksiService
from app.pembayaran.services import PembayaranService

with app.app_context():
    db.drop_all()
    db.create_all()
    pelanggan = Pelanggan(nama='Test', telepon='081300000000', alamat='X', status=True)
    db.session.add(pelanggan)
    db.session.flush()
    layanan = Layanan(nama='Cuci', harga=10000, durasi=2, durasi_unit='jam', kategori='Reguler', is_active=True)
    db.session.add(layanan)
    db.session.flush()
    transaksi = TransaksiService.create_transaksi(id_pelanggan=pelanggan.id_pelanggan, items=[{'id_layanan': layanan.id_layanan, 'kuantitas': 1}])
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Admin'
    resp = client.post(f'/transaksi/api/update-status-next/{transaksi.id_transaksi}')
    print(resp.status_code)
    print(resp.get_data(as_text=True))
