import os
import importlib
import sys
from datetime import datetime, timedelta


def test_promo_only_applies_when_active_and_caps_nominal_discount(app):
    with app.app_context():
        from app.models import Promo, utc_now

        promo = Promo(
            nama='Diskon Nominal',
            tipe='nominal',
            nilai=50000,
            minimal_transaksi=10000,
            tanggal_mulai=utc_now() - timedelta(minutes=1),
            is_active=True,
        )

        assert promo.calculate_discount(9000) == 0.0
        assert promo.calculate_discount(20000) == 20000.0

        promo.is_active = False
        assert promo.calculate_discount(20000) == 0.0
def test_create_payment_for_transaction():
    os.environ['FLASK_ENV'] = 'testing'
    os.environ.pop('USE_SQLITE_FALLBACK', None)
    sys.path.insert(0, os.getcwd())

    import app as app_module
    app_module = importlib.reload(app_module)
    app = app_module.create_app('testing')

    with app.app_context():
        from app.models import Pelanggan, Layanan, db
        from app.transaksi.services import TransaksiService
        from app.pembayaran.services import PembayaranService

        pelanggan = Pelanggan(nama='Test Payment', telepon='0813', alamat='Y', status=True)
        db.session.add(pelanggan)
        db.session.flush()

        layanan = Layanan(
            nama='Cuci Cepat',
            harga=12000,
            durasi=2,
            durasi_unit='jam',
            kategori='Reguler',
            is_active=True,
        )
        db.session.add(layanan)
        db.session.flush()

        transaksi = TransaksiService.create_transaksi(
            id_pelanggan=pelanggan.id_pelanggan,
            items=[{'id_layanan': layanan.id_layanan, 'kuantitas': 1}],
        )

        assert transaksi is not None

        pembayaran = PembayaranService.create_pembayaran(
            id_transaksi=transaksi.id_transaksi,
            jumlah=12000,
            metode_pembayaran='Cash',
            catatan='ok',
        )

        assert pembayaran is not None
        assert pembayaran.status_pembayaran == 'Lunas'


def test_update_status_to_next_workflow():
    os.environ['FLASK_ENV'] = 'testing'
    os.environ.pop('USE_SQLITE_FALLBACK', None)
    sys.path.insert(0, os.getcwd())

    import app as app_module
    app_module = importlib.reload(app_module)
    app = app_module.create_app('testing')

    with app.app_context():
        from app.models import Pelanggan, Layanan, db
        from app.transaksi.services import TransaksiService

        pelanggan = Pelanggan(nama='Test Flow', telepon='0814', alamat='Y', status=True)
        db.session.add(pelanggan)
        db.session.flush()

        layanan = Layanan(
            nama='Cuci Reguler',
            harga=15000,
            durasi=3,
            durasi_unit='jam',
            kategori='Reguler',
            is_active=True,
        )
        db.session.add(layanan)
        db.session.flush()

        transaksi = TransaksiService.create_transaksi(
            id_pelanggan=pelanggan.id_pelanggan,
            items=[{'id_layanan': layanan.id_layanan, 'kuantitas': 1}],
        )

        assert transaksi is not None
        assert transaksi.status_proses == 'Antrian'

        transaksi = TransaksiService.update_status_to_next(transaksi.id_transaksi)
        assert transaksi.status_proses == 'Cuci'

        transaksi = TransaksiService.update_status_to_next(transaksi.id_transaksi)
        assert transaksi.status_proses == 'Pengeringan'

        transaksi = TransaksiService.update_status_to_next(transaksi.id_transaksi)
        assert transaksi.status_proses == 'Setrika'

        transaksi = TransaksiService.update_status_to_next(transaksi.id_transaksi)
        assert transaksi.status_proses == 'Packing'

        transaksi = TransaksiService.update_status_to_next(transaksi.id_transaksi)
        assert transaksi.status_proses == 'Siap Ambil'

        transaksi_next = TransaksiService.update_status_to_next(transaksi.id_transaksi)
        assert transaksi_next is None


