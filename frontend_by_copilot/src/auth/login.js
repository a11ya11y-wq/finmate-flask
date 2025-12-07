import api from '../api/apiClient.js'

const form = document.getElementById('loginForm')
const statusDiv = document.getElementById('status_message')
const submitBtn = form?.querySelector('button[type="submit"]')
const btnText = submitBtn?.querySelector('.btn-text')
const spinner = submitBtn?.querySelector('.spinner-border')

function showError(message) {
  if (!statusDiv) {
    return
  }
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
    btnText.textContent = 'Signing in...'
    spinner.classList.remove('d-none')
  } else {
    btnText.textContent = 'Sign In'
    spinner.classList.add('d-none')
  }
}

async function saveTokenReliable(token){
  try{
    // Try set and confirm
    localStorage.setItem('finmate_token', token)
    for(let i=0;i<10;i++){
      if(localStorage.getItem('finmate_token')) return true
      await new Promise(r => setTimeout(r,50))
    }
    // localStorage failed to persist quickly; fallback to sessionStorage silently
    sessionStorage.setItem('finmate_token', token)
    return !!sessionStorage.getItem('finmate_token')
  }catch(e){
    try{ sessionStorage.setItem('finmate_token', token); return !!sessionStorage.getItem('finmate_token') }catch(_){ }
    return false
  }
}

if(form){
  form.addEventListener('submit', async (e) => {
    e.preventDefault()
    hideError()

    const email = document.getElementById('email').value.trim()
    const password = document.getElementById('password').value

    // Basic validation to reduce backend spam
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

    try{
      const data = await api.post('/auth/login', {email, password})
      // login response received
      if(data && data.access_token){
        const token = data.access_token
        const saved = await saveTokenReliable(token)
        // token persistence result: saved
        if(!saved){
          // fallback: set cookie for current origin
          try{
            document.cookie = `finmate_token=${encodeURIComponent(token)}; path=/;`;
          }catch(e){
            showError('Failed to save login token locally. Please check browser settings.')
            setLoading(false)
            return
          }
        }
        // redirect after token persisted — no token in URL
        window.location.href = window.location.origin + '/dashboard.html'
      } else {
        showError('No token received from server.')
        setLoading(false)
      }
    }catch(err){
      // Extract clean error message
      let errorMessage = 'Login failed. Please check your credentials.'
      if(err.message){
        // Remove status code prefix like "[401]" if present
        errorMessage = err.message.replace(/^\[\d+]\s*/, '')
      }

      showError(errorMessage)
      setLoading(false)
    }
  })
}

// no default export
