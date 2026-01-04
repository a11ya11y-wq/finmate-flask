import * as api from '../api/apiClient.js'
import { setToken } from './auth.js'

const form = document.getElementById('loginForm')
const statusDiv = document.getElementById('status_message')
const submitBtn = form?.querySelector('button[type="submit"]')
const btnText = submitBtn?.querySelector('.btn-text')
const spinner = submitBtn?.querySelector('.spinner-border')

function showError(message) {
  if (!statusDiv) return

  const statusText = statusDiv.querySelector('.status-text')
  if (statusText) {
    statusText.textContent = message
  }
  statusDiv.classList.remove('d-none')
}

function hideError() {
  if (statusDiv) statusDiv.classList.add('d-none')
}

function setLoading(loading) {
  if (!submitBtn) return

  submitBtn.disabled = loading
  if (loading) {
    if (btnText) btnText.textContent = 'Signing in...'
    if (spinner) spinner.classList.remove('d-none')
  } else {
    if (btnText) btnText.textContent = 'Sign In'
    if (spinner) spinner.classList.add('d-none')
  }
}

if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault()
    hideError()

    const email = document.getElementById('email')?.value.trim()
    const password = document.getElementById('password')?.value
    const rememberMe = document.getElementById('remember_me')?.checked || false

    // Basic validation
    if (!email || !password) {
      showError('Please fill in all fields')
      return
    }

    // Basic email format check
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showError('Please enter a valid email address')
      return
    }

    setLoading(true)

    try {
      // New login endpoint returns access_token in JSON and sets refresh_token as HttpOnly cookie
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
        showError('Invalid response from server. Please try again.')
        setLoading(false)
      }
    } catch (err) {
      let errorMessage = 'Login failed. Please check your credentials.'

      if (err.message) {
        errorMessage = err.message.replace(/^\[\d+]\s*/, '')
      }

      console.error('Login error:', err)
      showError(errorMessage)
      setLoading(false)
    }
  })
}

// no default export
