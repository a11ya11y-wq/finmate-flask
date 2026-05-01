const BASE_URL = import.meta.env.VITE_API_ROOT

// Interceptor Queue Pattern variables to prevent race conditions
let isRefreshing = false
let failedQueue = []

// JWT with HttpOnly Cookies - only manage access_token in localStorage
function getAccessToken(){
  try {
    return localStorage.getItem('finmate_access_token')
  } catch(e) {
    console.warn('Failed to access localStorage:', e)
    return null
  }
}

function setAccessToken(token) {
  try {
    localStorage.setItem('finmate_access_token', token)
    // Dispatch auth:login event for UI synchronization
    window.dispatchEvent(new Event('auth:login'))
  } catch(e) {
    console.error('Failed to save access token:', e)
  }
}

function clearAccessToken() {
  try {
    localStorage.removeItem('finmate_access_token')
    // Dispatch auth:logout event for UI synchronization
    window.dispatchEvent(new Event('auth:logout'))
  } catch(e) {
    console.warn('Failed to clear access token:', e)
  }
}

// Silent refresh function - simplified, no queue logic here
async function attemptSilentRefresh() {
  try {
    const response = await fetch(BASE_URL + '/auth/refresh', {
      method: 'POST',
      credentials: 'include', // Important: sends HttpOnly cookies
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`Refresh failed: ${response.status}`)
    }

    const data = await response.text()
    const parsed = data ? JSON.parse(data) : null

    if (parsed && parsed.access_token) {
      setAccessToken(parsed.access_token)
      return parsed.access_token
    }

    throw new Error('No access token in refresh response')
  } catch (error) {
    console.error('Silent refresh failed:', error)
    clearAccessToken()
    throw error
  }
}

function normalizePath(path){
  // Do not force a trailing slash — backend expects clean paths without trailing slash.
  try{
    const idx = path.indexOf('?')
    if(idx === -1){
      // remove trailing slash if present (except keep single slash)
      if(path.length > 1 && path.endsWith('/')) return path.slice(0, -1)
      return path
    } else {
      const base = path.slice(0, idx)
      const qs = path.slice(idx + 1)
      const nb = (base.length > 1 && base.endsWith('/')) ? base.slice(0, -1) : base
      return nb + '?' + qs
    }
  }catch(e){ return path }
}

async function authorizedFetch(path, options = {}) {
  path = normalizePath(path)

  const headers = options.headers || {}
  headers['Content-Type'] = 'application/json'

  const token = getAccessToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const fetchOptions = {
    ...options,
    headers,
    credentials: 'include', // Always include cookies for refresh token
    mode: 'cors'
  }

  const fullUrl = BASE_URL + path

  try {
    const response = await fetch(fullUrl, fetchOptions)

    // Handle 401 Unauthorized with Interceptor Queue pattern
    if (response.status === 401) {
      const isLoginRequest = path.includes('/auth/login')
      const isRefreshRequest = path.includes('/auth/refresh')

      // Don't attempt refresh for login or refresh endpoints
      if (isLoginRequest || isRefreshRequest) {
        return await handleResponse(response, fullUrl)
      }

      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token) => {
              // Retry original request with new token
              fetchOptions.headers['Authorization'] = `Bearer ${token}`
              fetch(fullUrl, fetchOptions)
                .then(response => handleResponse(response, fullUrl))
                .then(resolve)
                .catch(reject)
            },
            reject
          })
        })
      }

      // Start refresh process
      isRefreshing = true

      try {
        const newAccessToken = await attemptSilentRefresh()

        // Process all queued requests
        failedQueue.forEach(({ resolve }) => {
          resolve(newAccessToken)
        })
        failedQueue = []
        isRefreshing = false

        // Retry original request with new token
        fetchOptions.headers['Authorization'] = `Bearer ${newAccessToken}`
        const retryResponse = await fetch(fullUrl, fetchOptions)
        return await handleResponse(retryResponse, fullUrl)

      } catch (refreshError) {
        console.error('Silent refresh failed, redirecting to login:', refreshError)

        // Reject all queued requests
        failedQueue.forEach(({ reject }) => {
          reject(new Error('Authentication failed'))
        })
        failedQueue = []
        isRefreshing = false

        clearAccessToken()

        // Only redirect if we're not on login page
        if (!window.location.pathname.includes('login.html')) {
          window.location.href = '/login.html'
        }

        throw new Error('Authentication failed')
      }
    }

    return await handleResponse(response, fullUrl)

  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      console.error('Network error:', error)
      throw new Error('Network error. Please check your connection.')
    }
    throw error
  }
}

async function handleResponse(response, fullUrl) {
  const text = await response.text()
  let data = null

  try {
    data = text ? JSON.parse(text) : null
  } catch(e) {
    data = text
  }

  if (!response.ok) {
    let errorMessage = response.statusText || 'Request failed'

    if (data) {
      if (typeof data === 'string') {
        errorMessage = data
      } else if (data.error) {
        errorMessage = data.error
      } else if (data.message) {
        errorMessage = data.message
      }
    }

    console.error('[apiClient] Request failed:', {
      url: fullUrl,
      status: response.status,
      errorMessage,
      data
    })

    const error = new Error(errorMessage)
    error.status = response.status
    error.data = data

    // Handle validation errors with details array
    if (data && Array.isArray(data.details) && data.details.length > 0) {
      error.message = data.details.join('\n')
    }

    throw error
  }

  return data
}

// Logout function
export async function logout() {
  const token = getAccessToken()
  if (!token) {
    // No token to logout, just clear and redirect
    clearAccessToken()
    window.location.href = '/login.html'
    return
  }

  try {
    await authorizedFetch('/auth/logout', {
      method: 'POST'
    })
  } catch (error) {
    console.error('Logout request failed:', error)
    // Continue with local cleanup even if server request fails
  } finally {
    clearAccessToken()
    window.location.href = '/login.html'
  }
}

// API methods
export async function post(path, body) {
  return authorizedFetch(path, {
    method: 'POST',
    body: JSON.stringify(body)
  })
}

export async function get(path) {
  return authorizedFetch(path, {
    method: 'GET'
  })
}

export async function put(path, body) {
  return authorizedFetch(path, {
    method: 'PUT',
    body: JSON.stringify(body)
  })
}

export async function del(path) {
  return authorizedFetch(path, {
    method: 'DELETE'
  })
}

// Export token management functions for auth.js compatibility
export { getAccessToken as getToken, setAccessToken as setToken, clearAccessToken as clearToken }

export default {get, post, put, del}
