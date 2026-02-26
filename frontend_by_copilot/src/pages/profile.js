import * as api from '../api/apiClient.js'
import { getToken } from '../auth/auth.js'
import { renderHeader } from '../components/layout.js'
import { showSuccess, showError } from '../utils/toast.js'
import { confirmDelete, showConfirmDialog } from '../utils/confirmDialog.js'

// State
let currentUser = null
let selectedAvatar = null
let categories = []

// Available avatars
const AVAILABLE_AVATARS = [
    'avatars/default/default.svg',
    'avatars/default/1.svg',
    'avatars/default/2.svg',
    'avatars/default/3.svg',
    'avatars/default/4.svg',
    'avatars/default/5.svg',
    'avatars/default/6.svg',
    'avatars/default/7.svg',
    'avatars/default/8.svg',
    'avatars/default/9.svg'
]

// Initialize
async function init() {
    if (!getToken()) {
        window.location.href = '/login.html'
        return
    }

    try {
        await renderHeader()
        await loadUserProfile()
        await loadCategories()
        renderAvatarGallery()
        attachEventListeners()
    } catch (error) {
        console.error('[profile] Init error:', error)
        showError('Failed to load profile')
    }
}

// Load user profile (simplified - no cache, fresh data every time)
async function loadUserProfile() {
    try {
        const data = await api.get('/profile/me')
        currentUser = data

        // Update UI
        document.getElementById('userName').textContent = data.username || 'User'
        document.getElementById('userEmail').textContent = data.email || 'email@example.com'
        document.getElementById('userCurrency').textContent = data.currency || 'EUR'
        document.getElementById('newUsername').value = data.username || ''

        // Set currency select value
        const currencySelect = document.getElementById('userCurrencySelect')
        if (currencySelect) {
            currencySelect.value = data.currency || 'EUR'
        }

        // Update avatar
        let avatarPath = data.avatar || 'avatars/default/default.svg'
        if (avatarPath.includes('static/')) {
            avatarPath = avatarPath.replace('static/', '')
        }
        document.getElementById('userAvatar').src = `/${avatarPath}`
        selectedAvatar = avatarPath

        // Update Monobank status
        const badge = document.getElementById('monobankBadge')
        const statusText = document.getElementById('monobankStatusText')

        if (data.monobank_token_is_set) {
            if (badge) {
                badge.classList.add('connected')
                badge.innerHTML = '<i class="bi bi-check-circle-fill"></i>'
            }
            if (statusText) {
                statusText.innerHTML = '<i class="bi bi-check-circle"></i> <span style="color: var(--success)">Connected</span>'
            }
        } else {
            if (badge) {
                badge.classList.remove('connected')
                badge.innerHTML = '<i class="bi bi-credit-card"></i>'
            }
            if (statusText) {
                statusText.innerHTML = '<i class="bi bi-credit-card"></i> <span>Not connected</span>'
            }
        }

    } catch (error) {
        console.error('[profile] Error loading profile:', error)
        showError('Failed to load profile')
    }
}

// Load categories
async function loadCategories() {
    try {
        const raw = await api.get('/categories/all/')
        // Backend returns { data: [...] } or legacy array
        categories = Array.isArray(raw) ? raw : (raw && raw.data ? raw.data : [])
        renderCategories()
    } catch (error) {
        console.error('[profile] Error loading categories:', error)
        showError('Failed to load categories')
    }
}

// Simple HTML escaper
function escapeHtml(s){
    if(s === null || s === undefined) return ''
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')
}

// Render Categories List
function renderCategories() {
    const container = document.getElementById('categoriesList')
    if (!container) return

    if (!categories || categories.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 40px 20px;">No categories yet. Add your first category above!</p>'
        return
    }

    container.innerHTML = categories.map(cat => {
        // Backend provides icon (e.g., 'bi-bag-fill')
        const iconClass = cat.icon ? String(cat.icon).trim() : 'bi-tag-fill'
        const mccCode = cat.mcc_code || cat.mcc_codes || cat.mccCode || ''
        const mccDisplay = mccCode && mccCode.trim()
            ? `<div class="category-mcc-modal">MCC: ${mccCode}</div>`
            : '<div class="category-mcc-modal" style="color: var(--text-secondary);">No MCC codes</div>'

        return `
            <div class="category-item-modal">
                <div class="category-icon-modal">
                    <i class="${escapeHtml(iconClass)}"></i>
                </div>
                <div class="category-info-modal">
                    <div class="category-name-modal">${escapeHtml(cat.name)}</div>
                    ${mccDisplay}
                </div>
                <div class="category-actions-modal">
                    <button class="category-btn" onclick="window.editCategory(${cat.id})" title="Edit">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="category-btn delete" onclick="window.deleteCategory(${cat.id})" title="Delete">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `
    }).join('')
}

