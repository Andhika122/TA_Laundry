"""
DetailTransaksi Model - Transaction Items
"""
from app import db
from app.models import BaseModel


class DetailTransaksi(BaseModel):
    """Detail Item dari Transaksi"""
    __tablename__ = 'app_detail_transaksi'
    
    id_detail = db.Column(db.Integer, primary_key=True)
    id_transaksi = db.Column(db.Integer, db.ForeignKey('app_transaksi.id_transaksi'), nullable=False)
    id_layanan = db.Column(db.Integer, db.ForeignKey('app_layanan.id_layanan'), nullable=False)
    id_parfum = db.Column(db.Integer, db.ForeignKey('app_parfum.id_parfum'), nullable=True)
    kuantitas = db.Column(db.Numeric(10, 2), default=1)
    harga_satuan = db.Column(db.Numeric(10, 2), nullable=False)
    harga_parfum = db.Column(db.Numeric(10, 2), default=0)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    catatan = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<DetailTransaksi {self.id_detail}>'
    
    def calculate_subtotal(self):
        """Calculate subtotal"""
        total = (float(self.kuantitas) * float(self.harga_satuan)) + float(self.harga_parfum or 0)
        self.subtotal = total
        return total
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id_detail': self.id_detail,
            'id_transaksi': self.id_transaksi,
            'id_layanan': self.id_layanan,
            'id_parfum': self.id_parfum,
            'kuantitas': float(self.kuantitas),
            'harga_satuan': float(self.harga_satuan),
            'harga_parfum': float(self.harga_parfum or 0),
            'subtotal': float(self.subtotal),
            'catatan': self.catatan,
        }
