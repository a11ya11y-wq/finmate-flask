// Simple Modal Management (without Bootstrap)
let openModals = []

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

  // ✅ ВАЖЛИВО: Спочатку встановлюємо aria-hidden="false" ДО показу та фокусу
  modal.setAttribute('aria-hidden', 'false')

  // Show modal
  modal.style.display = 'block'
  modal.classList.add('show')

  // Add backdrop
  createBackdrop()

  // Prevent body scroll
  document.body.style.overflow = 'hidden'

  // Focus trap - використовуємо requestAnimationFrame для коректного часування
  const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
  if (firstFocusable) {
    // Використовуємо requestAnimationFrame замість setTimeout для синхронізації з браузером
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        firstFocusable.focus()
      })
    })
  }
}

export function closeModal(modalId) {
  const modal = document.getElementById(modalId)
  if (!modal) return


  // Remove from open modals list
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
  }
}

export function closeAllModals() {

  // Clone array to avoid modification during iteration
  const modalsToClose = [...openModals]

  modalsToClose.forEach(modalId => {
    closeModal(modalId)
  })

  // Force cleanup
  openModals = []
  removeBackdrop()
  document.body.style.overflow = ''
}

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

