"""
Role Model
"""
from app import db
from app.models import BaseModel


class Role(BaseModel):
    """Role untuk authentication dan authorization"""
    __tablename__ = 'app_role'
    
    id_role = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(50), unique=True, nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    
    # Relationships
    users = db.relationship('User', backref='role', lazy=True)
    
    def __repr__(self):
        return f'<Role {self.nama}>'
    
    @staticmethod
    def get_default_roles():
        """Get or create default roles"""
        roles_data = [
            {'nama': 'Admin', 'deskripsi': 'Administrator - Full Access'},
            {'nama': 'Kasir', 'deskripsi': 'Kasir - Handling Transactions'},
            {'nama': 'Operator', 'deskripsi': 'Operator - Laundry Process'},
        ]
        return roles_data
