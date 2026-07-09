import os
import importlib
import sys
from datetime import datetime


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
