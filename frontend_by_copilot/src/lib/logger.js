// Simple logger with levels that can be toggled centrally
const ENABLE_DEBUG = false
const ENABLE_INFO = false

export function debug(...args){ if(ENABLE_DEBUG) console.debug(...args) }
export function info(...args){ if(ENABLE_INFO) console.info(...args) }
export function error(...args){ console.error(...args) }

export default { debug, info, error }

