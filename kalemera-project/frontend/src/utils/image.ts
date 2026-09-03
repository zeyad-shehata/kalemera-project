import { API_BASE_URL } from '../api'

/**
 * Resolves a product image path to a full URL.
 * Safely handles both absolute cloud URLs (e.g. S3/R2/Vercel Blob)
 * and relative paths (e.g. /uploads/..., /storage/...).
 */
export function resolveImageUrl(
  imagePath: string | null | undefined,
  fallback: string = 'https://placehold.co/400x300/1e1a17/d49b54?text=Kalmera'
): string {
  if (!imagePath || !imagePath.trim()) {
    return fallback
  }
  const cleanPath = imagePath.trim()
  if (cleanPath.startsWith('http://') || cleanPath.startsWith('https://')) {
    return cleanPath
  }
  return `${API_BASE_URL}${cleanPath.startsWith('/') ? cleanPath : '/' + cleanPath}`
}
