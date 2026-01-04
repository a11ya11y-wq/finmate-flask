// Token management for JWT with HttpOnly cookies
export function setToken(accessToken) {
  try {
    localStorage.setItem('finmate_access_token', accessToken)
  } catch(e) {
    console.error('Failed to save access token:', e)
  }
}

export function getToken() {
  try {
    return localStorage.getItem('finmate_access_token')
  } catch(e) {
    console.warn('Failed to get access token:', e)
    return null
  }
}

export function clearToken() {
  try {
    localStorage.removeItem('finmate_access_token')
  } catch(e) {
    console.warn('Failed to clear access token:', e)
  }
}

export function isAuthenticated() {
  return !!getToken()
}

export function redirectToLogin() {
  window.location.href = '/login.html'
}

export function redirectToDashboard() {
  window.location.href = '/dashboard.html'
}

