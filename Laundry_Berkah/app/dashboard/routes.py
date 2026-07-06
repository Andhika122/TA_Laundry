"""
Dashboard Module
"""
from pathlib import Path

from flask import Blueprint, render_template, redirect, url_for, jsonify, session
from app.dashboard.services import DashboardService
from app.utils.auth import login_required, require_role

BASE_DIR = Path(__file__).resolve().parent.parent
dashboard_bp = Blueprint('dashboard', __name__, template_folder=str(BASE_DIR / 'templates' / 'dashboard'))


@dashboard_bp.route('/')
def dashboard():
    """Dashboard homepage dengan statistik realtime"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator', 'Kasir')
    if access:
        return access

    # Ambil data dari DashboardService
    dashboard_data = DashboardService.get_dashboard_summary()
    
    # Extract data untuk template
    status_counts = dashboard_data.get('status_counts', {})
    today_revenue = dashboard_data.get('today_revenue', 0)
    total_customers = dashboard_data.get('total_customers', 0)
    total_transactions = dashboard_data.get('total_transactions', 0)
    total_late_orders = dashboard_data.get('total_late_orders', 0)
    recent_transactions = dashboard_data.get('recent_transactions', [])
    service_statistics = dashboard_data.get('service_statistics', [])
    
    return render_template(
        'dashboard.html',
        username=session.get('username'),
        status_counts=status_counts,
        today_revenue=today_revenue,
        total_customers=total_customers,
        total_transactions=total_transactions,
        total_late_orders=total_late_orders,
        recent_transactions=recent_transactions,
        service_statistics=service_statistics,
        active_page='dashboard'
    )


@dashboard_bp.route('/api/stats')
def get_stats():
    """API endpoint untuk mendapatkan statistik realtime dalam JSON"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    dashboard_data = DashboardService.get_dashboard_summary()
    return jsonify(dashboard_data)
