"""
Layanan Module - Service Management
"""
from pathlib import Path

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from app.layanan.services import LayananService
from app.utils.auth import login_required, require_role

BASE_DIR = Path(__file__).resolve().parent.parent
layanan_bp = Blueprint('layanan', __name__, template_folder=str(BASE_DIR / 'templates' / 'layanan'))


KATEGORI_LIST = ['Charge Tambahan', 'Cuci Kering Lipat', 'Cuci Kering Setrika', 'Cuci Kering','Lainnya','Boneka']
DURASI_UNIT_LIST = ['jam', 'hari']


def render_tambah(form_data=None):
    return render_template(
        'layanan/tambah.html',
        kategori_list=KATEGORI_LIST,
        durasi_unit_list=DURASI_UNIT_LIST,
        form_data=form_data or {},
        active_page='layanan'
    )


def render_edit(layanan, form_data=None):
    return render_template(
        'layanan/edit.html',
        layanan=layanan,
        kategori_list=KATEGORI_LIST,
        durasi_unit_list=DURASI_UNIT_LIST,
        form_data=form_data or {},
        active_page='layanan'
    )


@layanan_bp.route('/')
def index():
    """List all services with pagination and search"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator')
    if access:
        return access
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    kategori = request.args.get('kategori', '', type=str)
    per_page = 10
    
    layanan_list, total_count, total_pages = LayananService.get_all_layanan(
        page=page,
        per_page=per_page,
        search=search if search else None,
        kategori=kategori if kategori else None
    )
    
    kategori_list = LayananService.get_kategori_list()
    
    return render_template(
        'layanan/layanan.html',
        layanan=layanan_list,
        total_count=total_count,
        total_pages=total_pages,
        current_page=page,
        search=search,
        kategori=kategori,
        kategori_list=kategori_list,
        active_page='layanan'
    )


@layanan_bp.route('/tambah', methods=['GET', 'POST'])
def tambah():
    """Add new service"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator')
    if access:
        return access
    
    if request.method == 'POST':
        form_data = request.form
        try:
            nama = request.form.get('nama', '').strip()
            harga = request.form.get('harga', '0')
            durasi = request.form.get('durasi', '1')
            durasi_unit = request.form.get('durasi_unit', 'jam').strip()
            kategori = request.form.get('kategori', '').strip()
            deskripsi = request.form.get('deskripsi', '').strip()
            
            # Validasi
            if not all([nama, harga, durasi, kategori]):
                flash('Nama, Harga, Durasi, dan Kategori harus diisi. Silakan perbaiki data.', 'danger')
                return render_tambah(form_data)
            
            # Create layanan
            result = LayananService.create_layanan(
                nama=nama,
                harga=harga,
                durasi=durasi,
                durasi_unit=durasi_unit,
                kategori=kategori,
                deskripsi=deskripsi
            )
            
            if result:
                flash('Layanan berhasil ditambahkan', 'success')
                return redirect(url_for('layanan.index'))
            else:
                flash('Nama layanan sudah terdaftar. Silakan ganti nama layanan.', 'danger')
                return render_tambah(form_data)
        except Exception as e:
            flash(f'Data belum valid: {str(e)}. Silakan perbaiki input.', 'danger')
            return render_tambah(form_data)
    
    return render_tambah()


@layanan_bp.route('/edit/<int:id_layanan>', methods=['GET', 'POST'])
def edit(id_layanan):
    """Edit service"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator')
    if access:
        return access
    
    layanan = LayananService.get_layanan_by_id(id_layanan)
    if not layanan:
        flash('Layanan tidak ditemukan', 'danger')
        return redirect(url_for('layanan.index'))
    
    if request.method == 'POST':
        form_data = request.form
        try:
            nama = request.form.get('nama', '').strip()
            harga = request.form.get('harga', '0')
            durasi = request.form.get('durasi', '1')
            durasi_unit = request.form.get('durasi_unit', 'jam').strip()
            kategori = request.form.get('kategori', '').strip()
            deskripsi = request.form.get('deskripsi', '').strip()
            
            # Validasi
            if not all([nama, harga, durasi, kategori]):
                flash('Nama, Harga, Durasi, dan Kategori harus diisi. Silakan perbaiki data.', 'danger')
                return render_edit(layanan, form_data)
            
            # Update layanan
            result = LayananService.update_layanan(
                id_layanan=id_layanan,
                nama=nama,
                harga=harga,
                durasi=durasi,
                durasi_unit=durasi_unit,
                kategori=kategori,
                deskripsi=deskripsi
            )
            
            if result:
                flash('Layanan berhasil diperbarui', 'success')
                return redirect(url_for('layanan.index'))
            else:
                flash('Nama layanan sudah terdaftar atau layanan tidak ditemukan. Silakan perbaiki data.', 'danger')
                return render_edit(layanan, form_data)
        except Exception as e:
            flash(f'Data belum valid: {str(e)}. Silakan perbaiki input.', 'danger')
            return render_edit(layanan, form_data)
    
    return render_edit(layanan)


@layanan_bp.route('/detail/<int:id_layanan>')
def detail(id_layanan):
    """View service detail"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    layanan = LayananService.get_layanan_by_id(id_layanan)
    if not layanan:
        flash('Layanan tidak ditemukan', 'danger')
        return redirect(url_for('layanan.index'))
    
    return render_template('layanan/detail.html', layanan=layanan, active_page='layanan')


@layanan_bp.route('/delete/<int:id_layanan>', methods=['POST'])
def delete(id_layanan):
    """Delete service (soft delete)"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator')
    if access:
        return access
    
    result = LayananService.delete_layanan(id_layanan)
    
    if result:
        flash('Layanan berhasil dihapus', 'success')
    else:
        flash('Layanan tidak ditemukan', 'danger')
    
    return redirect(url_for('layanan.index'))


@layanan_bp.route('/api/search')
def api_search():
    """API endpoint untuk search layanan (untuk autocomplete)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    keyword = request.args.get('q', '', type=str)
    kategori = request.args.get('kategori', '', type=str)
    limit = request.args.get('limit', 10, type=int)
    
    if len(keyword) < 2:
        return jsonify([])
    
    layanan_list = LayananService.search_layanan(keyword, limit)
    
    result = [
        {
            'id': l.id_layanan,
            'nama': l.nama,
            'harga': float(l.harga) if l.harga else 0,
            'durasi': l.durasi,
            'durasi_unit': l.durasi_unit,
            'kategori': l.kategori
        }
        for l in layanan_list
    ]
    
    return jsonify(result)


@layanan_bp.route('/api/kategori/<kategori>')
def api_kategori(kategori):
    """API endpoint untuk ambil layanan berdasarkan kategori"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    layanan_list = LayananService.get_layanan_by_kategori(kategori)
    
    result = [
        {
            'id': l.id_layanan,
            'nama': l.nama,
            'harga': float(l.harga) if l.harga else 0,
            'durasi': l.durasi,
            'durasi_unit': l.durasi_unit
        }
        for l in layanan_list
    ]
    
    return jsonify(result)
