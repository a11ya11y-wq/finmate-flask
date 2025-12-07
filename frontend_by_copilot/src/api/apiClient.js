const DEFAULT_BASE = '/api/v1'
const BASE_URL = (import.meta.env.VITE_API_ROOT || '').replace(/\/$/, '') || DEFAULT_BASE

function getToken(){
  let token = null
  try{
    token = localStorage.getItem('finmate_token') || sessionStorage.getItem('finmate_token')
  }catch(e){
    // access to localStorage might throw in some contexts
    try{ token = sessionStorage.getItem('finmate_token') }catch(_){ token = null }
  }

  // also check query param 'token' (dev fallback) and persist to sessionStorage
  if(!token && typeof window !== 'undefined'){
    try{
      const params = new URLSearchParams(window.location.search)
      const qtoken = params.get('token')
      if(qtoken){
        try{ sessionStorage.setItem('finmate_token', qtoken) }catch(_){ }
        token = qtoken
      }
    }catch(e){ /* ignore */ }
  }

  if(!token && typeof document !== 'undefined'){
    const m = document.cookie.match('(?:^|; )finmate_token=([^;]+)')
    if(m) token = decodeURIComponent(m[1])
  }

  return token
}

function normalizePath(path){
  // Ensure path part (before query) ends with a slash to avoid backend redirecting (308) which may change origin
  try{
    const idx = path.indexOf('?')
    if(idx === -1){
      if(!path.endsWith('/')) return path + '/'
      return path
    } else {
      const base = path.slice(0, idx)
      const qs = path.slice(idx + 1)
      const nb = base.endsWith('/') ? base : base + '/'
      return nb + '?' + qs
    }
  }catch(e){ return path }
}

async function request(path, options = {}){
  path = normalizePath(path)
  const headers = options.headers || {}
  headers['Content-Type'] = 'application/json'
  const token = getToken()
  if(token) headers['Authorization'] = `Bearer ${token}`

  // debug logs
  const fullUrl = (BASE_URL + path)
  // mask token for logs
  const maskedToken = token ? `${token.slice(0,8)}...${token.slice(-8)}` : null
  // request debug removed

  const fetchOptions = { ...options, headers, credentials: 'include', mode: 'cors' }
  const res = await fetch(fullUrl, fetchOptions)

  // response debug removed

  if(res.status === 401){
    // unauthorized
    // Exception: if this is a login request, don't redirect - just throw error to show message
    const isLoginRequest = path.includes('/auth/login')

    if(!isLoginRequest){
      // clear token and redirect to login for protected routes
      try{ localStorage.removeItem('finmate_token') }catch(_){}
      try{ sessionStorage.removeItem('finmate_token') }catch(_){}
      // clear cookie
      if(typeof document !== 'undefined') document.cookie = 'finmate_token=; path=/; Max-Age=0'
      window.location.href = '/login.html'
      throw new Error('Unauthorized')
    }
    // For login requests, parse error and throw it (will be caught by login form handler)
  }

  const text = await res.text()
  let data = null
  try{ data = text ? JSON.parse(text) : null }catch(e){ data = text }

  if(!res.ok){
    // Extract error message from response
    let errDetail = res.statusText
    if(data){
      if(typeof data === 'string'){
        errDetail = data
      } else if(data.error){
        errDetail = data.error
      } else if(data.message){
        errDetail = data.message
      } else {
        errDetail = JSON.stringify(data)
      }
    }

    console.error('[apiClient] Request failed:', { url: fullUrl, status: res.status, errDetail, data })

    // For user-friendly errors, throw just the message without status code prefix
    // (login form will add its own context)
    throw new Error(errDetail)
  }

  return data
}

export async function post(path, body){
  return request(path, {method: 'POST', body: JSON.stringify(body)})
}

export async function get(path){
  return request(path, {method: 'GET'})
}

export async function put(path, body){
  return request(path, {method: 'PUT', body: JSON.stringify(body)})
}

export async function del(path){
  return request(path, {method: 'DELETE'})
}

export default {get, post, put, del}
