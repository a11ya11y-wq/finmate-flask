// Confirm Dialog utility
import { showWarning } from './toast.js'

export async function confirmDelete(itemName = 'цей елемент') {
  return new Promise((resolve) => {
    const message = `Ви впевнені, що хочете видалити ${itemName}? Цю дію неможливо скасувати.`

    // Use native confirm for simplicity
    const result = confirm(message)

    if (!result) {
      showWarning('Видалення скасовано')
    }

    resolve(result)
  })
}

export async function confirmAction(message, confirmText = 'Підтвердити') {
  return new Promise((resolve) => {
    const result = confirm(message)
    resolve(result)
  })
}

