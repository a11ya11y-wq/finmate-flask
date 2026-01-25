// Toast notification system - Template-based, matches toast.css
const TOAST_DURATION = {
  SUCCESS: 3000,
  ERROR: 4000,
  WARNING: 3500,
  INFO: 3000
}

const TOAST_CONFIG = {
  success: {
    icon: 'bi-check-circle-fill',
    class: 'toast-success'
  },
  error: {
    icon: 'bi-x-circle-fill',
    class: 'toast-error'
  },
  warning: {
    icon: 'bi-exclamation-triangle-fill',
    class: 'toast-warning'
  },
  info: {
    icon: 'bi-info-circle-fill',
    class: 'toast-info'
  }
}

/**
 * Show a toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds (default: based on type)
 */
export function showToast(message, type = 'info', duration = null) {
  // Validate type
  if (!TOAST_CONFIG[type]) {
    console.warn(`[Toast] Invalid type "${type}", using "info"`)
    type = 'info'
  }

  // Use type-specific duration if not provided
  if (!duration) {
    duration = TOAST_DURATION[type.toUpperCase()] || TOAST_DURATION.INFO
  }

  // Get or create container
  const container = getOrCreateContainer()

  // Create toast element
  const toast = createToastElement(message, type)
  container.appendChild(toast)

  // Setup close handler
  setupCloseHandler(toast)

  // Trigger show animation
  requestAnimationFrame(() => {
    toast.classList.add('toast-visible')
  })

  // Auto-hide
  toast._hideTimeout = setTimeout(() => {
    hideToast(toast)
  }, duration)
}

/**
 * Convenience methods for different toast types
 */
export function showSuccess(message, duration = TOAST_DURATION.SUCCESS) {
  showToast(message, 'success', duration)
}

export function showError(message, duration = TOAST_DURATION.ERROR) {
  showToast(message, 'error', duration)
}

export function showWarning(message, duration = TOAST_DURATION.WARNING) {
  showToast(message, 'warning', duration)
}

export function showInfo(message, duration = TOAST_DURATION.INFO) {
  showToast(message, 'info', duration)
}

// ========================================
// INTERNAL HELPERS (Template-based)
// ========================================

function getOrCreateContainer() {
  let container = document.getElementById('toast-container')
  if (!container) {
    container = document.createElement('div')
    container.id = 'toast-container'
    container.className = 'toast-container'
    document.body.appendChild(container)
  }
  return container
}

function createToastElement(message, type) {
  const config = TOAST_CONFIG[type]

  const toast = document.createElement('div')
  toast.className = `toast ${config.class}`

  // Create icon element
  const iconSpan = document.createElement('span')
  iconSpan.className = 'toast-icon'
  const icon = document.createElement('i')
  icon.className = `bi ${config.icon}`
  iconSpan.appendChild(icon)

  // Create message element
  const messageSpan = document.createElement('span')
  messageSpan.className = 'toast-message'
  messageSpan.textContent = message

  // Create close button
  const closeBtn = document.createElement('button')
  closeBtn.className = 'toast-close'
  closeBtn.setAttribute('aria-label', 'Close')
  const closeIcon = document.createElement('i')
  closeIcon.className = 'bi bi-x'
  closeBtn.appendChild(closeIcon)

  // Append all elements
  toast.appendChild(iconSpan)
  toast.appendChild(messageSpan)
  toast.appendChild(closeBtn)

  return toast
}

function setupCloseHandler(toast) {
  const closeBtn = toast.querySelector('.toast-close')
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      // Clear auto-hide timeout
      if (toast._hideTimeout) {
        clearTimeout(toast._hideTimeout)
      }
      hideToast(toast)
    })
  }
}

function hideToast(toast) {
  toast.classList.remove('toast-visible')
  toast.classList.add('toast-hiding')

  setTimeout(() => {
    if (toast.parentElement) {
      toast.remove()
    }
  }, 300) // Match CSS transition duration
}

// ========================================
// DEBUG UTILITIES (exposed globally)
// ========================================

if (typeof window !== 'undefined') {
  window.testToast = {
    success: (msg = 'Test Success! ✅') => showSuccess(msg),
    error: (msg = 'Test Error! ❌') => showError(msg),
    warning: (msg = 'Test Warning! ⚠️') => showWarning(msg),
    info: (msg = 'Test Info! ℹ️') => showInfo(msg),
    all: () => {
      showSuccess('Success notification')
      setTimeout(() => showError('Error notification'), 200)
      setTimeout(() => showWarning('Warning notification'), 400)
      setTimeout(() => showInfo('Info notification'), 600)
    }
  }

  console.info('[Toast] Debug utilities available: window.testToast')
}

