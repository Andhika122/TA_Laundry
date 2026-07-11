"""
Transaksi Model - Transaction Management
"""
from app import db
from app.models import BaseModel, utc_now
from datetime import datetime


class Transaksi(BaseModel):
    """Data Transaksi / Transaction"""
    __tablename__ = 'app_transaksi'
    
    id_transaksi = db.Column(db.Integer, primary_key=True)
    nomor_transaksi = db.Column(db.String(50), unique=True, nullable=False)
    id_pelanggan = db.Column(db.Integer, db.ForeignKey('app_pelanggan.id_pelanggan'), nullable=False)
    tanggal_masuk = db.Column(db.DateTime, default=utc_now, nullable=False)
    tanggal_selesai_estimasi = db.Column(db.DateTime, nullable=True)
    tanggal_selesai_aktual = db.Column(db.DateTime, nullable=True)
    total_harga = db.Column(db.Numeric(10, 2), default=0)
    promo_id = db.Column(db.Integer, db.ForeignKey('app_promo.id_promo'), nullable=True)
    catatan = db.Column(db.Text, nullable=True)
    status_proses = db.Column(db.String(50), default='Antrian')  # Status workflow
    is_active = db.Column(db.Boolean, default=True)
    nota_image_url = db.Column(db.String(500), nullable=True)
    
    # Relationships
    detail_transaksi = db.relationship('DetailTransaksi', backref='transaksi', lazy=True, cascade='all, delete-orphan')
    pembayaran = db.relationship('Pembayaran', backref='transaksi', lazy=True, cascade='all, delete-orphan')
    status_history = db.relationship('Status', backref='transaksi', lazy=True, cascade='all, delete-orphan')
    promo = db.relationship('Promo', backref='transaksi_list', lazy=True)
    
    def __repr__(self):
        return f'<Transaksi {self.nomor_transaksi}>'
    
    def generate_nomor_transaksi(self):
        """Generate unique transaction number"""
        from datetime import datetime
        tanggal = datetime.now().strftime('%d%m%y')
        count = db.session.query(Transaksi).filter(
            db.func.date(Transaksi.tanggal_masuk) == datetime.now().date()
        ).count() + 1
        return f"TRX/{tanggal}/{count:03d}"
    
    def calculate_total(self):
        """Calculate total from detail transaksi"""
        total = 0
        for detail in self.detail_transaksi:
            total += float(detail.subtotal) if detail.subtotal else 0
        return total
    
    def update_status(self, status_baru):
        """Update transaction status"""
        from app.models import Status

        status_sebelumnya = self.status_proses
        self.status_proses = status_baru
        
        # Add status history
        status_log = Status(
            id_transaksi=self.id_transaksi,
            status_sebelumnya=status_sebelumnya,
            status_baru=status_baru,
            keterangan=f'Status changed to {status_baru}'
        )
        db.session.add(status_log)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id_transaksi': self.id_transaksi,
            'nomor_transaksi': self.nomor_transaksi,
            'id_pelanggan': self.id_pelanggan,
            'tanggal_masuk': str(self.tanggal_masuk),
            'total_harga': float(self.total_harga),
            'promo_id': self.promo_id,
            'promo_nama': self.promo.nama if self.promo else None,
            'status_proses': self.status_proses,
            'catatan': self.catatan,
            'nota_image_url': self.nota_image_url,
        }
