import api from '../api/apiClient.js'
import { clearToken } from '../auth/auth.js'
import { renderHeader } from '../components/layout.js'
import Chart from 'chart.js/auto'
import { openModal, closeModal, closeAllModals } from '../utils/simpleModal.js'
import { showSuccess, showError, showWarning } from '../utils/toast.js'

// New: mapping of category display names to badge styles (gradient background + icon color)
const CATEGORY_STYLES = {
  'Food': { bg: 'linear-gradient(135deg, #f59e0b, #d97706)', iconColor: '#fff' },
  'Transport': { bg: 'linear-gradient(135deg, #3b82f6, #2563eb)', iconColor: '#fff' },
  'Shopping': { bg: 'linear-gradient(135deg, #ec4899, #db2777)', iconColor: '#fff' },
  'Entertainment': { bg: 'linear-gradient(135deg, #8b5cf6, #7c3aed)', iconColor: '#fff' },
  'Health': { bg: 'linear-gradient(135deg, #ef4444, #dc2626)', iconColor: '#fff' },
  'Utilities': { bg: 'linear-gradient(135deg, #eab308, #ca8a04)', iconColor: '#fff' },
  'Salary': { bg: 'linear-gradient(135deg, #10b981, #059669)', iconColor: '#fff' },
  'Uncategorized': { bg: 'linear-gradient(135deg, #64748b, #475569)', iconColor: '#fff' }
}

function getCategoryStyle(name){
  if(!name) return CATEGORY_STYLES['Uncategorized']
  // Try exact match first, then case-insensitive
  if(CATEGORY_STYLES[name]) return CATEGORY_STYLES[name]
  const foundKey = Object.keys(CATEGORY_STYLES).find(k => String(name).toLowerCase() === String(k).toLowerCase())
  if(foundKey) return CATEGORY_STYLES[foundKey]
  return CATEGORY_STYLES['Uncategorized']
}

// Module-level state to avoid duplicate handlers and reuse/destroy Chart instances
let balanceChart = null
let categoryChart = null
let handlersAttached = false
let modalOpening = false
let loadInProgress = false
let pendingLoadPeriod = null
let lastClickedButton = null
let modalOpeningTimer = null
let currentPeriod = 'all' // ✅ Зберігаємо поточний вибраний період
let chartsRendering = false // ✅ Запобігаємо одночасному рендерингу діаграм
let lastChartRenderTime = 0 // ✅ Таймстамп останнього успішного рендерингу графіків
let userCurrency = 'USD' // ✅ Валюта користувача з профілю (default з моделі Users)

let modalSafetyAttached = false
// queue for modal open requests to avoid concurrent opens
let pendingModalQueue = []
// guard set to prevent duplicate opens for same txId
let openingTxIds = new Set()
// prevent duplicate delete requests: ids currently being deleted
let pendingDeletes = new Set()
// short-lived map of recently handled txIds to avoid duplicate handlers (id => timestamp)
let recentHandled = new Map()
const RECENT_TTL = 1200 // ms

// ✅ Scroll position preservation
let savedScrollPosition = 0

// ✅ Utility: Error logging helper
function logError(context, error){
  try{
    console.error(`[dashboard] ${context}:`, error)
  }catch(_){}
}

// ✅ Confirmation dialog for delete action
async function confirmDelete(){
  return new Promise((resolve) => {
    const modalHTML = `
      <div class="modal-overlay" id="deleteConfirmModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 9999; display: flex; align-items: center; justify-content: center;">
        <div class="modal-content modal-delete-transaction" style="background: #1a1d23; border-radius: 12px; padding: 24px; max-width: 400px; width: 90%; box-shadow: 0 8px 32px rgba(0,0,0,0.4);">
          <h5 style="color: #fff; margin-bottom: 16px; font-size: 18px; font-weight: 600;">
            <i class="bi bi-exclamation-triangle-fill" style="color: #ff6b6b; margin-right: 8px;"></i>
            Delete Transaction?
          </h5>
          <p style="color: #9aa1a6; margin-bottom: 24px; font-size: 14px;">
            This action cannot be undone. Are you sure you want to delete this transaction?
          </p>
          <div style="display: flex; gap: 12px; justify-content: flex-end;">
            <button id="cancelDeleteBtn" class="btn btn-secondary" style="padding: 8px 20px; font-size: 14px;">
              Cancel
            </button>
            <button id="confirmDeleteBtn" class="btn btn-danger" style="padding: 8px 20px; font-size: 14px;">
              <i class="bi bi-trash"></i> Delete
            </button>
          </div>
        </div>
      </div>
    `

    const modalDiv = document.createElement('div')
    modalDiv.innerHTML = modalHTML
    const modal = modalDiv.firstElementChild
    document.body.appendChild(modal)

    const cleanup = () => {
      try{ modal.remove() }catch(_){}
    }

    document.getElementById('confirmDeleteBtn')?.addEventListener('click', () => {
      cleanup()
      resolve(true)
    })

    document.getElementById('cancelDeleteBtn')?.addEventListener('click', () => {
      cleanup()
      resolve(false)
    })

    // Close on overlay click
    modal.addEventListener('click', (e) => {
      if(e.target === modal){
        cleanup()
        resolve(false)
      }
    })

    // Close on Escape key
    const escHandler = (e) => {
      if(e.key === 'Escape'){
        cleanup()
        document.removeEventListener('keydown', escHandler)
        resolve(false)
      }
    }
    document.addEventListener('keydown', escHandler)
  })
}

function saveScrollPosition(){
  try{
    savedScrollPosition = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0
    // Store in data attribute as backup
    document.body.setAttribute('data-scroll-y', savedScrollPosition)
  }catch(e){
    savedScrollPosition = 0
    try{ document.body.setAttribute('data-scroll-y', '0') }catch(_){}
  }
}

function restoreScrollPosition(){
  try{
    // Clean up any modal-related styles on body
    document.body.style.position = ''
    document.body.style.top = ''
    document.body.style.width = ''
    document.body.style.overflow = ''
    document.body.style.paddingRight = ''

    // Get saved position from variable or data attribute
    let scrollY = savedScrollPosition
    if(scrollY === 0){
      try{
        const stored = document.body.getAttribute('data-scroll-y')
        if(stored) scrollY = parseInt(stored) || 0
      }catch(_){}
    }

    // Restore scroll with slight delay to ensure DOM is ready
    requestAnimationFrame(()=>{
      try{
        window.scrollTo({
          top: scrollY,
          left: 0,
          behavior: 'instant'
        })
      }catch(_){
        // Fallback for older browsers
        window.scrollTo(0, scrollY)
      }
    })
  }catch(e){ /* ignore */ }
}

function isRecentlyHandled(id){
  try{
    if(!id) return false
    const t = recentHandled.get(id)
    if(!t) return false
    if((Date.now() - t) < RECENT_TTL) return true
    recentHandled.delete(id)
    return false
  }catch(e){ return false }
}
function markHandled(id){ try{ recentHandled.set(id, Date.now()); setTimeout(()=> recentHandled.delete(id), RECENT_TTL+50) }catch(e){} }


