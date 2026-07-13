"""
Transaksi Module - Transaction Management
"""
from pathlib import Path

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash, current_app
from app.transaksi.services import TransaksiService
from app.layanan.services import LayananService
from app.pelanggan.services import PelangganService
from app.pembayaran.services import PembayaranService
from app.models import Layanan, Pelanggan, Promo, Parfum, Transaksi, db
from app.utils.whatsapp import build_whatsapp_chat_url

BASE_DIR = Path(__file__).resolve().parent.parent
transaksi_bp = Blueprint('transaksi', __name__, template_folder=str(BASE_DIR / 'templates' / 'transaksi'))


def build_selected_items(form_data):
    layanan_ids = form_data.getlist('layanan[]') if form_data else []
    kuantitas_list = form_data.getlist('kuantitas[]') if form_data else []
    parfum_ids = form_data.getlist('parfum[]') if form_data else []

    selected_items = []
    for index, layanan_id in enumerate(layanan_ids):
        if not layanan_id:
            continue

        try:
            layanan_id_int = int(layanan_id)
        except (TypeError, ValueError):
            continue

        layanan = db.session.get(Layanan, layanan_id_int)
        selected_items.append({
            'id_layanan': layanan_id_int,
            'nama': layanan.nama if layanan else f'Layanan #{layanan_id}',
            'harga': float(layanan.harga) if layanan and layanan.harga else 0,
            'kuantitas': kuantitas_list[index] if index < len(kuantitas_list) else '1',
            'id_parfum': parfum_ids[index] if index < len(parfum_ids) else '',
        })
    return selected_items


def render_baru(form_data=None, selected_items=None, selected_pelanggan=None, edit_mode=False, transaksi=None):
    kategori_list = LayananService.get_kategori_list()
    # Do not present expired or not-yet-started promos as selectable discounts.
    promo_list = [
        promo.to_dict()
        for promo in Promo.query.filter_by(is_active=True).all()
        if promo.is_valid()
    ]
    parfum_list = [parfum.to_dict() for parfum in Parfum.query.filter_by(is_active=True).order_by(Parfum.nama).all()]
    if form_data and form_data.get('id_pelanggan'):
        try:
            selected_pelanggan = db.session.get(Pelanggan, int(form_data.get('id_pelanggan')))
        except (TypeError, ValueError):
            selected_pelanggan = selected_pelanggan

    if selected_items is None:
        selected_items = build_selected_items(form_data)

    return render_template(
        'transaksi/baru.html',
        kategori_list=kategori_list,
        promo_list=promo_list,
        form_data=form_data or {},
        selected_items=selected_items,
        selected_pelanggan=selected_pelanggan,
        edit_mode=edit_mode,
        transaksi=transaksi,
        active_page='transaksi',
        parfum_list=parfum_list
    )


@transaksi_bp.route('/')
def index():
    """List all transactions"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '', type=str)
    per_page = 10
    
    transaksi_list, total_count, total_pages = TransaksiService.get_all_transaksi(
        page=page,
        per_page=per_page,
        status=status if status else None
    )
    payment_status_map = {
        t.id_transaksi: PembayaranService.get_pembayaran_status(t.id_transaksi)
        for t in transaksi_list
    }
    whatsapp_chat_map = {
        t.id_transaksi: build_whatsapp_chat_url(t.pelanggan.telepon)
        for t in transaksi_list
    }
    
    return render_template(
        'transaksi/list.html',
        transaksi=transaksi_list,
        payment_status_map=payment_status_map,
        whatsapp_chat_map=whatsapp_chat_map,
        total_count=total_count,
        total_pages=total_pages,
        current_page=page,
        status=status,
        active_page='transaksi'
    )


@transaksi_bp.route('/baru', methods=['GET', 'POST'])
def baru():
    """Create new transaction"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        form_data = request.form
        try:
            id_pelanggan = request.form.get('id_pelanggan', type=int)
            catatan = request.form.get('catatan', '').strip()
            promo_id = request.form.get('promo_id', type=int)
            
            if not id_pelanggan:
                flash('Pelanggan harus dipilih. Data lain tetap tersimpan, silakan pilih pelanggan.', 'danger')
                return render_baru(form_data)

            # Ambil items dari form array
            item_count = len(request.form.getlist('layanan[]'))
            if item_count == 0:
                flash('Minimal harus ada satu layanan dipilih. Silakan tambahkan layanan.', 'danger')
                return render_baru(form_data)
            
            items = []
            layanan_ids = request.form.getlist('layanan[]')
            kuantitas_list = request.form.getlist('kuantitas[]')
            parfum_ids = request.form.getlist('parfum[]')
            
            for i in range(item_count):
                items.append({
                    'id_layanan': int(layanan_ids[i]),
                    'kuantitas': int(kuantitas_list[i]) if kuantitas_list[i] else 1,
                    'id_parfum': int(parfum_ids[i]) if parfum_ids[i] else None
                })
            
            # Create transaksi
            transaksi = TransaksiService.create_transaksi(
                id_pelanggan=id_pelanggan,
                items=items,
                promo_id=promo_id if promo_id else None,
                catatan=catatan
            )
            
            payment_option = request.form.get('payment_option', 'pay_later')
            if transaksi and payment_option == 'pay_now':
                pembayaran = PembayaranService.create_pembayaran(
                    id_transaksi=transaksi.id_transaksi,
                    jumlah=transaksi.total_harga,
                    metode_pembayaran='Cash',
                    catatan='Pembayaran otomatis bayar sekarang'
                )
                if pembayaran:
                    flash('Transaksi berhasil dibuat dan dibayar lunas', 'success')
                else:
                    flash('Transaksi dibuat, tetapi pembayaran otomatis gagal. Silakan lakukan pembayaran manual.', 'warning')
                return redirect(url_for('transaksi.detail', id_transaksi=transaksi.id_transaksi))

            if transaksi:
                flash('Transaksi berhasil dibuat', 'success')
                return redirect(url_for('transaksi.detail', id_transaksi=transaksi.id_transaksi))
            else:
                flash('Gagal membuat transaksi. Silakan periksa kembali data transaksi.', 'danger')
                return render_baru(form_data)
        except Exception as e:
            flash(f'Data belum valid: {str(e)}. Silakan perbaiki input.', 'danger')
            return render_baru(form_data)

    return render_baru()


