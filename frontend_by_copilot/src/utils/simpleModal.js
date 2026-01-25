// Simple Modal Management (without Bootstrap)
let openModals = []

/**
 * Open an existing modal by ID
 * @param {string} modalId - ID of the modal element
 */
export function openModal(modalId) {
  const modal = document.getElementById(modalId)
  if (!modal) {
    console.error(`[simpleModal] Modal with id "${modalId}" not found`)
    return
  }

  // Add to open modals list
  if (!openModals.includes(modalId)) {
    openModals.push(modalId)
  }

  // ✅ Set ARIA before showing
  modal.setAttribute('aria-hidden', 'false')

  // Show modal
  modal.style.display = 'block'
  modal.classList.add('show')

  // Add backdrop
  createBackdrop()

  // Prevent body scroll
  document.body.style.overflow = 'hidden'
  document.body.classList.add('modal-open')

  // Focus trap - use requestAnimationFrame for proper timing
  const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
  if (firstFocusable) {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        firstFocusable.focus()
      })
    })
  }
}

/**
 * Close a modal by ID
 * @param {string} modalId - ID of the modal element
 */
export function closeModal(modalId) {
  const modal = document.getElementById(modalId)
  if (!modal) return

  // Check if modal was opened with Bootstrap Modal API
  if (modal._bsModalInstance) {
    try {
      modal._bsModalInstance.hide()
      delete modal._bsModalInstance
      openModals = openModals.filter(id => id !== modalId)
      return
    } catch (err) {
      console.error('[simpleModal] Bootstrap close failed:', err)
    }
  }

  // Fallback: use manual close
  openModals = openModals.filter(id => id !== modalId)

  // Hide modal
  modal.classList.remove('show')
  modal.setAttribute('aria-hidden', 'true')
  setTimeout(() => {
    modal.style.display = 'none'
  }, 300)

  // Remove backdrop if no modals are open
  if (openModals.length === 0) {
    removeBackdrop()
    document.body.style.overflow = ''
    document.body.classList.remove('modal-open')
  }
}

/**
 * Close all open modals
 */
export function closeAllModals() {
  const modalsToClose = [...openModals]

  modalsToClose.forEach(modalId => {
    closeModal(modalId)
  })

  openModals = []
  removeBackdrop()

  const bsBackdrops = document.querySelectorAll('.modal-backdrop')
  bsBackdrops.forEach(backdrop => backdrop.remove())

  document.body.style.overflow = ''
  document.body.classList.remove('modal-open')
}

/**
 * Create and show a dynamic modal programmatically
 * @param {Object} options - Modal configuration
 * @param {string} options.title - Modal title
 * @param {string|HTMLElement} options.content - Modal body content (HTML string or element)
 * @param {Array} options.buttons - Array of button configs [{text, class, onClick}]
 * @param {string} options.size - Modal size: 'sm', 'lg', 'xl' (default: normal)
 * @param {boolean} options.closeOnBackdrop - Allow closing on backdrop click (default: true)
 * @returns {Object} - Modal control object with close() method
 */
