/**
 * Centralized Date Formatter with Timezone Handling.
 * Correctly converts UTC timestamps from the backend into the user's local timezone (Egypt / UTC+3).
 */
export function formatAppDate(dateStr: string | Date | null | undefined, locale: string = 'ar'): string {
  if (!dateStr) return ''

  let iso = typeof dateStr === 'string' ? dateStr : dateStr.toISOString()

  // If the ISO string lacks timezone information (no Z or +/- offset),
  // append 'Z' so JavaScript's Date parser correctly interprets it as UTC.
  if (!iso.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(iso)) {
    iso += 'Z'
  }

  const date = new Date(iso)
  if (isNaN(date.getTime())) return String(dateStr)

  const lang = locale === 'ar' ? 'ar-EG' : 'en-US'
  return date.toLocaleString(lang, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}