// ✅ Old showModalManual removed - using openModal from simpleModal.js instead
function renderSkeleton(){
  document.getElementById('app').innerHTML = `
  <!-- ✅ Universal Header -->
  <header class="app-header">
    <div class="container d-flex align-items-center justify-content-between">
      <a href="/dashboard.html" class="logo-link">
        <img src="/img/finmatelogo1.png" alt="FinMate" width="100" class="logo">
      </a>
      
      <div id="header-user-section">
        <!-- This will be populated by JavaScript -->
      </div>
    </div>
  </header>

  <!-- Animated Background Particles -->
  <div class="dashboard-bg-particles">
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
  </div>

  <!-- Modern Dashboard Header (FULL WIDTH STICKY) -->
  <div class="dashboard-header mb-4">
    <div class="dashboard-header-content">
      <div class="d-flex justify-content-between flex-wrap align-items-center">
        <h1 class="dashboard-title">
          <i class="bi bi-speedometer2 me-2"></i>Dashboard
        </h1>
        <div class="action-buttons">
          <div class="period-selector">
            <button class="period-btn" data-period="week">Week</button>
            <button class="period-btn" data-period="month">Month</button>
            <button class="period-btn active" data-period="all">All Time</button>
          </div>
          <button type="button" class="btn-modern btn-success-modern" id="add-transaction-button">
            <i class="bi bi-plus-lg"></i>
            <span>Add</span>
          </button>
          <button type="button" class="btn-modern btn-primary-modern" id="sync-button">
            <i class="bi bi-arrow-repeat"></i>
            <span>Sync</span>
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="container" style="position: relative; z-index: 1;">
    <!-- Hidden select for backward compatibility -->
    <select id="time-period-select" class="d-none">
      <option value="all" selected>All time</option>
      <option value="week">Last 7 days</option>
      <option value="month">Last 30 days</option>
    </select>

    <!-- Stats Cards Grid -->
    <div class="stats-grid">
      <div class="stat-card income-card">
        <div class="stat-card-icon" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1));">
          <i class="bi bi-arrow-down-circle-fill" style="color: #10b981;"></i>
        </div>
        <div class="stat-card-label">Total Income</div>
        <h3 class="stat-card-value" id="total-income">₴0.00</h3>
        <div class="stat-card-trend positive">
          <i class="bi bi-arrow-up"></i> <span>0%</span>
        </div>
      </div>

      <div class="stat-card expense-card">
        <div class="stat-card-icon" style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(239, 68, 68, 0.1));">
          <i class="bi bi-arrow-up-circle-fill" style="color: #ef4444;"></i>
        </div>
        <div class="stat-card-label">Total Expense</div>
        <h3 class="stat-card-value" id="total-expense">₴0.00</h3>
        <div class="stat-card-trend negative">
          <i class="bi bi-arrow-down"></i> <span>0%</span>
        </div>
      </div>

      <div class="stat-card balance-card">
        <div class="stat-card-icon" style="background: linear-gradient(135deg, rgba(58, 160, 255, 0.2), rgba(58, 160, 255, 0.1));">
          <i class="bi bi-wallet2" style="color: #3aa0ff;"></i>
        </div>
        <div class="stat-card-label">Current Balance</div>
        <h3 class="stat-card-value" id="current-balance">₴0.00</h3>
        <div class="stat-card-trend positive">
          <i class="bi bi-graph-up"></i> <span>Healthy</span>
        </div>
      </div>
    </div>

    <!-- Charts Grid -->
    <div class="charts-grid">
      <!-- Expenses by Category (LEFT - NARROW) -->
      <div class="chart-container">
        <div class="chart-header">
          <h3 class="chart-title">
            <i class="bi bi-pie-chart-fill me-2" style="color: #3aa0ff;"></i>
            Expenses by Category
          </h3>
        </div>
        <div class="donut-wrap" style="position: relative;">
          <canvas id="categoryDonutChart" width="280" height="280"></canvas>
          <div id="categoryChartEmpty" class="chart-empty-state" style="display: none;">
            <div class="empty-state-icon">
              <i class="bi bi-pie-chart"></i>
            </div>
            <div class="empty-state-text">No data to display</div>
            <div class="empty-state-subtext">Add transactions or show categories in the legend</div>
          </div>
        </div>
        <div id="categoryLegend" class="legend-ribbon"></div>
      </div>

      <!-- Balance Dynamics (RIGHT - WIDE) -->
      <div class="chart-container">
        <div class="chart-header">
          <h3 class="chart-title">
            <i class="bi bi-graph-up-arrow me-2" style="color: #10b981;"></i>
            Balance Dynamics
          </h3>
        </div>
        <div style="position: relative; height: 400px; max-height: 400px;">
          <canvas id="balanceLineChart"></canvas>
          <div id="balanceChartEmpty" class="chart-empty-state" style="display: none;">
            <div class="empty-state-icon">
              <i class="bi bi-graph-up"></i>
            </div>
            <div class="empty-state-text">No balance data</div>
            <div class="empty-state-subtext">Track your financial journey over time</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Transactions Section -->
    <div class="transactions-container">
      <div class="table-responsive">
        <table class="table-modern transactions-table">
          <colgroup>
            <col style="width:48px">
            <col style="width:37%">
            <col style="width:15%">
            <col style="width:160px">
            <col style="width:140px">
            <col style="width:140px">
          </colgroup>
          <thead>
            <tr>
              <th class="td-num">#</th>
              <th class="td-desc">Description</th>
              <th class="td-cat">Category</th>
              <th class="td-amount" style="text-align:right">Amount</th>
              <th class="td-date">Date</th>
              <th class="td-actions">Actions</th>
            </tr>
          </thead>
          <tbody id="transactions-list">
            <tr>
              <td colspan="6">
                <div class="empty-state">
                  <div class="empty-state-icon">
                    <i class="bi bi-inbox"></i>
                  </div>
                  <div class="empty-state-text">No transactions yet</div>
                  <div class="empty-state-subtext">Start tracking your finances by adding your first transaction</div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <footer class="d-flex flex-wrap justify-content-between align-items-center py-3 my-4 border-top">
      <span class="mb-3 mb-md-0 text-body-secondary">© 2025 FinMate, Inc</span>
    </footer>

    <!-- hidden legacy select used for some flows -->
    <select id="tx_category" hidden></select>
    <div id="status_message" hidden></div>

    <!-- Modals removed from here - will be appended to body separately -->

  </div>
  `
}

// ✅ NEW: Append modals as direct children of body (not inside #app)
// This prevents z-index and position conflicts with parent containers
function appendModalsToBody() {
  // Remove existing modals if any
  const existingEditModal = document.getElementById('editTransactionModal')
  const existingAddModal = document.getElementById('addTransactionModal')
  if (existingEditModal) existingEditModal.remove()
  if (existingAddModal) existingAddModal.remove()

  const modalsHTML = `
    <!-- Edit Transaction Modal -->
    <div class="modal fade" id="editTransactionModal" tabindex="-1" aria-labelledby="editModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content modal-edit-transaction">
          <form id="transactionForm" novalidate>
            <input type="hidden" id="edit_tx_id" name="tx_id" value="">

            <div class="modal-header">
              <h5 class="modal-title" id="editModalLabel">Edit Transaction</h5>
              <button type="button" class="btn-close" id="editModalCloseBtn" aria-label="Close"></button>
            </div>

            <div class="modal-body">
              <div class="mb-3">
                <label for="edit_title" class="form-label">Title</label>
                <input type="text" class="form-control" id="edit_title" name="title" required>
              </div>
              <div class="mb-3">
                <label class="form-label">Type</label>
                <div class="form-check">
                  <input class="form-check-input" type="radio" name="type" id="edit_expense" value="expense">
                  <label class="form-check-label" for="edit_expense">Expense</label>
                </div>
                <div class="form-check">
                  <input class="form-check-input" type="radio" name="type" id="edit_income" value="income">
                  <label class="form-check-label" for="edit_income">Income</label>
                </div>
              </div>
              <div class="mb-3">
                <label for="edit_amount" class="form-label">Amount</label>
                <input type="number" step="0.01" class="form-control" id="edit_amount" name="amount" required>
              </div>
              <div class="mb-3">
                <label for="edit_category" class="form-label">Category</label>
                <select class="form-select" id="edit_category" name="category_id" required>
                  <option disabled value="">Loading categories...</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="edit_date" class="form-label">Date</label>
                <input type="date" class="form-control" id="edit_date" name="created_at">
              </div>
              <div class="mb-3">
                <label for="edit_note" class="form-label">Note (optional)</label>
                <textarea class="form-control" id="edit_note" name="note" rows="2"></textarea>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" id="editModalCloseFooterBtn">Close</button>
              <button type="submit" class="btn-modern btn-primary-modern">Save Changes</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Add Transaction Modal -->
    <div class="modal fade" id="addTransactionModal" tabindex="-1" aria-labelledby="addModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content modal-add-transaction">
          <form id="addTransactionForm" novalidate>
            <div class="modal-header">
              <h5 class="modal-title" id="addModalLabel">Add New Transaction</h5>
              <button type="button" class="btn-close" id="addModalCloseBtn" aria-label="Close"></button>
            </div>

            <div class="modal-body">
              <div class="mb-3">
                <label for="add_title" class="form-label">Title</label>
                <input type="text" class="form-control" id="add_title" name="title" required>
              </div>
              <div class="mb-3">
                <label class="form-label">Type</label>
                <div class="form-check">
                  <input class="form-check-input" type="radio" name="add_type" id="add_expense" value="expense" checked>
                  <label class="form-check-label" for="add_expense">Expense</label>
                </div>
                <div class="form-check">
                  <input class="form-check-input" type="radio" name="add_type" id="add_income" value="income">
                  <label class="form-check-label" for="add_income">Income</label>
                </div>
              </div>
              <div class="mb-3">
                <label for="add_amount" class="form-label">Amount</label>
                <input type="number" step="0.01" class="form-control" id="add_amount" name="amount" required>
              </div>
              <div class="mb-3">
                <label for="add_category" class="form-label">Category</label>
                <select class="form-select" id="add_category" name="category_id" required>
                  <option disabled selected value="">Select category...</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="add_date" class="form-label">Date</label>
                <input type="date" class="form-control" id="add_date" name="created_at">
              </div>
              <div class="mb-3">
                <label for="add_note" class="form-label">Note (optional)</label>
                <textarea class="form-control" id="add_note" name="note" rows="2"></textarea>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" id="addModalCloseFooterBtn">Close</button>
              <button type="submit" class="btn-modern btn-success-modern">Add Transaction</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `

  // Create a temporary container to parse HTML
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = modalsHTML.trim()

  // Append each modal directly to body
  while (tempDiv.firstChild) {
    document.body.appendChild(tempDiv.firstChild)
  }


  // ✅ Attach close handlers to all modal close buttons
  setTimeout(() => {
    // Edit Transaction Modal close handlers
    const editCloseBtn = document.getElementById('editModalCloseBtn')
    const editCloseFooterBtn = document.getElementById('editModalCloseFooterBtn')
    if (editCloseBtn) {
      editCloseBtn.addEventListener('click', () => closeModal('editTransactionModal'))
    }
    if (editCloseFooterBtn) {
      editCloseFooterBtn.addEventListener('click', () => closeModal('editTransactionModal'))
    }

    // Add Transaction Modal close handlers
    const addCloseBtn = document.getElementById('addModalCloseBtn')
    const addCloseFooterBtn = document.getElementById('addModalCloseFooterBtn')
    if (addCloseBtn) {
      addCloseBtn.addEventListener('click', () => closeModal('addTransactionModal'))
    }
    if (addCloseFooterBtn) {
      addCloseFooterBtn.addEventListener('click', () => closeModal('addTransactionModal'))
    }
  }, 100)
}

