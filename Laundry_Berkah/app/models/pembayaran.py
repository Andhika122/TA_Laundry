"""
Pembayaran Model - Payment Management
"""
from app import db
from app.models import BaseModel, utc_now


class Pembayaran(BaseModel):
    """Data Pembayaran / Payment"""
    __tablename__ = 'app_pembayaran'
    
    id_pembayaran = db.Column(db.Integer, primary_key=True)
    id_transaksi = db.Column(db.Integer, db.ForeignKey('app_transaksi.id_transaksi'), nullable=False)
    jumlah = db.Column(db.Numeric(10, 2), nullable=False)
    metode_pembayaran = db.Column(db.String(50), nullable=True)
    status_pembayaran = db.Column(db.String(50), default='Belum Lunas')
    catatan = db.Column(db.Text, nullable=True)
    tanggal_pembayaran = db.Column(db.DateTime, nullable=True)
    bukti_transfer = db.Column(db.String(255), nullable=True)  # URL or file path
    struk_image_url = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<Pembayaran {self.id_pembayaran}>'
    
    def mark_as_paid(self):
        """Mark payment as paid"""
        self.status_pembayaran = 'Lunas'
        self.tanggal_pembayaran = utc_now()
    
    def calculate_kembalian(self, total_harga):
        """Calculate change"""
        kembalian = float(self.jumlah) - float(total_harga)
        return max(kembalian, 0)  # Return 0 if negative
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id_pembayaran': self.id_pembayaran,
            'id_transaksi': self.id_transaksi,
            'jumlah': float(self.jumlah),
            'metode_pembayaran': self.metode_pembayaran,
            'status_pembayaran': self.status_pembayaran,
            'catatan': self.catatan,
            'tanggal_pembayaran': str(self.tanggal_pembayaran) if self.tanggal_pembayaran else None,
            'struk_image_url': self.struk_image_url,
        }
