import { defineStore } from 'pinia'
import api from '../api'

export interface ProductVariant {
  id: number
  product_id: number
  name: string
  price: number
}

export interface Product {
  id: number
  name: string
  name_en: string | null
  description: string | null
  description_en: string | null
  price: number
  stock: number
  image_path: string | null
  category_id: number
  created_at: string
  variants?: ProductVariant[]
}

export interface Category {
  id: number
  name: string
  product_count?: number
  created_at: string
}

export interface PaginatedProducts {
  items: Product[]
  total: number
  page: number
  size: number
}

export const useProductStore = defineStore('products', {
  state: () => ({
    products: [] as Product[],
    totalProducts: 0,
    categories: [] as Category[],
    currentProduct: null as Product | null,
    loading: false,
  }),
  actions: {
    async fetchProducts(params: { search?: string; category?: number; sort_by?: string; sort_order?: string; page?: number; size?: number } = {}) {
      this.loading = true
      try {
        const response = await api.get<PaginatedProducts>('/api/products/', { params })
        this.products = response.data.items
        this.totalProducts = response.data.total
        return response.data
      } finally {
        this.loading = false
      }
    },
    async fetchProduct(id: number) {
      this.loading = true
      try {
        const response = await api.get<Product>(`/api/products/${id}`)
        this.currentProduct = response.data
        return response.data
      } finally {
        this.loading = false
      }
    },
    async fetchCategories() {
      this.loading = true
      try {
        const response = await api.get<Category[]>('/api/categories/')
        this.categories = response.data
        return response.data
      } finally {
        this.loading = false
      }
    },
  },
})
