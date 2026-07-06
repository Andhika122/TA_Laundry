/**
 * Laundry Process Management JavaScript
 */

/**
 * Advance laundry status to the next stage
 * @param {number} id_transaksi - Transaction ID
 * @param {Element} button - Button element that triggered the action
 */
function advanceLaundryStatus(id_transaksi, button) {
    if (!confirm('Apakah Anda yakin ingin melanjutkan ke tahap berikutnya?')) {
        return;
    }

    // Disable button dan tampilkan loading state
    button.disabled = true;
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memproses...';

    // Call API to advance status
    fetch(`/transaksi/api/update-status-next/${id_transaksi}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showNotification(`Status berhasil diubah menjadi <strong>${data.status_proses}</strong>`, 'success');
            
            // Reload page after short delay to show message
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            showNotification(data.error || 'Gagal mengupdate status', 'danger');
            button.disabled = false;
            button.innerHTML = originalContent;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Terjadi kesalahan pada server', 'danger');
        button.disabled = false;
        button.innerHTML = originalContent;
    });
}

/**
 * Show notification message
 * @param {string} message - Message to display
 * @param {string} type - Alert type (success, danger, warning, info)
 */
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Insert at top of page
    const container = document.querySelector('main') || document.querySelector('body');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
