"""
Pembayaran (Payment) Services
Layanan untuk CRUD operasi pembayaran dan status pembayaran
"""

from app.models import Pembayaran, Transaksi, db
from datetime import datetime
from decimal import Decimal
from flask import current_app


class PembayaranService:
    """Layanan untuk manajemen pembayaran"""
    
    # Valid payment methods
    METODE_PEMBAYARAN = ['Cash', 'Transfer', 'QRIS']
    STATUS_PEMBAYARAN = ['Belum Lunas', 'Lunas', 'Sebagian']
    
    @staticmethod
    def validate_metode_pembayaran(metode):
        """Validasi metode pembayaran"""
        return metode in PembayaranService.METODE_PEMBAYARAN
    
    @staticmethod
    def create_pembayaran(id_transaksi, jumlah, metode_pembayaran, catatan='', bukti_transfer=None):
        """
        Buat record pembayaran baru
        Returns: Pembayaran object atau None jika gagal
        """
        try:
            transaksi = db.session.get(Transaksi, id_transaksi)
            if not transaksi:
                return None
            
            # Validate metode
            if not PembayaranService.validate_metode_pembayaran(metode_pembayaran):
                return None
            
            # Validate jumlah
            jumlah = Decimal(str(jumlah))
            if jumlah <= 0:
                return None
            
            # Determine status pembayaran
            if jumlah >= transaksi.total_harga:
                status = 'Lunas'
            elif jumlah > 0:
                status = 'Sebagian'
            else:
                status = 'Belum Lunas'
            
            pembayaran = Pembayaran(
                id_transaksi=id_transaksi,
                jumlah=jumlah,
                metode_pembayaran=metode_pembayaran,
                status_pembayaran=status,
                tanggal_pembayaran=datetime.now(),
                catatan=catatan,
                bukti_transfer=bukti_transfer
            )
            
            db.session.add(pembayaran)
            
            db.session.commit()
            return pembayaran
        except Exception as e:
            db.session.rollback()
            print(f"Error in create_pembayaran: {str(e)}")
            return None
    
    @staticmethod
    def get_pembayaran_by_id(id_pembayaran):
        """Ambil data pembayaran berdasarkan ID"""
        try:
            return db.session.get(Pembayaran, id_pembayaran)
        except Exception as e:
            print(f"Error in get_pembayaran_by_id: {str(e)}")
            return None
    
    @staticmethod
    def get_pembayaran_by_transaksi(id_transaksi):
        """Ambil semua pembayaran untuk transaksi tertentu"""
        try:
            return Pembayaran.query.filter_by(id_transaksi=id_transaksi).order_by(
                Pembayaran.tanggal_pembayaran.desc()
            ).all()
        except Exception as e:
            print(f"Error in get_pembayaran_by_transaksi: {str(e)}")
            return []
    
    @staticmethod
    def calculate_change(id_transaksi, jumlah_bayar, metode='Cash'):
        """
        Hitung kembalian (change) untuk pembayaran cash
        Returns: Decimal - kembalian (0 jika bukan cash atau tidak ada kembalian)
        """
        try:
            transaksi = db.session.get(Transaksi, id_transaksi)
            if not transaksi or metode != 'Cash':
                return Decimal('0')
            
            jumlah_bayar = Decimal(str(jumlah_bayar))
            if jumlah_bayar >= transaksi.total_harga:
                return jumlah_bayar - transaksi.total_harga
            return Decimal('0')
        except Exception as e:
            print(f"Error in calculate_change: {str(e)}")
            return Decimal('0')
    
    @staticmethod
    def calculate_remaining_payment(id_transaksi):
        """
        Hitung sisa pembayaran yang belum dibayar
        Returns: Decimal - sisa pembayaran
        """
        try:
            transaksi = db.session.get(Transaksi, id_transaksi)
            if not transaksi:
                return Decimal('0')
            
            # Sum all payments
            total_paid = db.session.query(db.func.sum(Pembayaran.jumlah)).filter_by(
                id_transaksi=id_transaksi
            ).scalar() or 0
            
            total_harga = Decimal(str(transaksi.total_harga or 0))
            remaining = total_harga - Decimal(str(total_paid))
            return max(remaining, Decimal('0'))
        except Exception as e:
            print(f"Error in calculate_remaining_payment: {str(e)}")
            return Decimal('0')
    
    @staticmethod
    def get_pembayaran_status(id_transaksi):
        """
        Dapatkan status pembayaran saat ini
        Returns: dict dengan total_harga, total_paid, remaining, status
        """
        try:
            transaksi = db.session.get(Transaksi, id_transaksi)
            if not transaksi:
                return None
            
            total_paid = db.session.query(db.func.sum(Pembayaran.jumlah)).filter_by(
                id_transaksi=id_transaksi
            ).scalar() or 0
            
            total_paid = Decimal(str(total_paid))
            total_harga = Decimal(str(transaksi.total_harga or 0))
            remaining = total_harga - total_paid
            
            if remaining <= 0:
                status = 'Lunas'
            elif total_paid > 0:
                status = 'Sebagian'
            else:
                status = 'Belum Lunas'
            
            return {
                'total_harga': float(transaksi.total_harga),
                'total_paid': float(total_paid),
                'remaining': float(max(remaining, Decimal('0'))),
                'status': status
            }
        except Exception as e:
            print(f"Error in get_pembayaran_status: {str(e)}")
            return None
    
    @staticmethod
    def update_pembayaran_status(id_pembayaran, status_baru):
        """
        Update status pembayaran
        Returns: bool - True jika berhasil
        """
        try:
            pembayaran = db.session.get(Pembayaran, id_pembayaran)
            if not pembayaran or status_baru not in PembayaranService.STATUS_PEMBAYARAN:
                return False
            
            pembayaran.status_pembayaran = status_baru
            
            # If Lunas, update transaksi status
            if status_baru == 'Lunas':
                transaksi = db.session.get(Transaksi, pembayaran.id_transaksi)
                if transaksi:
                    transaksi.status_proses = 'Siap Ambil'
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error in update_pembayaran_status: {str(e)}")
            return False
    
    @staticmethod
    def get_payment_history(id_transaksi):
        """
        Dapatkan histori pembayaran lengkap untuk transaksi
        Returns: list of dicts dengan informasi pembayaran
        """
        try:
            pembayaran_list = Pembayaran.query.filter_by(id_transaksi=id_transaksi).order_by(
                Pembayaran.tanggal_pembayaran.asc()
            ).all()
            
            result = []
            for p in pembayaran_list:
                result.append({
                    'id': p.id_pembayaran,
                    'jumlah': float(p.jumlah),
                    'metode': p.metode_pembayaran,
                    'status': p.status_pembayaran,
                    'tanggal': p.tanggal_pembayaran,
                    'catatan': p.catatan
                })
            
            return result
        except Exception as e:
            print(f"Error in get_payment_history: {str(e)}")
            return []
    
    @staticmethod
    def is_transaksi_paid(id_transaksi):
        """
        Check apakah transaksi sudah fully paid
        Returns: bool
        """
        try:
            status = PembayaranService.get_pembayaran_status(id_transaksi)
            return status and status['status'] == 'Lunas'
        except Exception as e:
            print(f"Error in is_transaksi_paid: {str(e)}")
            return False
    
    @staticmethod
    def generate_receipt_data(id_pembayaran):
        """
        Generate data untuk print receipt
        Returns: dict dengan semua informasi untuk struk
        """
        try:
            pembayaran = db.session.get(Pembayaran, id_pembayaran)
            if not pembayaran:
                return None
            
            transaksi = pembayaran.transaksi
            pelanggan = transaksi.pelanggan
            
            total_harga = Decimal(str(transaksi.total_harga or 0))
            jumlah_bayar = Decimal(str(pembayaran.jumlah or 0))
            total_paid = db.session.query(db.func.sum(Pembayaran.jumlah)).filter_by(
                id_transaksi=transaksi.id_transaksi
            ).scalar() or 0
            total_paid = Decimal(str(total_paid))
            kurang = max(total_harga - total_paid, Decimal('0'))

            parfum_names = sorted({
                d.parfum.nama for d in transaksi.detail_transaksi if getattr(d, 'parfum', None)
            })

            item_total = sum(float(d.subtotal or 0) for d in transaksi.detail_transaksi)

            return {
                'id_transaksi': transaksi.id_transaksi,
                'merchant_name': current_app.config.get('MERCHANT_NAME', 'Laundry Berkah'),
                'merchant_address': current_app.config.get('MERCHANT_ADDRESS', 'MFWQ+JW5, Sidorejo Lor, Sidorejo, Salatiga City, Central Java 50715'),
                'merchant_phone': current_app.config.get('MERCHANT_PHONE', '087786181427'),
                'nomor_struk': f"STR/{pembayaran.id_pembayaran}/{pembayaran.tanggal_pembayaran.strftime('%Y%m%d')}",
                'nomor_transaksi': transaksi.nomor_transaksi,
                'pelanggan_nama': pelanggan.nama,
                'pelanggan_telepon': pelanggan.telepon,
                'kasir': 'Admin',
                'tanggal_masuk': transaksi.tanggal_masuk,
                'tanggal_pembayaran': pembayaran.tanggal_pembayaran,
                'tanggal_selesai_estimasi': transaksi.tanggal_selesai_estimasi,
                'total_harga': float(total_harga),
                'jumlah_bayar': float(jumlah_bayar),
                'total_paid': float(total_paid),
                'kurang': float(kurang),
                'metode_pembayaran': pembayaran.metode_pembayaran,
                'status_pembayaran': pembayaran.status_pembayaran,
                'catatan': transaksi.catatan or '',
                'item_count': sum(int(d.kuantitas or 0) for d in transaksi.detail_transaksi),
                'parfum': ', '.join(parfum_names) if parfum_names else '-',
                'subtotal': float(item_total),
                'detail_items': [
                    {
                        'nama': d.layanan.nama,
                        'kuantitas': int(d.kuantitas or 0),
                        'harga': float(d.harga_satuan),
                        'harga_parfum': float(d.harga_parfum or 0),
                        'parfum': d.parfum.nama if d.parfum else None,
                        'subtotal': float(d.subtotal)
                    }
                    for d in transaksi.detail_transaksi
                ]
            }
        except Exception as e:
            print(f"Error in generate_receipt_data: {str(e)}")
            return None

    @staticmethod
    def generate_receipt_data_for_transaksi(id_transaksi):
        """
        Generate data untuk print receipt untuk transaksi tanpa pembayaran
        Returns: dict dengan semua informasi untuk struk
        """
        try:
            transaksi = db.session.get(Transaksi, id_transaksi)
            if not transaksi:
                return None

            status_info = PembayaranService.get_pembayaran_status(id_transaksi)
            total_harga = Decimal(str(transaksi.total_harga or 0))
            total_paid = Decimal(str(status_info['total_paid'] if status_info else 0))
            kurang = Decimal(str(status_info['remaining'] if status_info else 0))
            status_label = status_info['status'] if status_info else 'Belum Lunas'

            parfum_names = sorted({
                d.parfum.nama for d in transaksi.detail_transaksi if getattr(d, 'parfum', None)
            })

            item_total = sum(float(d.subtotal or 0) for d in transaksi.detail_transaksi)

            return {
                'id_transaksi': transaksi.id_transaksi,
                'merchant_name': current_app.config.get('MERCHANT_NAME', 'Laundry Berkah'),
                'merchant_address': current_app.config.get('MERCHANT_ADDRESS', 'MFWQ+JW5, Sidorejo Lor, Sidorejo, Salatiga City, Central Java 50715'),
                'merchant_phone': current_app.config.get('MERCHANT_PHONE', '087786181427'),
                'nomor_struk': f"STR/{transaksi.nomor_transaksi}/{datetime.now().strftime('%Y%m%d')}",
                'nomor_transaksi': transaksi.nomor_transaksi,
                'pelanggan_nama': transaksi.pelanggan.nama,
                'pelanggan_telepon': transaksi.pelanggan.telepon,
                'kasir': 'Admin',
                'tanggal_masuk': transaksi.tanggal_masuk,
                'tanggal_pembayaran': datetime.now(),
                'tanggal_selesai_estimasi': transaksi.tanggal_selesai_estimasi,
                'total_harga': float(total_harga),
                'jumlah_bayar': 0.0,
                'total_paid': float(total_paid),
                'kurang': float(kurang),
                'metode_pembayaran': '-',
                'status_pembayaran': status_label,
                'catatan': transaksi.catatan or '',
                'item_count': sum(int(d.kuantitas or 0) for d in transaksi.detail_transaksi),
                'parfum': ', '.join(parfum_names) if parfum_names else '-',
                'subtotal': float(item_total),
                'detail_items': [
                    {
                        'nama': d.layanan.nama,
                        'kuantitas': int(d.kuantitas or 0),
                        'harga': float(d.harga_satuan),
                        'harga_parfum': float(d.harga_parfum or 0),
                        'parfum': d.parfum.nama if d.parfum else None,
                        'subtotal': float(d.subtotal)
                    }
                    for d in transaksi.detail_transaksi
                ]
            }
        except Exception as e:
            print(f"Error in generate_receipt_data_for_transaksi: {str(e)}")
            return None
