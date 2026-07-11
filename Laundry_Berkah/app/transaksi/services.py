"""
Transaksi (Transaction) Services
Layanan untuk CRUD operasi transaksi/pesanan
"""

from app.models import Transaksi, DetailTransaksi, Pembayaran, Status, Pelanggan, Layanan, Promo
from app.pembayaran.services import PembayaranService
from app import db
from datetime import datetime, timedelta
from decimal import Decimal


class TransaksiService:
    """Layanan untuk manajemen transaksi"""
    
    @staticmethod
    def generate_nomor_transaksi():
        """
        Generate nomor transaksi dengan format: TRX/DDMMYY/XXX
        Returns: string - nomor transaksi unik
        """
        try:
            today = datetime.now()
            date_str = today.strftime('%d%m%y')
            
            # Count transaksi hari ini
            count = Transaksi.query.filter(
                db.func.date(Transaksi.tanggal_masuk) == today.date()
            ).count() + 1
            
            return f"TRX/{date_str}/{count:03d}"
        except Exception as e:
            print(f"Error in generate_nomor_transaksi: {str(e)}")
            return None
    
    @staticmethod
    def create_transaksi(id_pelanggan, items, promo_id=None, catatan=''):
        """
        Buat transaksi baru dengan detail items
        items format: [{'id_layanan': 1, 'kuantitas': 1, 'id_parfum': None}, ...]
        Returns: Transaksi object atau None jika gagal
        """
        try:
            nomor_transaksi = TransaksiService.generate_nomor_transaksi()
            if not nomor_transaksi:
                return None
            
            # Create transaksi
            transaksi = Transaksi(
                nomor_transaksi=nomor_transaksi,
                id_pelanggan=id_pelanggan,
                tanggal_masuk=datetime.now(),
                status_proses='Antrian',
                is_active=True,
                catatan=catatan
            )
            
            db.session.add(transaksi)
            db.session.flush()  # Get id_transaksi
            
            # Add detail items
            total_harga = Decimal('0')
            max_duration = 0
            max_duration_unit = 'hari'

            for item in items:
                layanan = db.session.get(Layanan, item['id_layanan'])
                if not layanan:
                    continue
                
                harga_satuan = Decimal(str(layanan.harga))
                harga_parfum = Decimal('0')
                
                if item.get('id_parfum'):
                    from app.models import Parfum
                    parfum = db.session.get(Parfum, item['id_parfum'])
                    if parfum:
                        harga_parfum = Decimal(str(parfum.harga_tambahan))
                
                kuantitas = Decimal(str(item.get('kuantitas', 1)))
                subtotal = (harga_satuan + harga_parfum) * kuantitas
                
                detail = DetailTransaksi(
                    id_transaksi=transaksi.id_transaksi,
                    id_layanan=item['id_layanan'],
                    id_parfum=item.get('id_parfum'),
                    kuantitas=kuantitas,
                    harga_satuan=harga_satuan,
                    harga_parfum=harga_parfum,
                    subtotal=subtotal,
                    catatan=item.get('catatan', '')
                )
                
                db.session.add(detail)
                total_harga += subtotal

                # Track the longest duration service for estimated completion
                if layanan.durasi is not None:
                    if layanan.durasi_unit == 'jam':
                        duration_hours = int(layanan.durasi)
                    else:
                        duration_hours = int(layanan.durasi) * 24

                    if duration_hours > max_duration:
                        max_duration = duration_hours
                        max_duration_unit = layanan.durasi_unit
            
            # Store selected promo reference
            transaksi.promo_id = promo_id if promo_id else None

            # Apply promo if exists
            if promo_id:
                promo = db.session.get(Promo, promo_id)
                if promo and promo.is_valid() and total_harga >= promo.minimal_transaksi:
                    if promo.tipe == 'persentase':
                        discount = total_harga * Decimal(str(promo.nilai)) / Decimal('100')
                    else:  # nominal
                        discount = Decimal(str(promo.nilai))
                    
                    total_harga = max(total_harga - discount, Decimal('0'))
            
            transaksi.total_harga = total_harga

            if max_duration > 0:
                transaksi.tanggal_selesai_estimasi = transaksi.tanggal_masuk + timedelta(hours=max_duration)
            else:
                transaksi.tanggal_selesai_estimasi = None
            
            # Create initial status history
            status_history = Status(
                id_transaksi=transaksi.id_transaksi,
                status_sebelumnya=None,
                status_baru='Antrian',
                keterangan='Transaksi dibuat',
                tanggal_perubahan=datetime.now()
            )
            db.session.add(status_history)
            
            db.session.commit()
            return transaksi
        except Exception as e:
            db.session.rollback()
            print(f"Error in create_transaksi: {str(e)}")
            return None
    
    @staticmethod
    def get_transaksi_by_id(id_transaksi):
        """Ambil data transaksi berdasarkan ID"""
        try:
            return db.session.get(Transaksi, id_transaksi)
        except Exception as e:
            print(f"Error in get_transaksi_by_id: {str(e)}")
            return None
    
    @staticmethod
    def get_all_transaksi(page=1, per_page=10, status=None):
        """Ambil semua transaksi dengan pagination"""
        try:
            query = Transaksi.query.filter_by(is_active=True)
            
            if status:
                query = query.filter_by(status_proses=status)
            
            query = query.order_by(Transaksi.tanggal_masuk.desc())
            
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return paginated.items, paginated.total, paginated.pages
        except Exception as e:
            print(f"Error in get_all_transaksi: {str(e)}")
            return [], 0, 0

    @staticmethod
    def get_transaksi_by_statuses(status_list, limit=50):
        """Get transactions for multiple statuses"""
        try:
            if not status_list:
                return []
            return Transaksi.query.filter(
                Transaksi.is_active == True,
                Transaksi.status_proses.in_(status_list)
            ).order_by(Transaksi.tanggal_masuk.desc()).limit(limit).all()
        except Exception as e:
            print(f"Error in get_transaksi_by_statuses: {str(e)}")
            return []

    @staticmethod
    def get_status_counts():
        """Get count by transaction status"""
        try:
            result = db.session.query(
                Transaksi.status_proses,
                db.func.count(Transaksi.id_transaksi)
            ).filter(Transaksi.is_active == True).group_by(Transaksi.status_proses).all()
            return {row[0]: row[1] for row in result}
        except Exception as e:
            print(f"Error in get_status_counts: {str(e)}")
            return {}

    @staticmethod
    def get_recent_transactions(limit=8):
        """Get recent transactions"""
        try:
            return Transaksi.query.filter_by(is_active=True).order_by(Transaksi.tanggal_masuk.desc()).limit(limit).all()
        except Exception as e:
            print(f"Error in get_recent_transactions: {str(e)}")
            return []

    @staticmethod
    def calculate_total(id_transaksi):
        """Hitung total harga transaksi dari detail items"""
        try:
            details = DetailTransaksi.query.filter_by(id_transaksi=id_transaksi).all()
            
            total = Decimal('0')
            for detail in details:
                if detail.subtotal:
                    total += detail.subtotal
            
            return total
        except Exception as e:
            print(f"Error in calculate_total: {str(e)}")
            return Decimal('0')
    
    @staticmethod
    def get_transaksi_by_pelanggan(id_pelanggan, limit=10):
        """Ambil transaksi pelanggan tertentu"""
        try:
            return Transaksi.query.filter_by(
                id_pelanggan=id_pelanggan,
                is_active=True
            ).order_by(Transaksi.tanggal_masuk.desc()).limit(limit).all()
        except Exception as e:
            print(f"Error in get_transaksi_by_pelanggan: {str(e)}")
            return []
    
    @staticmethod
    def get_transaksi_by_nomor(nomor_transaksi):
        """Cari transaksi berdasarkan nomor"""
        try:
            return Transaksi.query.filter_by(nomor_transaksi=nomor_transaksi).first()
        except Exception as e:
            print(f"Error in get_transaksi_by_nomor: {str(e)}")
            return None
    
    @staticmethod
    def update_status_transaksi(id_transaksi, status_baru):
        """Update status transaksi"""
        try:
            from app.models import Status
            from datetime import datetime
            
            transaksi = db.session.get(Transaksi, id_transaksi)
            if not transaksi:
                return None
            
            # Validate status
            if not Status.is_valid_status(status_baru):
                return None
            
            status_sebelumnya = transaksi.status_proses
            
            # Prevent moving to Selesai if not fully paid
            if status_baru == 'Selesai':
                if not PembayaranService.is_transaksi_paid(id_transaksi):
                    return None

            # Update status
            transaksi.status_proses = status_baru
            if status_baru == 'Selesai':
                transaksi.tanggal_selesai_aktual = datetime.now()
            
            # Add to status history
            status_log = Status(
                id_transaksi=id_transaksi,
                status_sebelumnya=status_sebelumnya,
                status_baru=status_baru,
                keterangan=f'Diperbarui dari {status_sebelumnya}',
                tanggal_perubahan=datetime.now()
            )
            
            db.session.add(status_log)
            db.session.commit()
            return transaksi
        except Exception as e:
            db.session.rollback()
            print(f"Error in update_status_transaksi: {str(e)}")
            return None

    @staticmethod
    def get_next_status(id_transaksi):
        """Get the next workflow status for the transaction."""
        try:
            transaksi = db.session.get(Transaksi, id_transaksi)
            if not transaksi:
                return None
            from app.models import Status
            return Status.get_next_status(transaksi.status_proses)
        except Exception as e:
            print(f"Error in get_next_status: {str(e)}")
            return None

    @staticmethod
    def update_status_to_next(id_transaksi):
        """Advance the transaction to the next workflow status."""
        try:
            from app.models import Status

            transaksi = db.session.get(Transaksi, id_transaksi)
            if not transaksi:
                return None

            next_status = Status.get_next_status(transaksi.status_proses)
            if not next_status:
                return None
            if next_status == 'Selesai' and not PembayaranService.is_transaksi_paid(id_transaksi):
                return None

            status_sebelumnya = transaksi.status_proses
            transaksi.status_proses = next_status
            if next_status == 'Selesai':
                transaksi.tanggal_selesai_aktual = datetime.now()
            status_log = Status(
                id_transaksi=id_transaksi,
                status_sebelumnya=status_sebelumnya,
                status_baru=next_status,
                keterangan=f'Lanjut ke {next_status}',
                tanggal_perubahan=datetime.now()
            )
            db.session.add(status_log)
            db.session.commit()
            return transaksi
        except Exception as e:
            db.session.rollback()
            print(f"Error in update_status_to_next: {str(e)}")
            return None

    @staticmethod
    def get_status_workflow():
        """Get workflow status list"""
        try:
            from app.models import Status
            return Status.STATUS_WORKFLOW
        except Exception as e:
            print(f"Error in get_status_workflow: {str(e)}")
            return []
    
    @staticmethod
    def get_status_history(id_transaksi):
        """Get status history for transaction"""
        try:
            from app.models import Status
            return Status.query.filter_by(id_transaksi=id_transaksi).order_by(Status.tanggal_perubahan.desc()).all()
        except Exception as e:
            print(f"Error in get_status_history: {str(e)}")
            return []
    
    @staticmethod
    def search_transaksi_by_status_and_keyword(status_list, keyword='', limit=50):
        """Search transaksi by status dan keyword (nama pelanggan atau nomor HP)"""
        try:
            from app.models import Pelanggan
            query = Transaksi.query.filter(
                Transaksi.is_active == True,
                Transaksi.status_proses.in_(status_list)
            )
            
            if keyword:
                keyword = keyword.strip()
                # Search by customer name or phone number
                query = query.join(Pelanggan).filter(
                    db.or_(
                        Pelanggan.nama.ilike(f'%{keyword}%'),
                        Pelanggan.telepon.ilike(f'%{keyword}%'),
                        Transaksi.nomor_transaksi.ilike(f'%{keyword}%')
                    )
                )
            
            return query.order_by(Transaksi.tanggal_masuk.desc()).limit(limit).all()
        except Exception as e:
            print(f"Error in search_transaksi_by_status_and_keyword: {str(e)}")
            return []

    @staticmethod
    def can_edit_transaksi(role, id_transaksi):
        """Check whether the transaction may be edited by the current role."""
        if role in ('Admin', 'Operator'):
            return True
        if role == 'Kasir':
            transaksi = db.session.get(Transaksi, id_transaksi)
            return transaksi is not None and transaksi.status_proses == 'Antrian'
        return False

    @staticmethod
    def can_cancel_transaksi(role, id_transaksi):
        """Check whether the transaction may be canceled/deleted by the current role."""
        return role in ('Admin', 'Operator')

    @staticmethod
    def update_transaksi(id_transaksi, id_pelanggan, items, promo_id=None, catatan=''):
        """Update existing transaction data and its detail items."""
        try:
            transaksi = db.session.get(Transaksi, id_transaksi)
            if not transaksi:
                return None

            pelanggan = db.session.get(Pelanggan, id_pelanggan)
            if not pelanggan:
                return None

            transaksi.id_pelanggan = id_pelanggan
            transaksi.catatan = catatan

            # Remove existing detail items and rebuild from new values.
            for detail in list(transaksi.detail_transaksi):
                db.session.delete(detail)

            total_harga = Decimal('0')
            max_duration = 0
            max_duration_unit = 'hari'

            for item in items:
                layanan = db.session.get(Layanan, item['id_layanan'])
                if not layanan:
                    continue

                harga_satuan = Decimal(str(layanan.harga))
                harga_parfum = Decimal('0')
                if item.get('id_parfum'):
                    from app.models import Parfum
                    parfum = db.session.get(Parfum, item['id_parfum'])
                    if parfum:
                        harga_parfum = Decimal(str(parfum.harga_tambahan))

                kuantitas = Decimal(str(item.get('kuantitas', 1)))
                subtotal = (harga_satuan + harga_parfum) * kuantitas

                detail = DetailTransaksi(
                    id_transaksi=transaksi.id_transaksi,
                    id_layanan=item['id_layanan'],
                    id_parfum=item.get('id_parfum'),
                    kuantitas=kuantitas,
                    harga_satuan=harga_satuan,
                    harga_parfum=harga_parfum,
                    subtotal=subtotal,
                    catatan=item.get('catatan', '')
                )
                db.session.add(detail)
                total_harga += subtotal

                if layanan.durasi is not None:
                    if layanan.durasi_unit == 'jam':
                        duration_hours = int(layanan.durasi)
                    else:
                        duration_hours = int(layanan.durasi) * 24

                    if duration_hours > max_duration:
                        max_duration = duration_hours
                        max_duration_unit = layanan.durasi_unit

            transaksi.promo_id = promo_id if promo_id else None
            if promo_id:
                promo = db.session.get(Promo, promo_id)
                if promo and promo.is_valid() and total_harga >= promo.minimal_transaksi:
                    if promo.tipe == 'persentase':
                        discount = total_harga * Decimal(str(promo.nilai)) / Decimal('100')
                    else:
                        discount = Decimal(str(promo.nilai))
                    total_harga = max(total_harga - discount, Decimal('0'))

            transaksi.total_harga = total_harga
            if max_duration > 0:
                transaksi.tanggal_selesai_estimasi = transaksi.tanggal_masuk + timedelta(hours=max_duration)
            else:
                transaksi.tanggal_selesai_estimasi = None

            db.session.commit()
            return transaksi
        except Exception as e:
            db.session.rollback()
            print(f"Error in update_transaksi: {str(e)}")
            return None

    @staticmethod
    def cancel_transaksi(id_transaksi):
        """Delete transaksi and all related records."""
        try:
            transaksi = db.session.get(Transaksi, id_transaksi)
            if not transaksi:
                return False

            # Delete related detail, pembayaran, and status records explicitly
            db.session.query(DetailTransaksi).filter_by(id_transaksi=id_transaksi).delete(synchronize_session=False)
            db.session.query(Pembayaran).filter_by(id_transaksi=id_transaksi).delete(synchronize_session=False)
            db.session.query(Status).filter_by(id_transaksi=id_transaksi).delete(synchronize_session=False)

            db.session.delete(transaksi)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error in cancel_transaksi: {str(e)}")
            return False
