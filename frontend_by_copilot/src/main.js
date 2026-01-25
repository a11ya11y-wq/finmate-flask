// Entry point - minimal frontend setup
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import * as bootstrap from 'bootstrap'

import './styles/main.css'
import './styles/toast.css'
import './styles/settings.css'
import './styles/dashboard.css'

import { showSuccess, showError, showWarning, showInfo } from './utils/toast.js'
import { openModal, closeModal, closeAllModals, createDynamicModal } from './utils/simpleModal.js'
import { confirmDelete, confirmAction, showConfirmDialog } from './utils/confirmDialog.js'

if(typeof window !== 'undefined') {
  window.bootstrap = bootstrap

  // Toast utilities
  window.showSuccess = showSuccess
  window.showError = showError
  window.showWarning = showWarning
  window.showInfo = showInfo

  // Modal utilities
  window.openModal = openModal
  window.closeModal = closeModal
  window.closeAllModals = closeAllModals
  window.createDynamicModal = createDynamicModal

  // Confirm dialog utilities
  window.confirmDelete = confirmDelete
  window.confirmAction = confirmAction
  window.showConfirmDialog = showConfirmDialog
}

import Chart from 'chart.js/auto'
if(typeof globalThis !== 'undefined') globalThis.Chart = globalThis.Chart || Chart

if(typeof window !== 'undefined') {
  const originalError = console.error
  console.error = function(...args) {
    const errorMsg = args[0]?.toString() || ''
    if(
      errorMsg.includes('message port closed') ||
      errorMsg.includes('Extension context invalidated') ||
      errorMsg.includes('chrome-extension://') ||
      errorMsg.includes('moz-extension://')
    ) {
      return
    }
    originalError.apply(console, args)
  }

  window.addEventListener('unhandledrejection', (event) => {
    const errorMsg = event.reason?.message || event.reason?.toString() || ''
    if(
      errorMsg.includes('message port closed') ||
      errorMsg.includes('Extension context invalidated') ||
      errorMsg.includes('chrome-extension://') ||
      errorMsg.includes('moz-extension://')
    ) {
      event.preventDefault()
    }
  })
}
