"""
Layanan (Service/Package) Services
Layanan untuk CRUD operasi layanan/paket laundry
"""

import re

from app.models import Layanan
from app import db
from sqlalchemy import or_


class LayananService:
    """Layanan untuk manajemen layanan/paket"""

    @staticmethod
    def _normalize_name(value):
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value).strip()).casefold()

    @staticmethod
    def _has_duplicate_layanan(nama, exclude_id=None):
        normalized_name = LayananService._normalize_name(nama)
        if not normalized_name:
            return False

        query = Layanan.query
        if exclude_id is not None:
            query = query.filter(Layanan.id_layanan != exclude_id)

        for layanan in query.all():
            if LayananService._normalize_name(layanan.nama) == normalized_name:
                return True
        return False
    
    @staticmethod
    def create_layanan(nama, harga, durasi, durasi_unit, kategori, deskripsi):
        """
        Buat layanan baru
        Returns: Layanan object atau None jika gagal
        """
        try:
            if LayananService._has_duplicate_layanan(nama):
                return None
            
            layanan = Layanan(
                nama=nama,
                harga=float(harga),
                durasi=int(durasi),
                durasi_unit=durasi_unit,
                kategori=kategori,
                deskripsi=deskripsi,
                is_active=True
            )
            
            db.session.add(layanan)
            db.session.commit()
            return layanan
        except Exception as e:
            db.session.rollback()
            print(f"Error in create_layanan: {str(e)}")
            return None
    
    @staticmethod
    def get_layanan_by_id(id_layanan):
        """
        Ambil data layanan berdasarkan ID
        Returns: Layanan object atau None
        """
        try:
            return db.session.get(Layanan, id_layanan)
        except Exception as e:
            print(f"Error in get_layanan_by_id: {str(e)}")
            return None
    
    @staticmethod
    def get_all_layanan(page=1, per_page=10, search=None, kategori=None):
        """
        Ambil semua layanan dengan pagination
        Returns: tuple (layanan_list, total_count, pages)
        """
        try:
            query = Layanan.query.filter_by(is_active=True)
            
            # Filter berdasarkan kategori
            if kategori:
                query = query.filter_by(kategori=kategori)
            
            # Filter berdasarkan search
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Layanan.nama.ilike(search_term),
                        Layanan.deskripsi.ilike(search_term)
                    )
                )
            
            # Sort by nama
            query = query.order_by(Layanan.nama.asc())
            
            # Pagination
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return paginated.items, paginated.total, paginated.pages
        except Exception as e:
            print(f"Error in get_all_layanan: {str(e)}")
            return [], 0, 0
    
    @staticmethod
    def update_layanan(id_layanan, nama, harga, durasi, durasi_unit, kategori, deskripsi):
        """
        Update data layanan
        Returns: bool - True jika berhasil, False jika gagal
        """
        try:
            layanan = db.session.get(Layanan, id_layanan)
            if not layanan:
                return False
            
            if LayananService._has_duplicate_layanan(nama, exclude_id=id_layanan):
                return False
            
            layanan.nama = nama
            layanan.harga = float(harga)
            layanan.durasi = int(durasi)
            layanan.durasi_unit = durasi_unit
            layanan.kategori = kategori
            layanan.deskripsi = deskripsi
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error in update_layanan: {str(e)}")
            return False
    
    @staticmethod
    def toggle_layanan_status(id_layanan):
        """
        Toggle status layanan (active/inactive)
        Returns: bool - True jika berhasil
        """
        try:
            layanan = db.session.get(Layanan, id_layanan)
            if not layanan:
                return False
            
            layanan.is_active = not layanan.is_active
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error in toggle_layanan_status: {str(e)}")
            return False
    
    @staticmethod
    def delete_layanan(id_layanan):
        """
        Soft delete layanan (set is_active=False)
        Returns: bool - True jika berhasil
        """
        try:
            layanan = db.session.get(Layanan, id_layanan)
            if not layanan:
                return False
            
            layanan.is_active = False
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error in delete_layanan: {str(e)}")
            return False
    
    @staticmethod
    def get_layanan_by_kategori(kategori):
        """
        Ambil semua layanan berdasarkan kategori
        Returns: list of Layanan
        """
        try:
            return Layanan.query.filter_by(
                kategori=kategori,
                is_active=True
            ).order_by(Layanan.nama.asc()).all()
        except Exception as e:
            print(f"Error in get_layanan_by_kategori: {str(e)}")
            return []
    
    @staticmethod
    def get_kategori_list():
        """
        Ambil list semua kategori unik
        Returns: list of unique categories
        """
        try:
            categories = db.session.query(
                Layanan.kategori
            ).filter_by(is_active=True).distinct().all()
            
            return [cat[0] for cat in categories if cat[0]]
        except Exception as e:
            print(f"Error in get_kategori_list: {str(e)}")
            return []
    
    @staticmethod
    def search_layanan(keyword, limit=10):
        """
        Search layanan berdasarkan nama
        Returns: list of layanan
        """
        try:
            search_term = f"%{keyword}%"
            layanan = Layanan.query.filter(
                Layanan.is_active == True,
                Layanan.nama.ilike(search_term)
            ).limit(limit).all()
            
            return layanan
        except Exception as e:
            print(f"Error in search_layanan: {str(e)}")
            return []
