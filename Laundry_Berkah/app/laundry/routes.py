"""
Laundry Module - Laundry Process Management
"""
from pathlib import Path

from flask import Blueprint, render_template, redirect, url_for, request
from app.transaksi.services import TransaksiService
from app.pembayaran.services import PembayaranService
from app.utils.auth import login_required, require_role

BASE_DIR = Path(__file__).resolve().parent.parent
laundry_bp = Blueprint('laundry', __name__, template_folder=str(BASE_DIR / 'templates' / 'laundry'))


@laundry_bp.route('/')
def index():
    """Laundry process dashboard"""
    if login_required():
        return login_required()
    
    return redirect(url_for('laundry.antrian'))


@laundry_bp.route('/antrian')
def antrian():
    """Queue/Antrian"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator', 'Kasir')
    if access:
        return access
    
    keyword = request.args.get('search', '', type=str).strip()
    status_counts = TransaksiService.get_status_counts()
    
    if keyword:
        transaksi_list = TransaksiService.search_transaksi_by_status_and_keyword(['Antrian'], keyword, limit=50)
    else:
        transaksi_list = TransaksiService.get_transaksi_by_statuses(['Antrian'], limit=50)
    
    payment_status_map = {
        trx.id_transaksi: PembayaranService.get_pembayaran_status(trx.id_transaksi)
        for trx in transaksi_list
    }
    return render_template('antrian.html', status_counts=status_counts, transaksi_list=transaksi_list, payment_status_map=payment_status_map, search_keyword=keyword, active_page='laundry')


@laundry_bp.route('/proses')
def proses():
    """Proses laundry in progress"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator', 'Kasir')
    if access:
        return access
    
    keyword = request.args.get('search', '', type=str).strip()
    status_counts = TransaksiService.get_status_counts()
    
    if keyword:
        transaksi_list = TransaksiService.search_transaksi_by_status_and_keyword(['Cuci', 'Pengeringan', 'Setrika', 'Packing'], keyword, limit=50)
    else:
        transaksi_list = TransaksiService.get_transaksi_by_statuses(['Cuci', 'Pengeringan', 'Setrika', 'Packing'], limit=50)
    
    payment_status_map = {
        trx.id_transaksi: PembayaranService.get_pembayaran_status(trx.id_transaksi)
        for trx in transaksi_list
    }
    return render_template('proses.html', status_counts=status_counts, transaksi_list=transaksi_list, payment_status_map=payment_status_map, search_keyword=keyword, active_page='laundry')


@laundry_bp.route('/siap_ambil')
def siap_ambil():
    """Laundry ready for pickup"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator', 'Kasir')
    if access:
        return access
    
    keyword = request.args.get('search', '', type=str).strip()
    status_counts = TransaksiService.get_status_counts()
    
    if keyword:
        transaksi_list = TransaksiService.search_transaksi_by_status_and_keyword(['Siap Ambil'], keyword, limit=50)
    else:
        transaksi_list = TransaksiService.get_transaksi_by_statuses(['Siap Ambil'], limit=50)
    
    payment_status_map = {
        trx.id_transaksi: PembayaranService.get_pembayaran_status(trx.id_transaksi)
        for trx in transaksi_list
    }
    return render_template('siap_ambil.html', status_counts=status_counts, transaksi_list=transaksi_list, payment_status_map=payment_status_map, search_keyword=keyword, active_page='laundry')


@laundry_bp.route('/selesai')
def selesai():
    """Laundry completed"""
    if login_required():
        return login_required()

    access = require_role('Admin', 'Operator', 'Kasir')
    if access:
        return access
    
    keyword = request.args.get('search', '', type=str).strip()
    status_counts = TransaksiService.get_status_counts()
    
    if keyword:
        transaksi_list = TransaksiService.search_transaksi_by_status_and_keyword(['Selesai'], keyword, limit=50)
    else:
        transaksi_list = TransaksiService.get_transaksi_by_statuses(['Selesai'], limit=50)
    
    payment_status_map = {
        trx.id_transaksi: PembayaranService.get_pembayaran_status(trx.id_transaksi)
        for trx in transaksi_list
    }
    return render_template('selesai.html', status_counts=status_counts, transaksi_list=transaksi_list, payment_status_map=payment_status_map, search_keyword=keyword, active_page='laundry')
