import { getToken, clearToken } from '../auth/auth.js'
import { logout as apiLogout } from '../api/apiClient.js'
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

      // ✅ Add mobile bottom navigation
      addMobileBottomNav(user, avatarUrl)
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
      logoutBtn.addEventListener('click', async (e) => {
        e.preventDefault()

        // Disable button to prevent double clicks
        logoutBtn.disabled = true
        logoutBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-2 spin"></i>Signing out...'

        try {
          // Call API logout (handles server request + local cleanup)
          await apiLogout()
        } catch (error) {
          console.error('Logout error:', error)
          // Even if API call fails, ensure local cleanup and redirect
          clearToken()
          window.location.href = '/login.html'
        }
      })
    }

    // Mobile nav logout handler
    const mobileLogoutBtn = document.getElementById('mobile-logout-button')
    if(mobileLogoutBtn){
      mobileLogoutBtn.addEventListener('click', async (e) => {
        e.preventDefault()
        try {
          await apiLogout()
        } catch (error) {
          console.error('Logout error:', error)
          clearToken()
          window.location.href = '/login.html'
        }
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

// ✅ Mobile Bottom Navigation
function addMobileBottomNav(user, avatarUrl) {
  // Remove existing mobile nav if present
  const existingNav = document.getElementById('mobile-bottom-nav')
  if (existingNav) {
    existingNav.remove()
  }

  // Determine current page
  const currentPath = window.location.pathname
  const isDashboard = currentPath.includes('dashboard')
  const isBudgets = currentPath.includes('budget')
  const isProfile = currentPath.includes('profile')

  const mobileNavHTML = `
    <nav class="mobile-bottom-nav" id="mobile-bottom-nav">
      <a href="/dashboard.html" class="mobile-nav-item ${isDashboard ? 'active' : ''}">
        <i class="bi bi-speedometer2"></i>
        <span>Dashboard</span>
      </a>
      
      <a href="/budget.html" class="mobile-nav-item ${isBudgets ? 'active' : ''}">
        <i class="bi bi-piggy-bank"></i>
        <span>Budgets</span>
      </a>
      
      <a href="/profile.html" class="mobile-nav-item ${isProfile ? 'active' : ''}">
        <i class="bi bi-person"></i>
        <span>Profile</span>
      </a>
      
      <button class="mobile-nav-item" id="mobile-logout-button">
        <i class="bi bi-box-arrow-right"></i>
        <span>Logout</span>
      </button>
    </nav>
  `

  document.body.insertAdjacentHTML('beforeend', mobileNavHTML)
}

export default { renderHeader }
