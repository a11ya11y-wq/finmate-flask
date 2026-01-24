import * as api from '../api/apiClient.js'
import { getToken } from '../auth/auth.js'
import { renderHeader } from '../components/layout.js'
import { showSuccess, showError } from '../utils/toast.js'
import { getProfile, clearProfileCache } from '../utils/profileCache.js'

// State
let currentUser = null
let selectedAvatar = null
let categories = []
const MAX_CATEGORIES = 50

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

// Load user profile
async function loadUserProfile() {
    try {
        const data = await getProfile()
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
        // Обробка різних форматів шляху
        if (avatarPath.includes('static/')) {
            avatarPath = avatarPath.replace('static/', '')
        }
        document.getElementById('userAvatar').src = `/${avatarPath}`
        selectedAvatar = avatarPath

        // Update Monobank status (badge + text)
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
        // Backend now returns { data: [...] } or legacy array
        categories = Array.isArray(raw) ? raw : (raw && raw.data ? raw.data : [])
        renderCategories()
    } catch (error) {
        console.error('[profile] Error loading categories:', error)
        showError('Failed to load categories')
    }
}

// Category icons mapping
const CATEGORY_ICONS = {
    'food': 'basket',
    'transport': 'bus-front',
    'shopping': 'bag-heart',
    'utilities': 'lightning-charge',
    'entertainment': 'film',
    'health': 'heart-pulse',
    'uncategorized': 'question-circle',
    'default': 'tag'
}

// Get icon for category
function getCategoryIcon(categoryName) {
    const name = categoryName.toLowerCase()
    for (const [key, icon] of Object.entries(CATEGORY_ICONS)) {
        if (name.includes(key)) {
            return { icon, class: key }
        }
    }
    return { icon: CATEGORY_ICONS.default, class: 'default' }
}

// Simple HTML escaper used by templates
function escapeHtml(s){
    if(s === null || s === undefined) return ''
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')
}