// ✅ Helper function to fetch and populate categories
async function fetchCategories(selectId){
  try{
    const raw = await api.get('/categories/all/')
    const cats = Array.isArray(raw) ? raw : (raw && raw.data ? raw.data : [])

    const catSelect = selectId ? document.getElementById(selectId) : null
    if(catSelect){
      catSelect.innerHTML = '<option disabled selected value="">Select category...</option>' +
        cats.map(c=>`<option value="${c.id}">${c.name}</option>`).join('')
    }

    return cats
  }catch(e){
    console.error('[fetchCategories] Failed to load categories:', e)
    return []
  }
}

// helper: small currency symbol mapper (mirrors legacy)
function getCurrencySymbol(code){
  switch((code||'').toUpperCase()){
    case 'USD': return '$';
    case 'EUR': return '€';
    default: return '₴'
  }
}

// helper: get category icon based on name
function getCategoryIcon(categoryName) {
  const name = (categoryName || '').toLowerCase()
  if (name.includes('food') || name.includes('restaurant')) return 'bi-cup-hot-fill'
  if (name.includes('transport') || name.includes('car')) return 'bi-car-front-fill'
  if (name.includes('shop') || name.includes('clothing')) return 'bi-bag-fill'
  if (name.includes('health') || name.includes('medical')) return 'bi-heart-pulse-fill'
  if (name.includes('entertainment') || name.includes('fun')) return 'bi-controller'
  if (name.includes('utilities') || name.includes('bills')) return 'bi-lightning-charge-fill'
  if (name.includes('salary') || name.includes('income')) return 'bi-cash-coin'
  if (name.includes('gift')) return 'bi-gift-fill'
  return 'bi-tag-fill'
}

// helper: get category color based on name
function getCategoryColor(categoryName) {
  const name = (categoryName || '').toLowerCase()
  if (name.includes('food')) return 'linear-gradient(135deg, #f59e0b, #d97706)'
  if (name.includes('transport')) return 'linear-gradient(135deg, #3b82f6, #2563eb)'
  if (name.includes('shop') || name.includes('clothing')) return 'linear-gradient(135deg, #ec4899, #db2777)'
  if (name.includes('health')) return 'linear-gradient(135deg, #10b981, #059669)'
  if (name.includes('entertainment')) return 'linear-gradient(135deg, #3aa0ff, #2d7fcc)'
  if (name.includes('utilities')) return 'linear-gradient(135deg, #eab308, #ca8a04)'
  if (name.includes('salary') || name.includes('income')) return 'linear-gradient(135deg, #10b981, #059669)'
  return 'linear-gradient(135deg, rgba(58, 160, 255, 0.3), rgba(58, 160, 255, 0.2))'
}

