import { defineStore } from 'pinia'
import api from '../api'

export interface Notification {
  id: number
  user_id: number
  message: string
  is_read: boolean
  created_at: string
}

export const useNotificationStore = defineStore('notifications', {
  state: () => ({
    notifications: [] as Notification[],
    loading: false,
    pollingIntervalId: null as number | null,
  }),
  actions: {
    async fetchNotifications() {
      try {
        const response = await api.get<Notification[]>('/api/notifications/')
        this.notifications = response.data
        return response.data
      } catch (error) {
        console.error('Failed to fetch notifications:', error)
        return []
      }
    },
    async markAsRead(id: number) {
      try {
        await api.put(`/api/notifications/${id}/read`)
        this.notifications = this.notifications.filter((n) => n.id !== id)
      } catch (error) {
        console.error(`Failed to mark notification ${id} as read:`, error)
      }
    },
    startPolling(intervalMs: number = 10000) {
      if (this.pollingIntervalId) return
      
      // Initial fetch
      this.fetchNotifications()
      
      this.pollingIntervalId = window.setInterval(() => {
        this.fetchNotifications()
      }, intervalMs)
    },
    stopPolling() {
      if (this.pollingIntervalId) {
        clearInterval(this.pollingIntervalId)
        this.pollingIntervalId = null
      }
    },
  },
})
