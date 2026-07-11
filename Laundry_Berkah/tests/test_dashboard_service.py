import os
import importlib
import sys
from datetime import datetime, timedelta


def test_dashboard_summary_handles_empty_state():
    os.environ["FLASK_ENV"] = "development"
    os.environ["TIDB_HOST"] = "127.0.0.1"
    os.environ["TIDB_PORT"] = "1"
    os.environ["TIDB_USER"] = "root"
    os.environ["TIDB_PASSWORD"] = ""
    os.environ["TIDB_DB"] = "test_db"
    os.environ["USE_SQLITE_FALLBACK"] = "0"

    import app as app_module
    app_module = importlib.reload(app_module)
    app = app_module.create_app("development")

    with app.app_context():
        from app.dashboard.services import DashboardService

        summary = DashboardService.get_dashboard_summary()
        assert isinstance(summary, dict)
        assert summary["today_revenue"] >= 0
        assert summary["total_customers"] >= 0
        assert summary["total_transactions"] >= 0
        assert "status_counts" in summary
        assert set(summary["status_counts"].keys()) == {"Antrian", "Proses", "Siap Ambil"}
        assert summary["status_counts"]["Antrian"] >= 0
        assert summary["status_counts"]["Proses"] >= 0
        assert summary["status_counts"]["Siap Ambil"] >= 0


def test_today_revenue_includes_payments():
    os.environ["FLASK_ENV"] = "testing"
    os.environ.pop("USE_SQLITE_FALLBACK", None)
    sys.path.insert(0, os.getcwd())

    import app as app_module
    app_module = importlib.reload(app_module)
    app = app_module.create_app("testing")

    with app.app_context():
        from app.models import Pelanggan, Layanan, Pembayaran, Transaksi, db
        from app.dashboard.services import DashboardService

        pelanggan = Pelanggan(nama='Test Revenue', telepon='0819', alamat='Y', status=True)
        db.session.add(pelanggan)
        db.session.flush()

        layanan = Layanan(
            nama='Cuci Revenue',
            harga=10000,
            durasi=1,
            durasi_unit='jam',
            kategori='Reguler',
            is_active=True,
        )
        db.session.add(layanan)
        db.session.flush()

        transaksi = Transaksi(
            nomor_transaksi='TRX/REVENUE/001',
            id_pelanggan=pelanggan.id_pelanggan,
            tanggal_masuk=datetime.now(),
            total_harga=10000,
            status_proses='Antrian',
            is_active=True
        )
        db.session.add(transaksi)
        db.session.flush()

        pembayaran = Pembayaran(
            id_transaksi=transaksi.id_transaksi,
            jumlah=10000,
            metode_pembayaran='Cash',
            status_pembayaran='Sebagian',
            tanggal_pembayaran=datetime.now()
        )
        db.session.add(pembayaran)
        db.session.commit()

        summary = DashboardService.get_dashboard_summary()
        assert summary["today_revenue"] >= 10000


def test_total_late_orders_includes_overdue_unfinished_transactions():
    os.environ["FLASK_ENV"] = "testing"
    os.environ.pop("USE_SQLITE_FALLBACK", None)
    sys.path.insert(0, os.getcwd())

    import app as app_module
    app_module = importlib.reload(app_module)
    app = app_module.create_app("testing")

    with app.app_context():
        from app.models import Pelanggan, Layanan, Transaksi, db
        from app.dashboard.services import DashboardService

        pelanggan = Pelanggan(nama='Test Late', telepon='0819', alamat='Y', status=True)
        db.session.add(pelanggan)
        db.session.flush()

        layanan = Layanan(
            nama='Cuci Late',
            harga=10000,
            durasi=1,
            durasi_unit='jam',
            kategori='Reguler',
            is_active=True,
        )
        db.session.add(layanan)
        db.session.flush()

        transaksi1 = Transaksi(
            nomor_transaksi='TRX/LATE/001',
            id_pelanggan=pelanggan.id_pelanggan,
            tanggal_masuk=datetime.now(),
            tanggal_selesai_estimasi=datetime.now() - timedelta(hours=2),
            status_proses='Cuci',
            is_active=True
        )
        transaksi2 = Transaksi(
            nomor_transaksi='TRX/LATE/002',
            id_pelanggan=pelanggan.id_pelanggan,
            tanggal_masuk=datetime.now(),
            tanggal_selesai_estimasi=datetime.now() - timedelta(hours=4),
            tanggal_selesai_aktual=datetime.now() - timedelta(hours=1),
            status_proses='Selesai',
            is_active=True
        )
        transaksi3 = Transaksi(
            nomor_transaksi='TRX/LATE/003',
            id_pelanggan=pelanggan.id_pelanggan,
            tanggal_masuk=datetime.now(),
            tanggal_selesai_estimasi=datetime.now() + timedelta(hours=4),
            status_proses='Cuci',
            is_active=True
        )
        db.session.add_all([transaksi1, transaksi2, transaksi3])
        db.session.commit()

        summary = DashboardService.get_dashboard_summary()
        assert summary['total_late_orders'] >= 2
        assert summary['total_late_orders'] == 2