async function loadData(period = 'all'){
  // Serialize concurrent calls
  if(loadInProgress){
    pendingLoadPeriod = period
    return
  }
  loadInProgress = true

  // Використовуємо валюту користувача з профілю
  const currencySymbol = getCurrencySymbol(userCurrency)

  try{
   const data = await api.get(`/dashboard?period=${period}`)

    // 1. Безпечно дістаємо об'єкт stats
    const stats = data.stats || {}

    // 2. Дістаємо цифри (нові назви полів з Python). Якщо null -> ставимо 0.
    const incomeVal = stats.current_income || 0
    const expenseVal = stats.current_expense || 0
    const balanceVal = stats.current_balance || 0

    // 3. Дістаємо відсотки
    const incomePct = stats.income_percentage_change || 0
    const expensePct = stats.expense_percentage_change || 0

    // 4. Оновлюємо картку Income (Дохід)
    const incomeEl = document.getElementById('total-income')
    if(incomeEl) {
        incomeEl.textContent = `${currencySymbol}${incomeVal.toFixed(2)}`
        // Робимо текст зеленим
        incomeEl.classList.remove('text-muted', 'text-success')
        incomeEl.classList.add('text-success')
    }

    // 5. Оновлюємо картку Expense (Витрати)
    const expenseEl = document.getElementById('total-expense')
    if(expenseEl) {
        expenseEl.textContent = `${currencySymbol}${expenseVal.toFixed(2)}`
        // Робимо текст червоним
        expenseEl.classList.remove('text-muted', 'text-danger')
        expenseEl.classList.add('text-danger')
    }

    // 6. Оновлюємо картку Balance (Баланс)
    const cbEl = document.getElementById('current-balance')
    if(cbEl) {
        cbEl.textContent = `${currencySymbol}${balanceVal.toFixed(2)}`
        // Логіка кольору балансу (червоний якщо мінус)
        cbEl.classList.remove('text-danger', 'text-success', 'text-primary')
        if (balanceVal < 0) cbEl.classList.add('text-danger')
        else cbEl.classList.add('text-primary')
    }

    // 7. Оновлюємо бейджі з відсотками (Стрілочки)

    const updateTrend = (selector, value, isExpense) => {
        const container = document.querySelector(selector);
        if (!container) return;

        const textSpan = container.querySelector('span');
        // Знаходимо іконку стрілки (зазвичай це тег <i> або <svg>)
        const iconElement = container.querySelector('i');

        // Оновлюємо текст (+12.5%)
        if (textSpan) {
            const sign = value > 0 ? '+' : '';
            textSpan.textContent = `${sign}${Number(value).toFixed(1)}%`;
        }

        // --- ГОЛОВНА МАГІЯ ТУТ ---

        // Визначаємо, чи це "хороший" результат
        let isGoodOutcome = false;

        if (Math.abs(value) < 0.01) {
            // Якщо зміни майже немає (0%)
            container.className = 'stat-card-trend neutral';
            // Можна поставити іконку "риска" або прибрати стрілку
            if(iconElement) iconElement.className = 'bi bi-dash';
            return;
        }

        if (isExpense) {
            // Для ВИТРАТ: добре, коли вони падають (value < 0)
            isGoodOutcome = value < 0;
        } else {
            // Для ДОХОДІВ: добре, коли вони ростуть (value > 0)
            isGoodOutcome = value > 0;
        }

        // Застосовуємо стилі залежно від того, добре це чи погано
        container.classList.remove('positive', 'negative', 'neutral');

        if (isGoodOutcome) {
            // Усе супер: Зелений колір + Стрілка ВГОРУ
            container.classList.add('positive');
            if(iconElement) iconElement.className = 'bi bi-arrow-up';
        } else {
            // Усе погано: Червоний колір + Стрілка ВНИЗ
            container.classList.add('negative');
            if(iconElement) iconElement.className = 'bi bi-arrow-down';
        }
    };
    const balanceCard = document.querySelector('.balance-card');
    if (balanceCard) {
        const trendDiv = balanceCard.querySelector('.stat-card-trend');
        const icon = trendDiv ? trendDiv.querySelector('i') : null;
        const text = trendDiv ? trendDiv.querySelector('span') : null;

        if (trendDiv && icon && text) {
            trendDiv.classList.remove('positive', 'negative', 'neutral');

            if (balanceVal < 0) {
                // Якщо баланс мінусовий -> Червоний, "Critical", іконка тривоги
                trendDiv.classList.add('negative');
                icon.className = 'bi bi-exclamation-triangle-fill';
                text.textContent = 'Critical';
            } else {
                // Якщо баланс плюсовий -> Зелений, "Healthy", іконка успіху
                trendDiv.classList.add('positive');
                icon.className = 'bi bi-shield-check'; // Або bi-graph-up
                text.textContent = 'Healthy';
            }
        }
    }

    // Викликаємо оновлення для обох карток (код залишається тим самим)
    updateTrend('.income-card .stat-card-trend', incomePct, false);
    updateTrend('.expense-card .stat-card-trend', expensePct, true);

    const txList = data.recent_transactions || []
    const tbody = document.getElementById('transactions-list')
    if(txList.length === 0){
      tbody.innerHTML = `<tr><td colspan="6">
        <div class="empty-state">
          <div class="empty-state-icon"><i class="bi bi-inbox"></i></div>
          <div class="empty-state-text">No transactions yet</div>
          <div class="empty-state-subtext">Start tracking your finances by adding your first transaction</div>
        </div>
      </td></tr>`
    } else {
      tbody.innerHTML = txList.map((tx, idx) => {
        const amountNum = (typeof tx.amount === 'number') ? tx.amount : parseFloat(tx.amount || 0)
        const isIncome = tx.transaction_type === 'income'
        const amountFormatted = (typeof amountNum === 'number') ? Math.abs(amountNum).toFixed(2) : (tx.amount || '')
        const amountHTML = `<span class="${isIncome ? 'amount-positive' : 'amount-negative'}">${isIncome ? '+' : '-'}${currencySymbol}${amountFormatted}</span>`
        const desc = tx.title || ''

        // Category badge with icon
        // Strategy: use tx.category object if present; otherwise if backend included 'data.categories' try to match by id; fallback to tx.category_name
        let categoryObj = null
        if(tx && tx.category && typeof tx.category === 'object'){
          categoryObj = tx.category
        } else if(tx && (tx.category_id || tx.category) && Array.isArray(data.categories)){
          // tx.category might be id or category_id
          const cid = tx.category_id || tx.category
          try{ categoryObj = data.categories.find(c => c && (c.id === cid || String(c.id) === String(cid))) }catch(_){ categoryObj = null }
        }
        if(!categoryObj) categoryObj = { name: tx.category_name }

        // Determine iconClass: prefer tx.category_icon, then categoryObj.icon, fallback to 'bi-tag-fill'
        const rawIcon = (tx && tx.category_icon) ? tx.category_icon : (categoryObj && categoryObj.icon ? categoryObj.icon : 'bi-tag-fill')
        // Normalize: remove any leading 'bi ' if present so we can render as `bi ${name}` safely
        const iconName = String(rawIcon || '').trim().replace(/^bi\s+/, '')

        const categoryName = (categoryObj && categoryObj.name) ? categoryObj.name : (tx.category_name || 'Uncategorized')
        const styleObj = getCategoryStyle(categoryName)

        const categoryBadge = `
          <div class="d-flex align-items-center">
            <div class="category-icon-badge" style="background: ${escapeHtml(styleObj.bg)}; color: ${escapeHtml(styleObj.iconColor)}">
              <i class="bi ${escapeHtml(iconName)}" aria-hidden="true"></i>
            </div>
            <span>${escapeHtml(categoryName)}</span>
          </div>
        `

         return `
         <tr>
           <td class="td-num" style="color: var(--fm-muted)">${idx+1}</td>
           <td class="td-desc" title="${escapeHtml(desc + (tx.note ? (' - ' + tx.note) : ''))}">
             <div style="font-weight: 600;">${escapeHtml(desc)}</div>
             ${tx.note ? `<div class="small text-muted text-truncate" style="max-width:100%; opacity: 0.7">${escapeHtml(tx.note)}</div>` : ''}
           </td>
           <td class="td-cat">${categoryBadge}</td>
           <td class="td-amount" style="text-align:right">${amountHTML}</td>
           <td class="td-date" style="color: var(--fm-muted); font-size: 0.875rem">${tx.created_at ? formatDateDMY(tx.created_at) : ''}</td>
           <td class="td-actions">
             <div class="action-btn-group">
               <button class="action-btn btn-edit" data-tx-id="${tx.id}" data-action="edit">
                 <i class="bi bi-pencil"></i> Edit
               </button>
               <button class="action-btn btn-delete" data-tx-id="${tx.id}" data-action="delete">
                 <i class="bi bi-trash"></i>
               </button>
             </div>
           </td>
         </tr>
       `
       }).join('')
     }

     // populate categories for quick form
     try{
       const catSelect = document.getElementById('tx_category')
       if(catSelect){
         let cats = data && data.categories
         if(!cats || !Array.isArray(cats)){
           try{ cats = await fetchCategories() }catch(_){ cats = [] }
         }
         if(Array.isArray(cats)){
           catSelect.innerHTML = '<option value="">Select category</option>' + (cats.map(c=>`<option value="${c.id}">${c.name}</option>`).join(''))
         }
       }
     }catch(e){ /* Failed to populate quick form categories (silent) */ }

     // Charts with Modern Styling
    try{
      // ✅ КРИТИЧНА ПЕРЕВІРКА: Якщо немає даних графіків, пропускаємо рендеринг
      if(!data || !data.charts){
        console.error('[CHART UPDATE] ❌ NO CHART DATA!')
        return
      }

      // ✅ ЗАХИСТ: Якщо графіки щойно були створені (менше 500ms тому), пропускаємо повторний рендеринг
      const now = Date.now()
      const timeSinceLastRender = now - lastChartRenderTime
      if(balanceChart && categoryChart && timeSinceLastRender < 500){
        return
      }

      // ✅ ВИПРАВЛЕННЯ: Якщо попередній рендеринг "завис", скидаємо прапорець
      if(chartsRendering){
        // Reset flag silently
      }

      chartsRendering = true

      // ✅ КРИТИЧНО: Перевірити, чи Chart.js доступний
      if(typeof Chart === 'undefined'){
        console.error('[CHART UPDATE] Chart.js NOT LOADED! Waiting 50ms and retrying...')
        chartsRendering = false
        // Почекати трохи і спробувати знову
        setTimeout(() => {
          loadData(period)
        }, 50)
        return
      }

      const ctxLine = document.getElementById('balanceLineChart')
      const ctxDonut = document.getElementById('categoryDonutChart')

      if(!ctxLine && !ctxDonut){
        console.error('[CHART UPDATE] Canvas elements not found')
        chartsRendering = false
        return
      }

      // ✅ Ініціалізуємо контексти з willReadFrequently для уникнення попереджень
      if(ctxLine) {
        try{ ctxLine.getContext('2d', { willReadFrequently: true }) }catch(e){}
      }
      if(ctxDonut) {
        try{ ctxDonut.getContext('2d', { willReadFrequently: true }) }catch(e){}
      }

      // Force destroy all existing chart instances
      if(typeof Chart !== 'undefined' && Chart.instances){
        Object.values(Chart.instances).forEach(chart => {
          try{ chart.destroy() }catch(e){}
        })
      }

      // Balance Dynamics Line Chart
      if(ctxLine){
        const labels = ((data.charts && data.charts.balance_dynamics && data.charts.balance_dynamics.labels) || [])
        const values = ((data.charts && data.charts.balance_dynamics && data.charts.balance_dynamics.data) || [])

        try{
          if(balanceChart){
            try{ balanceChart.destroy() }catch(e){}
            balanceChart = null
          }

          // Показуємо/ховаємо empty state
          const balanceEmptyEl = document.getElementById('balanceChartEmpty')
          const hasBalanceData = labels.length > 0 && values.length > 0

          if(balanceEmptyEl) {
            balanceEmptyEl.style.display = hasBalanceData ? 'none' : 'block'
          }

          if(hasBalanceData) {
            if(ctxLine) ctxLine.style.opacity = '1'

            balanceChart = new Chart(ctxLine, {
              type: 'line',
              data: {
                labels,
                datasets: [{
                  label: 'Balance',
                  data: values,

                  // Лінія: Темно-синя, коли мінус (Deep Ocean)
                  segment: {
                    borderColor: ctx => {
                        return ctx.p1.parsed.y < 0 ? '#254e99' : 'rgba(58, 160, 255, 0.9)';
                    }
                  },

                  backgroundColor: 'rgba(58, 160, 255, 0.05)',
                  borderWidth: 2,
                  pointRadius: 0,
                  pointHoverRadius: 6,

                  // Точка: Темно-синя, коли мінус
                  pointHoverBackgroundColor: (ctx) => {
                      return ctx.raw < 0 ? '#254e99' : 'rgba(58, 160, 255, 0.9)';
                  },
                  pointHoverBorderColor: '#fff',
                  pointHoverBorderWidth: 2,
                  tension: 0.4,
                  fill: false
                }]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                devicePixelRatio: Math.max(window.devicePixelRatio || 1, 3),
                interaction: {
                  mode: 'index',
                  intersect: false
                },
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    backgroundColor: 'rgba(20, 25, 30, 0.95)',
                    padding: 12,
                    titleColor: '#9aa1a6',
                    titleFont: { size: 12, weight: 'normal' },
                    bodyFont: { size: 16, weight: 'bold' },
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    displayColors: false,

                    callbacks: {
                      label: function(context) {
                        return currencySymbol + context.parsed.y.toFixed(2)
                      },

                      // ✅ ТУТ ЗМІНА: Цифри стають ЧЕРВОНИМИ, якщо мінус
                      labelTextColor: function(context) {
                        return context.parsed.y < 0 ? '#ef4444' : '#10b981';
                      }
                    }
                  }
                },
                layout: { padding: { top: 10, right: 15, bottom: 5, left: 5 } },
                scales: {
                  x: {
                    ticks: { color: 'rgba(255, 255, 255, 0.6)', maxRotation: 45, minRotation: 25, autoSkip: true, maxTicksLimit: 12, font: { size: 11 } },
                    grid: { color: 'rgba(255, 255, 255, 0.03)', drawBorder: false }
                  },
                  y: {
                    ticks: { color: 'rgba(255, 255, 255, 0.6)', callback: function(value) { return currencySymbol + value.toFixed(0) }, padding: 5, font: { size: 11 } },
                    grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false }
                  }
                },
                animation: { duration: 400, easing: 'easeOutCubic' }
              }
            })
          } else {
            // Якщо немає даних, ховаємо canvas
            if(ctxLine) ctxLine.style.opacity = '0'
          }
        }catch(errLine){
          console.error('[CHART UPDATE] Balance chart error:', errLine)
        }
      } else {
        console.error('[CHART UPDATE] ❌ Canvas element #balanceLineChart not found!')
      }

      // Expenses by Category Doughnut Chart
      if (ctxDonut) {
        const labels = ((data.charts && data.charts.expenses_by_category && data.charts.expenses_by_category.labels) || [])
        const values = ((data.charts && data.charts.expenses_by_category && data.charts.expenses_by_category.data) || [])

        // Show/hide empty state
        const categoryEmptyEl = document.getElementById('categoryChartEmpty')
        const hasCategoryData = labels.length > 0 && values.length > 0 && values.some(v => v > 0)

        if (categoryEmptyEl) categoryEmptyEl.style.display = hasCategoryData ? 'none' : 'block'

        // Legend container
        const legendEl = document.getElementById('categoryLegend')
        if (legendEl) legendEl.style.display = hasCategoryData ? 'block' : 'none'

        if (hasCategoryData) {
          if (ctxDonut) ctxDonut.style.opacity = '1'

          try {
            if (categoryChart) {
              try { categoryChart.destroy() } catch (e) {}
              categoryChart = null
            }

            const bgColors = [
              '#6366f1', '#14b8a6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#10b981'
            ]

            categoryChart = new Chart(ctxDonut, {
              type: 'doughnut',
              data: {
                labels,
                datasets: [{
                  data: values,
                  backgroundColor: bgColors.slice(0, labels.length),
                  borderColor: 'rgba(15, 19, 22, 0.8)',
                  borderWidth: 3,
                  hoverBorderColor: '#fff',
                  hoverBorderWidth: 4
                }]
              },
              options: {
                responsive: false,
                maintainAspectRatio: true,
                aspectRatio: 1,
                devicePixelRatio: Math.max(window.devicePixelRatio || 1, 3),
                cutout: '65%',
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleColor: '#fff',
                    bodyColor: '#10b981',
                    borderColor: 'rgba(58, 160, 255, 0.5)',
                    borderWidth: 2,
                    cornerRadius: 8,
                    displayColors: true,
                    boxWidth: 12,
                    boxHeight: 12,
                    callbacks: {
                      label: function (context) {
                        const label = context.label || ''
                        const value = context.parsed || 0
                        const total = context.dataset.data.reduce((a, b) => a + b, 0)
                        const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0'
                        return label + ': ' + currencySymbol + value.toFixed(2) + ' (' + percentage + '%)'
                      }
                    }
                  }
                },
                elements: { arc: { borderWidth: 3, hoverOffset: 12, borderRadius: 4 } },
                layout: { padding: 10 },
                animation: { animateRotate: true, animateScale: true, duration: 200, easing: 'easeOutCubic' }
              }
            })

            // Build custom HTML legend enriched with server icons when available
            try {
              const catLegend = document.getElementById('categoryLegend')
              if (catLegend) {
                catLegend.innerHTML = ''
                const lbls = (categoryChart && categoryChart.data && categoryChart.data.labels) || []
                const total = values.reduce((a, b) => a + b, 0)
                const serverCats = (data && data.categories && Array.isArray(data.categories)) ? data.categories : []

                lbls.forEach((lbl, i) => {
                  const value = values[i] || 0
                  const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0'

                  const el = document.createElement('div')
                  el.className = 'legend-item'
                  el.setAttribute('role', 'button')
                  el.setAttribute('tabindex', '0')
                  el.style.cssText = 'cursor: pointer; padding: 6px 10px; border-radius: 6px; transition: all 0.2s ease; display:flex; align-items:center; gap:8px;'

                  // prefer server-provided icon (match by name case-insensitive)
                  let iconClass = null
                  try {
                    const found = serverCats.find(c => c && c.name && String(c.name).toLowerCase() === String(lbl).toLowerCase())
                    if (found && found.icon) iconClass = String(found.icon).trim()
                  } catch (_e) { iconClass = null }

                  if (iconClass) {
                    const iconEl = document.createElement('i')
                    iconEl.className = iconClass
                    iconEl.style.marginRight = '8px'
                    iconEl.setAttribute('aria-hidden', 'true')
                    el.appendChild(iconEl)
                  } else {
                    const colorBox = document.createElement('span')
                    colorBox.className = 'legend-color'
                    const bg = (categoryChart.data.datasets[0].backgroundColor[i] || '#666')
                    colorBox.style.backgroundColor = bg
                    colorBox.style.display = 'inline-block'
                    colorBox.style.width = '14px'
                    colorBox.style.height = '14px'
                    colorBox.style.minWidth = '14px'
                    colorBox.style.borderRadius = '3px'
                    colorBox.style.boxShadow = '0 1px 0 rgba(0,0,0,0.25) inset'
                    colorBox.style.border = '1px solid rgba(0,0,0,0.12)'
                    colorBox.setAttribute('aria-hidden', 'true')
                    colorBox.setAttribute('title', lbl + ' - ' + percentage + '%')
                    el.appendChild(colorBox)
                  }

                  const textSpan = document.createElement('span')
                  textSpan.style.cssText = 'font-weight: 500; color: rgba(255,255,255,0.9); font-size: 0.8125rem;'
                  textSpan.textContent = lbl

                  const valueSpan = document.createElement('span')
                  valueSpan.style.cssText = 'margin-left: auto; font-weight: 600; color: rgba(255,255,255,0.7); font-size: 0.8125rem;'
                  valueSpan.textContent = percentage + '%'

                  el.appendChild(textSpan)
                  el.appendChild(valueSpan)

                  el.addEventListener('mouseenter', () => { el.style.background = 'rgba(255,255,255,0.05)' })
                  el.addEventListener('mouseleave', () => { el.style.background = 'transparent' })

                  el.addEventListener('click', () => {
                    try {
                      const idx = i
                      if (categoryChart) {
                        const meta = categoryChart.getDatasetMeta(0)
                        meta.data[idx].hidden = !meta.data[idx].hidden
                        categoryChart.update()
                        el.style.opacity = meta.data[idx].hidden ? '0.4' : '1'

                        const allHidden = meta.data.every(arc => arc.hidden)
                        const categoryEmptyEl2 = document.getElementById('categoryChartEmpty')
                        const ctxDonut2 = document.getElementById('categoryDonutChart')

                        if (allHidden) {
                          if (categoryEmptyEl2) categoryEmptyEl2.style.display = 'block'
                          if (ctxDonut2) ctxDonut2.style.opacity = '0'
                        } else {
                          if (categoryEmptyEl2) categoryEmptyEl2.style.display = 'none'
                          if (ctxDonut2) ctxDonut2.style.opacity = '1'
                        }
                      }
                    } catch (_err) { }
                  })

                  catLegend.appendChild(el)
                })
              }
            } catch (_e) { /* silent */ }

          } catch (errDonut) {
            console.error('[CHART UPDATE] Donut chart error:', errDonut)
          }

        } else {
          // Якщо немає даних, ховаємо canvas
          if(ctxDonut) ctxDonut.style.opacity = '0'
        }
      }

      // ✅ Зберігаємо таймстамп успішного рендерингу
      if(balanceChart && categoryChart) {
        lastChartRenderTime = Date.now()
        window.__fmCharts = {
          balance: balanceChart,
          category: categoryChart,
          timestamp: lastChartRenderTime
        }
      }
    } catch(errCharts){
      console.error('[CHART UPDATE] Error:', errCharts)
    } finally {
      if(chartsRendering) chartsRendering = false
    }
   }catch(err){
     logError('Dashboard load error', err)
     if(err.message && err.message.toLowerCase().includes('unauthorized')){
       clearToken()
       window.location.href = '/login.html'
     } else {
       showError('Failed to load dashboard: ' + (err.message || 'unknown'))
     }
   } finally {
     loadInProgress = false
     if(pendingLoadPeriod !== null && pendingLoadPeriod !== period){
       const next = pendingLoadPeriod
       pendingLoadPeriod = null
       // silent processing of pending load
       setTimeout(()=> loadData(next), 0)
     }

     // ✅ Синхронізація активної кнопки періоду після завантаження даних
     // Використовуємо currentPeriod (глобальна змінна), а не параметр period
     try {
       const targetPeriod = currentPeriod || period

       document.querySelectorAll('.period-btn').forEach(btn => {
         if(btn.dataset.period === targetPeriod) {
           if(!btn.classList.contains('active')) {
             btn.classList.add('active')
           }
         } else {
           if(btn.classList.contains('active')) {
             btn.classList.remove('active')
           }
         }
       })
     } catch(e) {}
   }
}

