import axios from 'axios'
import router from './router'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002'

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Ensures cookies are sent with requests
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor to handle errors globally (e.g. 401 Unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear local session state (can trigger store action to reset user state)
      // Redirect to login if not already there
      const currentRoute = router.currentRoute.value.path
      if (currentRoute !== '/login' && currentRoute !== '/register') {
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

export default api
export { API_BASE_URL }
