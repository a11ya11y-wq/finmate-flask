// Entry point - minimal frontend setup
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import * as bootstrap from 'bootstrap'

import './styles/main.css'
import './styles/custom.css'
import './styles/toast.css'
import './styles/settings.css'
import './styles/dashboard.css'
import './styles/dashboard-buttons-fix.css'
import './styles/chart-fix-override.css'
import './styles/mobile-performance.css'  // ✅ MOBILE: Must be after dashboard.css to override
import './styles/vertical-center-fix.css'  // ✅ CRITICAL: Must be last to override all other styles

import { showSuccess, showError, showWarning, showInfo } from './utils/toast.js'
import { openModal, closeModal, closeAllModals } from './utils/simpleModal.js'

if(typeof window !== 'undefined') {
  window.bootstrap = bootstrap
  window.showSuccess = showSuccess
  window.showError = showError
  window.showWarning = showWarning
  window.showInfo = showInfo
  window.openModal = openModal
  window.closeModal = closeModal
  window.closeAllModals = closeAllModals
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