function attachHandlers(){
   if(handlersAttached) return

    // ✅ КРИТИЧНИЙ ЗАХИСТ: Постійно відстежуємо та відновлюємо активний стан кнопок періоду
    if(!window.__fmPeriodButtonProtection){
      window.__fmPeriodButtonProtection = true

      // MutationObserver для відстеження змін класів на кнопках
      const observer = new MutationObserver(() => {
        try{
          const expectedPeriod = currentPeriod || 'all'

          document.querySelectorAll('.period-btn').forEach(btn => {
            if(btn.dataset.period === expectedPeriod) {
              if(!btn.classList.contains('active')){
                btn.classList.add('active')
              }
            } else {
              if(btn.classList.contains('active')){
                btn.classList.remove('active')
              }
            }
          })
        }catch(e){}
      })

      // Спостерігаємо за всіма кнопками періоду
      setTimeout(() => {
        document.querySelectorAll('.period-btn').forEach(btn => {
          observer.observe(btn, { attributes: true, attributeFilter: ['class'] })
        })
      }, 100)

      // Також перевіряємо кожні 100мс (легкий fallback)
      setInterval(() => {
        try{
          const expectedPeriod = currentPeriod || 'all'
          document.querySelectorAll('.period-btn').forEach(btn => {
            if(btn.dataset.period === expectedPeriod) {
              if(!btn.classList.contains('active')){
                btn.classList.add('active')
              }
            } else {
              if(btn.classList.contains('active')){
                btn.classList.remove('active')
              }
            }
          })
        }catch(e){}
      }, 100)
    }

    // Modern period buttons
    document.querySelectorAll('.period-btn').forEach(btn => {
      btn.addEventListener('click', function(e) {
        e.preventDefault()
        e.stopPropagation()

        const period = this.dataset.period
        currentPeriod = period

        // Remove active from all buttons
        document.querySelectorAll('.period-btn').forEach(b => {
          b.classList.remove('active')
        })

        // Add active to clicked button
        this.classList.add('active')

        // Update hidden select
        const timeSelect = document.getElementById('time-period-select')
        if (timeSelect) timeSelect.value = period

        // Load data with selected period
        loadData(period)
      })
    })

    const timeSelect = document.getElementById('time-period-select')
    if(timeSelect) timeSelect.addEventListener('change', (e)=> loadData(e.target.value))

  // Quick form removed - using modal forms instead

  // delegate edit/delete buttons
  const txTable = document.getElementById('transactions-list')
  if(txTable){
    // Capture-phase handler: if other code blocks propagation, this still runs early and will schedule action
    try{
      if(!window.__finmate_capture_debug_attached){
        window.__finmate_capture_debug_attached = true
        // remember last handled txId + timestamp to avoid duplicates
        let _lastHandled = { id: null, t: 0 }
        // Diagnostic-only capture listener: log top-level info but don't perform actions here.
        document.addEventListener('click', (e)=>{
            const btn = e.target && e.target.closest ? e.target.closest('button[data-tx-id], button[data-id]') : null
            if(!btn) return
            const action = btn.dataset.action
            const txId = btn.dataset.txId || btn.dataset.id
            const now = Date.now()
            // avoid logging duplicate events within 100ms
            if(_lastHandled.id === txId && (now - _lastHandled.t) < 100) return
            _lastHandled = { id: txId, t: now }
        }, true)
      }
    }catch(e){ }

    txTable.addEventListener('click', (e)=>{
      // timing removed to keep handler lean
      const btn = (e.target && e.target.closest) ? e.target.closest('button[data-tx-id], button[data-id]') : null
      if(!btn) return
      // mark button as handled to prevent fallback duplicate handling
      try{ btn.dataset.fmHandled = '1' }catch(_){ }
      // stop propagation so global fallback doesn't see this click
      try{ e.stopPropagation && e.stopPropagation() }catch(_){ }
      const action = btn.dataset.action
      const txId = btn.dataset.txId || btn.dataset.id
      // tx action click
      if(action === 'edit'){
        if(modalOpening) return
        // MINIMAL synchronous work: remember the button and mark it disabled so user sees feedback
        lastClickedButton = btn
        try{ btn.disabled = true }catch(_){ }

        // Defer all heavier work to next event loop turn to allow browser to repaint and release :active state
        setTimeout(()=>{
          try{
            // attach lightweight safety handlers and start a timer to recover from stuck state
            try{ if(btn.__safetyHandler){ btn.removeEventListener('pointerup', btn.__safetyHandler); btn.removeEventListener('pointercancel', btn.__safetyHandler); btn.__safetyHandler = null } }catch(e){}
            const safetyHandler = ()=>{ try{ btn.classList.remove && btn.classList.remove('active'); btn.disabled = false; btn.blur && btn.blur() }catch(_){ } }
            btn.__safetyHandler = safetyHandler
            btn.addEventListener('pointerup', safetyHandler)
            btn.addEventListener('pointercancel', safetyHandler)

            try{ if(modalOpeningTimer) { clearTimeout(modalOpeningTimer); modalOpeningTimer = null } }catch(e){}
            modalOpeningTimer = setTimeout(()=>{
              try{ if(lastClickedButton){ lastClickedButton.disabled = false; lastClickedButton.classList.remove && lastClickedButton.classList.remove('active'); lastClickedButton.blur && lastClickedButton.blur() } }catch(e){}
              lastClickedButton = null
              modalOpening = false
              modalOpeningTimer = null
            }, 1000)

            // ensure modal safety helpers are registered
            try{ ensureModalSafety() }catch(_){ }

            // Now perform async opening (this runs outside the original click handler)
            openEditModal(txId).catch(err=> { /* silent fail */ })
          }catch(err){ /* silent fail */ }
        }, 0)

        // click handler executed; timing measurements removed (keeps handler lean)
        return
      }
      if(action === 'delete'){
        // prevent duplicate delete attempts
        if(!txId) return
        if(pendingDeletes.has(txId) || isRecentlyHandled(txId)){
          return
        }

        // mark as pending and disable the button immediately to give feedback
        pendingDeletes.add(txId)
        markHandled(txId)
        try{ btn.disabled = true }catch(_){ }

        // Show beautiful confirmation dialog and perform delete asynchronously
        setTimeout(async ()=>{
          try{
            const confirmed = await confirmDelete()
            if(!confirmed) {
              // User cancelled - re-enable button and remove from pending
              try{ btn.disabled = false; pendingDeletes.delete(txId) }catch(e){}
              return
            }

            await api.del(`/transactions/${txId}`)
            await loadData(currentPeriod)
            showSuccess('Transaction deleted successfully!')
          }catch(err){
            showError('Delete failed: ' + (err.message || err))
            logError('Delete failed', err)
          }finally{
            try{ pendingDeletes.delete(txId); btn.disabled = false }catch(e){}
          }
        }, 0)
      }
    })
  }

  // sync button
  const syncBtn = document.getElementById('sync-button')
  if(syncBtn){
    syncBtn.addEventListener('click', async ()=>{
      try{
        syncBtn.disabled = true
        await api.post('/monobank/sync-transactions', {})
        await loadData(currentPeriod)
        showSuccess('Transactions synced successfully!')
      }catch(e){
        logError('Sync failed', e)
        showError('Sync failed: ' + (e.message || e))
      }
      finally{ syncBtn.disabled = false }
    })
  }

  // Add Transaction button handler
  const addTxBtn = document.getElementById('add-transaction-button')
  if(addTxBtn){
    addTxBtn.addEventListener('click', async ()=>{
      const modalEl = document.getElementById('addTransactionModal')
      if(!modalEl) {
        return
      }

      // ✅ Save scroll position before opening modal
      saveScrollPosition()

      // Load categories into add form
      try{
        await fetchCategories('add_category')
      }catch(e){ /* silent fail */ }

      // Set today's date as default
      const dateInput = document.getElementById('add_date')
      if(dateInput && !dateInput.value){
        dateInput.value = new Date().toISOString().split('T')[0]
      }

      // Clear form
      document.getElementById('addTransactionForm').reset()

      // ✅ Use simple modal implementation
      openModal('addTransactionModal')
    })
  }

  // Add Transaction form submit
  const addTxForm = document.getElementById('addTransactionForm')
  if(addTxForm){
    addTxForm.addEventListener('submit', async (e)=>{
      e.preventDefault()
      const title = document.getElementById('add_title').value.trim()
      const amount = parseFloat(document.getElementById('add_amount').value)
      const type = (document.querySelector('input[name="add_type"]:checked') || {}).value || 'expense'
      const categoryId = parseInt(document.getElementById('add_category').value) || null
      const date = document.getElementById('add_date').value || undefined
      const note = document.getElementById('add_note').value || null

      // Basic validation to reduce backend spam
      if(!title || title.length < 2){
        showWarning('Transaction title must be at least 2 characters')
        return
      }
      if(!amount || isNaN(amount) || amount <= 0){
        showWarning('Please provide a valid amount (greater than 0)')
        return
      }
      if(!categoryId){
        showWarning('Please select a category')
        return
      }
      // ✅ Removed date validation - backend will handle it

      const payload = {
        title,
        amount,
        transaction_type: type,
        category_id: categoryId,
        created_at: date,
        note
      }

      try{
        await api.post('/transactions', payload)

        // ✅ Close modal using simple modal helper
        closeModal('addTransactionModal')

        // ✅ Restore scroll position after modal closes
        setTimeout(()=> restoreScrollPosition(), 100)

        await loadData()
        // Show success feedback
        showSuccess('Transaction added successfully!')

        const submitBtn = addTxForm.querySelector('button[type="submit"]')
        if(submitBtn){
          const origText = submitBtn.textContent
          submitBtn.textContent = 'Added!'
          submitBtn.classList.add('btn-outline-success')
          submitBtn.classList.remove('btn-success')
          setTimeout(()=>{
            submitBtn.textContent = origText
            submitBtn.classList.remove('btn-outline-success')
            submitBtn.classList.add('btn-success')
          }, 2000)
        }
      }catch(err){
        showError('Failed to create transaction: ' + (err.message || err))
        console.error('Create transaction failed', err)
      }
    })
  }

  // edit modal form submit
  const txForm = document.getElementById('transactionForm')
  if(txForm){
    txForm.addEventListener('submit', async (e)=>{
      e.preventDefault()
      const id = document.getElementById('edit_tx_id').value
      const title = document.getElementById('edit_title').value.trim()
      const amount = parseFloat(document.getElementById('edit_amount').value)
      const type = (document.querySelector('input[name="type"]:checked') || {}).value || ''
      const categoryId = parseInt(document.getElementById('edit_category').value) || null
      const date = document.getElementById('edit_date').value || undefined
      const note = document.getElementById('edit_note').value || null

      // Basic validation to reduce backend spam
      if(!title || title.length < 2){
        showWarning('Transaction title must be at least 2 characters')
        return
      }
      if(!amount || isNaN(amount) || amount <= 0){
        showWarning('Please provide a valid amount (greater than 0)')
        return
      }
      if(!categoryId){
        showWarning('Please select a category')
        return
      }

      const payload = {
        title,
        amount,
        transaction_type: type,
        category_id: categoryId,
        created_at: date,
        note
      }
      try{
        await api.put(`/transactions/${id}`, payload)

        // ✅ Close modal using simple modal helper
        closeModal('editTransactionModal')

        // ✅ Restore scroll position after modal closes
        setTimeout(()=> restoreScrollPosition(), 100)

        await loadData()
        showSuccess('Transaction updated successfully!')
      }catch(err){
        showError('Save failed: ' + (err.message || err))
      }
    })
  }

  // ✅ Add listeners to modal close buttons to restore scroll
  try{
    document.querySelectorAll('.modal .btn-close, .modal [data-bs-dismiss="modal"]').forEach(btn => {
      btn.addEventListener('click', ()=> {
        setTimeout(()=> restoreScrollPosition(), 100)
      })
    })
  }catch(e){ /* failed to attach modal close listeners */ }

  // Listen to legacy UI actions dispatched by older scripts (non-blocking)
  try{
    document.addEventListener('fm:legacy-tx-action', (ev)=>{
      try{
        const detail = (ev && ev.detail) || {}
        const { action, id } = detail
        if(!action || !id) return
        if(action === 'edit'){
          // open edit modal using existing flow
          lastClickedButton = null
          openEditModal(id)
    // Prefer Bootstrap Modal when available, fallback to manual show
    try{
      if(typeof window !== 'undefined' && window.bootstrap && bootstrap.Modal && typeof bootstrap.Modal.getOrCreateInstance === 'function'){
        bootstrap.Modal.getOrCreateInstance(modalEl).show()
      } else {
        showModalManual(modalEl)
      }
    }catch(e){ console.error('Modal show failed', e) }

    // focus first empty field (heuristic)
    try{
      const firstEmpty = (modalEl.querySelector('input[required]:not([value]), textarea:not([value])') || modalEl.querySelector('input[required]'))
      if(firstEmpty) setTimeout(()=>{ try{ firstEmpty.focus() }catch(e){} }, 50)
    }catch(e){ /* ignore */ }
          if(pendingDeletes.has(id) || isRecentlyHandled(id)) return
          markHandled(id)
          pendingDeletes.add(id)
          api.del(`/transactions/${id}`).then(()=> {
            pendingDeletes.delete(id)
            loadData()
            showSuccess('Transaction deleted successfully!')
          }).catch(err=>{
            pendingDeletes.delete(id)
            showError('Delete failed: ' + (err.message || err))
            logError('Legacy delete failed', err)
          })
        }
      }catch(e){ /* fm:legacy-tx-action handler failed (silent) */ }
    })
  }catch(e){ /* failed to attach fm:legacy-tx-action listener (silent) */ }

  // fallback global listener: ensures clicks reach openEditModal even if delegation failed
  if(!window.__finmate_fallback_click_attached){
    window.__finmate_fallback_click_attached = true
    document.body.addEventListener('click', (e)=>{
       try{
         const btn = e.target && e.target.closest && e.target.closest('button[data-tx-id], button[data-id]')
         if(!btn) return
        // if already handled by delegated table handler, ignore
        if(btn.dataset && btn.dataset.fmHandled){ try{ delete btn.dataset.fmHandled }catch(_){ btn.dataset.fmHandled = null } return }
         const action = btn.dataset.action
         const txId = btn.dataset.txId || btn.dataset.id
         if(!action || !txId) return
         // Debug: always log so user/developer can see clicks
         if(action === 'edit'){
           // ensure we don't block UI — schedule microtask
           lastClickedButton = btn
           try{
             Promise.resolve().then(()=> openEditModal(txId).catch(err=> logError('openEditModal failed', err)))
           }catch(e){
             setTimeout(()=> openEditModal(txId).catch(err=> logError('openEditModal failed (fallback setTimeout)', err)), 0)
           }
         }
         if(action === 'delete'){
           // avoid duplicate deletes
           if(pendingDeletes.has(txId) || isRecentlyHandled(txId)) return
           // schedule delete without blocking
           markHandled(txId)
           pendingDeletes.add(txId)
           setTimeout(async ()=>{ try{ if(confirm('Delete transaction?')){ await api.del(`/transactions/${txId}`); await loadData() } }catch(err){ alert('Delete failed: ' + (err.message || err)); logError('Delete failed (fallback)', err) } finally{ pendingDeletes.delete(txId) } }, 0)
         }
       }catch(e){ /* swallow */ }
    }, false)
  }

  handlersAttached = true
}

