<template>
  <v-container class="py-12">
    <h1 class="text-h4 font-weight-bold mb-6">{{ t('myOrders') }}</h1>

    <!-- Loading State -->
    <div v-if="orderStore.loading" class="d-flex justify-center my-12">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <!-- Empty Orders State -->
    <v-row v-else-if="orderStore.orders.length === 0" justify="center" class="my-12">
      <v-col cols="12" class="text-center">
        <v-icon size="80" color="grey-lighten-1">mdi-package-variant-closed</v-icon>
        <h3 class="text-h6 text-grey mt-4">{{ t('noOrdersTitle') }}</h3>
        <p class="text-grey mb-6">{{ t('noOrdersSubtitle') }}</p>
        <v-btn color="primary" size="large" to="/" class="font-weight-bold">{{ t('startShopping') }}</v-btn>
      </v-col>
    </v-row>

    <!-- Orders Accordion List -->
    <v-row v-else>
      <v-col cols="12">
        <v-expansion-panels variant="accordion">
          <v-expansion-panel
            v-for="order in orderStore.orders"
            :key="order.id"
            class="elevation-2 mb-3 rounded-lg border overflow-hidden"
          >
            <!-- Expansion Header -->
            <v-expansion-panel-title>
              <template v-slot:default>
                <v-row no-gutters align="center">
                  <v-col cols="12" sm="3" class="font-weight-bold text-subtitle-1">
                    {{ t('orderNum', { id: order.id }) }}
                  </v-col>
                  
                  <v-col cols="12" sm="3" class="text-grey-darken-1 text-subtitle-2">
                    {{ formatDate(order.created_at) }}
                  </v-col>
                  
                  <v-col cols="12" sm="3" class="font-weight-bold color-primary">
                    {{ t('totalLabel', { price: order.total_price.toFixed(2) }) }}
                  </v-col>
                  
                  <v-col cols="12" sm="3" class="text-right pr-4">
                    <v-chip :color="getStatusColor(order.status)" size="small" class="font-weight-bold text-uppercase">
                      {{ t(order.status) }}
                    </v-chip>
                  </v-col>
                </v-row>
              </template>
            </v-expansion-panel-title>
 
            <!-- Expansion Content Details -->
            <v-expansion-panel-text class="bg-grey-lighten-5">
              <v-divider class="mb-4"></v-divider>
              
              <div class="mb-4">
                <h3 class="text-subtitle-2 font-weight-bold mb-2">{{ t('orderItems') }}</h3>
                <v-list class="pa-0 bg-transparent">
                  <v-list-item
                    v-for="item in order.items"
                    :key="item.id"
                    lines="two"
                    class="border-bottom py-2 px-0"
                  >
                    <v-list-item-title class="font-weight-bold d-flex align-center">
                      {{ localeStore.currentLocale === 'en' && item.product_name_en_snapshot ? item.product_name_en_snapshot : item.product_name_snapshot }}
                      <v-chip size="x-small" color="primary" class="ml-2 font-weight-bold" v-if="item.variant_name_snapshot">
                        {{ t('sizePrefix') }} {{ item.variant_name_snapshot }}
                      </v-chip>
                    </v-list-item-title>
                    <v-list-item-subtitle>
                      {{ t('qtyPrefix') }} {{ item.quantity }} × {{ item.price_snapshot.toFixed(2) }} EGP
                    </v-list-item-subtitle>
                    
                    <template v-slot:append>
                      <span class="font-weight-bold">{{ item.subtotal.toFixed(2) }} EGP</span>
                    </template>
                  </v-list-item>
                </v-list>
              </div>

              <!-- Extra Order Details -->
              <v-row class="mt-4">
                <v-col cols="12" sm="6">
                  <span class="text-caption text-grey">{{ t('lastUpdated') }}</span>
                  <div class="text-body-2">{{ formatDate(order.updated_at) }}</div>
                </v-col>
                <v-col cols="12" sm="6">
                  <div class="text-body-2 mb-1">
                    <span class="text-caption text-grey">{{ t('fulfillmentMethod') }}:</span>
                    <v-chip size="x-small" color="primary" class="font-weight-bold ml-1">
                      {{ order.fulfillment_type === 'PICKUP' || order.delivery_address === 'استلام من الصالة' ? t('pickupFromHall') : t('delivery') }}
                    </v-chip>
                  </div>
                  <div class="text-body-2" v-if="order.delivery_address && order.fulfillment_type !== 'PICKUP' && order.delivery_address !== 'استلام من الصالة'">
                    <span class="text-caption text-grey">{{ t('deliveryAddress') }}:</span>
                    <span class="font-weight-bold"> {{ order.delivery_address }}</span>
                  </div>
                  <div class="text-body-2 mt-2 px-3 py-2 bg-white border rounded" v-if="order.notes">
                    <span class="text-caption text-grey">{{ t('orderNotes') }}:</span>
                    <div class="font-weight-bold text-primary">{{ order.notes }}</div>
                  </div>
                  <div class="text-body-2 mt-2">
                    <span class="text-caption text-grey">{{ t('deliveryFee') }}:</span>
                    <span class="font-weight-bold" v-if="order.delivery_fee"> {{ order.delivery_fee.toFixed(2) }} EGP</span>
                    <span class="font-weight-bold text-success" v-else> {{ t('free') }} (0.00 EGP)</span>
                  </div>
                  <div class="text-body-2">
                    <span class="text-caption text-grey">{{ t('subtotal') }}:</span>
                    <span class="font-weight-bold"> {{ (order.total_price - (order.delivery_fee || 0)).toFixed(2) }} EGP</span>
                  </div>
                </v-col>
                <v-col cols="12" sm="6" class="text-sm-right" v-if="canCancel(order)">
                  <v-btn color="error" variant="outlined" size="small" class="font-weight-bold" @click="cancelOrder(order.id)">
                    {{ t('cancelOrder') }}
                  </v-btn>
                </v-col>
              </v-row>

              <!-- Review / Rating -->
              <v-row v-if="order.status === 'DELIVERED'" class="mt-2">
                <v-col cols="12">
                  <v-divider class="mb-4"></v-divider>
                  <div v-if="order.review">
                    <span class="text-caption text-grey">{{ t('rateOrder') }}:</span>
                    <v-rating :model-value="order.review.rating" readonly density="compact" size="small" color="amber"></v-rating>
                    <div v-if="order.review.comment" class="text-body-2 font-italic">"{{ order.review.comment }}"</div>
                  </div>
                  <div v-else>
                    <div class="text-subtitle-2 font-weight-bold mb-2">{{ t('rateOrder') }}</div>
                    <v-rating
                      v-model="reviewDrafts[order.id].rating"
                      density="compact"
                      color="amber"
                      hover
                    ></v-rating>
                    <v-textarea
                      v-model="reviewDrafts[order.id].comment"
                      :label="t('yourReview')"
                      rows="2"
                      maxlength="500"
                      density="compact"
                      variant="outlined"
                      class="mt-2"
                    ></v-textarea>
                    <v-alert v-if="reviewDrafts[order.id].error" type="error" variant="tonal" density="compact" class="mb-2">
                      {{ reviewDrafts[order.id].error }}
                    </v-alert>
                    <v-btn
                      color="primary"
                      size="small"
                      class="font-weight-bold"
                      :loading="reviewDrafts[order.id].submitting"
                      @click="submitReview(order)"
                    >
                      {{ t('submitReview') }}
                    </v-btn>
                  </div>
                </v-col>
              </v-row>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted, reactive, watch } from 'vue'
