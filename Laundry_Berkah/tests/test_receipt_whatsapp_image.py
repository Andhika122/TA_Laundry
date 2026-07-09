from app import db
from app.models import Layanan, Pelanggan
from app.pembayaran.services import PembayaranService
from app.transaksi.services import TransaksiService
from app.utils.fonte_whatsapp import build_fonnte_form_payload


def create_paid_transaction():
    pelanggan = Pelanggan(nama='Pelanggan Nota', telepon='08123456789', alamat='Alamat', status=True)
    db.session.add(pelanggan)
    db.session.flush()

    layanan = Layanan(
        nama='Cuci Nota',
        harga=12000,
        durasi=1,
        durasi_unit='hari',
        kategori='Cuci',
        is_active=True,
    )
    db.session.add(layanan)
    db.session.flush()

    transaksi = TransaksiService.create_transaksi(
        id_pelanggan=pelanggan.id_pelanggan,
        items=[{'id_layanan': layanan.id_layanan, 'kuantitas': 1}],
    )
    pembayaran = PembayaranService.create_pembayaran(
        id_transaksi=transaksi.id_transaksi,
        jumlah=12000,
        metode_pembayaran='Cash',
    )
    return transaksi, pembayaran


def test_receipt_image_url_is_saved_to_pembayaran(app, monkeypatch):
    with app.app_context():
        _, pembayaran = create_paid_transaction()
        receipt_data = PembayaranService.generate_receipt_data(pembayaran.id_pembayaran)

        import app.pembayaran.routes as pembayaran_routes

        monkeypatch.setattr(pembayaran_routes, 'is_cloudinary_configured', lambda: True)
        monkeypatch.setattr(pembayaran_routes, 'render_receipt_image', lambda data: b'png-bytes')
        monkeypatch.setattr(
            pembayaran_routes,
            'upload_image_bytes',
            lambda image_bytes, public_id=None: 'https://res.cloudinary.com/demo/struk.png',
        )

        with app.test_request_context():
            image_url = pembayaran_routes.get_or_create_pembayaran_image_url(
                pembayaran.id_pembayaran,
                receipt_data,
                require_cloudinary=True,
            )

        db.session.refresh(pembayaran)
        assert image_url == 'https://res.cloudinary.com/demo/struk.png'
        assert pembayaran.struk_image_url == image_url


def test_fonnte_payload_uses_image_url_as_media():
    payload = build_fonnte_form_payload(
        {
            'pelanggan_telepon': '08123456789',
            'nomor_transaksi': 'TRX/090726/001',
            'pelanggan_nama': 'Pelanggan Nota',
            'total_harga': 12000,
            'jumlah_bayar': 12000,
            'kurang': 0,
        },
        image_url='https://res.cloudinary.com/demo/struk.png',
    )

    assert payload['target'] == '628123456789'
    assert payload['url'] == 'https://res.cloudinary.com/demo/struk.png'
    assert payload['filename'].endswith('.png')
