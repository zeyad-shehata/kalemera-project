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
                  :src="resolveImageUrl(item.product.image_path, 'https://placehold.co/100x75?text=No+Image')"
                  :alt="localeStore.currentLocale === 'en' && item.product.name_en ? item.product.name_en : item.product.name"
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

        <!-- Fulfillment Method Section -->
        <v-card class="elevation-3 rounded-lg pa-6 mb-6">
          <h2 class="text-h6 font-weight-bold mb-4 d-flex align-center ga-2">
            <v-icon color="primary">mdi-package-variant-closed</v-icon>
            {{ t('fulfillmentMethod') }}
          </h2>

          <v-btn-toggle
            v-model="fulfillmentType"
            mandatory
            color="primary"
            variant="outlined"
            divided
            class="d-flex w-100 rounded-lg overflow-hidden border-bronze mb-4"
          >
            <v-btn
              value="DELIVERY"
              class="flex-1-1 font-weight-bold py-3"
              :class="{ 'bg-primary text-white': fulfillmentType === 'DELIVERY' }"
            >
              <v-icon start>mdi-moped</v-icon>
              {{ t('delivery') }}
            </v-btn>
            <v-btn
              value="PICKUP"
              class="flex-1-1 font-weight-bold py-3"
              :class="{ 'bg-primary text-white': fulfillmentType === 'PICKUP' }"
            >
              <v-icon start>mdi-storefront-outline</v-icon>
              {{ t('pickupFromHall') }}
            </v-btn>
          </v-btn-toggle>

          <!-- Delivery Address Selector (Shown only when DELIVERY is chosen) -->
          <div v-if="fulfillmentType === 'DELIVERY'">
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
              class="bg-surface rounded-lg mb-2"
              hide-details
              :error="showAddressError"
              :error-messages="addressErrorText"
            ></v-select>

            <v-chip v-if="deliveryFee" class="font-weight-bold mt-2" color="info" label>
              <v-icon start>mdi-truck-delivery</v-icon>
              {{ t('deliveryFee') }}: {{ deliveryFee.toFixed(2) }} EGP
            </v-chip>
            <v-chip v-else class="font-weight-bold mt-2" color="grey" label>
              <v-icon start>mdi-truck-delivery</v-icon>
              {{ t('selectAddressForFee') }}
            </v-chip>
          </div>

          <!-- Pickup Notice (Shown only when PICKUP is chosen) -->
          <div v-else class="pa-4 bg-surface-variant rounded-lg border-bronze">
            <div class="d-flex align-center ga-2 text-primary font-weight-bold mb-1">
              <v-icon color="primary">mdi-check-circle-outline</v-icon>
              <span>{{ t('pickupFree') }}</span>
            </div>
            <p class="text-caption text-copper-muted mb-0">
              {{ t('pickupNotice') }}
            </p>
          </div>
        </v-card>

        <!-- Order Notes -->
        <v-card class="elevation-3 rounded-lg pa-6 mb-6">
          <h2 class="text-h6 font-weight-bold mb-4 d-flex align-center ga-2">
            <v-icon color="primary">mdi-note-edit-outline</v-icon>
            {{ t('orderNotes') }}
          </h2>
          <v-textarea
            v-model="orderNotes"
            :label="t('orderNotesHint')"
            variant="outlined"
            density="comfortable"
            rows="2"
            hide-details
            class="bg-surface rounded-lg"
          ></v-textarea>
        </v-card>

        <!-- Customer Info -->
        <v-card class="elevation-3 rounded-lg pa-6">
          <h2 class="text-h6 font-weight-bold mb-4">{{ t('billingDetails') }}</h2>
          <v-row>
            <v-col cols="12" sm="6">
              <v-text-field :label="t('fullName')" v-model="shippingName" variant="outlined" density="comfortable" readonly></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field :label="t('phoneNumber')" variant="outlined" density="comfortable" :value="authStore.currentUser?.phone || ''" readonly dir="ltr" prepend-inner-icon="mdi-phone"></v-text-field>
            </v-col>
          </v-row>
        </v-card>
      </v-col>

      <!-- Pay and Finalize Card -->
      <v-col cols="12" md="4">
        <v-card class="elevation-3 rounded-lg pa-6 bg-grey-lighten-5 border">
          <h2 class="text-h6 font-weight-bold mb-4">{{ t('paymentSummary') }}</h2>

          <div class="d-flex justify-space-between mb-3">
            <span>{{ t('fulfillmentMethod') }}:</span>
            <span class="font-weight-bold text-primary">
              {{ fulfillmentType === 'PICKUP' ? t('pickupFromHall') : t('delivery') }}
            </span>
          </div>

          <div class="d-flex justify-space-between mb-3">
            <span>{{ t('subtotal') }}:</span>
            <span class="font-weight-bold">{{ cartStore.subtotal.toFixed(2) }} EGP</span>
          </div>

          <div class="d-flex justify-space-between mb-3">
            <span>{{ t('deliveryFee') }}:</span>
            <span v-if="fulfillmentType === 'PICKUP'" class="font-weight-bold text-success">{{ t('free') }} (0.00 EGP)</span>
            <span v-else-if="deliveryFee" class="font-weight-bold text-secondary">{{ deliveryFee.toFixed(2) }} EGP</span>
            <span v-else class="font-weight-bold text-grey">{{ t('selectAddressForFee') }}</span>
          </div>

          <v-divider class="my-4"></v-divider>

          <div class="d-flex justify-space-between mb-6 text-h5 font-weight-bold">
            <span>{{ t('orderTotal') }}</span>
            <span class="color-primary">{{ orderTotal.toFixed(2) }} EGP</span>
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
            :disabled="cartStore.items.length === 0 || storeClosed || orderStore.loading"
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
import { resolveImageUrl } from '../utils/image'
import api from '../api'