function escapeHtml(s){
  if(s === null || s === undefined) return ''
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')
}

// Format date as dd.mm.yyyy (no time) — safe for various input formats
function formatDateDMY(dateInput){
  if(!dateInput) return ''
  try{
    const d = new Date(dateInput)
    if(isNaN(d)) return String(dateInput)
    const dd = String(d.getDate()).padStart(2,'0')
    const mm = String(d.getMonth()+1).padStart(2,'0')
    const yyyy = d.getFullYear()
    return `${dd}.${mm}.${yyyy}`
  }catch(e){ return String(dateInput) }
}

async function openEditModal(txId){
  // Guard: if this txId is already being opened, ignore duplicate requests
  if (openingTxIds.has(txId)) return
  openingTxIds.add(txId)

  // ✅ Save scroll position before opening modal
  saveScrollPosition()

  // If another modal opening flow is in progress, queue the request instead of scheduling retries
    if(modalOpening){
     try{
       if(!pendingModalQueue.includes(txId)) pendingModalQueue.push(txId)
       // silent queueing (no log)
     }catch(e){ /* failed to queue modal open (silent) */ }
     return
   }
   modalOpening = true
   const btn = lastClickedButton
   try{
     // openEditModal started for txId
     if(btn) try{ btn.disabled = true }catch(_){ }

    // load transaction
    const data = await api.get(`/transactions/${txId}`)
    // transaction data loaded

    // populate form fields
    const modalEl = document.getElementById('editTransactionModal')
    if(!modalEl){ console.error('[dashboard] editTransactionModal not found'); alert('UI error: edit modal not found'); return }
    const txIdInput = modalEl.querySelector('input#edit_tx_id')
    const titleInput = modalEl.querySelector('input#edit_title')
    const amountInput = modalEl.querySelector('input#edit_amount')
    const dateInput = modalEl.querySelector('input#edit_date')
    const noteInput = modalEl.querySelector('textarea#edit_note')
    if(txIdInput) txIdInput.value = data.id || ''
    if(titleInput) titleInput.value = data.title || ''
    // transaction_type is represented with radios: edit_expense / edit_income
    try{
      const expenseRadio = modalEl.querySelector('#edit_expense')
      const incomeRadio = modalEl.querySelector('#edit_income')
      if(expenseRadio) expenseRadio.checked = (data.transaction_type === 'expense')
      if(incomeRadio) incomeRadio.checked = (data.transaction_type === 'income')
    }catch(_){ }
    if(amountInput) amountInput.value = (typeof data.amount === 'number' ? data.amount : (data.amount || ''))
    // clear existing category options (will repopulate below)
    try{ const catSelClear = modalEl.querySelector('select#edit_category'); if(catSelClear) catSelClear.innerHTML = '' }catch(_){ }
    if(dateInput) dateInput.value = data.created_at ? new Date(data.created_at).toISOString().split('T')[0] : ''
    if(noteInput) noteInput.value = data.note || ''

    // fetch and populate categories
    try{
      const catSelect = modalEl.querySelector('select#edit_category')
      if(catSelect){
        // Завантажуємо категорії з API
        const catsRaw = await api.get('/categories/all/')
        const cats = Array.isArray(catsRaw) ? catsRaw : (catsRaw && catsRaw.data ? catsRaw.data : [])
        if(Array.isArray(cats)){
          catSelect.innerHTML = cats.map(c=>`<option value="${c.id}" ${data.category_id === c.id ? 'selected' : ''}>${c.name}</option>`).join('')
        }
      }
    }catch(e){
      console.error('[dashboard] Failed to populate edit form categories', e)
    }

    // ✅ Use simple modal implementation
    openModal('editTransactionModal')

  }catch(e){
    console.error('[dashboard] openEditModal error', e)
    showError('Failed to open transaction for editing: ' + (e.message || e))
  } finally {
    // guaranteed cleanup: re-enable and blur button, clear state
    try{ if(btn){ btn.disabled = false; try{ btn.blur() }catch(_){ } try{ btn.classList.remove && btn.classList.remove('active') }catch(_){ } } }catch(e){}
    lastClickedButton = null
    // clear safety timer and remove safety handlers if any
    try{
      if(modalOpeningTimer){ clearTimeout(modalOpeningTimer); modalOpeningTimer = null }
      if(btn && btn.__safetyHandler){ btn.removeEventListener('pointerup', btn.__safetyHandler); btn.removeEventListener('pointercancel', btn.__safetyHandler); btn.__safetyHandler = null }
    }catch(e){}
    modalOpening = false
    // remove guard
    try{ openingTxIds.delete(txId) }catch(e){}
     // if any queued modal requests exist, process next one (small delay to let DOM settle)
    // if any queued modal requests exist, process next one (small delay to let DOM settle)
     try{
       if(pendingModalQueue.length > 0){
         const nextId = pendingModalQueue.shift()
         setTimeout(()=>{
           try{ openEditModal(nextId) }catch(e){ logError('[dashboard] failed to open queued modal', e) }
         }, 50)
       }
     }catch(e){ /* pendingModalQueue processing failed (silent) */ }
  }
}

