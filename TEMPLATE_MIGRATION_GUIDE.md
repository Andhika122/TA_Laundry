# Template Migration Guide - Laundry Berkah

## Status: 7/29 Templates Completed ✅

### Completed Conversions
- ✅ dashboard/dashboard.html  
- ✅ pelanggan/tambah.html, edit.html, detail.html, pelanggan.html
- ✅ laporan/laporan.html
- ✅ akun/profile.html

---

## Pattern for Migration

### Before (Legacy - Full HTML Shell)
```html
<!DOCTYPE html>
<html>
<head>...</head>
<body>
  <nav class="navbar">...</nav>
  <div class="sidebar">...</div>
  <div class="main-content">
    <!-- PAGE CONTENT HERE -->
  </div>
</body>
</html>
```

### After (New - Shared Layout)
```jinja2
{% extends 'layout/base.html' %}
{% set active_page = 'pelanggan' %}
{% block title %}Page Title - Laundry Berkah{% endblock %}
{% block page_title %}Page Header{% endblock %}
{% block content %}
    <!-- PAGE CONTENT ONLY (no navbar/sidebar) -->
{% endblock %}
{% block styles %}
    <style>/* page-specific CSS */</style>
{% endblock %}
```

---

## Remaining Templates to Convert (22/29)

### Category 1: Transaksi (3 files)
- [ ] `transaksi/list.html` → active_page='transaksi'
- [ ] `transaksi/baru.html` → active_page='transaksi'  
- [ ] `transaksi/detail.html` → active_page='transaksi'

### Category 2: Pembayaran (3 files)
- [ ] `pembayaran/bayar.html` → active_page='transaksi'
- [ ] `pembayaran/riwayat.html` → active_page='transaksi'
- [ ] `pembayaran/struk.html` → active_page='transaksi' ✓ (may already be done)

### Category 3: Laundry (4 files)
- [ ] `laundry/antrian.html` → active_page='laundry'
- [ ] `laundry/proses.html` → active_page='laundry'
- [ ] `laundry/siap_ambil.html` → active_page='laundry'
- [ ] `laundry/selesai.html` → active_page='laundry'

### Category 4: Layanan (4 files)
- [ ] `layanan/layanan.html` → active_page='layanan'
- [ ] `layanan/tambah.html` → active_page='layanan' ✓ (already has active_page)
- [ ] `layanan/edit.html` → active_page='layanan' ✓ (already has active_page)
- [ ] `layanan/detail.html` → active_page='layanan' ✓ (already has active_page)

### Category 5: Auth & Other (8 files)
- [ ] `auth/login.html` → (may use own simple layout)
- [ ] Other placeholder templates

---

## Conversion Steps (for each template)

### 1. **Remove HTML Shell**
- Delete `<!DOCTYPE html>` through `</head>`
- Delete opening `<body>` and `<nav class="navbar">...</nav>` sections
- Delete `<div class="container-fluid">...</div>` wrapper and sidebar

### 2. **Add Layout Inheritance**
```jinja2
{% extends 'layout/base.html' %}
{% set active_page = 'SECTION_NAME' %}
```

### 3. **Define Blocks**
- `{% block title %}Page Title - Laundry Berkah{% endblock %}`
- `{% block page_title %}Display Title{% endblock %}`
- `{% block content %}...{% endblock %}`
- `{% block styles %}...{% endblock %}` (if has custom CSS)
- `{% block scripts %}...{% endblock %}` (if has JavaScript)

### 4. **Extract Content**
- Copy only the `<div class="main-content">` content
- Remove the `.main-content` wrapper div
- Place inside `{% block content %}`

### 5. **Extract CSS**
- Move any `<style>` block content to `{% block styles %}`
- Keep only page-specific CSS (remove navbar/sidebar/container CSS)

### 6. **Extract JS** 
- Move any `<script>` to `{% block scripts %}`

---

## Active Page Values

Use these exact values in route handlers and templates:

```python
# In route handlers:
render_template('page.html', active_page='SECTION')

# Active page values:
'dashboard'     # Dashboard
'pelanggan'     # Customers
'transaksi'     # Transactions (also for pembayaran routes)
'laundry'       # Laundry Process
'layanan'       # Services  
'laporan'       # Reports
'akun'          # Account
```

---

## Routes Already Updated ✅

```python
✅ dashboard/routes.py - renders with active_page='dashboard'
✅ pelanggan/routes.py - all routes pass active_page='pelanggan'
✅ laundry/routes.py - antrian route has active_page='laundry'
✅ transaksi/routes.py - list, baru, struk pass active_page='transaksi'
✅ pembayaran/routes.py - all routes pass active_page='transaksi'
✅ layanan/routes.py - all routes pass active_page='layanan'
✅ laporan/routes.py - index passes active_page='laporan'
✅ akun/routes.py - profile passes active_page='akun'
```

---

## Quick Reference: Sidebar Active Values

The sidebar uses `{% if active_page == 'SECTION' %}active{% endif %}`:
- Dashboard link: `'dashboard'`
- Pelanggan link: `'pelanggan'`
- Transaksi link: `'transaksi'`
- Proses Laundry link: `'laundry'`
- Layanan link: `'layanan'`
- Laporan link: `'laporan'`
- Akun link: `'akun'`

---

## Implementation Checklist

- [x] Dashboard converted
- [x] Pelanggan module converted (5 files)
- [x] Laporan converted
- [x] Akun converted
- [ ] Transaksi module (3 files)
- [ ] Pembayaran module (3 files) 
- [ ] Laundry module (4 files)
- [ ] Layanan module (verify all 4)
- [ ] Auth/Login (if needed)
- [ ] Other templates

---

## Testing After Conversion

1. Test sidebar highlighting - check `{% if active_page == 'X' %}` matches current route
2. Test content displays correctly without navbar/sidebar duplication
3. Test page title shows in {% block page_title %}
4. Test custom CSS still applies
5. Test any page-specific JavaScript still works