const router = useRouter()
const cartStore = useCartStore()
const orderStore = useOrderStore()
const authStore = useAuthStore()
const localeStore = useLocaleStore()
const { t } = localeStore

const errorMessage = ref('')
const storeClosed = ref(false)
let statusTimer: number | null = null

const fulfillmentType = ref<'DELIVERY' | 'PICKUP'>('DELIVERY')
const orderNotes = ref('')

// Idempotency key: generated once per checkout attempt and reused across
// retries of the SAME attempt (e.g. a network error), so a resubmission
// cannot create a duplicate order. Regenerated after success or when the
// cart changes, since that represents a genuinely new order.
const idempotencyKey = ref(crypto.randomUUID())

const deliveryOptions = [
  { label: 'سكن الولاد الداخلي', value: 'سكن الولاد الداخلي', fee: 20 },
  { label: 'سكن البنات الداخلي', value: 'سكن البنات الداخلي', fee: 15 },
  { label: 'الحي الراقي', value: 'الحي الراقي', fee: 25 },
]
const deliveryAddress = ref(null as string | null)
const showAddressError = ref(false)

const shippingName = computed(() => authStore.currentUser?.full_name || '')

const deliveryFee = computed(() => {
  if (fulfillmentType.value === 'PICKUP') return 0
  const opt = deliveryOptions.find((o) => o.value === deliveryAddress.value)
  return opt ? opt.fee : 0
})

const orderTotal = computed(() => cartStore.subtotal + deliveryFee.value)

const addressErrorText = computed(() =>
  localeStore.currentLocale === 'ar'
    ? 'يرجى اختيار عنوان التوصيل أولاً'
    : 'Please select a delivery address first'
)

const checkBusinessHours = async () => {
  try {
    const res = await api.get('/api/business-hours')
    storeClosed.value = Boolean(res.data?.closed)
  } catch (e) {
    storeClosed.value = false
  }
}

const confirmOrder = async () => {
  if (cartStore.items.length === 0 || storeClosed.value || orderStore.loading) return

  if (fulfillmentType.value === 'DELIVERY' && !deliveryAddress.value) {
    showAddressError.value = true
    errorMessage.value = localeStore.currentLocale === 'ar' 
      ? 'يرجى اختيار عنوان التوصيل أولاً'
      : 'Please select a delivery address first'
    return
  }

  showAddressError.value = false
  errorMessage.value = ''

  const orderItems = cartStore.items.map((item) => ({
    product_id: item.product.id,
    variant_id: item.variant?.id || null,
    quantity: item.quantity,
  }))

  try {
    const addressToPass = fulfillmentType.value === 'DELIVERY' ? deliveryAddress.value : 'استلام من الصالة'
    await orderStore.placeOrder(orderItems, addressToPass, fulfillmentType.value, orderNotes.value, idempotencyKey.value)
    idempotencyKey.value = crypto.randomUUID()
    cartStore.clearCart()
    router.push('/orders')
  } catch (error: any) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      errorMessage.value = detail
    } else if (Array.isArray(detail)) {
      // FastAPI 422 validation errors: array of {loc, msg, type} objects.
      errorMessage.value = detail.map((d: any) => d.msg || String(d)).join('. ')
    } else {
      errorMessage.value = t('failOrder')
    }
    if (error.response && (error.response.status === 403 || error.response.status === 409)) {
      storeClosed.value = true
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
