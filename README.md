# Laundry Berkah — Local Setup

Petunjuk singkat untuk menjalankan proyek secara lokal.

## Prasyarat
- Python 3.10+ (direkomendasikan)
- Git (opsional)

## Menyiapkan lingkungan
1. Buat virtual environment:

```powershell
python -m venv .venv
& .venv\Scripts\Activate.ps1
```

2. Pasang dependensi production:

```powershell
pip install -r requirements.txt
```

3. (Opsional) Pasang dependensi development (format/lint):

```powershell
pip install -r requirements-dev.txt
```

## Konfigurasi environment
Salin contoh `.env` (jika ada) dan isi nilai sensitif seperti DB, Cloudinary, Fonte WA.
File konfigurasi utama: `Laundry_Berkah/.env`.

Untuk menjalankan aplikasi tanpa koneksi ke TiDB, set `FLASK_ENV=testing` untuk menggunakan SQLite in-memory.

## Menjalankan test
Jalankan seluruh test suite:

```powershell
python -m pytest -q
```

## Menjalankan aplikasi (development)
Jalankan aplikasi Flask:

```powershell
python Laundry_Berkah/app.py
```

Jika ingin menjalankan app dalam mode testing (SQLite in-memory):

```powershell
$env:FLASK_ENV='testing'
python Laundry_Berkah/app.py
```

## Format & Lint
Format kode dengan Black dan isort, lalu periksa dengan flake8:

```powershell
.venv\Scripts\black Laundry_Berkah
.venv\Scripts\isort Laundry_Berkah
.venv\Scripts\flake8 Laundry_Berkah --max-line-length=120
```

## Catatan
- Konfigurasi Fonte WA berada di `Laundry_Berkah/.env` (`FONTE_TOKEN`, `FONTE_PHONE`, `FONTE_API_URL`).
- Jangan commit file `.env` yang berisi kredensial ke repositori publik.

Jika mau, saya bisa: menambahkan badge test ke README, membuat skrip `run_tests.cmd`, atau commit perubahan. Pilih aksi selanjutnya.