@transaksi_bp.route('/edit/<int:id_transaksi>', methods=['GET', 'POST'])
def edit(id_transaksi):
    """Edit existing transaction"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    transaksi = TransaksiService.get_transaksi_by_id(id_transaksi)
    if not transaksi:
        flash('Transaksi tidak ditemukan', 'danger')
        return redirect(url_for('transaksi.index'))

    role = session.get('role')
    if not TransaksiService.can_edit_transaksi(role, id_transaksi):
        flash('Anda tidak memiliki izin untuk mengedit transaksi ini.', 'warning')
        return redirect(url_for('transaksi.detail', id_transaksi=id_transaksi))

    if request.method == 'POST':
        form_data = request.form
        try:
            id_pelanggan = request.form.get('id_pelanggan', type=int)
            catatan = request.form.get('catatan', '').strip()
            promo_id = request.form.get('promo_id', type=int)

            if not id_pelanggan:
                flash('Pelanggan harus dipilih. Data lain tetap tersimpan, silakan pilih pelanggan.', 'danger')
                return render_baru(form_data, selected_pelanggan=transaksi.pelanggan, edit_mode=True, transaksi=transaksi)

            item_count = len(request.form.getlist('layanan[]'))
            if item_count == 0:
                flash('Minimal harus ada satu layanan dipilih. Silakan tambahkan layanan.', 'danger')
                return render_baru(form_data, selected_pelanggan=transaksi.pelanggan, edit_mode=True, transaksi=transaksi)

            items = []
            layanan_ids = request.form.getlist('layanan[]')
            kuantitas_list = request.form.getlist('kuantitas[]')
            parfum_ids = request.form.getlist('parfum[]')

            for i in range(item_count):
                items.append({
                    'id_layanan': int(layanan_ids[i]),
                    'kuantitas': int(kuantitas_list[i]) if kuantitas_list[i] else 1,
                    'id_parfum': int(parfum_ids[i]) if parfum_ids[i] else None
                })

            updated_transaksi = TransaksiService.update_transaksi(
                id_transaksi=id_transaksi,
                id_pelanggan=id_pelanggan,
                items=items,
                promo_id=promo_id if promo_id else None,
                catatan=catatan
            )

            if updated_transaksi:
                flash('Transaksi berhasil diperbarui', 'success')
                return redirect(url_for('transaksi.detail', id_transaksi=id_transaksi))
            else:
                flash('Gagal memperbarui transaksi. Silakan periksa kembali data.', 'danger')
                return render_baru(form_data, selected_pelanggan=transaksi.pelanggan, edit_mode=True, transaksi=transaksi)
        except Exception as e:
            flash(f'Data belum valid: {str(e)}. Silakan perbaiki input.', 'danger')
            return render_baru(form_data, selected_pelanggan=transaksi.pelanggan, edit_mode=True, transaksi=transaksi)

    selected_items = [
        {
            'id_layanan': detail.id_layanan,
            'nama': detail.layanan.nama if detail.layanan else f'Layanan #{detail.id_layanan}',
            'harga': float(detail.harga_satuan or 0),
            'kuantitas': int(detail.kuantitas or 1),
            'id_parfum': detail.id_parfum
        }
        for detail in transaksi.detail_transaksi
    ]

    return render_baru(
        form_data={
            'id_pelanggan': transaksi.id_pelanggan,
            'catatan': transaksi.catatan or '',
            'promo_id': transaksi.promo_id
        },
        selected_items=selected_items,
        selected_pelanggan=transaksi.pelanggan,
        edit_mode=True,
        transaksi=transaksi
    )


@transaksi_bp.route('/detail/<int:id_transaksi>')
def detail(id_transaksi):
    """View transaction detail"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    transaksi = TransaksiService.get_transaksi_by_id(id_transaksi)
    if not transaksi:
        flash('Transaksi tidak ditemukan', 'danger')
        return redirect(url_for('transaksi.index'))
    
    payment_status = PembayaranService.get_pembayaran_status(id_transaksi)
    next_status = TransaksiService.get_next_status(id_transaksi)
    can_advance = bool(next_status and (next_status != 'Selesai' or (payment_status and payment_status.get('status') == 'Lunas')))

    latest_payment = PembayaranService.get_pembayaran_by_transaksi(id_transaksi)
    receipt_print_url = None
    if latest_payment:
        latest_pembayaran = latest_payment[0]
        receipt_print_url = url_for('pembayaran.struk', id_pembayaran=latest_pembayaran.id_pembayaran)
    else:
        receipt_print_url = url_for('pembayaran.struk_transaksi', id_transaksi=id_transaksi)

    whatsapp_chat_url = build_whatsapp_chat_url(transaksi.pelanggan.telepon)
    role = session.get('role')
    can_cancel = TransaksiService.can_cancel_transaksi(role, id_transaksi)

    return render_template(
        'transaksi/detail.html',
        transaksi=transaksi,
        payment_status=payment_status,
        next_status=next_status,
        can_advance=can_advance,
        receipt_print_url=receipt_print_url,
        whatsapp_chat_url=whatsapp_chat_url,
        can_cancel=can_cancel,
        role=role,
        active_page='transaksi'
    )


