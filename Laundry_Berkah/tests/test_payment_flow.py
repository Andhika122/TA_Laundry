import os
import importlib
import sys


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
