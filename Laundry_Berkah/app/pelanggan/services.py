"""
Pelanggan (Customer) Services
Layanan untuk CRUD operasi pelanggan
"""

import re

from app.models import Pelanggan
from app import db
from sqlalchemy import or_


class PelangganService:
    """Layanan untuk manajemen pelanggan"""

    @staticmethod
    def _normalize_text(value):
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value).strip()).casefold()

    @staticmethod
    def _normalize_telepon(value):
        if value is None:
            return ""
        return re.sub(r"[\s\-\.\(\)]+", "", str(value).strip())

    @staticmethod
    def _has_duplicate_pelanggan(nama, telepon, exclude_id=None):
        normalized_nama = PelangganService._normalize_text(nama)
        normalized_telepon = PelangganService._normalize_telepon(telepon)
        query = Pelanggan.query.filter(Pelanggan.status == True)
        if exclude_id is not None:
            query = query.filter(Pelanggan.id_pelanggan != exclude_id)

        for pelanggan in query.all():
            if normalized_telepon and PelangganService._normalize_telepon(pelanggan.telepon) == normalized_telepon:
                return True
            if normalized_nama and PelangganService._normalize_text(pelanggan.nama) == normalized_nama:
                return True
        return False
    
    @staticmethod
    def create_pelanggan(nama, telepon, email, alamat, jenis_kelamin):
        """
        Buat pelanggan baru
        Returns: Pelanggan object atau None jika gagal
        """
        try:
            if PelangganService._has_duplicate_pelanggan(nama, telepon):
                return None
            
            pelanggan = Pelanggan(
                nama=nama,
                telepon=telepon,
                email=email,
                alamat=alamat,
                jenis_kelamin=jenis_kelamin,
                status=True
            )
            
            db.session.add(pelanggan)
            db.session.commit()
            return pelanggan
        except Exception as e:
            db.session.rollback()
            print(f"Error in create_pelanggan: {str(e)}")
            return None
    
    @staticmethod
    def get_pelanggan_by_id(id_pelanggan):
        """
        Ambil data pelanggan berdasarkan ID
        Returns: Pelanggan object atau None
        """
        try:
            return db.session.get(Pelanggan, id_pelanggan)
        except Exception as e:
            print(f"Error in get_pelanggan_by_id: {str(e)}")
            return None
    
    @staticmethod
    def get_all_pelanggan(page=1, per_page=10, search=None):
        """
        Ambil semua pelanggan dengan pagination
        Returns: tuple (pelanggan_list, total_count, pages)
        """
        try:
            query = Pelanggan.query.filter_by(status=True)
            
            # Filter berdasarkan search
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Pelanggan.nama.ilike(search_term),
                        Pelanggan.telepon.ilike(search_term),
                        Pelanggan.email.ilike(search_term)
                    )
                )
            
            # Sort by nama
            query = query.order_by(Pelanggan.nama.asc())
            
            # Pagination
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return paginated.items, paginated.total, paginated.pages
        except Exception as e:
            print(f"Error in get_all_pelanggan: {str(e)}")
            return [], 0, 0
    
    @staticmethod
    def update_pelanggan(id_pelanggan, nama, telepon, email, alamat, jenis_kelamin):
        """
        Update data pelanggan
        Returns: bool - True jika berhasil, False jika gagal
        """
        try:
            pelanggan = db.session.get(Pelanggan, id_pelanggan)
            if not pelanggan:
                return False
            
            if PelangganService._has_duplicate_pelanggan(nama, telepon, exclude_id=id_pelanggan):
                return False
            
            pelanggan.nama = nama
            pelanggan.telepon = telepon
            pelanggan.email = email
            pelanggan.alamat = alamat
            pelanggan.jenis_kelamin = jenis_kelamin
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error in update_pelanggan: {str(e)}")
            return False
    
    @staticmethod
    def delete_pelanggan(id_pelanggan):
        """
        Soft delete pelanggan (set status=False)
        Returns: bool - True jika berhasil
        """
        try:
            pelanggan = db.session.get(Pelanggan, id_pelanggan)
            if not pelanggan:
                return False
            
            pelanggan.status = False
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error in delete_pelanggan: {str(e)}")
            return False
    
    @staticmethod
    def get_pelanggan_by_telepon(telepon):
        """
        Cari pelanggan berdasarkan nomor telepon
        Returns: Pelanggan object atau None
        """
        try:
            return Pelanggan.query.filter_by(telepon=telepon, status=True).first()
        except Exception as e:
            print(f"Error in get_pelanggan_by_telepon: {str(e)}")
            return None
    
    @staticmethod
    def search_pelanggan(keyword, limit=10):
        """
        Search pelanggan berdasarkan nama atau telepon
        Returns: list of pelanggan
        """
        try:
            search_term = f"%{keyword}%"
            pelanggan = Pelanggan.query.filter(
                Pelanggan.status == True,
                or_(
                    Pelanggan.nama.ilike(search_term),
                    Pelanggan.telepon.ilike(search_term)
                )
            ).limit(limit).all()
            
            return pelanggan
        except Exception as e:
            print(f"Error in search_pelanggan: {str(e)}")
            return []
