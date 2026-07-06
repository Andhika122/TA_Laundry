"""
Status Model - Transaction Status History
"""
from app import db
from app.models import BaseModel, utc_now


class Status(BaseModel):
    """Status History untuk Transaksi"""
    __tablename__ = 'app_status'
    
    id_status = db.Column(db.Integer, primary_key=True)
    id_transaksi = db.Column(db.Integer, db.ForeignKey('app_transaksi.id_transaksi'), nullable=False)
    status_sebelumnya = db.Column(db.String(50), nullable=True)
    status_baru = db.Column(db.String(50), nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    tanggal_perubahan = db.Column(db.DateTime, default=utc_now, nullable=False)
    
    # Workflow stages
    STATUS_WORKFLOW = [
        'Antrian',
        'Cuci',
        'Pengeringan',
        'Setrika',
        'Packing',
        'Siap Ambil',
        'Selesai',
    ]
    
    def __repr__(self):
        return f'<Status {self.status_baru}>'
    
    @staticmethod
    def get_next_status(current_status):
        """Get next status in workflow"""
        try:
            current_index = Status.STATUS_WORKFLOW.index(current_status)
            if current_index < len(Status.STATUS_WORKFLOW) - 1:
                return Status.STATUS_WORKFLOW[current_index + 1]
        except (ValueError, IndexError):
            pass
        return None
    
    @staticmethod
    def is_valid_status(status):
        """Check if status is valid"""
        return status in Status.STATUS_WORKFLOW
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id_status': self.id_status,
            'id_transaksi': self.id_transaksi,
            'status_sebelumnya': self.status_sebelumnya,
            'status_baru': self.status_baru,
            'keterangan': self.keterangan,
            'tanggal_perubahan': str(self.tanggal_perubahan),
        }
