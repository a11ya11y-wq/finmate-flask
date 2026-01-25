import * as api from '../api/apiClient.js'
import {
  validateEmail,
  validateUsername,
  validatePassword,
  showError,
  showSuccess,
  hideStatus,
  setButtonLoading,
  parseApiError,
  getFormValue
} from './authUtils.js'

const form = document.getElementById('registerForm')
const statusDiv = document.getElementById('status_message')
const submitBtn = form?.querySelector('button[type="submit"]')
const termsCheckbox = document.getElementById('terms')

if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault()
    hideStatus(statusDiv)

    const username = getFormValue('username')
    const email = getFormValue('email')
    const password = document.getElementById('password')?.value || ''
    const confirmPassword = document.getElementById('confirm_password')?.value || ''

    // --- Validation Section ---

    // 1. Check if empty
    if (!username || !email || !password || !confirmPassword) {
      showError(statusDiv, 'Please fill in all fields')
      return
    }

    // 2. Username validation
    const usernameValidation = validateUsername(username)
    if (!usernameValidation.valid) {
      showError(statusDiv, usernameValidation.message)
      return
    }

    // 3. Email validation
    if (!validateEmail(email)) {
      showError(statusDiv, 'Please enter a valid email address')
      return
    }

    // 4. Password validation
    const passwordValidation = validatePassword(password)
    if (!passwordValidation.valid) {
      showError(statusDiv, passwordValidation.message)
      return
    }

    // 5. Password match
    if (password !== confirmPassword) {
      showError(statusDiv, 'Passwords do not match')
      return
    }

    // 6. Terms checkbox
    if (termsCheckbox && !termsCheckbox.checked) {
      showError(statusDiv, 'You must agree to the Terms of Service and Privacy Policy')
      return
    }

    // --- API Request ---
    setButtonLoading(submitBtn, true, {
      loadingText: 'Creating Account...',
      defaultText: 'Create Account'
    })

    try {
      await api.post('/auth/register', {
        username,
        email,
        password,
        confirm_password: confirmPassword
      })

      // On success show message and redirect to login
      showSuccess(statusDiv, 'Account created successfully! Redirecting to login...')

      setTimeout(() => {
        window.location.href = '/login.html'
      }, 1500)

    } catch (err) {
      const errorMessage = parseApiError(err, 'Registration failed. Please try again.')
      console.error('[register] Registration error:', err)
      showError(statusDiv, errorMessage)
      setButtonLoading(submitBtn, false, { defaultText: 'Create Account' })
    }
  })
}

export default {}

