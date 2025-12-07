// Profile Cache - уникаємо дублювання запитів до /profile/me
import api from '../api/apiClient.js'

let cachedProfile = null
let cachePromise = null
let cacheTimestamp = 0
const CACHE_DURATION = 60000 // 1 хвилина

export async function getProfile(forceRefresh = false) {
  const now = Date.now()

  // Якщо є свіжий кеш і не потрібне примусове оновлення
  if (!forceRefresh && cachedProfile && (now - cacheTimestamp) < CACHE_DURATION) {
    return cachedProfile
  }

  // Якщо вже йде запит, повертаємо той самий Promise
  if (cachePromise) {
    return cachePromise
  }

  // Робимо новий запит
  cachePromise = api.get('/profile/me')
    .then(data => {
      cachedProfile = data
      cacheTimestamp = Date.now()
      cachePromise = null
      return data
    })
    .catch(err => {
      cachePromise = null
      throw err
    })

  return cachePromise
}

export function clearProfileCache() {
  cachedProfile = null
  cachePromise = null
  cacheTimestamp = 0
}

export function getCachedProfile() {
  return cachedProfile
}

