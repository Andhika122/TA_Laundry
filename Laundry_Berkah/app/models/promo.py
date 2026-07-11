"""
Promo Model - Promotion/Discount Management
"""
from app import db
from app.models import BaseModel, utc_now
from datetime import datetime


class Promo(BaseModel):
    """Data Promo / Promotion"""
    __tablename__ = 'app_promo'
    
    id_promo = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    tipe = db.Column(db.Enum('persentase', 'nominal'), nullable=False)  # % atau nominal
    nilai = db.Column(db.Numeric(10, 2), nullable=False)
    minimal_transaksi = db.Column(db.Numeric(10, 2), default=0)
    tanggal_mulai = db.Column(db.DateTime, default=utc_now)
    tanggal_akhir = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Promo {self.nama}>'
    
    def is_valid(self):
        """Check if promo is still valid"""
        now = datetime.now()
        return (self.is_active and 
                self.tanggal_mulai <= now and 
                (self.tanggal_akhir is None or self.tanggal_akhir >= now))
    
    def calculate_discount(self, amount):
        """Calculate discount amount"""
        if self.tipe == 'persentase':
            return float(amount) * (float(self.nilai) / 100)
        else:
            return float(self.nilai)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id_promo': self.id_promo,
            'nama': self.nama,
            'deskripsi': self.deskripsi,
            'tipe': self.tipe,
            'nilai': float(self.nilai),
            'minimal_transaksi': float(self.minimal_transaksi),
            'is_valid': self.is_valid(),
        }
