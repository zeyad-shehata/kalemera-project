import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Product, ProductVariant } from './products'

export interface CartItem {
  product: Product
  variant?: ProductVariant
  quantity: number
}

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const justAdded = ref(false)

  const itemCount = computed(() => items.value.reduce((sum, item) => sum + item.quantity, 0))
  const subtotal = computed(() => items.value.reduce((sum, item) => {
    const price = item.variant ? item.variant.price : item.product.price
    return sum + price * item.quantity
  }, 0))

  function loadCart() {
    const savedCart = localStorage.getItem('cart')
    if (savedCart) {
      try {
        items.value = JSON.parse(savedCart)
      } catch (e) {
        items.value = []
      }
    }
  }

  function saveCart() {
    localStorage.setItem('cart', JSON.stringify(items.value))
  }

  function addToCart(product: Product, quantity: number = 1, variant?: ProductVariant) {
    const chosenVariant = variant || (product.variants && product.variants.length > 0 ? product.variants[0] : undefined)
    const existing = items.value.find(
      (item) => item.product.id === product.id && item.variant?.id === chosenVariant?.id
    )
    if (existing) {
      existing.quantity += quantity
    } else {
      items.value.push({ product, quantity, variant: chosenVariant })
    }
    saveCart()
    justAdded.value = true
  }

  function removeFromCart(productId: number, variantId?: number) {
    items.value = items.value.filter(
      (item) => !(item.product.id === productId && item.variant?.id === variantId)
    )
    saveCart()
  }

  function updateQuantity(productId: number, variantId: number | undefined, quantity: number) {
    const item = items.value.find(
      (i) => i.product.id === productId && i.variant?.id === variantId
    )
    if (item) {
      item.quantity = quantity
      if (item.quantity <= 0) {
        removeFromCart(productId, variantId)
      } else {
        saveCart()
      }
    }
  }

  function clearCart() {
    items.value = []
    saveCart()
  }

  function clearJustAdded() {
    justAdded.value = false
  }

  return {
    items,
    justAdded,
    itemCount,
    subtotal,
    loadCart,
    saveCart,
    addToCart,
    removeFromCart,
    updateQuantity,
    clearCart,
    clearJustAdded,
  }
})

