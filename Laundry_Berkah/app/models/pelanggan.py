"""
Pelanggan Model - Customer Management
"""
from app import db
from app.models import BaseModel


class Pelanggan(BaseModel):
    """Data Pelanggan / Customer"""
    __tablename__ = 'app_pelanggan'
    
    id_pelanggan = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    telepon = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=True)
    alamat = db.Column(db.Text, nullable=True)
    jenis_kelamin = db.Column(db.Enum('Laki-laki', 'Perempuan'), nullable=True)
    status = db.Column(db.Boolean, default=True)
    
    # Relationships
    transaksi = db.relationship('Transaksi', backref='pelanggan', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Pelanggan {self.nama}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id_pelanggan': self.id_pelanggan,
            'nama': self.nama,
            'telepon': self.telepon,
            'email': self.email,
            'alamat': self.alamat,
            'jenis_kelamin': self.jenis_kelamin,
            'status': self.status,
            'created_at': str(self.created_at),
        }
