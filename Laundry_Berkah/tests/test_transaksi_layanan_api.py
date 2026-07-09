from app import db
from app.models import Layanan


def test_transaksi_layanan_api_accepts_query_category(client, app):
    with app.app_context():
        db.session.add(Layanan(
            nama='Cuci Kering Setrika Reguler',
            harga=6000,
            durasi=2,
            durasi_unit='hari',
            kategori='Cuci Kering Setrika',
            is_active=True,
        ))
        db.session.commit()

    response = client.get('/transaksi/api/layanan?kategori=Cuci%20Kering%20Setrika')

    assert response.status_code == 200
    assert response.get_json()[0]['nama'] == 'Cuci Kering Setrika Reguler'


def test_transaksi_layanan_api_keeps_path_category_compatibility(client, app):
    with app.app_context():
        db.session.add(Layanan(
            nama='Boneka Kecil',
            harga=10000,
            durasi=2,
            durasi_unit='hari',
            kategori='Boneka',
            is_active=True,
        ))
        db.session.commit()

    response = client.get('/transaksi/api/layanan/Boneka')

    assert response.status_code == 200
    assert response.get_json()[0]['nama'] == 'Boneka Kecil'
