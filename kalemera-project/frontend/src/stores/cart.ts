import { defineStore } from 'pinia'
import type { Product, ProductVariant } from './products'

export interface CartItem {
  product: Product
  variant?: ProductVariant
  quantity: number
}

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [] as CartItem[],
  }),
  getters: {
    itemCount: (state) => state.items.reduce((sum, item) => sum + item.quantity, 0),
    subtotal: (state) => state.items.reduce((sum, item) => {
      const price = item.variant ? item.variant.price : item.product.price
      return sum + price * item.quantity
    }, 0),
  },
  actions: {
    loadCart() {
      const savedCart = localStorage.getItem('cart')
      if (savedCart) {
        try {
          this.items = JSON.parse(savedCart)
        } catch (e) {
          this.items = []
        }
      }
    },
    saveCart() {
      localStorage.setItem('cart', JSON.stringify(this.items))
    },
    addToCart(product: Product, quantity: number = 1, variant?: ProductVariant) {
      const chosenVariant = variant || (product.variants && product.variants.length > 0 ? product.variants[0] : undefined)
      const existing = this.items.find(
        (item) => item.product.id === product.id && item.variant?.id === chosenVariant?.id
      )
      if (existing) {
        existing.quantity += quantity
      } else {
        this.items.push({ product, quantity, variant: chosenVariant })
      }
      this.saveCart()
    },
    removeFromCart(productId: number, variantId?: number) {
      this.items = this.items.filter(
        (item) => !(item.product.id === productId && item.variant?.id === variantId)
      )
      this.saveCart()
    },
    updateQuantity(productId: number, variantId: number | undefined, quantity: number) {
      const item = this.items.find(
        (i) => i.product.id === productId && i.variant?.id === variantId
      )
      if (item) {
        item.quantity = quantity
        if (item.quantity <= 0) {
          this.removeFromCart(productId, variantId)
        } else {
          this.saveCart()
        }
      }
    },
    clearCart() {
      this.items = []
      this.saveCart()
    },
  },
})