import { useOrderStore } from '../stores/orders'
import { useLocaleStore } from '../stores/locale'
import type { Order } from '../stores/orders'
import api from '../api'

import { formatAppDate } from '../utils/date'

const orderStore = useOrderStore()
const localeStore = useLocaleStore()
const { t } = localeStore

interface ReviewDraft {
  rating: number
  comment: string
  submitting: boolean
  error: string
}

const reviewDrafts = reactive<Record<number, ReviewDraft>>({})

const ensureReviewDrafts = (orders: Order[]) => {
  for (const order of orders) {
    if (!reviewDrafts[order.id]) {
      reviewDrafts[order.id] = { rating: 0, comment: '', submitting: false, error: '' }
    }
  }
}

watch(() => orderStore.orders, (orders) => ensureReviewDrafts(orders), { immediate: true })

onMounted(() => {
  orderStore.fetchMyOrders()
})

const submitReview = async (order: Order) => {
  const draft = reviewDrafts[order.id]
  if (!draft.rating || draft.rating < 1) {
    draft.error = t('selectRatingFirst')
    return
  }
  draft.error = ''
  draft.submitting = true
  try {
    const res = await api.post(`/api/reviews/orders/${order.id}`, {
      rating: draft.rating,
      comment: draft.comment || null,
    })
    order.review = res.data
  } catch (e: any) {
    draft.error = e.response?.data?.detail || t('failSubmitReview')
  } finally {
    draft.submitting = false
  }
}

const formatDate = (dateStr: string) => {
  return formatAppDate(dateStr, localeStore.currentLocale)
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'PENDING':
      return 'warning'
    case 'PROCESSING':
      return 'info'
    case 'SHIPPED':
      return 'secondary'
    case 'DELIVERED':
      return 'success'
    case 'CANCELLED':
      return 'error'
    default:
      return 'grey'
  }
}

const canCancel = (order: any) => {
  if (order.status !== 'PENDING') return false
  let dateStr = order.created_at
  if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
    dateStr += 'Z'
  }
  const orderTime = new Date(dateStr).getTime()
  const now = new Date().getTime()
  return (now - orderTime) <= 600000 // 10 minutes
}

const cancelOrder = async (orderId: number) => {
  if (confirm(t('confirmCancelOrder', { id: orderId }))) {
    try {
      await orderStore.cancelOrder(orderId)
      await orderStore.fetchMyOrders()
    } catch (error) {
      alert(t('failCancelOrder'))
    }
  }
}
</script>
