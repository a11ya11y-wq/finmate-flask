import * as api from '../api/apiClient.js'

const form = document.getElementById('registerForm')
const statusDiv = document.getElementById('status_message')
const submitBtn = form?.querySelector('button[type="submit"]')
const btnText = submitBtn?.querySelector('.btn-text')
const spinner = submitBtn?.querySelector('.spinner-border')
const termsCheckbox = document.getElementById('terms')

// === Helpers ===

const iconError = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="me-2"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`;
const iconSuccess = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="me-2"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`;

function showError(message) {
  if (!statusDiv) return;

  // Форматуємо повідомлення
  try {
     const m = (message || '').toString();
     if (m.toLowerCase().includes('part after the @-sign') || m.toLowerCase().includes('top-level domain')) {
        message = 'Please enter a valid email address';
     }
  } catch (e) {}

  const formattedMessage = message ? message.replace(/\n/g, '<br>') : 'Unknown error';

  // 1. Жорстко задаємо стилі через JS, щоб перебити будь-які CSS налаштування
  statusDiv.className = 'alert alert-danger d-flex align-items-center'; // Bootstrap класи
  statusDiv.style.borderColor = '#ff4d4f'; // Червона рамка
  statusDiv.style.color = '#ff4d4f';       // Червоний текст
  statusDiv.style.backgroundColor = 'rgba(255, 77, 79, 0.1)'; // Легкий червоний фон

  // 2. Вставляємо ІКОНКУ помилки + текст
  statusDiv.innerHTML = `
    ${iconError}
    <div>${formattedMessage}</div>
  `;

  statusDiv.classList.remove('d-none');
}

function showSuccess(message) {
  if (!statusDiv) return;

  // 1. Жорстко задаємо стилі успіху
  statusDiv.className = 'alert alert-success d-flex align-items-center';
  statusDiv.style.borderColor = '#28a745'; // Зелена рамка
  statusDiv.style.color = '#28a745';       // Зелений текст
  statusDiv.style.backgroundColor = 'rgba(40, 167, 69, 0.1)'; // Легкий зелений фон

  // 2. Вставляємо ІКОНКУ успіху + текст
  statusDiv.innerHTML = `
    ${iconSuccess}
    <div>${message}</div>
  `;

  statusDiv.classList.remove('d-none');
}

function hideError() {
  if (statusDiv) statusDiv.classList.add('d-none')
}

function setLoading(loading) {
  if (!submitBtn) return
  submitBtn.disabled = loading
  if (loading) {
    if (btnText) btnText.textContent = 'Creating Account...'
    if (spinner) spinner.classList.remove('d-none')
  } else {
    if (btnText) btnText.textContent = 'Create Account'
    if (spinner) spinner.classList.add('d-none')
  }
}

function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

// === Main Logic ===

if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault()
    hideError()

    const username = document.getElementById('username').value.trim()
    const email = document.getElementById('email').value.trim()
    const password = document.getElementById('password').value
    const confirm_password = document.getElementById('confirm_password').value

    // --- Validation Section ---

    // 1. Check if empty
    if (!username || !email || !password || !confirm_password) {
      showError('Please fill in all fields')
      return
    }

    // 2. Username
    if (username.length < 3) {
      showError('Username must be at least 3 characters long')
      return
    }

    // 3. Email
    if (!validateEmail(email)) {
      showError('Please enter a valid email address')
      return
    }

    // 4. Password
    if (password.length < 6) {
      showError('Password must be at least 6 characters long')
      return
    }

    // 5. Match
    if (password !== confirm_password) {
      showError('Passwords do not match')
      return
    }

    // 6. Terms
    if (termsCheckbox && !termsCheckbox.checked) {
      showError('You must agree to the Terms of Service and Privacy Policy')
      return
    }

    // --- API Request ---
    setLoading(true)

    try {
      await api.post('/auth/register', {
        username,
        email,
        password,
        confirm_password
      })

      // on success show message and redirect to login
      showSuccess('Account created successfully! Redirecting to login...')
      setTimeout(() => {
        window.location.href = '/login.html'
      }, 1500)
    } catch (err) {
      // Improved error handling: prefer details array from backend 422 responses
      let msg = 'Registration failed. Please try again.'
      try {
        let data = err?.data || err?.response?.data || null
        console.error('[register] request error (initial):', { err, data })

        // If no structured data, try to parse JSON from err.errDetail or err.message
        if (!data) {
          const candidate = err?.errDetail || err?.message || null
          if (candidate && typeof candidate === 'string') {
            try {
              const parsed = JSON.parse(candidate)
              if (parsed) data = parsed
              console.warn('[register] parsed JSON from errDetail/message', parsed)
            } catch (e) {
              // not JSON
            }
          }
        }

        if (data) {
          // 1) details as array of strings
          if (Array.isArray(data.details) && data.details.length) {
            msg = data.details.join('\n')

          // 2) details as object like {email: ['msg'], password: ['msg']}
          } else if (data.details && typeof data.details === 'object') {
            const parts = []
            for (const k of Object.keys(data.details)) {
              const v = data.details[k]
              if (Array.isArray(v)) parts.push(...v)
              else if (typeof v === 'string') parts.push(v)
            }
            if (parts.length) msg = parts.join('\n')

          // 3) generic errors array
          } else if (Array.isArray(data.errors) && data.errors.length) {
            msg = data.errors.join('\n')

          // 4) fallback message fields
          } else if (typeof data.error === 'string' && data.error) {
            msg = data.error
          } else if (typeof data.message === 'string' && data.message) {
            msg = data.message
          } else if (typeof data === 'string' && data) {
            msg = data
          }
        } else if (typeof err?.errDetail === 'string' && err.errDetail) {
          msg = err.errDetail
        } else if (typeof err?.message === 'string' && err.message) {
          msg = err.message
        }
      } catch (e) {
        // ignore parsing errors and keep generic message
        console.error('[register] error parsing failure response', e)
      }

      showError(msg)
    } finally {
      setLoading(false)
    }
  })
}

export default {}