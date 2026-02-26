// Confirm Dialog utility — unified dark-theme design

/**
 * Show a confirmation dialog.
 * @param {Object} options
 * @param {string} options.title
 * @param {string} options.message
 * @param {string} [options.confirmText='Confirm']
 * @param {string} [options.cancelText='Cancel']
 * @param {string} [options.type='danger'] - 'danger' | 'warning' | 'info'
 * @param {boolean} [options.compact=false] - Smaller modal (for Profile pages)
 * @returns {Promise<boolean>}
 */
export async function showConfirmDialog(options = {}) {
  const {
    title = 'Confirm',
    message = 'Are you sure?',
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    type = 'danger',
    compact = false
  } = options

  return new Promise((resolve) => {
    const overlayId = 'cdOverlay-' + Date.now()

    const iconMap = {
      danger:  { icon: 'bi-exclamation-triangle-fill', color: '#ef4444', bg: 'rgba(239,68,68,0.15)' },
      warning: { icon: 'bi-exclamation-circle-fill',   color: '#f59e0b', bg: 'rgba(245,158,11,0.15)' },
      info:    { icon: 'bi-info-circle-fill',           color: '#3b82f6', bg: 'rgba(59,130,246,0.15)' }
    }
    const cfg = iconMap[type] || iconMap.danger

    const overlay = document.createElement('div')
    overlay.id = overlayId
    overlay.style.cssText = `
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.75);
      z-index: 10500;
      display: flex; align-items: center; justify-content: center;
      padding: 20px;
    `

    const accentGradients = {
      danger:  'linear-gradient(135deg, #ef4444, #dc2626)',
      warning: 'linear-gradient(135deg, #f59e0b, #d97706)',
      info:    'linear-gradient(135deg, #3b82f6, #2563eb)'
    }
    const confirmGradient = accentGradients[type] || accentGradients.danger

    overlay.innerHTML = `
      <div class="cd-modal-box cd-modal-accent-${type} ${compact ? 'cd-modal-compact' : ''}">
        <!-- Close X -->
        <button class="cd-close-btn" data-action="cancel" aria-label="Close">
          <i class="bi bi-x"></i>
        </button>

        <!-- Icon -->
        <div class="cd-icon-wrap ${compact ? 'cd-icon-wrap--sm' : ''}" style="background:${cfg.bg};">
          <i class="bi ${cfg.icon}" style="color:${cfg.color};"></i>
        </div>

        <!-- Title -->
        <h5 class="cd-title">${title}</h5>

        <!-- Message -->
        <p class="cd-message">${message}</p>

        <!-- Buttons -->
        <div class="cd-btn-row">
          <button class="cd-btn-cancel" data-action="cancel">${cancelText}</button>
          <button class="cd-btn-confirm cd-btn-confirm--${type}" data-action="confirm" style="background:${confirmGradient};">${confirmText}</button>
        </div>
      </div>
    `

    document.body.appendChild(overlay)

    // Animate in
    requestAnimationFrame(() => {
      const box = overlay.querySelector('.cd-modal-box')
      if (box) {
        box.style.transform = 'scale(1)'
        box.style.opacity   = '1'
      }
    })

    function cleanup() {
      const box = overlay.querySelector('.cd-modal-box')
      if (box) {
        box.style.transform = 'scale(0.95)'
        box.style.opacity   = '0'
      }
      overlay.style.opacity = '0'
      setTimeout(() => {
        if (overlay.parentElement) overlay.remove()
        document.removeEventListener('keydown', handleEscape)
      }, 200)
    }

    overlay.querySelectorAll('[data-action="confirm"]').forEach(btn =>
      btn.addEventListener('click', () => { cleanup(); resolve(true) })
    )
    overlay.querySelectorAll('[data-action="cancel"]').forEach(btn =>
      btn.addEventListener('click', () => { cleanup(); resolve(false) })
    )

    // Close on backdrop click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) { cleanup(); resolve(false) }
    })

    function handleEscape(e) {
      if (e.key === 'Escape') { cleanup(); resolve(false) }
    }
    document.addEventListener('keydown', handleEscape)
  })
}

/**
 * Show delete confirmation dialog (compact for Profile pages).
 * Clicking Cancel only closes the modal — no toast.
 * @param {string} itemName
 * @param {boolean} [compact=false]
 * @returns {Promise<boolean>}
 */
export async function confirmDelete(itemName = 'this item', compact = false) {
  return await showConfirmDialog({
    title: 'Delete?',
    message: `Are you sure you want to delete ${itemName}? This action cannot be undone.`,
    confirmText: 'Delete',
    cancelText: 'Cancel',
    type: 'danger',
    compact
  })
}

/**
 * Show generic confirmation dialog.
 * @param {string} message
 * @param {string} [confirmText='Confirm']
 * @returns {Promise<boolean>}
 */
export async function confirmAction(message, confirmText = 'Confirm') {
  return await showConfirmDialog({
    title: 'Confirm',
    message,
    confirmText,
    cancelText: 'Cancel',
    type: 'info'
  })
}


