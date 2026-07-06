def test_create_and_duplicate_customer_handling(app):
    with app.app_context():
        from app.pelanggan.services import PelangganService

        first = PelangganService.create_pelanggan(
            nama='Budi Santoso',
            telepon='0812000001',
            email='budi@example.com',
            alamat='Jl. A',
            jenis_kelamin='Laki-laki',
        )
        assert first is not None

        duplicate = PelangganService.create_pelanggan(
            nama='Budi Santoso',
            telepon='0812000001',
            email='budi2@example.com',
            alamat='Jl. B',
            jenis_kelamin='Laki-laki',
        )
        assert duplicate is None