export function createDynamicModal(options = {}) {
  const {
    title = 'Modal',
    content = '',
    buttons = [],
    size = '',
    closeOnBackdrop = true
  } = options

  // Generate unique ID
  const modalId = 'dynamic-modal-' + Date.now()

  // Create modal element
  const modal = document.createElement('div')
  modal.id = modalId
  modal.className = 'modal fade'
  modal.setAttribute('tabindex', '-1')
  modal.setAttribute('role', 'dialog')
  modal.setAttribute('aria-labelledby', `${modalId}-title`)
  modal.setAttribute('aria-hidden', 'true')

  // Size class
  const sizeClass = size ? `modal-${size}` : ''

  modal.innerHTML = `
    <div class="modal-dialog modal-dialog-centered ${sizeClass}">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="${modalId}-title">${title}</h5>
          <button type="button" class="btn-close" data-dismiss="${modalId}" aria-label="Close"></button>
        </div>
        <div class="modal-body" id="${modalId}-body">
          ${typeof content === 'string' ? content : ''}
        </div>
        ${buttons.length > 0 ? `
          <div class="modal-footer" id="${modalId}-footer">
            ${buttons.map((btn, idx) => `
              <button type="button" 
                      class="btn ${btn.class || 'btn-secondary'}" 
                      data-button-index="${idx}">
                ${btn.text || 'Button'}
              </button>
            `).join('')}
          </div>
        ` : ''}
      </div>
    </div>
  `

  // Append content if it's an element
  if (content instanceof HTMLElement) {
    const bodyEl = modal.querySelector(`#${modalId}-body`)
    bodyEl.innerHTML = ''
    bodyEl.appendChild(content)
  }

  // Add to DOM
  document.body.appendChild(modal)

  // Setup button handlers
  buttons.forEach((btn, idx) => {
    const btnEl = modal.querySelector(`[data-button-index="${idx}"]`)
    if (btnEl && btn.onClick) {
      btnEl.addEventListener('click', () => {
        btn.onClick(modalControl)
      })
    }
  })

  // Setup close button
  modal.querySelector(`[data-dismiss="${modalId}"]`)?.addEventListener('click', () => {
    modalControl.close()
  })

  // Backdrop click handler
  if (closeOnBackdrop) {
    const backdrop = document.getElementById('modal-backdrop')
    if (backdrop) {
      backdrop.addEventListener('click', () => {
        modalControl.close()
      })
    }
  }

  // Control object
  const modalControl = {
    id: modalId,
    element: modal,
    close: () => {
      modal.classList.remove('show')
      removeBackdrop()
      setTimeout(() => {
        if (modal.parentElement) {
          modal.remove()
        }
      }, 300)
    },
    setContent: (newContent) => {
      const bodyEl = modal.querySelector(`#${modalId}-body`)
      if (typeof newContent === 'string') {
        bodyEl.innerHTML = newContent
      } else if (newContent instanceof HTMLElement) {
        bodyEl.innerHTML = ''
        bodyEl.appendChild(newContent)
      }
    }
  }

  // Show modal
  setTimeout(() => {
    modal.style.display = 'block'
    modal.classList.add('show')
    createBackdrop()
  }, 10)

  return modalControl
}

// ========================================
// INTERNAL HELPERS
// ========================================

function createBackdrop() {
  // Remove existing backdrop first
  removeBackdrop()

  const backdrop = document.createElement('div')
  backdrop.id = 'modal-backdrop'
  backdrop.className = 'modal-backdrop fade show'
  backdrop.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 1040;
    backdrop-filter: blur(4px);
  `

  backdrop.addEventListener('click', () => {
    if (openModals.length > 0) {
      closeModal(openModals[openModals.length - 1])
    }
  })

  document.body.appendChild(backdrop)
}

function removeBackdrop() {
  const backdrop = document.getElementById('modal-backdrop')
  if (backdrop) {
    backdrop.remove()
  }
}

// ========================================
// EVENT LISTENERS
// ========================================

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && openModals.length > 0) {
    closeModal(openModals[openModals.length - 1])
  }
})

// Delegated event handler for close buttons with data-modal-dismiss
document.addEventListener('click', (e) => {
  const dismissBtn = e.target.closest('[data-modal-dismiss]')
  if (dismissBtn) {
    const modalId = dismissBtn.getAttribute('data-modal-dismiss')
    if (modalId) {
      closeModal(modalId)
    } else if (openModals.length > 0) {
      // If no specific modal ID, close the top modal
      closeModal(openModals[openModals.length - 1])
    }
  }
})

// Initialize modals on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeModalButtons)
} else {
  initializeModalButtons()
}

function initializeModalButtons() {
  // Add click handlers to elements with data-modal-target
  document.querySelectorAll('[data-modal-target]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault()
      const modalId = btn.getAttribute('data-modal-target')
      if (modalId) openModal(modalId)
    })
  })
}

