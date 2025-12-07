import { getToken, clearToken } from '../auth/auth.js'
import { getProfile } from '../utils/profileCache.js'

export async function renderHeader(){
  const headerUserSection = document.getElementById('header-user-section')
  if(!headerUserSection) return

  const token = getToken()

  if(token){
    try{
      const user = await getProfile()
      // determine avatar URL
      let avatarUrl = '/avatars/default/default.svg'
      if(user){
        if(user.avatar_url) avatarUrl = user.avatar_url
        else if(user.avatar && typeof user.avatar === 'string'){
          const a = user.avatar
          if(a.startsWith('/')){
            avatarUrl = a
          } else if(a.includes('static/avatars')){
            avatarUrl = '/' + a.replace(/^static\//, '')
          } else if(a.includes('avatars')){
            avatarUrl = '/' + a
          } else {
            avatarUrl = '/avatars/default/default.svg'
          }
        }
      }

      headerUserSection.innerHTML = `
        <div class="d-flex align-items-center gap-3" id="user-dropdown">
          <img src="${avatarUrl}" alt="avatar" width="32" height="32" class="rounded-circle user-avatar" />
          <div class="dropdown">
            <a href="#" class="dropdown-toggle text-light text-decoration-none" data-bs-toggle="dropdown" data-bs-auto-close="true" id="userDropdown">
              ${user.username}
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
              <li><a class="dropdown-item" href="/dashboard.html"><i class="bi bi-speedometer2 me-2"></i>Dashboard</a></li>
              <li><a class="dropdown-item" href="/budget.html"><i class="bi bi-piggy-bank me-2"></i>Budgets</a></li>
              <li><a class="dropdown-item" href="/profile.html"><i class="bi bi-person me-2"></i>Profile</a></li>
              <li><hr class="dropdown-divider" /></li>
              <li><button class="dropdown-item text-danger" id="logout-button"><i class="bi bi-box-arrow-right me-2"></i>Sign out</button></li>
            </ul>
          </div>
        </div>
      `
     }catch(e){
       // failed to load profile - show login buttons
       headerUserSection.innerHTML = `
         <div class="d-flex align-items-center gap-3" id="auth-controls">
           <a href="/login.html" class="btn btn-outline-primary btn-sm">Login</a>
           <a href="/register.html" class="btn btn-primary btn-sm">Sign up</a>
         </div>
       `
     }
   } else {
     // Not logged in - show login buttons
     headerUserSection.innerHTML = `
       <div class="d-flex align-items-center gap-3" id="auth-controls">
         <a href="/login.html" class="btn btn-outline-primary btn-sm">Login</a>
         <a href="/register.html" class="btn btn-primary btn-sm">Sign up</a>
       </div>
     `
   }


  // Attach event handlers after DOM update
  setTimeout(() => {
    // Logout handler
    const logoutBtn = document.getElementById('logout-button')
    if(logoutBtn){
      logoutBtn.addEventListener('click', (e)=>{
        e.preventDefault()
        clearToken()
        window.location.href = '/login.html'
      })
    }

    // Initialize Bootstrap Dropdown
    const dropdownToggle = document.getElementById('userDropdown')
    if(dropdownToggle && typeof bootstrap !== 'undefined'){
      try {
        new bootstrap.Dropdown(dropdownToggle, {
          autoClose: true
        })
      } catch(e) {
        console.error('Failed to initialize dropdown:', e)
      }
    }
  }, 100)
}

export default { renderHeader }