// Render avatar gallery
function renderAvatarGallery() {
    const gallery = document.getElementById('avatarGallery')

    gallery.innerHTML = AVAILABLE_AVATARS.map(path => `
        <label class="avatar-item ${path === selectedAvatar ? 'selected' : ''}" 
               data-avatar="${path}">
            <input type="radio" name="avatar" value="${path}" 
                   ${path === selectedAvatar ? 'checked' : ''}>
            <img src="/${path}" alt="Avatar">
        </label>
    `).join('')

    // Add click handlers
    gallery.querySelectorAll('.avatar-item').forEach(item => {
        item.addEventListener('click', () => {
            gallery.querySelectorAll('.avatar-item').forEach(i => i.classList.remove('selected'))
            item.classList.add('selected')
            selectedAvatar = item.dataset.avatar
        })
    })
}

// Helper: Force close modal and remove backdrop
function forceCloseModal(modalId) {
    const modalEl = document.getElementById(modalId)
    if (!modalEl) return

    // Get existing modal instance
    let modal = bootstrap.Modal.getInstance(modalEl)

    if (modal) {
        // Dispose existing instance completely
        modal.dispose()
    }

    // Manually hide modal
    modalEl.classList.remove('show')
    modalEl.style.display = 'none'
    modalEl.removeAttribute('aria-modal')
    modalEl.setAttribute('aria-hidden', 'true')

    // Force cleanup immediately and after delay
    const cleanup = () => {
        // Remove ALL backdrops (sometimes Bootstrap creates multiple)
        document.querySelectorAll('.modal-backdrop').forEach(el => {
            el.remove()
        })

        // Clean body classes
        document.body.classList.remove('modal-open')
        document.body.style.overflow = ''
        document.body.style.paddingRight = ''
    }

    // Run cleanup twice - once immediately, once after animation
    cleanup()
    setTimeout(cleanup, 400)
}

// Update profile (username + avatar + currency)
async function updateProfile(e) {
    e.preventDefault()

    const newUsername = document.getElementById('newUsername').value.trim()
    const currency = document.getElementById('userCurrencySelect').value

    if (!newUsername || newUsername.length < 3) {
        showError('Username must be at least 3 characters')
        return
    }

    try {
        await api.put('/profile/me/', {
            username: newUsername,
            avatar: selectedAvatar,
            currency: currency
        })

        // Reload fresh profile data
        await loadUserProfile()

        showSuccess('Profile updated successfully')

        // Reload header to update avatar
        await renderHeader('header-container')

        // Close modal
        forceCloseModal('editProfileModal')
    } catch (error) {
        console.error('[profile] Error updating profile:', error)
        showError(error.message || 'Failed to update profile')
    }
}

// Change password
async function changePassword(e) {
    e.preventDefault()

    const oldPassword = document.getElementById('oldPassword').value.trim()
    const newPassword = document.getElementById('newPassword').value.trim()
    const confirmPassword = document.getElementById('confirmPassword').value.trim()

    // Basic validation to reduce backend spam
    if (!oldPassword || !newPassword || !confirmPassword) {
        showError('Please fill in all fields')
        return
    }

    if (newPassword.length < 6) {
        showError('New password must be at least 6 characters')
        return
    }

    if (newPassword !== confirmPassword) {
        showError('Passwords do not match')
        return
    }

    try {
        await api.post('/profile/change-password/', {
            old_password: oldPassword,
            new_password: newPassword,
            confirm_password: confirmPassword
        })

        showSuccess('Password changed successfully')
        document.getElementById('changePasswordForm').reset()
        // Close modal with force cleanup
        forceCloseModal('securityModal')
    } catch (error) {
        console.error('[profile] Error changing password:', error)
        showError(error.message || 'Failed to change password')
    }
}

