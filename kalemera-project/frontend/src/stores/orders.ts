import { defineStore } from 'pinia'
import api from '../api'

export interface OrderItemResponse {
  id: number
  product_id: number
  product_name_snapshot: string
  product_name_en_snapshot: string | null
  variant_id: number | null
  variant_name_snapshot: string | null
  price_snapshot: number
  quantity: number
  subtotal: number
}

export interface Order {
  id: number
  user_id: number
  status: 'PENDING' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED'
  total_price: number
  created_at: string
  updated_at: string
  items: OrderItemResponse[]
  user?: {
    id: number
    phone?: string
    full_name: string
  }
}

export const useOrderStore = defineStore('orders', {
  state: () => ({
    orders: [] as Order[],
    currentOrder: null as Order | null,
    loading: false,
  }),
  actions: {
    async placeOrder(items: { product_id: number; variant_id: number | null; quantity: number }[]) {
      this.loading = true
      try {
        const response = await api.post<Order>('/api/orders/', { items })
        return response.data
      } finally {
        this.loading = false
      }
    },
    async cancelOrder(orderId: number) {
      this.loading = true
      try {
        const response = await api.post<Order>(`/api/orders/${orderId}/cancel`)
        return response.data
      } finally {
        this.loading = false
      }
    },
    async fetchMyOrders() {
      this.loading = true
      try {
        const response = await api.get<Order[]>('/api/orders/')
        this.orders = response.data
        return response.data
      } finally {
        this.loading = false
      }
    },
    async fetchOrderDetail(id: number) {
      this.loading = true
      try {
        const response = await api.get<Order>(`/api/orders/${id}`)
        this.currentOrder = response.data
        return response.data
      } finally {
        this.loading = false
      }
    },
  },
})
