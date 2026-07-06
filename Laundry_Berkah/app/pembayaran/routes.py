"""
Pembayaran Module - Payment Management
"""
from pathlib import Path
import re
from urllib.parse import quote

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash
from app.pembayaran.services import PembayaranService
from app.models import Pembayaran, Transaksi, db
from decimal import Decimal

BASE_DIR = Path(__file__).resolve().parent.parent
pembayaran_bp = Blueprint('pembayaran', __name__, template_folder=str(BASE_DIR / 'templates' / 'pembayaran'))


@pembayaran_bp.route('/bayar/<int:id_transaksi>', methods=['GET', 'POST'])
def bayar(id_transaksi):
    """Form pembayaran transaksi"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    transaksi = db.session.get(Transaksi, id_transaksi)
    if not transaksi:
        flash('Transaksi tidak ditemukan', 'danger')
        return redirect(url_for('transaksi.index'))
    
    if request.method == 'POST':
        form_data = request.form
        try:
            jumlah_str = request.form.get('jumlah', '0').strip()
            jumlah_clean = re.sub(r'[^0-9.]', '', jumlah_str)
            jumlah = Decimal(jumlah_clean or '0')
            metode = request.form.get('metode_pembayaran', '').strip()
            catatan = request.form.get('catatan', '').strip()
            
            # Validate
            if jumlah <= 0:
                flash('Jumlah pembayaran harus lebih besar dari 0. Silakan ganti nominal.', 'danger')
                status_pembayaran = PembayaranService.get_pembayaran_status(id_transaksi)
                return render_template('pembayaran/bayar.html', transaksi=transaksi, status_pembayaran=status_pembayaran, metode_list=PembayaranService.METODE_PEMBAYARAN, form_data=form_data, active_page='transaksi')

            if not PembayaranService.validate_metode_pembayaran(metode):
                flash('Metode pembayaran tidak valid. Silakan pilih metode pembayaran.', 'danger')
                status_pembayaran = PembayaranService.get_pembayaran_status(id_transaksi)
                return render_template('pembayaran/bayar.html', transaksi=transaksi, status_pembayaran=status_pembayaran, metode_list=PembayaranService.METODE_PEMBAYARAN, form_data=form_data, active_page='transaksi')
            
            # Create pembayaran
            pembayaran = PembayaranService.create_pembayaran(
                id_transaksi=id_transaksi,
                jumlah=jumlah,
                metode_pembayaran=metode,
                catatan=catatan
            )
            
            if pembayaran:
                flash('Pembayaran berhasil dicatat', 'success')
                return redirect(url_for('pembayaran.struk', id_pembayaran=pembayaran.id_pembayaran))
            else:
                flash('Gagal mencatat pembayaran. Silakan periksa kembali data pembayaran.', 'danger')
                status_pembayaran = PembayaranService.get_pembayaran_status(id_transaksi)
                return render_template('pembayaran/bayar.html', transaksi=transaksi, status_pembayaran=status_pembayaran, metode_list=PembayaranService.METODE_PEMBAYARAN, form_data=form_data, active_page='transaksi')
        except Exception as e:
            flash(f'Data belum valid: {str(e)}. Silakan perbaiki input.', 'danger')
            status_pembayaran = PembayaranService.get_pembayaran_status(id_transaksi)
            return render_template('pembayaran/bayar.html', transaksi=transaksi, status_pembayaran=status_pembayaran, metode_list=PembayaranService.METODE_PEMBAYARAN, form_data=form_data, active_page='transaksi')
    
    # GET request - show form
    status_pembayaran = PembayaranService.get_pembayaran_status(id_transaksi)
    metode_list = PembayaranService.METODE_PEMBAYARAN
    
    return render_template(
        'pembayaran/bayar.html',
        transaksi=transaksi,
        status_pembayaran=status_pembayaran,
        metode_list=metode_list,
        form_data={},
        active_page='transaksi'
    )


@pembayaran_bp.route('/riwayat/<int:id_transaksi>')
def riwayat(id_transaksi):
    """Lihat riwayat pembayaran"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    transaksi = db.session.get(Transaksi, id_transaksi)
    if not transaksi:
        flash('Transaksi tidak ditemukan', 'danger')
        return redirect(url_for('transaksi.index'))
    
    payment_history = PembayaranService.get_payment_history(id_transaksi)
    status_pembayaran = PembayaranService.get_pembayaran_status(id_transaksi)
    
    return render_template(
        'pembayaran/riwayat.html',
        transaksi=transaksi,
        payment_history=payment_history,
        status_pembayaran=status_pembayaran,
        active_page='transaksi'
    )


