def test_laporan_index_no_data_shows_zero(client):
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert response.status_code == 200

    response = client.get('/laporan/')
    assert response.status_code == 200
    assert b'Total Transaksi' in response.data
    assert b'Rp 0' in response.data
    assert b'Belum ada data transaksi' in response.data


def test_laporan_export_excel_returns_xlsx(client):
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert response.status_code == 200

    response = client.get('/laporan/export?format=excel')
    assert response.status_code == 200
    assert response.headers.get('Content-Type', '') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert response.data[:2] == b'PK'


def test_laporan_export_pdf_returns_pdf(client):
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert response.status_code == 200

    response = client.get('/laporan/export?format=pdf')
    assert response.status_code == 200
    assert response.headers.get('Content-Type', '').startswith('application/pdf')
    assert response.data.startswith(b'%PDF')


def test_laporan_filter_by_specific_date(client):
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert response.status_code == 200

    with client.application.app_context():
        from app.models import Pelanggan, Layanan, db
        from app.transaksi.services import TransaksiService
        from datetime import datetime

        pelanggan = Pelanggan(nama='Test Filter Tanggal', telepon='081500000004', alamat='Alamat Filter', status=True)
        layanan = Layanan(
            nama='Cuci Filter',
            harga=9000,
            durasi=1,
            durasi_unit='hari',
            kategori='Reguler',
            is_active=True,
        )
        db.session.add_all([pelanggan, layanan])
        db.session.commit()

        transaksi = TransaksiService.create_transaksi(
            id_pelanggan=pelanggan.id_pelanggan,
            items=[{'id_layanan': layanan.id_layanan, 'kuantitas': 1}],
        )
        assert transaksi is not None
        from app.pembayaran.services import PembayaranService
        pembayaran = PembayaranService.create_pembayaran(
            id_transaksi=transaksi.id_transaksi,
            jumlah=9000,
            metode_pembayaran='Cash',
            catatan='Pembayaran penuh'
        )
        assert pembayaran is not None
        selected_date = datetime.now().date().isoformat()

    response = client.get(f'/laporan/?range=per_tanggal&custom_date={selected_date}')
    assert response.status_code == 200
    assert b'Periode Laporan' in response.data
    assert b'Per Tanggal' in response.data
    assert selected_date.encode() in response.data
    assert b'Rp 9.000' in response.data


def test_laporan_filter_by_month(client):
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert response.status_code == 200

    with client.application.app_context():
        from app.models import Pelanggan, Layanan, db
        from app.transaksi.services import TransaksiService
        from datetime import datetime

        pelanggan = Pelanggan(nama='Test Filter Bulan', telepon='081500000005', alamat='Alamat Filter Bulan', status=True)
        layanan = Layanan(
            nama='Cuci Bulan',
            harga=11000,
            durasi=1,
            durasi_unit='hari',
            kategori='Reguler',
            is_active=True,
        )
        db.session.add_all([pelanggan, layanan])
        db.session.commit()

        transaksi = TransaksiService.create_transaksi(
            id_pelanggan=pelanggan.id_pelanggan,
            items=[{'id_layanan': layanan.id_layanan, 'kuantitas': 1}],
        )
        assert transaksi is not None
        from app.pembayaran.services import PembayaranService
        pembayaran = PembayaranService.create_pembayaran(
            id_transaksi=transaksi.id_transaksi,
            jumlah=11000,
            metode_pembayaran='Cash',
            catatan='Pembayaran penuh'
        )
        assert pembayaran is not None
        selected_month = datetime.now().strftime('%Y-%m')

    response = client.get(f'/laporan/?range=per_bulan&custom_month={selected_month}')
    assert response.status_code == 200
    assert b'Rp 11.000' in response.data
    assert b'Per Bulan' in response.data
