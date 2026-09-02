/**
 * Pure navigation helpers (no Vite/Vue dependencies so they are testable under
 * plain Node). They encode two rules:
 *
 *  1. Back must return to the actual previous route/history entry.
 *  2. Only when there is no valid browser/router history should we fall back to
 *     Home ("/").
 */

export interface RouterHistoryStateLike {
  back?: unknown
  forward?: unknown
  position?: number
}

/** True when the current history state points to a valid in-app previous route. */
export function hasValidBackEntry(historyState: unknown): boolean {
  if (historyState === null || typeof historyState !== 'object') return false
  const back = (historyState as RouterHistoryStateLike).back
  return typeof back === 'string' && back.length > 0 && back.startsWith('/')
}

/**
 * Returns the previous in-app route (fullPath) to go back to, or null when no
 * valid history entry exists (caller should fall back to Home).
 */
export function resolveBackTarget(historyState: unknown): string | null {
  if (!hasValidBackEntry(historyState)) return null
  return (historyState as RouterHistoryStateLike).back as string
}

/**
 * Decides where an already-authenticated user should be sent when they land on
 * /login or /register (e.g. a stale back-history entry left by the
 * ?redirect= login flow).
 *
 * Returns the previous route to preserve (using replace) when there is a real
 * in-app source, or null to instruct the caller to use Home as fallback.
 */
export function resolveAuthPageRedirect(fromFullPath: string, toFullPath: string): string | null {
  if (fromFullPath && fromFullPath !== toFullPath && fromFullPath !== '/') {
    return fromFullPath
  }
  return null
}