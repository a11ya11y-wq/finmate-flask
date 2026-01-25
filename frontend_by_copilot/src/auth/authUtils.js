// Shared Auth Utilities
// Centralized validation and UI helpers for login and register pages

import { showSuccess as toastSuccess, showError as toastError } from '../utils/toast.js'

// ========================================
// VALIDATION UTILITIES
// ========================================

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} - True if valid
 */
export function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validate password strength
 * @param {string} password - Password to validate
 * @returns {Object} - {valid: boolean, message: string, strength: string}
 */
export function validatePassword(password) {
  if (!password) {
    return { valid: false, message: 'Password is required', strength: 'none' }
  }

  if (password.length < 6) {
    return {
      valid: false,
      message: 'Password must be at least 6 characters long',
      strength: 'weak'
    }
  }

  // Calculate strength
  let strength
  let score = 0

  if (password.length >= 8) score++
  if (password.length >= 12) score++
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++
  if (/\d/.test(password)) score++
  if (/[^a-zA-Z0-9]/.test(password)) score++

  if (score <= 2) strength = 'weak'
  else if (score === 3) strength = 'fair'
  else if (score === 4) strength = 'good'
  else strength = 'strong'

  return { valid: true, message: '', strength }
}

/**
 * Validate username
 * @param {string} username - Username to validate
 * @returns {Object} - {valid: boolean, message: string}
 */
export function validateUsername(username) {
  if (!username || username.trim().length === 0) {
    return { valid: false, message: 'Username is required' }
  }

  if (username.length < 3) {
    return { valid: false, message: 'Username must be at least 3 characters long' }
  }

  if (username.length > 50) {
    return { valid: false, message: 'Username must be less than 50 characters' }
  }

  return { valid: true, message: '' }
}

// ========================================
// UI UTILITIES
// ========================================

/**
 * Show error message in status div
 * @param {HTMLElement} statusDiv - Status message container
 * @param {string} message - Error message
 */
export function showError(statusDiv, message) {
  if (!statusDiv) return

  // Format message
  let formattedMessage = message || 'Unknown error'

  // Clean up common backend error messages
  if (formattedMessage.toLowerCase().includes('part after the @-sign') ||
      formattedMessage.toLowerCase().includes('top-level domain')) {
    formattedMessage = 'Please enter a valid email address'
  }

  formattedMessage = formattedMessage.replace(/\n/g, '<br>')

  // Error icon SVG
  const iconError = `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" 
         viewBox="0 0 24 24" stroke="currentColor" class="me-2">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  `

  // Set styles and content
  statusDiv.className = 'alert alert-danger d-flex align-items-center'
  statusDiv.style.borderColor = '#ff4d4f'
  statusDiv.style.color = '#ff4d4f'
  statusDiv.style.backgroundColor = 'rgba(255, 77, 79, 0.1)'
  statusDiv.innerHTML = `${iconError}<div>${formattedMessage}</div>`
  statusDiv.classList.remove('d-none')
}

/**
 * Show success message in status div
 * @param {HTMLElement} statusDiv - Status message container
 * @param {string} message - Success message
 */
export function showSuccess(statusDiv, message) {
  if (!statusDiv) return

  // Success icon SVG
  const iconSuccess = `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" 
         viewBox="0 0 24 24" stroke="currentColor" class="me-2">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  `

  // Set styles and content
  statusDiv.className = 'alert alert-success d-flex align-items-center'
  statusDiv.style.borderColor = '#28a745'
  statusDiv.style.color = '#28a745'
  statusDiv.style.backgroundColor = 'rgba(40, 167, 69, 0.1)'
  statusDiv.innerHTML = `${iconSuccess}<div>${message}</div>`
  statusDiv.classList.remove('d-none')
}

/**
 * Hide status message
 * @param {HTMLElement} statusDiv - Status message container
 */
export function hideStatus(statusDiv) {
  if (statusDiv) {
    statusDiv.classList.add('d-none')
  }
}

/**
 * Set loading state for submit button
 * @param {HTMLElement} submitBtn - Submit button element
 * @param {boolean} loading - Loading state
 * @param {Object} options - Button text options
 */
export function setButtonLoading(submitBtn, loading, options = {}) {
  if (!submitBtn) return

  const {
    loadingText = 'Loading...',
    defaultText = 'Submit'
  } = options

  const btnText = submitBtn.querySelector('.btn-text')
  const spinner = submitBtn.querySelector('.spinner-border')

  submitBtn.disabled = loading

  if (loading) {
    if (btnText) btnText.textContent = loadingText
    if (spinner) spinner.classList.remove('d-none')
  } else {
    if (btnText) btnText.textContent = defaultText
    if (spinner) spinner.classList.add('d-none')
  }
}

// ========================================
// ERROR PARSING UTILITIES
// ========================================

/**
 * Parse API error response and extract user-friendly message
 * @param {Error} err - Error object from API call
 * @param {string} defaultMessage - Default message if parsing fails
 * @returns {string} - User-friendly error message
 */
export function parseApiError(err, defaultMessage = 'Request failed') {
  let message = defaultMessage

  try {
    let data = err?.data || err?.response?.data || null

    // Try to parse JSON from errDetail or message if data is not structured
    if (!data) {
      const candidate = err?.errDetail || err?.message || null
      if (candidate && typeof candidate === 'string') {
        try {
          const parsed = JSON.parse(candidate)
          if (parsed) data = parsed
        } catch (e) {
          // Not JSON, use as-is
          if (candidate) message = candidate
        }
      }
    }

    if (data) {
      // 1) details as array of strings
      if (Array.isArray(data.details) && data.details.length) {
        message = data.details.join('\n')

      // 2) details as object like {email: ['msg'], password: ['msg']}
      } else if (data.details && typeof data.details === 'object') {
        const parts = []
        for (const key of Object.keys(data.details)) {
          const value = data.details[key]
          if (Array.isArray(value)) parts.push(...value)
          else if (typeof value === 'string') parts.push(value)
        }
        if (parts.length) message = parts.join('\n')

      // 3) generic errors array
      } else if (Array.isArray(data.errors) && data.errors.length) {
        message = data.errors.join('\n')

      // 4) fallback message fields
      } else if (typeof data.error === 'string' && data.error) {
        message = data.error
      } else if (typeof data.message === 'string' && data.message) {
        message = data.message
      } else if (typeof data === 'string' && data) {
        message = data
      }
    } else if (typeof err?.errDetail === 'string' && err.errDetail) {
      message = err.errDetail
    } else if (typeof err?.message === 'string' && err.message) {
      // Clean up error codes like [422]
      message = err.message.replace(/^\[\d+]\s*/, '')
    }
  } catch (e) {
    console.error('[authUtils] Error parsing API error:', e)
  }

  return message
}

// ========================================
// FORM UTILITIES
// ========================================

/**
 * Get trimmed form value
 * @param {string} elementId - Input element ID
 * @returns {string} - Trimmed value or empty string
 */
export function getFormValue(elementId) {
  const element = document.getElementById(elementId)
  return element ? element.value.trim() : ''
}

/**
 * Validate required fields
 * @param {Object} fields - Object with field names and values
 * @returns {Object} - {valid: boolean, message: string}
 */
export function validateRequiredFields(fields) {
  for (const [name, value] of Object.entries(fields)) {
    if (!value || value.trim().length === 0) {
      return {
        valid: false,
        message: `${name.charAt(0).toUpperCase() + name.slice(1)} is required`
      }
    }
  }
  return { valid: true, message: '' }
}

