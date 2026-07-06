"""
Akun Module - User Account Management
"""
from flask import Blueprint, render_template, session, redirect, url_for

akun_bp = Blueprint('akun', __name__)


@akun_bp.route('/profile')
def profile():
    """User profile"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    return render_template('akun/profile.html', active_page='akun')