def test_create_transaction_with_parfum_and_promo_and_receipt_data():
    os.environ['FLASK_ENV'] = 'testing'
    os.environ.pop('USE_SQLITE_FALLBACK', None)
    sys.path.insert(0, os.getcwd())

    import app as app_module
    app_module = importlib.reload(app_module)
    app = app_module.create_app('testing')

    with app.app_context():
        from app.models import Pelanggan, Layanan, Promo, Parfum, db
        from app.pembayaran.services import PembayaranService
        from app.transaksi.services import TransaksiService
        from datetime import datetime

        pelanggan = Pelanggan(nama='Test Parfum', telepon='081500000000', alamat='Alamat Test', status=True)
        db.session.add(pelanggan)
        db.session.flush()

        layanan = Layanan(
            nama='Cuci Premium',
            harga=10000,
            durasi=2,
            durasi_unit='jam',
            kategori='Premium',
            is_active=True,
        )
        db.session.add(layanan)

        parfum = Parfum(
            nama='Lavender',
            deskripsi='Parfum Lavender',
            harga_tambahan=2000,
            is_active=True,
        )
        db.session.add(parfum)

        promo = Promo(
            nama='Diskon 10%',
            deskripsi='Promo uji coba',
            tipe='persentase',
            nilai=10,
            minimal_transaksi=5000,
            tanggal_mulai=datetime.now(),
            tanggal_akhir=None,
            is_active=True,
        )
        db.session.add(promo)
        db.session.flush()

        transaksi = TransaksiService.create_transaksi(
            id_pelanggan=pelanggan.id_pelanggan,
            items=[{'id_layanan': layanan.id_layanan, 'kuantitas': 1, 'id_parfum': parfum.id_parfum}],
            promo_id=promo.id_promo,
        )

        assert transaksi is not None
        assert float(transaksi.total_harga) == 10800.0
        assert transaksi.promo_id == promo.id_promo
        assert transaksi.detail_transaksi
        assert transaksi.detail_transaksi[0].id_parfum == parfum.id_parfum
        assert float(transaksi.detail_transaksi[0].harga_parfum) == 2000.0

        receipt_data = PembayaranService.generate_receipt_data_for_transaksi(transaksi.id_transaksi)
        assert receipt_data is not None
        assert receipt_data['parfum'] == 'Lavender'
        assert receipt_data['promo_id'] == promo.id_promo
        assert receipt_data['promo_nama'] == 'Diskon 10%'
        assert receipt_data['diskon'] == 1200.0
        assert receipt_data['detail_items'][0]['parfum'] == 'Lavender'
        assert receipt_data['total_harga'] == 10800.0


