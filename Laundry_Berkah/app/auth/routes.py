"""
Auth Module - Authentication Blueprint
"""
from pathlib import Path

from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, flash
from app import db
from app.models.user import User
from app.models.role import Role


def _ensure_login_defaults():
    """Create default role and admin account if missing."""
    try:
        role = Role.query.filter_by(nama='Admin').first()
        if not role:
            role = Role(nama='Admin', deskripsi='Administrator')
            db.session.add(role)
            db.session.commit()

        admin_username = current_app.config.get('ADMIN_USERNAME', 'admin')
        admin_password = current_app.config.get('ADMIN_PASSWORD', 'admin')
        admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@laundry.com')
        user = User.query.filter_by(username=admin_username).first()
        if not user:
            user = User(
                username=admin_username,
                email=admin_email,
                nama_lengkap='Administrator',
                id_role=role.id_role,
                status=True,
            )
            user.set_password(admin_password)
            db.session.add(user)
            db.session.commit()
    except Exception:
        db.session.rollback()

BASE_DIR = Path(__file__).resolve().parent.parent
auth_bp = Blueprint('auth', __name__, template_folder=str(BASE_DIR / 'templates' / 'auth'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate input
        if not username or not password:
            flash('Username dan password harus diisi', 'danger')
            return redirect(url_for('auth.login'))
        
        if username == current_app.config.get('ADMIN_USERNAME', 'admin'):
            _ensure_login_defaults()

        try:
            # Find user
            user = User.query.filter_by(username=username).first()
        except Exception as exc:
            current_app.logger.exception('Login query failed')
            flash('Terjadi kesalahan saat memproses login. Silakan coba lagi nanti.', 'danger')
            return redirect(url_for('auth.login'))
        
        if user and user.check_password(password) and getattr(user, 'status', True):
            # Set session
            session['user_id'] = user.id_user
            session['username'] = user.username
            session['role'] = user.role.nama if user.role else None
            session.permanent = True
            
            flash(f'Selamat datang, {user.nama_lengkap or user.username}!', 'success')
            user_role = session.get('role')
            if user_role == 'Kasir':
                return redirect(url_for('dashboard.dashboard'))
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Username atau password salah', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Anda telah logout', 'info')
    return redirect(url_for('auth.login'))
