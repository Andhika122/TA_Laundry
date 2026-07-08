"""
Pembayaran Module - Payment Management
"""
from pathlib import Path
from io import BytesIO
import re

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash, Response, current_app
from app.pembayaran.services import PembayaranService
from app.models import Pembayaran, Transaksi, db
from app.utils.receipt_image import render_receipt_image
from app.utils.cloudinary_upload import is_cloudinary_configured, upload_image_bytes
from app.utils.fonte_whatsapp import is_fonte_configured as is_fonte_whatsapp_configured, send_whatsapp_via_fonte
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


@pembayaran_bp.route('/struk/image/<int:id_pembayaran>')
def struk_image(id_pembayaran):
    """Return receipt image as PNG."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    receipt_data = PembayaranService.generate_receipt_data(id_pembayaran)
    if not receipt_data:
        flash('Struk tidak ditemukan', 'danger')
        return redirect(url_for('transaksi.index'))

    receipt_data['tracking_url'] = url_for('transaksi.public_status', id=receipt_data.get('id_transaksi') or receipt_data.get('nomor_transaksi'), _external=True)
    try:
        png_bytes = render_receipt_image(receipt_data)
        return Response(png_bytes, mimetype='image/png', headers={
            'Content-Disposition': f'inline; filename="struk-{id_pembayaran}.png"'
        })
    except Exception as exc:
        current_app.logger.exception('Failed to render receipt image for id %s', id_pembayaran)
        return jsonify({'error': 'Failed to render receipt image'}), 500


@pembayaran_bp.route('/struk/image/transaksi/<int:id_transaksi>')
def struk_image_transaksi(id_transaksi):
    """Return receipt image PNG for transaksi without payment."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    receipt_data = PembayaranService.generate_receipt_data_for_transaksi(id_transaksi)
    if not receipt_data:
        flash('Struk tidak ditemukan', 'danger')
        return redirect(url_for('transaksi.index'))

    receipt_data['tracking_url'] = url_for('transaksi.public_status', id=id_transaksi, _external=True)
    try:
        png_bytes = render_receipt_image(receipt_data)
        return Response(png_bytes, mimetype='image/png', headers={
            'Content-Disposition': f'inline; filename="struk-transaksi-{id_transaksi}.png"'
        })
    except Exception as exc:
        current_app.logger.exception('Failed to render receipt image for transaksi %s', id_transaksi)
        return jsonify({'error': 'Failed to render receipt image'}), 500


# QR code endpoint removed: receipts no longer include QR tracking images


