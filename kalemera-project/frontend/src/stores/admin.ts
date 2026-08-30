import { defineStore } from 'pinia'
import api from '../api'
import type { Product, Category, Order, StorageBreakdown } from '../types'

export interface DashboardSummary {
  totalSales: number
  ordersToday: number
  topProducts: { name: string; quantity: number }[]
}

export interface SalesReportItem {
  date: string
  sales: number
}

export const useAdminStore = defineStore('admin', {
  state: () => ({
    summary: null as DashboardSummary | null,
    salesData: [] as SalesReportItem[],
    storage: null as StorageBreakdown | null,
    loading: false,
  }),
  actions: {
    // Storage & Hosting Overview
    async fetchStorageOverview() {
      try {
        const response = await api.get<StorageBreakdown>('/api/storage/overview')
        this.storage = response.data
        return response.data
      } catch (err) {
        console.error('Failed to fetch storage overview:', err)
        return null
      }
    },
    async triggerBackup() {
      const response = await api.post('/api/storage/backup')
      await this.fetchStorageOverview()
      return response.data
    },
    async cleanOrphanImages() {
      const response = await api.post('/api/storage/clean-orphans')
      await this.fetchStorageOverview()
      return response.data
    },

    // Reports & Dashboard
    async fetchDashboardSummary() {
      this.loading = true
      try {
        const response = await api.get<DashboardSummary>('/api/reports/dashboard')
        this.summary = response.data
        return response.data
      } finally {
        this.loading = false
      }
    },
    async fetchSalesReport(startDate: string, endDate: string) {
      this.loading = true
      try {
        const response = await api.get<SalesReportItem[]>('/api/reports/sales', {
          params: { start_date: startDate, end_date: endDate }
        })
        this.salesData = response.data
        return response.data
      } finally {
        this.loading = false
      }
    },

    // Categories CRUD
    async createCategory(name: string) {
      const response = await api.post<Category>('/api/categories/', { name })
      return response.data
    },
    async updateCategory(id: number, name: string) {
      const response = await api.put<Category>(`/api/categories/${id}`, { name })
      return response.data
    },
    async deleteCategory(id: number) {
      await api.delete(`/api/categories/${id}`)
    },

    // Products CRUD (FormData for file upload support)
    async createProduct(formData: FormData) {
      const response = await api.post<Product>('/api/products/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },
    async updateProduct(id: number, formData: FormData) {
      const response = await api.put<Product>(`/api/products/${id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },
    async deleteProduct(id: number) {
      await api.delete(`/api/products/${id}`)
    },

    // Order status update
    async updateOrderStatus(orderId: number, status: string) {
      const response = await api.put<Order>(`/api/orders/${orderId}/status`, { status })
      return response.data
    },
  },
})
