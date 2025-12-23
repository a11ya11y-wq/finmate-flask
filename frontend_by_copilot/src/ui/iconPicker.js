// filepath: c:\PycharmProj\FinMate\frontend_by_copilot\src\ui\iconPicker.js
import { ALLOWED_ICONS } from '../utils/constants.js'

// Renders a grid of icons into containerEl and wires click handling to update hiddenInput.
// containerEl: DOM element or selector where to render grid
// hiddenInput: DOM element or selector for hidden input (value updated with selected icon class)
// initialIcon: optional string like 'bi-bag'
export function initIconPicker(containerEl, hiddenInputSelectorOrEl, initialIcon = null){
  const container = (typeof containerEl === 'string') ? document.querySelector(containerEl) : containerEl
  if(!container) return

  const hiddenInput = (typeof hiddenInputSelectorOrEl === 'string') ? document.querySelector(hiddenInputSelectorOrEl) : hiddenInputSelectorOrEl

  // Render icons as buttons with class `icon-option-btn`
  container.innerHTML = ALLOWED_ICONS.map(ic => {
    // ic is like 'bi-cart' already (per constants)
    const normalized = String(ic).trim()
    const isActive = initialIcon && (normalized === initialIcon || (initialIcon && initialIcon.replace(/^bi-/, '') === normalized.replace(/^bi-/, '')) || (`bi-${normalized}` === initialIcon))
    return `<button type="button" class="icon-option-btn ${isActive ? 'active' : ''}" data-icon="${normalized}" aria-pressed="${isActive ? 'true' : 'false'}"><i class="${normalized}" aria-hidden="true"></i></button>`
  }).join('')

  // Ensure hidden input exists
  let inputEl = hiddenInput
  if(!inputEl){
    const hi = document.createElement('input')
    hi.type = 'hidden'
    hi.name = 'icon'
    hi.value = initialIcon || ''
    container.insertAdjacentElement('afterend', hi)
    inputEl = hi
  } else {
    try{ inputEl.value = initialIcon || '' }catch(e){}
  }

  // Helper to clear active state within this container
  function clearActive(){
    container.querySelectorAll('button.icon-option-btn').forEach(b=>{
      b.classList.remove('active')
      b.setAttribute('aria-pressed','false')
    })
  }

  // Event delegation
  container.addEventListener('click', (ev)=>{
    const btn = ev.target && ev.target.closest ? ev.target.closest('button.icon-option-btn') : null
    if(!btn) return
    const icon = btn.getAttribute('data-icon')

    // clear other selections and set active on clicked
    clearActive()
    btn.classList.add('active')
    btn.setAttribute('aria-pressed','true')

    // update hidden input
    const input = inputEl || container.parentElement.querySelector('input[name="icon"]')
    if(input) input.value = icon
  })
}