// Add category
async function addCategory(e) {
    e.preventDefault()

    const name = document.getElementById('categoryName').value.trim()
    const mccCodes = document.getElementById('mccCodes').value.trim()
    // selected icon from picker (use selectedIcon from HTML)
    const iconInput = document.getElementById('selectedIcon') || document.getElementById('addCategoryIcon')
    const iconValue = iconInput ? (iconInput.value || null) : null

    // Basic validation to reduce backend spam
    if (!name || name.length < 2) {
        showError('Category name must be at least 2 characters')
        return
    }

    try {
        await api.post('/categories/', {
            name: name,
            mcc_code: mccCodes || null,  // Backend expects mcc_code (singular)
            icon: iconValue || null
        })

        showSuccess('Category added successfully')
        document.getElementById('addCategoryForm').reset()
        // Reset icon selection to first icon
        const firstIcon = document.querySelector('.icon-picker-item')
        if (firstIcon) {
            document.querySelectorAll('.icon-picker-item').forEach(btn => btn.classList.remove('selected'))
            firstIcon.classList.add('selected')
            if (iconInput) iconInput.value = firstIcon.getAttribute('data-icon')
        }
        await loadCategories()
    } catch (error) {
        console.error('[profile] Error adding category:', error)
        showError(error.message || 'Failed to add category')
    }
}

// Edit category
window.editCategory = async function(categoryId) {
    const category = categories.find(c => c.id === categoryId)
    if (!category) return

    document.getElementById('editCategoryId').value = categoryId
    document.getElementById('editCategoryName').value = category.name
    // Backend uses mcc_code (singular)
    document.getElementById('editMccCodes').value = category.mcc_code || ''

    // Set selected icon in the static icon picker
    const editSelectedIconInput = document.getElementById('editSelectedIcon')
    const categoryIcon = category.icon || 'bi-tag-fill'

    if (editSelectedIconInput) {
        editSelectedIconInput.value = categoryIcon
    }

    // Update visual selection in icon picker
    const editIconButtons = document.querySelectorAll('.icon-picker-item-edit')
    editIconButtons.forEach(btn => {
        btn.classList.remove('selected')
        if (btn.getAttribute('data-icon') === categoryIcon) {
            btn.classList.add('selected')
        }
    })

    // If no icon is selected, select first one
    if (!document.querySelector('.icon-picker-item-edit.selected') && editIconButtons.length > 0) {
        editIconButtons[0].classList.add('selected')
        if (editSelectedIconInput) {
            editSelectedIconInput.value = editIconButtons[0].getAttribute('data-icon')
        }
    }

    const modal = new bootstrap.Modal(document.getElementById('editCategoryModal'))
    modal.show()
}

// Save edited category
async function saveEditCategory() {
    const categoryId = document.getElementById('editCategoryId').value
    const name = document.getElementById('editCategoryName').value.trim()
    const mccCodes = document.getElementById('editMccCodes').value.trim()
    const iconInput = document.getElementById('editSelectedIcon')
    const iconValue = iconInput ? (iconInput.value || null) : null

    // Basic validation to reduce backend spam
    if (!name || name.length < 2) {
        showError('Category name must be at least 2 characters')
        return
    }

    try {
        await api.put(`/categories/${categoryId}/`, {
            name: name,
            mcc_code: mccCodes || null,  // Backend expects mcc_code (singular)
            icon: iconValue || null
        })

        showSuccess('Category updated successfully')
        forceCloseModal('editCategoryModal')
        await loadCategories()
    } catch (error) {
        console.error('[profile] Error updating category:', error)
        showError(error.message || 'Failed to update category')
    }
}

// Delete category
window.deleteCategory = async function(categoryId) {
    const category = categories.find(c => c.id === categoryId)
    const categoryName = category ? category.name : 'this category'

    const confirmed = await confirmDelete(`"${categoryName}"`, true)
    if (!confirmed) return

    try {
        await api.del(`/categories/${categoryId}/`)
        showSuccess('Category deleted successfully')
        await loadCategories()
    } catch (error) {
        console.error('[profile] Error deleting category:', error)
        showError(error.message || 'Failed to delete category')
    }
}