@transaksi_bp.route('/cancel/<int:id_transaksi>', methods=['POST'])
def cancel(id_transaksi):
    """Cancel a transaction if permitted by the current role."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    transaksi = TransaksiService.get_transaksi_by_id(id_transaksi)
    if not transaksi:
        flash('Transaksi tidak ditemukan', 'danger')
        return redirect(url_for('transaksi.index'))

    role = session.get('role')
    if not TransaksiService.can_cancel_transaksi(role, id_transaksi):
        flash('Anda tidak memiliki izin untuk membatalkan transaksi yang sudah dibayar lunas.', 'warning')
        return redirect(url_for('transaksi.detail', id_transaksi=id_transaksi))

    if TransaksiService.cancel_transaksi(id_transaksi):
        current_app.logger.info('Transaksi %s berhasil dibatalkan oleh user_id %s role %s', id_transaksi, session.get('user_id'), role)
        flash('Transaksi berhasil dibatalkan.', 'success')
    else:
        current_app.logger.error('Gagal membatalkan transaksi %s oleh user_id %s role %s', id_transaksi, session.get('user_id'), role)
        flash('Gagal membatalkan transaksi. Silakan coba lagi.', 'danger')

    return redirect(url_for('transaksi.index'))



@transaksi_bp.route('/nota')
def public_status():
    """Public status page for laundry tracking via QR."""
    id_transaksi = request.args.get('id', type=int)
    if not id_transaksi:
        return render_template('transaksi/public_status.html', error='Transaksi tidak ditemukan.', transaksi=None, payment_status=None)

    transaksi = TransaksiService.get_transaksi_by_id(id_transaksi)
    if not transaksi:
        return render_template('transaksi/public_status.html', error='Transaksi tidak ditemukan.', transaksi=None, payment_status=None)

    payment_status = PembayaranService.get_pembayaran_status(id_transaksi)
    return render_template(
        'transaksi/public_status.html',
        transaksi=transaksi,
        payment_status=payment_status,
        error=None
    )


@transaksi_bp.route('/api/layanan')
@transaksi_bp.route('/api/layanan/<kategori>')
def api_layanan_by_kategori(kategori=None):
    """API endpoint untuk ambil layanan berdasarkan kategori"""
    # Allow public access to layanan list so frontend can fetch available
    # services without requiring user login. This endpoint only returns
    # non-sensitive read-only data.
    kategori = (kategori or request.args.get('kategori', '', type=str)).strip()
    if not kategori:
        return jsonify([])

    layanan_list = LayananService.get_layanan_by_kategori(kategori)
    
    result = [
        {
            'id': l.id_layanan,
            'nama': l.nama,
            'harga': float(l.harga),
            'durasi': l.durasi,
            'durasi_unit': l.durasi_unit
        }
        for l in layanan_list
    ]
    
    return jsonify(result)


@transaksi_bp.route('/api/pelanggan/<keyword>')
def api_search_pelanggan(keyword):
    """API endpoint untuk search pelanggan"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    pelanggan_list = PelangganService.search_pelanggan(keyword, limit=10)
    
    result = [
        {
            'id': p.id_pelanggan,
            'nama': p.nama,
            'telepon': p.telepon,
            'alamat': p.alamat
        }
        for p in pelanggan_list
    ]
    
    return jsonify(result)


