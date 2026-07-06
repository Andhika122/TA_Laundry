"""
User Model
"""
from app import db
from app.models import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash


class User(BaseModel):
    """User untuk login dan authentication"""
    __tablename__ = 'app_user'
    
    id_user = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    nama_lengkap = db.Column(db.String(100), nullable=True)
    status = db.Column(db.Boolean, default=True)
    id_role = db.Column(db.Integer, db.ForeignKey('app_role.id_role'), nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password, password)
    
    def get_role_name(self):
        """Get role name"""
        return self.role.nama if self.role else None
    
    @staticmethod
    def create_default_admin(username='admin', password='admin', email='admin@laundry.com'):
        """Create default admin user"""
        from app.models.role import Role
        
        # Check if admin role exists
        admin_role = Role.query.filter_by(nama='Admin').first()
        if not admin_role:
            admin_role = Role(nama='Admin', deskripsi='Administrator')
            db.session.add(admin_role)
            db.session.commit()
        
        # Check if admin user exists
        admin_user = User.query.filter_by(username=username).first()
        if not admin_user:
            admin_user = User(
                username=username,
                email=email,
                nama_lengkap='Administrator',
                id_role=admin_role.id_role
            )
            admin_user.set_password(password)
            db.session.add(admin_user)
            db.session.commit()
            return admin_user
        
        return admin_user
