import api from '../api/apiClient.js'
import { clearToken } from '../auth/auth.js'
import { renderHeader } from '../components/layout.js'
import { showError, showSuccess } from '../utils/toast.js'

let currentUser = null
let categories = []
let budgets = []
let budgetToDelete = null

// Currency symbol mapping
const currencySymbols = {
  'USD': '$',
  'EUR': '€',
  'UAH': '₴',
  'GBP': '£'
}

// Initialize page
async function initBudgetPage() {
  try {
    await renderHeader()
    await loadUserProfile()
    await loadCategories()
    await loadBudgets()
    attachEventListeners()
  } catch (error) {
    console.error('Failed to initialize budget page:', error)
    if (error.message === 'Unauthorized') {
      clearToken()
      window.location.href = '/login.html'
    } else {
      showError('Failed to load budget page')
    }
  }
}

// Load user profile
async function loadUserProfile() {
  try {
    currentUser = await api.get('/profile/me/')
    // directly set currency symbol in DOM (avoid redundant local variable)
    document.getElementById('currencySymbol').textContent = currencySymbols[currentUser.currency] || currentUser.currency
  } catch (error) {
    console.error('Failed to load user profile:', error)
    throw error
  }
}

// Load categories
async function loadCategories() {
  try {
    const raw = await api.get('/categories/all/')
    categories = Array.isArray(raw) ? raw : (raw && raw.data ? raw.data : [])

    const categorySelect = document.getElementById('budgetCategory')
    if (!categorySelect) {
      return
    }

    // Clear existing options
    categorySelect.innerHTML = ''

    // Create a placeholder option programmatically to avoid HTML parsing quirks
    const placeholder = document.createElement('option')
    placeholder.value = ''
    placeholder.disabled = true
    placeholder.selected = true
    placeholder.textContent = 'Select category...'
    categorySelect.appendChild(placeholder)

    // В моделі Category немає поля type, тому використовуємо всі категорії
    categories.forEach(category => {
      const option = document.createElement('option')
      option.value = category.id
      option.textContent = category.name
      // styling options inline is fragile; keep minimal and rely on CSS
      // option.style.background = '#1a1f28'
      // option.style.color = 'rgba(255, 255, 255, 0.9)'
      categorySelect.appendChild(option)
    })
  } catch (error) {
    console.error('Failed to load categories:', error)
    showError('Failed to load categories')
  }
}

// Load budgets
async function loadBudgets() {
  try {
    budgets = await api.get('/budgets/')

    // Update budget limit progress
    updateBudgetLimitProgress()

    // Render budgets
    renderBudgets()
  } catch (error) {
    console.error('Failed to load budgets:', error)
    showError('Failed to load budgets')
  }
}

// Update budget limit progress
function updateBudgetLimitProgress() {
  const maxBudgets = 5
  const currentCount = budgets.length
  const percentage = (currentCount / maxBudgets) * 100

  document.getElementById('budgetLimitText').textContent = `${currentCount} / ${maxBudgets} used`

  const progressBar = document.getElementById('budgetLimitBar')
  progressBar.style.width = `${percentage}%`

  // Change color based on usage
  if (percentage >= 90) {
    progressBar.style.background = '#ef4444'
  } else if (percentage >= 70) {
    progressBar.style.background = '#f59e0b'
  } else {
    progressBar.style.background = '#3aa0ff'
  }
}