// Ensure modal safety helpers attach light-weight handlers to recover from stuck backdrops/active buttons
function ensureModalSafety(){
  if(modalSafetyAttached) return
  modalSafetyAttached = true

  // If a backdrop exists but no visible modal, cleanup on any user interaction (capture phase)
  document.addEventListener('pointerdown', ()=>{
    try{
      const hasBackdrop = !!document.querySelector('.modal-backdrop')
      const hasShowModal = !!document.querySelector('.modal.show')
      if(hasBackdrop && !hasShowModal){ closeAllModals() }
      // also clear any stuck button active state
      document.querySelectorAll('button.active').forEach(b=>{ try{ b.classList.remove('active'); b.disabled = false; b.blur && b.blur() }catch(_){ } })
    }catch(e){}
  }, true)

  // click capture: also remove leftover backdrop if present
  document.addEventListener('click', ()=>{
    try{
      const hasBackdrop = !!document.querySelector('.modal-backdrop')
      const hasShowModal = !!document.querySelector('.modal.show')
      if(hasBackdrop && !hasShowModal){ closeAllModals() }
    }catch(e){}
  }, true)

  // ESC key safety
  document.addEventListener('keydown', (e)=>{
    try{
      if(e.key === 'Escape'){
        const hasBackdrop = !!document.querySelector('.modal-backdrop')
        const hasShowModal = !!document.querySelector('.modal.show')
        if(hasBackdrop && !hasShowModal) closeAllModals()
      }
    }catch(e){}
  }, true)

  // Watchdog as last resort: if backdrop present without modal, clean every second for up to 30s
  try{
    let ticks = 0
    const maxTicks = 30
    const watcher = setInterval(()=>{
      try{
        const hasBackdrop = !!document.querySelector('.modal-backdrop')
        const hasShowModal = !!document.querySelector('.modal.show')
        if(hasBackdrop && !hasShowModal){ /* watchdog cleaning leftover backdrop */ closeAllModals() }
        ticks++
        if(ticks > maxTicks) clearInterval(watcher)
      }catch(e){}
    }, 1000)
    window.addEventListener('beforeunload', ()=> clearInterval(watcher))
  }catch(e){ /* modal watchdog failed (silent) */ }
}

