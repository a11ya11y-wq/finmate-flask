import api from '../api/apiClient.js'

const form = document.getElementById('registerForm')
const statusDiv = document.getElementById('status_message')
const submitBtn = form?.querySelector('button[type="submit"]')
const btnText = submitBtn?.querySelector('.btn-text')
const spinner = submitBtn?.querySelector('.spinner-border')
// Reference the terms checkbox (exists in register.html with id="terms")
const termsCheckbox = document.getElementById('terms')

function showError(message) {
  if (!statusDiv) return
  const statusText = statusDiv.querySelector('.status-text')
  if (statusText) statusText.textContent = message
  statusDiv.classList.remove('d-none')
  statusDiv.classList.remove('alert-success')
  statusDiv.classList.add('alert-danger')
}

function showSuccess(message) {
  if (!statusDiv) return
  const statusText = statusDiv.querySelector('.status-text')
  if (statusText) statusText.textContent = message
  statusDiv.classList.remove('d-none')
  statusDiv.classList.remove('alert-danger')
  statusDiv.classList.add('alert-success')
}

function hideError() {
  if (statusDiv) statusDiv.classList.add('d-none')
}

function setLoading(loading) {
  if (!submitBtn) return
  submitBtn.disabled = loading
  if (loading) {
    btnText.textContent = 'Creating Account...'
    spinner.classList.remove('d-none')
  } else {
    btnText.textContent = 'Create Account'
    spinner.classList.add('d-none')
  }
}

function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

function validatePassword(password) {
  if (password.length < 8) {
    return 'Password must be at least 8 characters long'
  }
  return null
}

if(form){
  form.addEventListener('submit', async (e) => {
    e.preventDefault()
    hideError()

    const username = document.getElementById('username').value.trim()
    const email = document.getElementById('email').value.trim()
    const password = document.getElementById('password').value
    const confirm_password = document.getElementById('confirm_password').value

    // Basic validation to reduce backend spam
    if (!username || !email || !password || !confirm_password) {
      showError('Please fill in all fields')
      return
    }

    if (username.length < 3) {
      showError('Username must be at least 3 characters')
      return
    }

    // Basic email format check
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showError('Please enter a valid email address')
      return
    }

    if (password.length < 6) {
      showError('Password must be at least 6 characters')
      return
    }

    if (password !== confirm_password) {
      showError('Passwords do not match')
      return
    }

    // Client-side validation
    if (!username || username.length < 3) {
      showError('Username must be at least 3 characters long')
      return
    }

    if (!email || !validateEmail(email)) {
      showError('Please enter a valid email address')
      return
    }

    const passwordError = validatePassword(password)
    if (passwordError) {
      showError(passwordError)
      return
    }

    if (password !== confirm_password) {
      showError('Passwords do not match')
      return
    }

    if (termsCheckbox && !termsCheckbox.checked) {
      showError('You must agree to the Terms of Service and Privacy Policy')
      return
    }

    setLoading(true)

    try{
      await api.post('/auth/register', {username, email, password, confirm_password})
      // on success show message and redirect to login
      showSuccess('Account created successfully! Redirecting to login...')
      setTimeout(() => {
        window.location.href = '/login.html'
      }, 1500)
    }catch(err){
      showError(err.message || 'Registration failed. Please try again.')
      setLoading(false)
    }
  })
}

export default {}
