"""
Pelanggan Module - Customer Management
"""
from pathlib import Path

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, session
from app.pelanggan.services import PelangganService
from app.transaksi.services import TransaksiService
from app.utils.auth import login_required, require_role
from app.utils.whatsapp import build_whatsapp_chat_url

BASE_DIR = Path(__file__).resolve().parent.parent
pelanggan_bp = Blueprint('pelanggan', __name__, template_folder=str(BASE_DIR / 'templates' / 'pelanggan'))


def render_tambah(form_data=None):
    return render_template(
        'pelanggan/tambah.html',
        form_data=form_data or {},
        active_page='pelanggan'
    )


def render_edit(pelanggan, form_data=None):
    return render_template(
        'pelanggan/edit.html',
        pelanggan=pelanggan,
        form_data=form_data or {},
        active_page='pelanggan'
    )


@pelanggan_bp.route('/')
def index():
    """List all customers with pagination and search"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator')
    if access:
        return access
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    per_page = 10
    
    pelanggan_list, total_count, total_pages = PelangganService.get_all_pelanggan(
        page=page,
        per_page=per_page,
        search=search if search else None
    )
    whatsapp_chat_map = {
        p.id_pelanggan: build_whatsapp_chat_url(p.telepon)
        for p in pelanggan_list
    }
    
    return render_template(
        'pelanggan/pelanggan.html',
        pelanggan=pelanggan_list,
        total_count=total_count,
        total_pages=total_pages,
        current_page=page,
        search=search,
        whatsapp_chat_map=whatsapp_chat_map,
        active_page='pelanggan'
    )


@pelanggan_bp.route('/tambah', methods=['GET', 'POST'])
def tambah():
    """Add new customer"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator')
    if access:
        return access
    
    if request.method == 'POST':
        form_data = request.form
        try:
            nama = request.form.get('nama', '').strip()
            telepon = request.form.get('telepon', '').strip()
            email = request.form.get('email', '').strip()
            alamat = request.form.get('alamat', '').strip()
            jenis_kelamin = request.form.get('jenis_kelamin', '').strip()
            
            # Validasi
            if not all([nama, telepon, email, alamat, jenis_kelamin]):
                flash('Semua field harus diisi. Silakan perbaiki data yang kurang.', 'danger')
                return render_tambah(form_data)
            
            # Create pelanggan
            result = PelangganService.create_pelanggan(
                nama=nama,
                telepon=telepon,
                email=email,
                alamat=alamat,
                jenis_kelamin=jenis_kelamin
            )
            
            if result:
                flash('Pelanggan berhasil ditambahkan', 'success')
                return redirect(url_for('pelanggan.index'))
            else:
                flash('Nomor telepon sudah terdaftar. Silakan ganti nomor telepon.', 'danger')
                return render_tambah(form_data)
        except Exception as e:
            flash(f'Data belum valid: {str(e)}. Silakan perbaiki input.', 'danger')
            return render_tambah(form_data)
    
    return render_tambah()


@pelanggan_bp.route('/edit/<int:id_pelanggan>', methods=['GET', 'POST'])
def edit(id_pelanggan):
    """Edit customer"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator')
    if access:
        return access
    
    pelanggan = PelangganService.get_pelanggan_by_id(id_pelanggan)
    if not pelanggan:
        flash('Pelanggan tidak ditemukan', 'danger')
        return redirect(url_for('pelanggan.index'))
    
    if request.method == 'POST':
        form_data = request.form
        try:
            nama = request.form.get('nama', '').strip()
            telepon = request.form.get('telepon', '').strip()
            email = request.form.get('email', '').strip()
            alamat = request.form.get('alamat', '').strip()
            jenis_kelamin = request.form.get('jenis_kelamin', '').strip()
            
            # Validasi
            if not all([nama, telepon, email, alamat, jenis_kelamin]):
                flash('Semua field harus diisi. Silakan perbaiki data yang kurang.', 'danger')
                return render_edit(pelanggan, form_data)
            
            # Update pelanggan
            result = PelangganService.update_pelanggan(
                id_pelanggan=id_pelanggan,
                nama=nama,
                telepon=telepon,
                email=email,
                alamat=alamat,
                jenis_kelamin=jenis_kelamin
            )
            
            if result:
                flash('Pelanggan berhasil diperbarui', 'success')
                return redirect(url_for('pelanggan.index'))
            else:
                flash('Nomor telepon sudah terdaftar atau pelanggan tidak ditemukan. Silakan perbaiki data.', 'danger')
                return render_edit(pelanggan, form_data)
        except Exception as e:
            flash(f'Data belum valid: {str(e)}. Silakan perbaiki input.', 'danger')
            return render_edit(pelanggan, form_data)
    
    return render_edit(pelanggan)


@pelanggan_bp.route('/detail/<int:id_pelanggan>')
def detail(id_pelanggan):
    """View customer detail"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    pelanggan = PelangganService.get_pelanggan_by_id(id_pelanggan)
    if not pelanggan:
        flash('Pelanggan tidak ditemukan', 'danger')
        return redirect(url_for('pelanggan.index'))
    
    # Get customer transaction history
    riwayat_transaksi = TransaksiService.get_transaksi_by_pelanggan(id_pelanggan, limit=20)
    whatsapp_chat_url = build_whatsapp_chat_url(pelanggan.telepon)
    
    return render_template(
        'pelanggan/detail.html', 
        pelanggan=pelanggan, 
        riwayat_transaksi=riwayat_transaksi,
        whatsapp_chat_url=whatsapp_chat_url,
        active_page='pelanggan'
    )


@pelanggan_bp.route('/delete/<int:id_pelanggan>', methods=['POST'])
def delete(id_pelanggan):
    """Delete customer (soft delete)"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator')
    if access:
        return access
    
    result = PelangganService.delete_pelanggan(id_pelanggan)
    
    if result:
        flash('Pelanggan berhasil dihapus', 'success')
    else:
        flash('Pelanggan tidak ditemukan', 'danger')
    
    return redirect(url_for('pelanggan.index'))


@pelanggan_bp.route('/toggle/<int:id_pelanggan>', methods=['POST'])
def toggle_status(id_pelanggan):
    """Toggle pelanggan active/inactive status via AJAX POST"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator')
    if access:
        return access

    # Accept form or JSON
    status = None
    if request.is_json:
        data = request.get_json()
        status = data.get('status')
    else:
        status = request.form.get('status')

    # Normalize to boolean
    status_bool = False
    if isinstance(status, bool):
        status_bool = status
    elif isinstance(status, str):
        status_bool = status.lower() in ('1', 'true', 'yes', 'on')

    result = PelangganService.set_status(id_pelanggan, status_bool)

    if result:
        return jsonify({'success': True, 'status': status_bool})
    return jsonify({'success': False}), 400


@pelanggan_bp.route('/api/search')
def api_search():
    """API endpoint untuk search pelanggan (untuk autocomplete)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    keyword = request.args.get('q', '', type=str)
    limit = request.args.get('limit', 10, type=int)
    
    if len(keyword) < 2:
        return jsonify([])
    
    pelanggan_list = PelangganService.search_pelanggan(keyword, limit)
    
    result = [
        {
            'id': p.id_pelanggan,
            'nama': p.nama,
            'telepon': p.telepon,
            'email': p.email
        }
        for p in pelanggan_list
    ]
    
    return jsonify(result)
