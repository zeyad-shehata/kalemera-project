import { defineStore } from 'pinia'
import api from '../api'

export interface User {
  id: number
  phone: string
  full_name: string
  role: 'ADMIN' | 'CUSTOMER'
  created_at: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    currentUser: null as User | null,
    loading: false,
    initialized: false,
  }),
  getters: {
    isAuthenticated: (state) => !!state.currentUser,
    isAdmin: (state) => state.currentUser?.role === 'ADMIN',
  },
  actions: {
    async fetchCurrentUser() {
      this.loading = true
      try {
        const response = await api.get<User>('/api/auth/me')
        this.currentUser = response.data
        return true
      } catch (error) {
        this.currentUser = null
        return false
      } finally {
        this.loading = false
        this.initialized = true
      }
    },
    async login(credentials: { phone: string; password: string }) {
      this.loading = true
      try {
        const response = await api.post<User>('/api/auth/login', credentials)
        this.currentUser = response.data
        return response.data
      } catch (error) {
        this.currentUser = null
        throw error
      } finally {
        this.loading = false
      }
    },
    async register(user: { phone: string; password: string; full_name: string }) {
      this.loading = true
      try {
        const response = await api.post<User>('/api/auth/register', user)
        // Automatically login the newly registered user
        await this.login({ phone: user.phone, password: user.password })
        return response.data
      } finally {
        this.loading = false
      }
    },
    async logout() {
      this.loading = true
      try {
        await api.post('/api/auth/logout')
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        this.currentUser = null
        this.loading = false
      }
    },
  },
})
