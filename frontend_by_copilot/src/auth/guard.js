import { getToken } from './auth.js'

export function requireAuth(){
  const token = getToken()
  if(!token){
    window.location.href = '/login.html'
    return false
  }
  return true
}

export default { requireAuth }

