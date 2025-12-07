// Entry point - minimal frontend setup
// Import Bootstrap CSS and icons (via npm) so styles are available project-wide
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
// Import Bootstrap JS (bundle) to enable components like dropdowns and modals
import * as bootstrap from 'bootstrap'
// ✅ Порядок імпорту стилів: Bootstrap → базові → кастомні → специфічні сторінки
import './styles/main.css'
import './styles/custom.css'
import './styles/toast.css' // Toast notifications
import './styles/settings.css' // Settings page styles
import './styles/dashboard.css' // Містить .period-btn стилі

// ✅ Import toast utility for global availability
import { showSuccess, showError, showWarning, showInfo } from './utils/toast.js'
// ✅ Import modal utilities
import { openModal, closeModal, closeAllModals } from './utils/simpleModal.js'

// Expose Bootstrap globally for components (Modal, Dropdown, etc.)
if(typeof window !== 'undefined') {
  window.bootstrap = bootstrap
  // Expose toast functions globally for easy access from all pages
  window.showSuccess = showSuccess
  window.showError = showError
  window.showWarning = showWarning
  window.showInfo = showInfo
  // Expose modal functions globally
  window.openModal = openModal
  window.closeModal = closeModal
  window.closeAllModals = closeAllModals
}

// Expose Chart globally to avoid HMR/duplicate issues
import Chart from 'chart.js/auto'
if(typeof globalThis !== 'undefined') globalThis.Chart = globalThis.Chart || Chart

// ✅ Глобальний обробник помилок для фільтрації помилок розширень браузера
if(typeof window !== 'undefined') {
  // Ігноруємо помилки від розширень браузера
  const originalError = console.error
  console.error = function(...args) {
    const errorMsg = args[0]?.toString() || ''
    // Фільтруємо помилки розширень Chrome/Edge
    if(
      errorMsg.includes('message port closed') ||
      errorMsg.includes('Extension context invalidated') ||
      errorMsg.includes('chrome-extension://') ||
      errorMsg.includes('moz-extension://')
    ) {
      return // Ігноруємо ці помилки
    }
    originalError.apply(console, args)
  }

  // Обробник для unhandledrejection
  window.addEventListener('unhandledrejection', (event) => {
    const errorMsg = event.reason?.message || event.reason?.toString() || ''
    // Фільтруємо помилки розширень
    if(
      errorMsg.includes('message port closed') ||
      errorMsg.includes('Extension context invalidated') ||
      errorMsg.includes('chrome-extension://') ||
      errorMsg.includes('moz-extension://')
    ) {
      event.preventDefault() // Запобігаємо виведенню в консоль
    }
  })
}
