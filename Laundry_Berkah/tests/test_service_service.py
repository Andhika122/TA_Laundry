def test_create_and_duplicate_service_handling(app):
    with app.app_context():
        from app.layanan.services import LayananService

        first = LayananService.create_layanan(
            nama='Cuci Express',
            harga='15000',
            durasi='2',
            durasi_unit='jam',
            kategori='Cuci',
            deskripsi='Cepat',
        )
        assert first is not None

        duplicate = LayananService.create_layanan(
            nama='  cuci express  ',
            harga='16000',
            durasi='3',
            durasi_unit='jam',
            kategori='Cuci',
            deskripsi='Ulang',
        )
        assert duplicate is None
