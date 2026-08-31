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
  created_at: string
  product_count?: number
}

export interface OrderItem {
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

export interface OrderUser {
  id: number
  phone?: string | null
  full_name: string
}

export interface Order {
  id: number
  user_id: number
  status: 'PENDING' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED'
  total_price: number
  delivery_address?: string | null
  created_at: string
  updated_at: string
  items: OrderItem[]
  user?: OrderUser | null
}

export interface Notification {
  id: number
  user_id: number
  message: string
  is_read: boolean
  created_at: string
}

export interface User {
  id: number
  phone: string
  full_name: string
  role: 'ADMIN' | 'CUSTOMER'
  created_at: string
}

export interface StorageBreakdown {
  images_bytes: number
  images_mb: number
  database_bytes: number
  database_mb: number
  backups_bytes: number
  backups_mb: number
  temp_bytes: number
  total_app_bytes: number
  total_app_mb: number
  disk_free_bytes: number
  disk_free_gb: number
  hosting_limit_bytes: number
  hosting_limit_gb: number
  usage_percent: number
}