// Render budgets
function renderBudgets() {
  const container = document.getElementById('budgetsContainer')

  if (budgets.length === 0) {
    container.innerHTML = `
      <div class="text-center py-5">
        <i class="bi bi-piggy-bank" style="font-size: 64px; color: rgba(255,255,255,0.2);"></i>
        <p class="mt-3" style="color: rgba(255,255,255,0.75);">No budgets yet. Create your first budget to start tracking!</p>
      </div>
    `
    return
  }

  const currencySymbol = currencySymbols[currentUser.currency] || currentUser.currency

  container.innerHTML = budgets.map(budget => {
    const spent = parseFloat(budget.total_spent || 0)
    const amount = parseFloat(budget.amount)
    const percentage = parseFloat(budget.percentage || 0)
    const remaining = parseFloat(budget.remaining || 0)

    let progressColor = '#10b981'
    if (percentage >= 100) progressColor = '#ef4444'
    else if (percentage >= 80) progressColor = '#f59e0b'
    else if (percentage >= 60) progressColor = '#3aa0ff'

    return `
      <div class="card mb-3" style="background: rgba(20, 25, 30, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px;">
        <div class="card-body p-4">
          <div class="d-flex justify-content-between align-items-start mb-3">
            <div>
              <h6 class="mb-1" style="color: #fff; font-weight: 600;">${budget.category_name}</h6>
              <span class="badge ${budget.is_recurring ? 'bg-primary' : 'bg-secondary'}" style="font-size: 11px;">
                <i class="bi ${budget.is_recurring ? 'bi-arrow-repeat' : 'bi-calendar'}"></i>
                ${budget.is_recurring ? 'Recurring' : 'One-time'}
              </span>
            </div>
            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-outline-danger" onclick="window.openDeleteModal(${budget.id})" style="border-radius: 8px;">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>

          <div class="d-flex justify-content-between align-items-center mb-2">
            <span style="color: rgba(255,255,255,0.7); font-size: 14px;">Spent</span>
            <span style="color: #fff; font-weight: 600; font-size: 16px;">${currencySymbol}${spent.toFixed(2)}</span>
          </div>

          <div class="progress mb-2" style="height: 10px; background: rgba(255,255,255,0.05); border-radius: 5px;">
            <div class="progress-bar" role="progressbar" style="width: ${Math.min(percentage, 100)}%; background: ${progressColor}; transition: width 0.3s ease;"></div>
          </div>

          <div class="d-flex justify-content-between align-items-center">
            <span style="color: rgba(255,255,255,0.75); font-size: 13px;">${percentage.toFixed(1)}% used</span>
            <span style="color: ${remaining >= 0 ? '#10b981' : '#ef4444'}; font-weight: 600; font-size: 14px;">
              ${remaining >= 0 ? currencySymbol + remaining.toFixed(2) + ' left' : 'Over budget!'}
            </span>
          </div>

          <div class="mt-2 pt-2" style="border-top: 1px solid rgba(255,255,255,0.05);">
            <small style="color: rgba(255,255,255,0.75);">Budget: ${currencySymbol}${amount.toFixed(2)}</small>
            ${budget.deadline_info ? `<small class="ms-2" style="color: rgba(255,255,255,0.65);">• ${budget.deadline_info}</small>` : ''}
          </div>
        </div>
      </div>
    `
  }).join('')
}

// Attach event listeners
function attachEventListeners() {
  document.getElementById('budgetForm').addEventListener('submit', handleBudgetSubmit)
  document.getElementById('confirmDeleteBtn').addEventListener('click', handleDeleteBudget)
}

// Reset form
function resetForm() {
  document.getElementById('budgetForm').reset()
  document.getElementById('budgetId').value = ''
}

// Handle budget form submit
async function handleBudgetSubmit(e) {
  e.preventDefault()

  const budgetId = document.getElementById('budgetId').value
  const categoryId = parseInt(document.getElementById('budgetCategory').value)
  const amount = parseFloat(document.getElementById('budgetAmount').value)
  const isRecurring = document.getElementById('isRecurring').checked

  if (!categoryId || !amount || amount <= 0) {
    showError('Please fill all required fields')
    return
  }

  try {
    const data = {
      category_id: categoryId,
      amount: amount,
      is_recurring: isRecurring
    }

    // Use POST for both create and update per request (include id for update)
    if (budgetId) {
      data.id = parseInt(budgetId)
    }
    await api.post('/budgets/', data)
    showSuccess(budgetId ? 'Budget updated successfully!' : 'Budget created successfully!')

    resetForm()
    await loadBudgets()
  } catch (error) {
    console.error('Failed to save budget:', error)
    showError(error.message || 'Failed to save budget')
  }
}

// Open delete modal
function openDeleteModal(budgetId) {
  budgetToDelete = budgetId
  const modal = new bootstrap.Modal(document.getElementById('deleteBudgetModal'))
  modal.show()
}

// Handle delete budget
async function handleDeleteBudget() {
  if (!budgetToDelete) return

  try {
    await api.del(`/budgets/${budgetToDelete}/`)
    showSuccess('Budget deleted successfully!')

    const modal = bootstrap.Modal.getInstance(document.getElementById('deleteBudgetModal'))
    modal.hide()

    budgetToDelete = null
    await loadBudgets()
  } catch (error) {
    console.error('Failed to delete budget:', error)
    showError('Failed to delete budget')
  }
}

// Dropdown is now handled by layout.js with Bootstrap - no manual initialization needed

// Export functions to window for onclick handlers
window.openDeleteModal = openDeleteModal

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initBudgetPage()
  })
} else {
  initBudgetPage()
}
