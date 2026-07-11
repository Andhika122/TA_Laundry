"""
Dashboard Services
Layanan untuk mengambil data statistik realtime dari database
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.models import Transaksi, DetailTransaksi, Pembayaran, Pelanggan, User
from app import db


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


class DashboardService:
    """Layanan untuk dashboard statistics"""

    STATUS_GROUPS = {
        'Antrian': ['Antrian'],
        'Proses': ['Cuci', 'Pengeringan', 'Setrika', 'Packing'],
        'Siap Ambil': ['Siap Ambil']
    }

    @staticmethod
    def default_status_counts():
        return {group: 0 for group in DashboardService.STATUS_GROUPS}
    
    @staticmethod
    def get_transaction_status_counts():
        """
        Ambil jumlah transaksi berdasarkan status proses
        Returns: dict dengan key sebagai status dan value jumlah transaksi
        """
        try:
            counts = DashboardService.default_status_counts()
            for group, statuses in DashboardService.STATUS_GROUPS.items():
                count = Transaksi.query.filter(
                    Transaksi.status_proses.in_(statuses),
                    Transaksi.is_active == True
                ).count()
                counts[group] = count
            
            return counts
        except Exception as e:
            print(f"Error in get_transaction_status_counts: {str(e)}")
            return DashboardService.default_status_counts()
    
    @staticmethod
    def get_today_revenue():
        """
        Ambil total pendapatan hari ini
        Returns: Numeric - jumlah pendapatan hari ini
        """
        try:
            today = datetime.now().date()
            
            total = db.session.query(
                func.sum(Pembayaran.jumlah)
            ).filter(
                func.date(Pembayaran.tanggal_pembayaran) == today
            ).scalar()
            
            return _safe_float(total)
        except Exception as e:
            print(f"Error in get_today_revenue: {str(e)}")
            return 0
    
    @staticmethod
    def get_total_customers():
        """
        Ambil total jumlah pelanggan
        Returns: Integer - jumlah pelanggan aktif
        """
        try:
            count = Pelanggan.query.filter_by(status=True).count()
            return count
        except Exception as e:
            print(f"Error in get_total_customers: {str(e)}")
            return 0
    
    @staticmethod
    def get_total_transactions():
        """
        Ambil total jumlah transaksi
        Returns: Integer - jumlah transaksi aktif
        """
        try:
            count = Transaksi.query.filter_by(is_active=True).count()
            return count
        except Exception as e:
            print(f"Error in get_total_transactions: {str(e)}")
            return 0
    
    @staticmethod
    def get_total_late_orders():
        """
        Ambil total pesanan terlambat diselesaikan atau transaksi aktif yang sudah melewati estimasi.
        Returns: Integer - jumlah transaksi terlambat berdasarkan estimasi selesai.
        """
        try:
            now = datetime.now()
            count = Transaksi.query.filter(
                Transaksi.is_active == True,
                Transaksi.tanggal_selesai_estimasi != None,
                or_(
                    and_(
                        Transaksi.status_proses == 'Selesai',
                        Transaksi.tanggal_selesai_aktual != None,
                        Transaksi.tanggal_selesai_aktual > Transaksi.tanggal_selesai_estimasi,
                    ),
                    and_(
                        Transaksi.status_proses != 'Selesai',
                        Transaksi.tanggal_selesai_estimasi < now,
                    )
                )
            ).count()
            return count
        except Exception as e:
            print(f"Error in get_total_late_orders: {str(e)}")
            return 0
    
    @staticmethod
    def get_total_users():
        """
        Ambil total jumlah pengguna
        Returns: Integer - jumlah pengguna aktif
        """
        try:
            count = User.query.filter_by(status=True).count()
            return count
        except Exception as e:
            print(f"Error in get_total_users: {str(e)}")
            return 0
    
    @staticmethod
    def get_monthly_revenue(months=12):
        """
        Ambil pendapatan bulanan untuk grafik
        Returns: list[dict] dengan struktur {'bulan': 'Jan', 'revenue': 0}
        """
        try:
            data = []
            today = datetime.now()
            
            for i in range(months - 1, -1, -1):
                month_date = today - timedelta(days=30*i)
                month_start = month_date.replace(day=1)
                
                # Tentukan hari pertama bulan berikutnya
                if month_date.month == 12:
                    month_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
                else:
                    month_end = month_date.replace(month=month_date.month + 1, day=1)
                
                revenue = db.session.query(
                    func.sum(Pembayaran.jumlah)
                ).filter(
                    and_(
                        Pembayaran.tanggal_pembayaran >= month_start,
                        Pembayaran.tanggal_pembayaran < month_end
                    )
                ).scalar()
                
                bulan_names = [
                    'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                    'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'
                ]
                
                data.append({
                    'bulan': bulan_names[month_start.month - 1],
                    'revenue': _safe_float(revenue)
                })
            
            return data
        except Exception as e:
            print(f"Error in get_monthly_revenue: {str(e)}")
            return []
    
    @staticmethod
    def get_recent_transactions(limit=5):
        """
        Ambil transaksi terbaru
        Returns: list[dict] dengan transaksi terbaru
        """
        try:
            transactions = Transaksi.query.filter_by(
                is_active=True
            ).order_by(
                Transaksi.tanggal_masuk.desc()
            ).limit(limit).all()
            
            result = []
            for trx in transactions:
                pelanggan = db.session.get(Pelanggan, trx.id_pelanggan)
                result.append({
                    'nomor': trx.nomor_transaksi,
                    'pelanggan': pelanggan.nama if pelanggan else 'Unknown',
                    'status': trx.status_proses,
                    'total': _safe_float(getattr(trx, 'total_harga', 0)),
                    'tanggal': trx.tanggal_masuk.strftime('%d %b %Y %H:%M') if trx.tanggal_masuk else ''
                })
            
            return result
        except Exception as e:
            print(f"Error in get_recent_transactions: {str(e)}")
            return []
    
    @staticmethod
    def get_service_statistics():
        """
        Ambil statistik layanan yang paling banyak digunakan
        Returns: list[dict] dengan service statistics
        """
        try:
            from app.models import Layanan
            
            services = db.session.query(
                Layanan.nama,
                func.count(DetailTransaksi.id_detail).label('jumlah')
            ).join(
                DetailTransaksi, Layanan.id_layanan == DetailTransaksi.id_layanan
            ).group_by(
                Layanan.nama
            ).order_by(
                func.count(DetailTransaksi.id_detail).desc()
            ).limit(5).all()
            
            result = []
            for service, count in services:
                result.append({
                    'layanan': service,
                    'jumlah': count
                })
            
            return result
        except Exception as e:
            print(f"Error in get_service_statistics: {str(e)}")
            return []
    
    @staticmethod
    def get_dashboard_summary():
        """
        Ambil ringkasan dashboard lengkap
        Returns: dict dengan semua data dashboard
        """
        try:
            status_counts = DashboardService.get_transaction_status_counts()
            
            return {
                'status_counts': status_counts,
                'today_revenue': DashboardService.get_today_revenue(),
                'total_customers': DashboardService.get_total_customers(),
                'total_transactions': DashboardService.get_total_transactions(),
                'total_late_orders': DashboardService.get_total_late_orders(),
                'total_users': DashboardService.get_total_users(),
                'monthly_revenue': DashboardService.get_monthly_revenue(),
                'recent_transactions': DashboardService.get_recent_transactions(),
                'service_statistics': DashboardService.get_service_statistics(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error in get_dashboard_summary: {str(e)}")
            return {}