def test_transaction_with_promo_and_parfum_can_view_struk(client):
    # Login as admin to get access to transaction and receipt routes
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data or b'Logout' in response.data

    with client.application.app_context():
        from app.models import Pelanggan, Layanan, Parfum, Promo, Transaksi, db

        pelanggan = Pelanggan(nama='Test Struk', telepon='081500000001', alamat='Alamat Struk', status=True)
        db.session.add(pelanggan)
        layanan = Layanan(
            nama='Cuci Premium',
            harga=10000,
            durasi=2,
            durasi_unit='jam',
            kategori='Premium',
            is_active=True,
        )
        db.session.add(layanan)
        parfum = Parfum(
            nama='Lavender',
            deskripsi='Parfum Lavender',
            harga_tambahan=2000,
            is_active=True,
        )
        promo = Promo(
            nama='Diskon 10%',
            deskripsi='Promo uji coba',
            tipe='persentase',
            nilai=10,
            minimal_transaksi=5000,
            tanggal_mulai=datetime.now(),
            tanggal_akhir=None,
            is_active=True,
        )
        db.session.add(parfum)
        db.session.add(promo)
        db.session.commit()

        layanan = Layanan.query.filter_by(nama='Cuci Premium').first()
        assert layanan is not None
        id_pelanggan = pelanggan.id_pelanggan
        id_parfum = parfum.id_parfum
        id_promo = promo.id_promo

    response = client.post(
        '/transaksi/baru',
        data={
            'id_pelanggan': id_pelanggan,
            'catatan': 'Test transaksi promo parfum',
            'promo_id': id_promo,
            'layanan[]': [layanan.id_layanan],
            'kuantitas[]': [1],
            'parfum[]': [id_parfum],
            'payment_option': 'pay_later',
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b'Transaksi berhasil dibuat' in response.data

    with client.application.app_context():
        transaksi = Transaksi.query.order_by(Transaksi.id_transaksi.desc()).first()
        assert transaksi is not None
        assert transaksi.promo_id == id_promo
        assert float(transaksi.total_harga) == 10800.0

    response = client.get(f'/pembayaran/struk/transaksi/{transaksi.id_transaksi}')
    assert response.status_code == 200
    assert b'Lavender' in response.data
    assert b'Parfum' in response.data
    assert b'Rp 10.800' in response.data


def test_cancel_transaction_removes_related_data_and_excludes_from_laporan(client):
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert response.status_code == 200

    with client.application.app_context():
        from app.models import Pelanggan, Layanan, Transaksi, db
        from app.transaksi.services import TransaksiService

        pelanggan = Pelanggan(nama='Test Cancel', telepon='081500000003', alamat='Alamat Cancel', status=True)
        layanan = Layanan(
            nama='Cuci Kilo 2',
            harga=8000,
            durasi=1,
            durasi_unit='hari',
            kategori='Reguler',
            is_active=True,
        )
        db.session.add_all([pelanggan, layanan])
        db.session.commit()

        transaksi = TransaksiService.create_transaksi(
            id_pelanggan=pelanggan.id_pelanggan,
            items=[{'id_layanan': layanan.id_layanan, 'kuantitas': 2}],
        )
        assert transaksi is not None
        transaksi_id = transaksi.id_transaksi
        assert db.session.get(Transaksi, transaksi_id) is not None

    response = client.post(f'/transaksi/cancel/{transaksi_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Transaksi berhasil dibatalkan' in response.data

    with client.application.app_context():
        assert db.session.get(Transaksi, transaksi_id) is None

    response = client.get('/laporan/')
    assert response.status_code == 200
    assert b'Rp 0' in response.data


def test_laporan_export_pdf_returns_ok_when_no_transactions(client):
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert response.status_code == 200

    response = client.get('/laporan/export?format=pdf', follow_redirects=True)
    assert response.status_code == 200
    assert response.headers.get('Content-Type', '').startswith('application/pdf')


def test_cancel_transaction_removes_data_and_excludes_from_laporan(client):
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert response.status_code == 200

    with client.application.app_context():
        from app.models import Pelanggan, Layanan, Transaksi, db
        from app.transaksi.services import TransaksiService

        pelanggan = Pelanggan(nama='Test Cancel', telepon='081500000002', alamat='Alamat Cancel', status=True)
        layanan = Layanan(
            nama='Cuci Kilo',
            harga=10000,
            durasi=1,
            durasi_unit='hari',
            kategori='Reguler',
            is_active=True,
        )
        db.session.add_all([pelanggan, layanan])
        db.session.commit()

        transaksi = TransaksiService.create_transaksi(
            id_pelanggan=pelanggan.id_pelanggan,
            items=[{'id_layanan': layanan.id_layanan, 'kuantitas': 2}],
        )
        assert transaksi is not None
        transaksi_id = transaksi.id_transaksi

    response = client.post(f'/transaksi/cancel/{transaksi_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Transaksi berhasil dibatalkan' in response.data

    with client.application.app_context():
        assert db.session.get(Transaksi, transaksi_id) is None
        assert Transaksi.query.filter_by(is_active=True).count() == 0

    response = client.get('/laporan/')
    assert response.status_code == 200
    assert b'Total Transaksi' in response.data
    assert b'Rp 0' in response.data
