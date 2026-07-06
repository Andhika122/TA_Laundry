"""
SQLAlchemy Models
Database: TiDB (MySQL Compatible)
"""
from datetime import UTC, datetime
from app import db


def utc_now():
    """Return current UTC time without timezone info for database storage."""
    return datetime.now(UTC).replace(tzinfo=None)


class BaseModel(db.Model):
    """Base model with common fields"""
    __abstract__ = True
    
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Import all models
from .role import Role
from .user import User
from .pelanggan import Pelanggan
from .transaksi import Transaksi
from .detail_transaksi import DetailTransaksi
from .pembayaran import Pembayaran
from .layanan import Layanan
from .parfum import Parfum
from .promo import Promo
from .status import Status

__all__ = [
    'BaseModel',
    'utc_now',
    'Role',
    'User',
    'Pelanggan',
    'Transaksi',
    'DetailTransaksi',
    'Pembayaran',
    'Layanan',
    'Parfum',
    'Promo',
    'Status',
]
