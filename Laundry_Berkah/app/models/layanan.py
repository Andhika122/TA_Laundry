"""
Layanan Model - Service/Package Management
"""
from app import db
from app.models import BaseModel


class Layanan(BaseModel):
    """Data Layanan / Service"""
    __tablename__ = 'app_layanan'
    
    id_layanan = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    harga = db.Column(db.Numeric(10, 2), nullable=False)
    durasi = db.Column(db.Integer, nullable=True)  # Durasi dalam hari
    durasi_unit = db.Column(db.String(20), default='hari')  # hari, jam
    deskripsi = db.Column(db.Text, nullable=True)
    kategori = db.Column(db.String(50), nullable=True)  # Cuci, Kering, Setrika, dll
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    detail_transaksi = db.relationship('DetailTransaksi', backref='layanan', lazy=True)
    
    def __repr__(self):
        return f'<Layanan {self.nama}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id_layanan': self.id_layanan,
            'nama': self.nama,
            'harga': float(self.harga),
            'durasi': self.durasi,
            'durasi_unit': self.durasi_unit,
            'deskripsi': self.deskripsi,
            'kategori': self.kategori,
            'is_active': self.is_active,
        }