def build_whatsapp_url(receipt_data):
    phone = receipt_data.get('pelanggan_telepon') or ''
    phone = re.sub(r'[^0-9]', '', phone)
    if not phone:
        return None
    if phone.startswith('0'):
        phone = '62' + phone[1:]
    if phone.startswith('62'):
        pass
    elif phone.startswith('8'):
        phone = '62' + phone
    else:
        # Keep as-is for other international formats
        pass

    message_lines = [
        'Laundry Berkah - Struk Pembayaran',
        f'Order ID: {receipt_data.get("nomor_transaksi", "-")}',
        f'Pelanggan: {receipt_data.get("pelanggan_nama", "-")}',
        f'Total: Rp {int(receipt_data.get("total_harga", 0)):,}'.replace(',', '.'),
        f'Dibayar: Rp {int(receipt_data.get("jumlah_bayar", 0)):,}'.replace(',', '.'),
        f'Kurang: Rp {int(receipt_data.get("kurang", 0)):,}'.replace(',', '.'),
        '',
        'Terima kasih telah menggunakan Laundry Berkah.'
    ]
    return f'https://wa.me/{phone}?text={quote("\n".join(message_lines))}'


@pembayaran_bp.route('/struk/<int:id_pembayaran>')
def struk(id_pembayaran):
    """Print receipt pembayaran"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    receipt_data = PembayaranService.generate_receipt_data(id_pembayaran)
    if not receipt_data:
        flash('Struk tidak ditemukan', 'danger')
        return redirect(url_for('transaksi.index'))

    receipt_data['whatsapp_url'] = build_whatsapp_url(receipt_data)
    return render_template('pembayaran/struk.html', receipt=receipt_data, active_page='transaksi')


@pembayaran_bp.route('/struk/transaksi/<int:id_transaksi>')
def struk_transaksi(id_transaksi):
    """Print receipt transaksi tanpa pembayaran"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    receipt_data = PembayaranService.generate_receipt_data_for_transaksi(id_transaksi)
    if not receipt_data:
        flash('Struk tidak ditemukan', 'danger')
        return redirect(url_for('transaksi.index'))

    receipt_data['whatsapp_url'] = build_whatsapp_url(receipt_data)
    return render_template('pembayaran/struk.html', receipt=receipt_data, active_page='transaksi')


@pembayaran_bp.route('/api/status/<int:id_transaksi>')
def api_status(id_transaksi):
    """API endpoint untuk status pembayaran"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    status = PembayaranService.get_pembayaran_status(id_transaksi)
    if not status:
        return jsonify({'error': 'Transaksi tidak ditemukan'}), 404
    
    return jsonify(status)


@pembayaran_bp.route('/api/calculate-change', methods=['POST'])
def api_calculate_change():
    """API endpoint untuk hitung kembalian"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        id_transaksi = request.json.get('id_transaksi')
        jumlah_bayar = request.json.get('jumlah_bayar')
        metode = request.json.get('metode', 'Cash')
        
        change = PembayaranService.calculate_change(id_transaksi, jumlah_bayar, metode)
        
        return jsonify({
            'kembalian': float(change),
            'metode': metode
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
