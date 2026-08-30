import axios from 'axios'
import router from './router'

const API_BASE_URL =
  import.meta.env.VITE_API_URL !== undefined
    ? import.meta.env.VITE_API_URL
    : import.meta.env.PROD
      ? ''
      : 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Ensures cookies are sent with requests
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor to handle errors globally (e.g. 401 Unauthorized on protected routes)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const url = error.config?.url || ''
      // Do not redirect to login during initial guest session check (/api/auth/me) or auth forms
      if (!url.includes('/api/auth/me') && !url.includes('/api/auth/login') && !url.includes('/api/auth/register')) {
        const currentRoute = router.currentRoute.value.path
        if (currentRoute !== '/login' && currentRoute !== '/register') {
          router.push('/login')
        }
      }
    }
    return Promise.reject(error)
  }
)


export default api
export { API_BASE_URL }
