// Toast notification system
export function showToast(message, type = 'info', duration = 3000) {
  // Create container if it doesn't exist
  let container = document.getElementById('toast-container')
  if (!container) {
    container = document.createElement('div')
    container.id = 'toast-container'
    container.className = 'toast-container'
    document.body.appendChild(container)
  }

  // Create toast element
  const toast = document.createElement('div')
  toast.className = `toast toast-${type}`

  // Modern Bootstrap Icons
  const icons = {
    success: '<i class="bi bi-check-circle-fill"></i>',
    error: '<i class="bi bi-x-circle-fill"></i>',
    warning: '<i class="bi bi-exclamation-triangle-fill"></i>',
    info: '<i class="bi bi-info-circle-fill"></i>'
  }

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-message">${message}</span>
    <button class="toast-close" aria-label="Close">
      <i class="bi bi-x"></i>
    </button>
  `

  container.appendChild(toast)

  // Close button handler
  const closeBtn = toast.querySelector('.toast-close')
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      toast.classList.remove('toast-visible')
      toast.classList.add('toast-hiding')
      setTimeout(() => {
        if (toast.parentElement) {
          toast.remove()
        }
      }, 300)
    })
  }

  // Trigger animation
  setTimeout(() => {
    toast.classList.add('toast-visible')
  }, 10)

  // Auto-hide
  setTimeout(() => {
    toast.classList.remove('toast-visible')
    toast.classList.add('toast-hiding')
    setTimeout(() => {
      if (toast.parentElement) {
        toast.remove()
      }
    }, 300)
  }, duration)
}

export function showSuccess(message, duration = 3000) {
  showToast(message, 'success', duration)
}

export function showError(message, duration = 4000) {
  showToast(message, 'error', duration)
}

export function showWarning(message, duration = 3500) {
  showToast(message, 'warning', duration)
}

export function showInfo(message, duration = 3000) {
  showToast(message, 'info', duration)
}

// Expose globally for debugging
if (typeof window !== 'undefined') {
  window.testToast = {
    success: (msg = 'Test Success!') => showSuccess(msg),
    error: (msg = 'Test Error!') => showError(msg),
    warning: (msg = 'Test Warning!') => showWarning(msg),
    info: (msg = 'Test Info!') => showInfo(msg)
  }
}

