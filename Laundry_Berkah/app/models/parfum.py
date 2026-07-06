"""
Parfum Model - Fragrance/Perfume Options
"""
from app import db
from app.models import BaseModel


class Parfum(BaseModel):
    """Data Parfum / Fragrance Options"""
    __tablename__ = 'app_parfum'
    
    id_parfum = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    harga_tambahan = db.Column(db.Numeric(10, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Parfum {self.nama}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id_parfum': self.id_parfum,
            'nama': self.nama,
            'deskripsi': self.deskripsi,
            'harga_tambahan': float(self.harga_tambahan),
            'is_active': self.is_active,
        }
