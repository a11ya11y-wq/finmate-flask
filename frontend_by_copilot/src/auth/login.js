import * as api from '../api/apiClient.js'
import { setToken } from './auth.js'
import {
  validateEmail,
  showError,
  hideStatus,
  setButtonLoading,
  parseApiError,
  getFormValue
} from './authUtils.js'

const form = document.getElementById('loginForm')
const statusDiv = document.getElementById('status_message')
const submitBtn = form?.querySelector('button[type="submit"]')

if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault()
    hideStatus(statusDiv)

    const email = getFormValue('email')
    const password = document.getElementById('password')?.value || ''
    const rememberMe = document.getElementById('remember_me')?.checked || false

    // Validation
    if (!email || !password) {
      showError(statusDiv, 'Please fill in all fields')
      return
    }

    if (!validateEmail(email)) {
      showError(statusDiv, 'Please enter a valid email address')
      return
    }

    setButtonLoading(submitBtn, true, {
      loadingText: 'Signing in...',
      defaultText: 'Sign In'
    })

    try {
      // Login endpoint returns access_token in JSON and sets refresh_token as HttpOnly cookie
      const data = await api.post('/auth/login', {
        email,
        password,
        remember_me: rememberMe
      })

      if (data && data.access_token) {
        // Save access token to localStorage
        setToken(data.access_token)

        // Redirect to dashboard
        window.location.href = '/dashboard.html'
      } else {
        showError(statusDiv, 'Invalid response from server. Please try again.')
        setButtonLoading(submitBtn, false, { defaultText: 'Sign In' })
      }
    } catch (err) {
      const errorMessage = parseApiError(err, 'Login failed. Please check your credentials.')
      console.error('Login error:', err)
      showError(statusDiv, errorMessage)
      setButtonLoading(submitBtn, false, { defaultText: 'Sign In' })
    }
  })
}