// Save Monobank token
async function saveMonobankToken(e) {
    e.preventDefault()

    const token = document.getElementById('monobankToken').value.trim()

    // Basic validation to reduce backend spam
    if (!token || token.length < 10) {
        showError('Please enter a valid API token')
        return
    }

    try {
        // New backend endpoint: PUT /profile/monobank/
        await api.put('/profile/monobank/', {
            token: token
        })

        showSuccess('Token saved successfully')
        document.getElementById('monobankToken').value = ''
        await loadUserProfile()
        // Close modal with force cleanup
        forceCloseModal('monobankModal')
    } catch (error) {
        console.error('[profile] Error saving token:', error)
        showError(error.message || 'Failed to save token')
    }
}

// Delete Monobank token
async function deleteMonobankToken() {
    const confirmed = await showConfirmDialog({
        title: 'Disconnect Monobank',
        message: 'Are you sure you want to disconnect your Monobank account?',
        confirmText: 'Disconnect',
        cancelText: 'Cancel',
        type: 'danger',
        compact: true
    })

    if (!confirmed) return

    try {
        await api.del('/profile/monobank/')
        showSuccess('Token deleted successfully')
        await loadUserProfile()
        forceCloseModal('monobankModal')
    } catch (error) {
        console.error('[profile] Error deleting token:', error)
        showError(error.message || 'Failed to delete token')
    }
}

// Delete account
async function deleteAccount() {
    const confirmed = await showConfirmDialog({
        title: 'Delete Account',
        message: 'All your data will be permanently deleted. This cannot be undone.',
        confirmText: 'Delete Account',
        cancelText: 'Cancel',
        type: 'danger',
        compact: true
    })

    if (!confirmed) return

    try {
        await api.del('/profile/me/')
        showSuccess('Account deleted')
        await api.logout()
    } catch (error) {
        console.error('[profile] Error deleting account:', error)
        showError(error.message || 'Failed to delete account')
    }
}

// Attach event listeners
function attachEventListeners() {
    // Update profile form
    const updateForm = document.getElementById('updateProfileForm')
    if (updateForm) {
        updateForm.addEventListener('submit', updateProfile)
    }

    // Change password form
    const passwordForm = document.getElementById('changePasswordForm')
    if (passwordForm) {
        passwordForm.addEventListener('submit', changePassword)
    }

    // Auto-fill hidden username field when Security modal opens (for password managers)
    const securityModal = document.getElementById('securityModal')
    if (securityModal) {
        securityModal.addEventListener('show.bs.modal', () => {
            const hiddenUsername = document.getElementById('username-hidden')
            if (hiddenUsername && currentUser && currentUser.username) {
                hiddenUsername.value = currentUser.username
            }
        })
    }

    // Add category form
    const categoryForm = document.getElementById('addCategoryForm')
    if (categoryForm) {

        categoryForm.addEventListener('submit', addCategory)
    }

    // Save edited category
    const saveEditBtn = document.getElementById('saveEditCategory')
    if (saveEditBtn) {
        saveEditBtn.addEventListener('click', saveEditCategory)
    }

    // Monobank form
    const monobankForm = document.getElementById('monobankForm')
    if (monobankForm) {
        monobankForm.addEventListener('submit', saveMonobankToken)
    }

    const deleteTokenBtn = document.getElementById('deleteMonobankToken')
    if (deleteTokenBtn) {
        deleteTokenBtn.addEventListener('click', deleteMonobankToken)
    }

    // Delete account
    const deleteAccountBtn = document.getElementById('confirmDeleteAccount')
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', deleteAccount)
    }
}

// Global cleanup for Bootstrap modals
document.addEventListener('hidden.bs.modal', () => {
    setTimeout(() => {
        // Remove any leftover backdrops
        document.querySelectorAll('.modal-backdrop').forEach(b => b.remove())

        // Clean body if no modals are shown
        if (document.querySelectorAll('.modal.show').length === 0) {
            document.body.classList.remove('modal-open')
            document.body.style.overflow = ''
            document.body.style.paddingRight = ''
        }
    }, 100)
})


// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
} else {
    init()
}

export default {}