@pembayaran_bp.route('/struk/<int:id_pembayaran>')
def struk(id_pembayaran):
    """Print receipt pembayaran"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    receipt_data = PembayaranService.generate_receipt_data(id_pembayaran)
    if not receipt_data:
        flash('Struk tidak ditemukan', 'danger')
        return redirect(url_for('transaksi.index'))

    receipt_data['struk_image_url'] = url_for('pembayaran.struk_image', id_pembayaran=id_pembayaran, _external=True)
    receipt_data['tracking_url'] = url_for('transaksi.public_status', id=receipt_data.get('id_transaksi'), _external=True)
    if is_cloudinary_configured():
        try:
            image_bytes = render_receipt_image(receipt_data)
            cloud_url = upload_image_bytes(image_bytes, public_id=f'struk_{id_pembayaran}')
            if cloud_url:
                receipt_data['whatsapp_image_url'] = cloud_url
            else:
                receipt_data['whatsapp_image_url'] = receipt_data['struk_image_url']
        except Exception:
            current_app.logger.exception('Cloudinary upload or rendering failed for pembayaran %s', id_pembayaran)
            receipt_data['whatsapp_image_url'] = receipt_data['struk_image_url']
    else:
        receipt_data['whatsapp_image_url'] = receipt_data['struk_image_url']

    receipt_data['whatsapp_via_fonte_enabled'] = is_fonte_whatsapp_configured()
    receipt_data['whatsapp_via_fonte_url'] = url_for('pembayaran.kirim_whatsapp', id_pembayaran=id_pembayaran)
    return render_template('pembayaran/struk.html', receipt=receipt_data, active_page='transaksi')


@pembayaran_bp.route('/kirim-wa/<int:id_pembayaran>', methods=['POST'])
def kirim_whatsapp(id_pembayaran):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    receipt_data = PembayaranService.generate_receipt_data(id_pembayaran)
    if not receipt_data:
        flash('Struk tidak ditemukan', 'danger')
        return redirect(url_for('pembayaran.struk', id_pembayaran=id_pembayaran))

    receipt_data['struk_image_url'] = url_for('pembayaran.struk_image', id_pembayaran=id_pembayaran, _external=True)
    if is_cloudinary_configured():
        image_bytes = render_receipt_image(receipt_data)
        cloud_url = upload_image_bytes(image_bytes, public_id=f'struk_{id_pembayaran}')
        image_url = cloud_url or receipt_data['struk_image_url']
    else:
        image_url = receipt_data['struk_image_url']

    success, message = send_whatsapp_via_fonte(receipt_data, image_url=image_url)
    if success:
        flash('Struk dikirim ke WhatsApp pelanggan via Fonte.', 'success')
    else:
        flash(f'Gagal mengirim WA via Fonte: {message}', 'danger')
    return redirect(url_for('pembayaran.struk', id_pembayaran=id_pembayaran))


@pembayaran_bp.route('/struk/transaksi/<int:id_transaksi>')
def struk_transaksi(id_transaksi):
    """Print receipt transaksi tanpa pembayaran"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    receipt_data = PembayaranService.generate_receipt_data_for_transaksi(id_transaksi)
    if not receipt_data:
        flash('Struk tidak ditemukan', 'danger')
        return redirect(url_for('transaksi.index'))

    receipt_data['tracking_url'] = url_for('transaksi.public_status', id=id_transaksi, _external=True)
    receipt_data['struk_image_url'] = url_for('pembayaran.struk_image_transaksi', id_transaksi=id_transaksi, _external=True)
    if is_cloudinary_configured():
        try:
            image_bytes = render_receipt_image(receipt_data)
            cloud_url = upload_image_bytes(image_bytes, public_id=f'struk_transaksi_{id_transaksi}')
            if cloud_url:
                receipt_data['whatsapp_image_url'] = cloud_url
            else:
                receipt_data['whatsapp_image_url'] = receipt_data['struk_image_url']
        except Exception:
            current_app.logger.exception('Cloudinary upload or rendering failed for transaksi %s', id_transaksi)
            receipt_data['whatsapp_image_url'] = receipt_data['struk_image_url']
    else:
        receipt_data['whatsapp_image_url'] = receipt_data['struk_image_url']

    receipt_data['whatsapp_via_fonte_enabled'] = is_fonte_whatsapp_configured()
    receipt_data['whatsapp_via_fonte_url'] = url_for('pembayaran.kirim_whatsapp_transaksi', id_transaksi=id_transaksi)
    return render_template('pembayaran/struk.html', receipt=receipt_data, active_page='transaksi')


@pembayaran_bp.route('/kirim-wa/transaksi/<int:id_transaksi>', methods=['POST'])
def kirim_whatsapp_transaksi(id_transaksi):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    receipt_data = PembayaranService.generate_receipt_data_for_transaksi(id_transaksi)
    if not receipt_data:
        flash('Struk tidak ditemukan', 'danger')
        return redirect(url_for('pembayaran.struk_transaksi', id_transaksi=id_transaksi))

    receipt_data['struk_image_url'] = url_for('pembayaran.struk_image_transaksi', id_transaksi=id_transaksi, _external=True)
    if is_cloudinary_configured():
        image_bytes = render_receipt_image(receipt_data)
        cloud_url = upload_image_bytes(image_bytes, public_id=f'struk_transaksi_{id_transaksi}')
        image_url = cloud_url or receipt_data['struk_image_url']
    else:
        image_url = receipt_data['struk_image_url']

    success, message = send_whatsapp_via_fonte(receipt_data, image_url=image_url)
    if success:
        flash('Struk dikirim ke WhatsApp pelanggan via Fonte.', 'success')
    else:
        flash(f'Gagal mengirim WA via Fonte: {message}', 'danger')
    return redirect(url_for('pembayaran.struk_transaksi', id_transaksi=id_transaksi))


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
