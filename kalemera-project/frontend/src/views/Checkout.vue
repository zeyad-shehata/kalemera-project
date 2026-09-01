<template>
  <v-container class="py-12">
    <h1 class="text-h4 font-weight-bold mb-6">{{ t('checkout') }}</h1>

    <v-row>
      <!-- Order Summary Card -->
      <v-col cols="12" md="8">
        <v-card class="elevation-3 rounded-lg pa-6 mb-6">
          <h2 class="text-h6 font-weight-bold mb-4">{{ t('confirmItems') }}</h2>
          <v-list class="pa-0">
            <v-list-item
              v-for="item in cartStore.items"
              :key="item.product.id + '-' + (item.variant?.id || 'none')"
              lines="two"
              class="border-bottom py-3 px-0"
            >
              <template v-slot:prepend>
                <v-img
                  :src="item.product.image_path ? `${apiBaseUrl}${item.product.image_path}` : 'https://placehold.co/100x75?text=No+Image'"
                  width="60"
                  height="45"
                  cover
                  class="rounded-lg mr-4 bg-grey-lighten-2"
                ></v-img>
              </template>
              
              <v-list-item-title class="font-weight-bold d-flex align-center">
                {{ localeStore.currentLocale === 'en' && item.product.name_en ? item.product.name_en : item.product.name }}
                <v-chip size="x-small" color="primary" class="ml-2 font-weight-bold" v-if="item.variant">
                  {{ t('sizePrefix') }} {{ item.variant.name }}
                </v-chip>
              </v-list-item-title>
              <v-list-item-subtitle class="text-grey-darken-1">
                {{ t('qtyPrefix') }} {{ item.quantity }} × {{ (item.variant ? item.variant.price : item.product.price).toFixed(2) }} EGP
              </v-list-item-subtitle>
              
              <template v-slot:append>
                <span class="font-weight-bold">{{ ((item.variant ? item.variant.price : item.product.price) * item.quantity).toFixed(2) }} EGP</span>
              </template>
            </v-list-item>
          </v-list>
        </v-card>

        <!-- Billing Info -->
        <v-card class="elevation-3 rounded-lg pa-6">
          <h2 class="text-h6 font-weight-bold mb-4">{{ t('billingDetails') }}</h2>
          <v-row>
            <v-col cols="12" sm="6">
              <v-text-field :label="t('fullName')" v-model="shippingName" variant="outlined" density="comfortable" readonly></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field :label="t('phoneNumber')" variant="outlined" density="comfortable" :value="authStore.currentUser?.phone || ''" readonly></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-select
                :label="t('deliveryAddress')"
                v-model="deliveryAddress"
                :items="deliveryOptions"
                item-title="label"
                item-value="value"
                variant="outlined"
                density="comfortable"
                color="primary"
                prepend-inner-icon="mdi-map-marker-radius"
                class="bg-surface rounded-lg"
                hide-details
              ></v-select>
            </v-col>
            <v-col cols="12">
              <v-chip class="font-weight-bold" color="info" label>
                <v-icon start>mdi-truck-delivery</v-icon>
                {{ t('freeDelivery') }}
              </v-chip>
            </v-col>
          </v-row>
        </v-card>
      </v-col>

      <!-- Pay and Finalize Card -->
      <v-col cols="12" md="4">
        <v-card class="elevation-3 rounded-lg pa-6 bg-grey-lighten-5 border">
          <h2 class="text-h6 font-weight-bold mb-4">{{ t('paymentSummary') }}</h2>

          <div class="d-flex justify-space-between mb-3">
            <span>{{ t('subtotal') }}:</span>
            <span class="font-weight-bold">{{ cartStore.subtotal.toFixed(2) }} EGP</span>
          </div>

          <div class="d-flex justify-space-between mb-3">
            <span>{{ t('shipping') }}:</span>
            <span class="font-weight-bold text-success">{{ t('free') }}</span>
          </div>

          <v-divider class="my-4"></v-divider>

          <div class="d-flex justify-space-between mb-6 text-h5 font-weight-bold">
            <span>{{ t('orderTotal') }}</span>
            <span class="color-primary">{{ cartStore.subtotal.toFixed(2) }} EGP</span>
          </div>

          <v-alert v-if="errorMessage" type="error" variant="tonal" class="mb-4">
            {{ errorMessage }}
          </v-alert>

          <v-alert v-else-if="storeClosed" type="warning" variant="tonal" class="mb-4">
            <div class="d-flex align-center ga-2">
              <v-icon>mdi-clock-alert</v-icon>
              <span class="font-weight-bold">{{ t('storeClosed') }}</span>
            </div>
          </v-alert>

          <v-btn
            color="primary"
            size="large"
            block
            class="font-weight-bold text-uppercase rounded-lg"
            :loading="orderStore.loading"
            :disabled="cartStore.items.length === 0 || storeClosed"
            @click="confirmOrder"
          >
            {{ t('confirmOrder') }}
          </v-btn>

          <v-btn
            variant="text"
            color="secondary"
            block
            class="font-weight-bold text-uppercase rounded-lg mt-2"
            to="/cart"
          >
            {{ t('editCart') }}
          </v-btn>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '../stores/cart'
import { useOrderStore } from '../stores/orders'
import { useAuthStore } from '../stores/auth'
import { useLocaleStore } from '../stores/locale'
import api, { API_BASE_URL } from '../api'

const router = useRouter()
const cartStore = useCartStore()
const orderStore = useOrderStore()
const authStore = useAuthStore()
const localeStore = useLocaleStore()
const { t } = localeStore

const apiBaseUrl = API_BASE_URL
const errorMessage = ref('')
const storeClosed = ref(false)
let statusTimer: number | null = null

const deliveryOptions = [
  { label: 'سكن الولاد الداخلي', value: 'سكن الولاد الداخلي' },
  { label: 'سكن البنات الداخلي', value: 'سكن البنات الداخلي' },
  { label: 'الحي الراقي', value: 'الحي الراقي' },
]
const deliveryAddress = ref(null as string | null)

const shippingName = computed(() => authStore.currentUser?.full_name || '')

const checkBusinessHours = async () => {
  try {
    const res = await api.get('/api/business-hours')
    storeClosed.value = Boolean(res.data?.closed)
  } catch (e) {
    storeClosed.value = false
  }
}

const confirmOrder = async () => {
  if (cartStore.items.length === 0 || storeClosed.value) return

  if (!deliveryAddress.value) {
    errorMessage.value = localeStore.currentLocale === 'ar' 
      ? 'يرجى اختيار عنوان التوصيل أولاً'
      : 'Please select a delivery address first'
    return
  }

  errorMessage.value = ''

  const orderItems = cartStore.items.map((item) => ({
    product_id: item.product.id,
    variant_id: item.variant?.id || null,
    quantity: item.quantity,
  }))

  try {
    await orderStore.placeOrder(orderItems, deliveryAddress.value)
    cartStore.clearCart()
    router.push('/orders')
  } catch (error: any) {
    if (error.response && error.response.data && error.response.data.detail) {
      errorMessage.value = error.response.data.detail
      if (error.response.status === 403 || error.response.status === 409) {
        storeClosed.value = true
      }
    } else {
      errorMessage.value = t('failOrder')
    }
  }
}

onMounted(async () => {
  await checkBusinessHours()
  statusTimer = window.setInterval(checkBusinessHours, 60000)
})

onUnmounted(() => {
  if (statusTimer) window.clearInterval(statusTimer)
})
</script>
