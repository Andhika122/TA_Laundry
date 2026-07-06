from flask import redirect, url_for, session, flash


def login_required():
    """Return redirect to login if user is not authenticated."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return None


def require_role(*allowed_roles):
    """Return redirect if current user role is not allowed."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    role = session.get('role')
    if role not in allowed_roles:
        flash('Akses ditolak. Anda tidak memiliki izin untuk melihat halaman ini.', 'warning')
        return redirect(url_for('transaksi.index'))

    return None
