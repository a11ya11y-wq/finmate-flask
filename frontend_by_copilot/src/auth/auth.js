export function setToken(token){
  localStorage.setItem('finmate_token', token)
}
export function getToken(){
  return localStorage.getItem('finmate_token')
}
export function clearToken(){
  localStorage.removeItem('finmate_token')
}

export function redirectToLogin(){
  window.location.href = '/login.html'
}

