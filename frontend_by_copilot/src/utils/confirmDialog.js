// Confirm Dialog utility - uses simpleModal for consistent UX
import { showWarning } from './toast.js'

/**
 * Create and show a confirmation dialog using our modal system
 * @param {Object} options - Dialog configuration
 * @param {string} options.title - Dialog title
 * @param {string} options.message - Dialog message
 * @param {string} options.confirmText - Confirm button text (default: 'Підтвердити')
 * @param {string} options.cancelText - Cancel button text (default: 'Скасувати')
 * @param {string} options.type - Dialog type: 'danger', 'warning', 'info' (default: 'warning')
 * @returns {Promise<boolean>} - Resolves to true if confirmed, false if canceled
 */
export async function showConfirmDialog(options = {}) {
  const {
    title = 'Підтвердження',
    message = 'Ви впевнені?',
    confirmText = 'Підтвердити',
    cancelText = 'Скасувати',
    type = 'warning'
  } = options

  return new Promise((resolve) => {
    // Create modal element
    const modalId = 'confirmDialog-' + Date.now()
    const modal = createConfirmModal({
      modalId,
      title,
      message,
      confirmText,
      cancelText,
      type,
      onConfirm: () => {
        cleanup()
        resolve(true)
      },
      onCancel: () => {
        cleanup()
        resolve(false)
      }
    })

    // Append to body
    document.body.appendChild(modal)

    // Show modal
    setTimeout(() => {
      modal.style.display = 'block'
      modal.classList.add('show')
      createBackdrop(modalId)
    }, 10)

    // Cleanup function
    function cleanup() {
      modal.classList.remove('show')
      removeBackdrop()
      setTimeout(() => {
        if (modal.parentElement) {
          modal.remove()
        }
      }, 300)
    }

    // Handle escape key
    function handleEscape(e) {
      if (e.key === 'Escape') {
        cleanup()
        resolve(false)
        document.removeEventListener('keydown', handleEscape)
      }
    }

    document.addEventListener('keydown', handleEscape)
  })
}

/**
 * Show delete confirmation dialog
 * @param {string} itemName - Name of item to delete
 * @returns {Promise<boolean>}
 */
export async function confirmDelete(itemName = 'цей елемент') {
  const result = await showConfirmDialog({
    title: 'Підтвердження видалення',
    message: `Ви впевнені, що хочете видалити ${itemName}? Цю дію неможливо скасувати.`,
    confirmText: 'Видалити',
    cancelText: 'Скасувати',
    type: 'danger'
  })

  if (!result) {
    showWarning('Видалення скасовано')
  }

  return result
}

/**
 * Show generic confirmation dialog
 * @param {string} message - Dialog message
 * @param {string} confirmText - Confirm button text
 * @returns {Promise<boolean>}
 */
export async function confirmAction(message, confirmText = 'Підтвердити') {
  return await showConfirmDialog({
    title: 'Підтвердження',
    message,
    confirmText,
    cancelText: 'Скасувати',
    type: 'info'
  })
}

// ========================================
// INTERNAL HELPERS (Template-based)
// ========================================

function createConfirmModal({ modalId, title, message, confirmText, cancelText, type, onConfirm, onCancel }) {
  const modal = document.createElement('div')
  modal.id = modalId
  modal.className = 'modal fade'
  modal.setAttribute('tabindex', '-1')
  modal.setAttribute('role', 'dialog')
  modal.setAttribute('aria-labelledby', `${modalId}-title`)
  modal.setAttribute('aria-hidden', 'true')

  // Type-specific colors
  const colors = {
    danger: {
      icon: 'bi-exclamation-triangle-fill',
      iconColor: '#ef4444',
      iconBg: 'rgba(239, 68, 68, 0.15)',
      btnClass: 'btn-danger'
    },
    warning: {
      icon: 'bi-exclamation-circle-fill',
      iconColor: '#f59e0b',
      iconBg: 'rgba(245, 158, 11, 0.15)',
      btnClass: 'btn-warning'
    },
    info: {
      icon: 'bi-info-circle-fill',
      iconColor: '#3b82f6',
      iconBg: 'rgba(59, 130, 246, 0.15)',
      btnClass: 'btn-primary'
    }
  }

  const config = colors[type] || colors.info

  modal.innerHTML = `
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header border-0 pb-0">
          <h5 class="modal-title" id="${modalId}-title">
            <i class="bi ${config.icon}" style="color: ${config.iconColor}; background: ${config.iconBg}; padding: 8px; border-radius: 50%; font-size: 20px;"></i>
            ${title}
          </h5>
          <button type="button" class="btn-close" data-action="cancel" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p style="margin: 0; color: rgba(255, 255, 255, 0.85); line-height: 1.6;">${message}</p>
        </div>
        <div class="modal-footer border-0" style="gap: 12px;">
          <button type="button" class="btn btn-secondary" data-action="cancel">${cancelText}</button>
          <button type="button" class="btn ${config.btnClass}" data-action="confirm" autofocus>${confirmText}</button>
        </div>
      </div>
    </div>
  `

  // Event listeners
  modal.querySelectorAll('[data-action="confirm"]').forEach(btn => {
    btn.addEventListener('click', onConfirm)
  })

  modal.querySelectorAll('[data-action="cancel"]').forEach(btn => {
    btn.addEventListener('click', onCancel)
  })

  return modal
}

function createBackdrop(modalId) {
  const backdrop = document.createElement('div')
  backdrop.id = `${modalId}-backdrop`
  backdrop.className = 'modal-backdrop fade show'
  backdrop.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 1040;
  `
  document.body.appendChild(backdrop)
}

function removeBackdrop() {
  const backdrops = document.querySelectorAll('[id$="-backdrop"]')
  backdrops.forEach(b => b.remove())
}

