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

    // Throw an Error object but attach response data and status so callers can inspect details
    const err = new Error(errDetail)
    try{ err.status = res.status }catch(e){}
    try{ err.data = data }catch(e){}
    // keep original res.statusText for reference
    try{ err.errDetail = errDetail }catch(e){}

    // If backend provided detailed validation messages, build a combined message
    try{
      if(data){
        if(Array.isArray(data.details) && data.details.length){
          err.message = data.details.join('\n')
        } else if(data.details && typeof data.details === 'object'){
          const parts = []
          for(const k of Object.keys(data.details)){
            const v = data.details[k]
            if(Array.isArray(v)) parts.push(...v)
            else if(typeof v === 'string') parts.push(v)
          }
          if(parts.length) err.message = parts.join('\n')
        }
      }
    }catch(e){ /* ignore */ }

    throw err
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