// Global: log unhandled promise rejections to console for easier debugging
if(typeof window !== 'undefined' && !window.__fm_unhandled_logged){
  window.__fm_unhandled_logged = true
  window.addEventListener('unhandledrejection', (ev)=>{
    try{ console.error('[FinMate] unhandledrejection', ev.reason) }catch(e){}
  })
}

// Entry
try{ renderSkeleton() }catch(e){ console.error('[Init] renderSkeleton failed:', e) }
try{ appendModalsToBody() }catch(e){ console.error('[Init] appendModalsToBody failed:', e) }

// Async initialization
;(async ()=>{
  try{
    await renderHeader()
  }catch(e){
    console.error('[Init] renderHeader failed:', e)
  }

  // Завантажуємо профіль користувача для отримання валюти (використовуємо кеш)
  try{
    const { getProfile } = await import('../utils/profileCache.js')
    const profile = await getProfile()
    if(profile && profile.currency){
      userCurrency = profile.currency
    }
  }catch(e){
    console.error('[Init] Failed to load user profile:', e)
    // Залишаємо дефолтну валюту UAH
  }

  try{ attachHandlers() }catch(e){
    console.error('[Init] attachHandlers failed:', e)
    logError('Failed to attach handlers', e)
  }

  // Ініціалізуємо currentPeriod
  try{
    const activeBtn = document.querySelector('.period-btn.active')
    currentPeriod = activeBtn ? activeBtn.dataset.period : 'all'
  }catch(e){ currentPeriod = 'all' }

  // Викликаємо loadData() для завантаження даних
  chartsRendering = false
  loadInProgress = false

  try{
    await loadData(currentPeriod)
  }catch(e){
    console.error('[Init] loadData failed:', e)
    logError('Failed to load dashboard data', e)
  }

  // ensure modal element is present directly under body to avoid z-index/overflow/initialization races
  try{
    const modalEl = document.getElementById('editTransactionModal')
    if(modalEl && !document.body.contains(modalEl)){
      document.body.appendChild(modalEl)
    }
  }catch(e){ /* failed to move modal into body (silent) */ }

  // attach global safety handlers to remove leftover backdrops if any
  try{ ensureModalSafety() }catch(e){ logError('ensureModalSafety failed', e) }

  // Listen to legacy UI actions dispatched by older scripts (non-blocking)
  try{
    document.addEventListener('fm:legacy-tx-action', (ev)=>{
      try{
        const detail = (ev && ev.detail) || {}
        const { action, id } = detail
        if(!action || !id) return
        if(action === 'edit'){
          lastClickedButton = null
          openEditModal(id)
        } else if(action === 'delete'){
          if(pendingDeletes.has(id) || isRecentlyHandled(id)) return
          markHandled(id)
          pendingDeletes.add(id)
          api.del(`/transactions/${id}`).then(()=> {
            pendingDeletes.delete(id)
            loadData(currentPeriod)
            showSuccess('Transaction deleted successfully!')
          }).catch(err=>{
            pendingDeletes.delete(id)
            showError('Delete failed: ' + (err.message || err))
            logError('Legacy delete failed', err)
          })
        }
      }catch(e){ /* fm:legacy-tx-action handler failed (silent) */ }
    })
  }catch(e){ /* failed to attach fm:legacy-tx-action listener (silent) */ }

  // Charts are now properly managed and only destroyed before re-creation
})();

// ✅ HMR (Hot Module Reload) Protection for Vite dev server
if (import.meta.hot) {
  import.meta.hot.accept(() => {
    console.log('[HMR] Dashboard module reloaded - preserving charts')
  })

  // Prevent chart destruction on HMR
  import.meta.hot.dispose(() => {
    console.log('[HMR] Module disposing - keeping charts alive')
    // Don't destroy charts on HMR, only on manual cleanup
  })
}