// Render Categories List on Main Page
function renderCategories() {
    // Render Categories List directly on page (not in modal anymore)
    const container = document.getElementById('categoriesList')
    if (container) {
        if (!categories || categories.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 40px 20px;">No categories yet. Add your first category above!</p>'
        } else {
            container.innerHTML = categories.map(cat => {
                // Prefer icon from backend (may be 'bi-bag' etc.). If absent, fall back to name-based mapping.
                const rawIcon = cat.icon ? String(cat.icon).trim() : null
                const { icon: fallbackIcon } = getCategoryIcon(cat.name)
                const iconClass = rawIcon ? rawIcon : `bi-${fallbackIcon}`

                // Backend uses mcc_code (singular)
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
                            <div class="category-name-modal">${cat.name}</div>
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
    }
}

// Note: updateCategoryProgress removed - replaced by individual progress bars in Spending Breakdown

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

    // Basic validation to reduce backend spam
    if (!newUsername || newUsername.length < 3) {
        showError('Username must be at least 3 characters')
        return
    }

    try {
        // Update profile (username + avatar + currency) in single request
        await api.put('/profile/me/', {
            username: newUsername,
            avatar: selectedAvatar,
            currency: currency
        })

        // Очищаємо кеш профілю та завантажуємо свіжі дані
        clearProfileCache()
        await loadUserProfile() // Це оновить кеш новими даними

        showSuccess('Profile updated successfully')

        // Reload header to update avatar (візьме дані з вже оновленого кешу)
        await renderHeader('header-container')
        // Close modal with force cleanup
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

// Show custom confirmation dialog (replaces browser confirm())
function showConfirmDialog(title, message, confirmText = 'Confirm', type = 'danger') {
    return new Promise((resolve) => {
        // Create custom overlay (instead of Bootstrap backdrop)
        const customOverlay = document.createElement('div')
        customOverlay.id = 'customConfirmOverlay'
        customOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1050;
            opacity: 0;
            transition: opacity 0.15s ease;
        `

        // Create modal HTML (z-index ВИЩИЙ за overlay - модалка світла!)
        const modalHTML = `
            <div class="modal" id="confirmDialog" tabindex="-1" style="display: block; z-index: 9999 !important; position: fixed;">
                <div class="modal-dialog modal-dialog-centered modal-sm" style="position: relative; z-index: 10000 !important;">
                    <div class="modal-content">
                        <div class="modal-header ${type === 'danger' ? 'border-danger' : ''}">
                            <h5 class="modal-title ${type === 'danger' ? 'text-danger' : ''}">
                                <i class="bi bi-${type === 'danger' ? 'exclamation-triangle' : 'question-circle'}"></i>
                                ${title}
                            </h5>
                            <button type="button" class="btn-close" id="confirmDialogClose" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p style="color: var(--text-primary); margin: 0; font-size: 0.95rem; line-height: 1.6;">
                                ${message}
                            </p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" id="confirmDialogCancel">Cancel</button>
                            <button type="button" class="btn btn-${type}" id="confirmDialogBtn">
                                <i class="bi bi-check-lg"></i> ${confirmText}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `

        // Remove existing dialog if any
        const existing = document.getElementById('confirmDialog')
        if (existing) existing.remove()
        const existingOverlay = document.getElementById('customConfirmOverlay')
        if (existingOverlay) existingOverlay.remove()

        // Append overlay and modal to body
        document.body.appendChild(customOverlay)
        document.body.insertAdjacentHTML('beforeend', modalHTML)

        const modalEl = document.getElementById('confirmDialog')

        // Force ЕКСТРЕМАЛЬНО високий z-index через JavaScript
        // Overlay ЗА модалкою - не затемнює її!
        customOverlay.style.zIndex = '1050'
        modalEl.style.zIndex = '9999'
        const dialogEl = modalEl.querySelector('.modal-dialog')
        if (dialogEl) dialogEl.style.zIndex = '10000'

        // Animate in
        setTimeout(() => {
            customOverlay.style.opacity = '1'
            modalEl.classList.add('show')
            // Force z-index ЗНОВУ після анімації
            modalEl.style.zIndex = '9999'
            if (dialogEl) dialogEl.style.zIndex = '10000'
        }, 10)

        // Close function
        const closeDialog = (result) => {
            customOverlay.style.opacity = '0'
            modalEl.classList.remove('show')

            setTimeout(() => {
                customOverlay.remove()
                modalEl.remove()
                resolve(result)
            }, 150)
        }

        // Handle confirm
        document.getElementById('confirmDialogBtn').addEventListener('click', () => {
            closeDialog(true)
        })

        // Handle cancel
        document.getElementById('confirmDialogCancel').addEventListener('click', () => {
            closeDialog(false)
        })

        // Handle X button
        document.getElementById('confirmDialogClose').addEventListener('click', () => {
            closeDialog(false)
        })

        // Handle overlay click (close on background click)
        customOverlay.addEventListener('click', () => {
            closeDialog(false)
        })

        // Prevent clicks inside modal from closing overlay
        modalEl.addEventListener('click', (e) => {
            e.stopPropagation()
        })
    })
}

// Delete category
window.deleteCategory = async function(categoryId) {
    // Create custom confirmation modal instead of browser alert
    const category = categories.find(c => c.id === categoryId)
    const categoryName = category ? category.name : 'this category'

    const confirmed = await showConfirmDialog(
        'Delete Category',
        `Are you sure you want to delete "${categoryName}"? This action cannot be undone.`,
        'Delete',
        'danger'
    )

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
    const confirmed = await showConfirmDialog(
        'Delete Monobank Token',
        'Are you sure you want to disconnect your Monobank account? You will need to re-enter your API token to reconnect.',
        'Delete Token',
        'danger'
    )

    if (!confirmed) return

    try {
        // New backend endpoint: DELETE /profile/monobank/
        await api.del('/profile/monobank/')

        showSuccess('Token deleted successfully')
        await loadUserProfile()
        // Close modal with force cleanup
        forceCloseModal('monobankModal')
    } catch (error) {
        console.error('[profile] Error deleting token:', error)
        showError(error.message || 'Failed to delete token')
    }
}

// Delete account
async function deleteAccount() {
    // Use custom confirmation dialog instead of modal with text input
    const confirmed = await showConfirmDialog(
        'Delete Account',
        'Warning! This action is irreversible. All your data will be permanently deleted. Are you sure you want to delete your account?',
        'Delete My Account',
        'danger'
    )

    if (!confirmed) return

    try {
        await api.del('/profile/me/')
        showSuccess('Account deleted')

        // Use the proper logout function from API client
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

// Global cleanup for all modals
document.addEventListener('hidden.bs.modal', (e) => {
    // Small delay to ensure Bootstrap cleanup is done
    setTimeout(() => {
        // Remove any leftover backdrops
        const backdrops = document.querySelectorAll('.modal-backdrop')
        if (backdrops.length > 0) {
            backdrops.forEach(b => b.remove())
        }

        // Clean body if no modals are shown
        const openModals = document.querySelectorAll('.modal.show')
        if (openModals.length === 0) {
            document.body.classList.remove('modal-open')
            document.body.style.overflow = ''
            document.body.style.paddingRight = ''
        }
    }, 100)
})

// Additional: АГРЕСИВНИЙ FIX для backdrop - постійний моніторинг
document.addEventListener('show.bs.modal', (e) => {
    const modal = e.target

    // Функція для виправлення z-index
    const fixZIndex = () => {
        if (modal) {
            modal.style.setProperty('z-index', '10060', 'important')

            const modalDialog = modal.querySelector('.modal-dialog')
            if (modalDialog) {
                modalDialog.style.setProperty('z-index', '10061', 'important')
            }

            const modalContent = modal.querySelector('.modal-content')
            if (modalContent) {
                modalContent.style.setProperty('z-index', '10062', 'important')
                modalContent.style.setProperty('pointer-events', 'auto', 'important')
            }
        }

        // Fix ALL backdrops
        const backdrops = document.querySelectorAll('.modal-backdrop')
        backdrops.forEach((backdrop, index) => {
            if (index === backdrops.length - 1) {
                // Last backdrop - keep it but fix z-index
                backdrop.style.setProperty('z-index', '10050', 'important')
            } else {
                // Remove old backdrops
                backdrop.remove()
            }
        })
    }

    // Fix immediately
    fixZIndex()

    // Fix repeatedly during animation (Bootstrap can override)
    const intervals = [10, 50, 100, 150, 200, 300, 500]
    intervals.forEach(delay => {
        setTimeout(fixZIndex, delay)
    })
})

// Additional: Force fix z-index after modal is shown (after animation completes)
document.addEventListener('shown.bs.modal', (e) => {
    const modal = e.target

    const fixZIndex = () => {
        if (modal) {
            modal.style.setProperty('z-index', '10060', 'important')

            const modalDialog = modal.querySelector('.modal-dialog')
            if (modalDialog) {
                modalDialog.style.setProperty('z-index', '10061', 'important')
            }

            const modalContent = modal.querySelector('.modal-content')
            if (modalContent) {
                modalContent.style.setProperty('z-index', '10062', 'important')
                modalContent.style.setProperty('pointer-events', 'auto', 'important')
            }
        }

        const backdrops = document.querySelectorAll('.modal-backdrop')
        backdrops.forEach(backdrop => {
            backdrop.style.setProperty('z-index', '10050', 'important')
        })
    }

    // Fix multiple times after modal is shown
    fixZIndex()
    setTimeout(fixZIndex, 50)
    setTimeout(fixZIndex, 100)
    setTimeout(fixZIndex, 200)
})

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
} else {
    init()
}

export default {}