@transaksi_bp.route('/api/pelanggan', methods=['POST'])
def api_create_pelanggan():
    """API endpoint untuk create pelanggan baru dari halaman transaksi"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    nama = data.get('nama', '').strip()
    telepon = data.get('telepon', '').strip()
    email = data.get('email', '').strip()
    alamat = data.get('alamat', '').strip()
    jenis_kelamin = data.get('jenis_kelamin', '').strip()

    if not all([nama, telepon, email, alamat, jenis_kelamin]):
        return jsonify({'error': 'Semua field pelanggan harus diisi.'}), 400

    pelanggan = PelangganService.create_pelanggan(
        nama=nama,
        telepon=telepon,
        email=email,
        alamat=alamat,
        jenis_kelamin=jenis_kelamin
    )

    if not pelanggan:
        return jsonify({'error': 'Nomor telepon sudah terdaftar atau data tidak valid.'}), 400

    return jsonify({
        'id': pelanggan.id_pelanggan,
        'nama': pelanggan.nama,
        'telepon': pelanggan.telepon,
        'email': pelanggan.email,
        'alamat': pelanggan.alamat
    })


@transaksi_bp.route('/api/promo/<int:promo_id>')
def api_promo_detail(promo_id):
    """API endpoint untuk detail promo"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    promo = db.session.get(Promo, promo_id)
    if not promo or not promo.is_valid():
        return jsonify({'error': 'Promo tidak valid'}), 400
    
    return jsonify({
        'id': promo.id_promo,
        'nama': promo.nama,
        'tipe': promo.tipe,
        'nilai': float(promo.nilai),
        'minimal_transaksi': float(promo.minimal_transaksi) if promo.minimal_transaksi else 0
    })


@transaksi_bp.route('/api/update-status/<int:id_transaksi>', methods=['POST'])
def api_update_status(id_transaksi):
    """API endpoint untuk update status transaksi"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json() or {}
    status_baru = data.get('status_baru', '').strip()
    
    if not status_baru:
        return jsonify({'error': 'Status tidak valid'}), 400
    
    transaksi = TransaksiService.update_status_transaksi(id_transaksi, status_baru)
    
    if not transaksi:
        return jsonify({'error': 'Gagal mengupdate status atau transaksi tidak ditemukan'}), 400
    
    return jsonify({
        'success': True,
        'message': f'Status berhasil diupdate menjadi {status_baru}',
        'status_proses': transaksi.status_proses
    })


@transaksi_bp.route('/api/update-status-next/<int:id_transaksi>', methods=['POST'])
def api_update_status_next(id_transaksi):
    """API endpoint untuk move transaction to the next process status"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    from app.pembayaran.services import PembayaranService

    transaksi = db.session.get(Transaksi, id_transaksi)
    if not transaksi:
        return jsonify({'error': 'Transaksi tidak ditemukan'}), 404

    next_status = TransaksiService.get_next_status(id_transaksi)
    if next_status == 'Selesai' and not PembayaranService.is_transaksi_paid(id_transaksi):
        return jsonify({'error': 'Pembayaran belum lunas. Silakan selesaikan pembayaran terlebih dahulu.'}), 400

    updated_transaksi = TransaksiService.update_status_to_next(id_transaksi)
    if not updated_transaksi:
        return jsonify({'error': 'Gagal mengupdate status transaksi'}), 400

    return jsonify({
        'success': True,
        'message': f'Status berhasil diupdate menjadi {updated_transaksi.status_proses}',
        'status_proses': updated_transaksi.status_proses
    })
