<template>
  <v-container class="pa-0">
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-black text-bronze-gradient">{{ t('dashboardTitle') }}</h1>
        <p class="text-copper-muted">{{ t('dashboardSubtitle') }}</p>
      </div>
      <v-btn color="primary" variant="outlined" prepend-icon="mdi-refresh" class="rounded-lg font-weight-bold" @click="loadData">
        {{ t('refreshData') }}
      </v-btn>
    </div>

    <!-- Storage Monitor for 5GB Hosting Limit -->
    <StorageMonitor />

    <!-- Loading State -->
    <div v-if="adminStore.loading && !adminStore.summary" class="d-flex justify-center my-12">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <div v-else>
      <!-- Summary Cards Grid -->
      <v-row class="mb-6">
        <!-- Total Sales Card -->
        <v-col cols="12" sm="6" md="4">
          <v-card class="elevation-6 rounded-xl pa-6 bg-surface border-left-primary border-bronze">
            <div class="d-flex justify-space-between align-center">
              <div>
                <span class="text-caption text-copper-muted text-uppercase font-weight-bold">{{ t('revenueLabel') }}</span>
                <h2 class="text-h4 font-weight-black text-primary mt-1">
                  {{ adminStore.summary?.totalSales.toFixed(2) || '0.00' }} EGP
                </h2>
              </div>
              <v-avatar color="primary" variant="tonal" size="56">
                <v-icon color="primary" size="large">mdi-currency-usd</v-icon>
              </v-avatar>
            </div>
          </v-card>
        </v-col>

        <!-- Orders Today Card -->
        <v-col cols="12" sm="6" md="4">
          <v-card class="elevation-6 rounded-xl pa-6 bg-surface border-left-secondary border-bronze">
            <div class="d-flex justify-space-between align-center">
              <div>
                <span class="text-caption text-copper-muted text-uppercase font-weight-bold">{{ t('ordersToday') }}</span>
                <h2 class="text-h4 font-weight-black text-secondary mt-1">
                  {{ adminStore.summary?.ordersToday || 0 }}
                </h2>
              </div>
              <v-avatar color="secondary" variant="tonal" size="56">
                <v-icon color="secondary" size="large">mdi-cart-arrow-down</v-icon>
              </v-avatar>
            </div>
          </v-card>
        </v-col>

        <!-- Total Products Alert/Stat Card -->
        <v-col cols="12" md="4">
          <v-card class="elevation-6 rounded-xl pa-6 bg-surface border-left-info border-bronze">
            <div class="d-flex justify-space-between align-center">
              <div>
                <span class="text-caption text-copper-muted text-uppercase font-weight-bold">{{ t('topItem') }}</span>
                <h2 class="text-h6 font-weight-bold text-bronze-gradient mt-1 text-truncate" style="max-width: 180px;">
                  {{ topProductText }}
                </h2>
              </div>
              <v-avatar color="accent" variant="tonal" size="56">
                <v-icon color="primary" size="large">mdi-trophy-outline</v-icon>
              </v-avatar>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Charts Section -->
      <v-row>
        <v-col cols="12">
          <v-card class="elevation-6 rounded-xl pa-6 bg-surface border-bronze">
            <h3 class="text-h6 font-weight-bold text-bronze-gradient mb-4">{{ t('topProductsChart') }}</h3>
            <div class="chart-container" style="position: relative; height: 350px;">
              <Bar v-if="chartData.datasets[0].data.length > 0" :data="chartData" :options="chartOptions" />
              <div v-else class="d-flex align-center justify-center fill-height">
                <span class="text-copper-muted">{{ t('noSalesData') }}</span>
              </div>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Admin Orders Management Section (workflow buckets) -->
      <v-card class="elevation-6 rounded-xl pa-4 pa-sm-6 bg-surface border-bronze mt-6 overflow-hidden">
        <div class="d-flex align-center justify-space-between mb-4">
          <div>
            <h3 class="text-h6 font-weight-bold text-bronze-gradient">{{ t('manageOrders') }}</h3>
            <p class="text-caption text-copper-muted">{{ t('ordersSub') }}</p>
          </div>
        </div>

        <!-- Grouped by status: NEW → PREPARING → READY → DELIVERED -->
        <div v-for="group in workflowGroups" :key="group.key" class="mb-6">
          <div class="d-flex align-center ga-2 mb-2">
            <v-icon size="small" :color="group.color">{{ group.icon }}</v-icon>
            <h4 class="text-subtitle-1 font-weight-bold text-primary">{{ group.label }}</h4>
            <v-chip size="x-small" :color="group.color" class="font-weight-bold">{{ group.orders.length }}</v-chip>
          </div>

          <template v-if="group.orders.length > 0">
            <div class="pa-2 pa-sm-3 border-bronze rounded-lg bg-surface-variant d-flex flex-column ga-3">
              <div
                v-for="order in group.orders"
                :key="order.id"
                class="pa-3 pa-sm-4 rounded-lg bg-surface border-bronze elevation-2"
              >
                <!-- Row 1: Order ID, Customer Name, Status Chip -->
                <div class="d-flex align-center justify-space-between flex-wrap ga-2 mb-2">
                  <div class="d-flex align-center ga-2 flex-wrap">
                    <v-avatar color="primary" variant="tonal" size="32">
                      <span class="font-weight-black text-primary text-caption">#{{ order.id }}</span>
                    </v-avatar>
                    <span class="font-weight-bold text-subtitle-2 text-copper-muted">
                      {{ order.user?.full_name || 'N/A' }}
                    </span>
                  </div>
                  <v-chip :color="getStatusColor(order.status)" size="small" class="font-weight-bold text-uppercase">
                    {{ order.status }}
                  </v-chip>
                </div>

                <!-- Row 2: Standalone, dedicated Phone Number block -->
                <div v-if="order.user?.phone" class="d-flex align-center ga-2 mb-2 text-caption">
                  <v-icon size="small" color="primary">mdi-phone</v-icon>
                  <span class="font-weight-bold text-primary" dir="ltr">{{ order.user.phone }}</span>
                </div>

                <!-- Row 3: Meta info (Date, Address/Fulfillment, Price) -->
                <div class="d-flex align-center justify-space-between flex-wrap ga-2 text-caption text-copper-muted mb-3">
                  <div class="d-flex align-center ga-3 flex-wrap">
                    <span>
                      <v-icon size="x-small" class="mr-1">mdi-clock-outline</v-icon>
                      {{ formatDate(order.created_at) }}
                    </span>
                    <span v-if="order.fulfillment_type === 'PICKUP' || order.delivery_address === 'استلام من الصالة'" class="text-primary font-weight-bold">
                      <v-icon size="x-small" class="mr-1" color="primary">mdi-storefront-outline</v-icon>
                      {{ t('pickupFromHall') }} (مجاني)
                    </span>
                    <span v-else-if="order.delivery_address">
                      <v-icon size="x-small" class="mr-1">mdi-map-marker</v-icon>
                      {{ order.delivery_address }}
                    </span>
                  </div>
                  <div class="font-weight-black text-subtitle-2 text-primary">
                    {{ order.total_price.toFixed(2) }} EGP
                  </div>
                </div>

                <!-- Row 4: Action Buttons (Responsive flex row) -->
                <div class="d-flex align-center justify-end ga-2 flex-wrap pt-2 border-top">
                  <v-menu v-if="group.key !== 'delivered'">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        color="primary"
                        variant="tonal"
                        size="small"
                        class="font-weight-bold rounded-lg"
                        v-bind="props"
                      >
                        {{ t('changeStatus') }}
                      </v-btn>
                    </template>
                    <v-list>
                      <v-list-item
                        v-for="statusOpt in statusOptionsFor(order.status)"
                        :key="statusOpt"
                        @click="updateStatus(order.id, statusOpt)"
                      >
                        <v-list-item-title class="font-weight-bold">{{ statusOpt }}</v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </v-menu>
                  <v-btn
                    color="secondary"
                    variant="flat"
                    size="small"
                    class="font-weight-bold rounded-lg"
                    @click="viewOrderDetails(order)"
                  >
                    {{ t('details') }}
                  </v-btn>
                  <v-btn
                    v-if="group.key !== 'delivered'"
                    color="error"
                    variant="outlined"
                    size="small"
                    class="font-weight-bold rounded-lg"
                    prepend-icon="mdi-delete"
                    @click="openDeleteDialog(order)"
                  >
                    {{ t('delete') }}
                  </v-btn>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="text-center text-copper-muted pa-4 bg-surface-variant rounded-lg border-bronze">
            {{ t('noOrdersAdmin') }}
          </div>
        </div>

        <!-- Delivered history pagination (avoid loading all rows on Neon) -->
        <div
          v-if="workflow.delivered.length < workflow.delivered_total"
          class="text-center mt-2"
        >
          <v-btn
            color="primary"
            variant="outlined"
            size="small"
            class="font-weight-bold"
            :loading="loadingMoreDelivered"
            @click="loadMoreDelivered"
          >
            {{ t('loadMoreDelivered', { shown: workflow.delivered.length, total: workflow.delivered_total }) }}
          </v-btn>
        </div>
      </v-card>

      <!-- Order Details Dialog -->
      <v-dialog v-model="detailsDialog" max-width="500px">
        <v-card class="rounded-xl pa-4 bg-surface border-bronze">
          <v-card-title class="text-h5 font-weight-black text-bronze-gradient">
            {{ t('orderDetailTitle') }} #{{ selectedOrder?.id }}
          </v-card-title>
          <v-card-text>
            <div class="mb-2 text-copper-muted">
              <strong>{{ t('customerLabel') }}:</strong> {{ selectedOrder?.user?.full_name }} ({{ selectedOrder?.user?.phone }})
            </div>
            <div class="mb-2 text-copper-muted">
              <strong>{{ t('fulfillmentMethod') }}:</strong>
              <span class="font-weight-bold text-primary ml-1">
                {{ selectedOrder?.fulfillment_type === 'PICKUP' || selectedOrder?.delivery_address === 'استلام من الصالة' ? t('pickupFromHall') : t('delivery') }}
              </span>
            </div>
            <div v-if="selectedOrder?.delivery_address && selectedOrder?.fulfillment_type !== 'PICKUP' && selectedOrder?.delivery_address !== 'استلام من الصالة'" class="mb-2 text-copper-muted">
              <strong>{{ t('deliveryAddress') }}:</strong> {{ selectedOrder.delivery_address }}
            </div>
            <div v-if="selectedOrder?.notes" class="mb-4 text-copper-muted bg-surface-variant pa-3 rounded-lg border-bronze">
              <strong><v-icon size="small" class="mr-1" color="primary">mdi-note-text</v-icon> {{ t('orderNotes') }}:</strong>
              <div class="mt-1 font-weight-medium">{{ selectedOrder.notes }}</div>
            </div>
            <v-divider class="mb-4 border-bronze"></v-divider>
            <div class="font-weight-bold text-subtitle-1 mb-2 text-primary">{{ t('itemsLabel') }}:</div>
            <v-list class="bg-transparent pa-0">
              <v-list-item
                v-for="item in selectedOrder?.items"
                :key="item.id"
                class="px-0 py-2 border-bottom"
              >
                <v-list-item-title class="font-weight-bold text-copper-muted">
                  {{ item.product_name_snapshot }}
                  <v-chip size="x-small" color="primary" class="ml-2 font-weight-bold" v-if="item.variant_name_snapshot">
                    حجم {{ item.variant_name_snapshot }}
                  </v-chip>
                </v-list-item-title>
                <v-list-item-subtitle class="text-copper-muted">
                  {{ item.quantity }} × {{ item.price_snapshot.toFixed(2) }} EGP
                </v-list-item-subtitle>
                <template v-slot:append>
                  <span class="font-weight-bold text-secondary">{{ item.subtotal.toFixed(2) }} EGP</span>
                </template>
              </v-list-item>
            </v-list>
            <v-divider class="my-4 border-bronze"></v-divider>
            <div v-if="selectedOrder" class="d-flex justify-space-between text-subtitle-1 text-copper-muted">
              <span>{{ t('subtotal') }}</span>
              <span>{{ (selectedOrder.total_price - (selectedOrder.delivery_fee || 0)).toFixed(2) }} EGP</span>
            </div>
            <div v-if="selectedOrder?.delivery_fee" class="d-flex justify-space-between text-subtitle-1 text-copper-muted mt-1">
              <span>{{ t('deliveryFee') }}</span>
              <span>{{ selectedOrder.delivery_fee.toFixed(2) }} EGP</span>
            </div>
            <div v-else-if="selectedOrder?.fulfillment_type === 'PICKUP' || selectedOrder?.delivery_address === 'استلام من الصالة'" class="d-flex justify-space-between text-subtitle-1 text-copper-muted mt-1">
              <span>{{ t('deliveryFee') }}</span>
              <span class="text-success font-weight-bold">0.00 EGP (مجاني)</span>
            </div>
            <div class="d-flex justify-space-between text-h6 font-weight-black text-primary mt-2">
              <span>{{ t('orderTotal') }}</span>
              <span>{{ selectedOrder?.total_price.toFixed(2) }} EGP</span>
            </div>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="secondary" class="font-weight-bold" @click="detailsDialog = false">{{ t('close') }}</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <!-- Admin Order Deletion Confirmation Dialog -->
      <v-dialog v-model="deleteDialog" max-width="460px">
        <v-card class="rounded-xl pa-4 bg-surface border-bronze">
          <v-card-title class="text-h5 font-weight-black text-error">
            {{ t('deleteOrderTitle') }}
          </v-card-title>
          <v-card-text class="text-copper-muted">
            <p class="mb-2">
              {{ t('deleteOrderConfirm') }} <strong>#{{ deleteTarget?.id }}</strong>?
            </p>
            <p v-if="deleteTarget" class="text-caption">
              {{ t('deleteOrderSub') }}
            </p>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="secondary" variant="tonal" class="font-weight-bold" @click="deleteDialog = false">
              {{ t('cancel') }}
            </v-btn>
            <v-btn color="error" class="font-weight-bold" :loading="deleting" @click="confirmDeleteOrder">
              {{ t('delete') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useAdminStore } from '../../stores/admin'
import { useNotificationStore } from '../../stores/notifications'
import { useLocaleStore } from '../../stores/locale'
import { Bar } from 'vue-chartjs'
import api from '../../api'
import type { Order } from '../../types'
import StorageMonitor from '../../components/StorageMonitor.vue'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

import { formatAppDate } from '../../utils/date'

const adminStore = useAdminStore()
const localeStore = useLocaleStore()
const { t } = localeStore

interface WorkflowData {
  new: Order[]
  preparing: Order[]
  ready: Order[]
  delivered: Order[]
  cancelled: Order[]
  delivered_total: number
}

const workflow = ref<WorkflowData>({
  new: [],
  preparing: [],
  ready: [],
  delivered: [],
  cancelled: [],
  delivered_total: 0,
})
const deliveredOffset = ref(0)
const deliveredLimit = 50
const loadingMoreDelivered = ref(false)
const detailsDialog = ref(false)
const selectedOrder = ref<Order | null>(null)

const deleteDialog = ref(false)
const deleteTarget = ref<Order | null>(null)
const deleting = ref(false)

const workflowGroups = computed(() => [
  { key: 'new',       label: t('newOrders'),       color: 'warning', icon: 'mdi-inbox-arrow-down', orders: workflow.value.new },
  { key: 'preparing', label: t('preparingOrders'), color: 'info',    icon: 'mdi-silverware-fork-knife', orders: workflow.value.preparing },
  { key: 'ready',     label: t('readyOrders'),     color: 'secondary', icon: 'mdi-package-variant', orders: workflow.value.ready },
  { key: 'delivered', label: t('deliveredOrders'), color: 'success', icon: 'mdi-check-decagram',    orders: workflow.value.delivered },
])

// Logical transition options per current status:
// NEW → PREPARING / CANCELLED ; PREPARING → READY / CANCELLED ; READY → DELIVERED / CANCELLED
const statusOptionsFor = (status: string) => {
  switch (status) {
    case 'PENDING': return ['PROCESSING', 'CANCELLED']
    case 'PROCESSING': return ['SHIPPED', 'CANCELLED']
    case 'SHIPPED': return ['DELIVERED', 'CANCELLED']
    default: return []
  }
}

const openDeleteDialog = (order: Order) => {
  deleteTarget.value = order
  deleteDialog.value = true
}

const confirmDeleteOrder = async () => {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await adminStore.deleteOrder(deleteTarget.value.id)
    deleteDialog.value = false
    deleteTarget.value = null
    await loadData()
  } catch (error) {
    alert(t('deleteOrderFailed'))
  } finally {
    deleting.value = false
  }
}

const loadWorkflow = async () => {
  try {
    const response = await api.get<WorkflowData>('/api/orders/workflow', {
      params: { delivered_limit: deliveredLimit, delivered_offset: deliveredOffset.value },
    })
    workflow.value = {
      new: response.data.new || [],
      preparing: response.data.preparing || [],
      ready: response.data.ready || [],
      delivered: response.data.delivered || [],
      cancelled: response.data.cancelled || [],
      delivered_total: response.data.delivered_total || 0,
    }
  } catch (error) {
    console.error(error)
  }
}

const loadMoreDelivered = async () => {
  loadingMoreDelivered.value = true
  try {
    deliveredOffset.value += deliveredLimit
    const response = await api.get<WorkflowData>('/api/orders/workflow', {
      params: { delivered_limit: deliveredLimit, delivered_offset: deliveredOffset.value },
    })
    const more = response.data.delivered || []
    workflow.value.delivered = [...workflow.value.delivered, ...more]
    workflow.value.delivered_total = response.data.delivered_total || workflow.value.delivered_total
  } catch (error) {
    console.error(error)
  } finally {
    loadingMoreDelivered.value = false
  }
}

const updateStatus = async (orderId: number, status: string) => {
  try {
    await adminStore.updateOrderStatus(orderId, status)
    await loadWorkflow()
    await loadData()
  } catch (error) {
    alert(t('statusUpdateFailed'))
  }
}

const viewOrderDetails = (order: Order) => {
  selectedOrder.value = order
  detailsDialog.value = true
}

const notificationStore = useNotificationStore()
let pollingTimer: number | null = null
let loadDataInFlight = false

const loadData = () => {
  // Guard against overlapping calls: the notification-triggered watch and the
  // background polling timer can both fire loadData() around the same moment.
  if (loadDataInFlight) return
  loadDataInFlight = true
  Promise.allSettled([adminStore.fetchDashboardSummary(), loadWorkflow()]).finally(() => {
    loadDataInFlight = false
  })
}

// Watch incoming notifications to refresh workflow and summary live without manual reload
watch(
  () => notificationStore.notifications.length,
  () => {
    loadData()
  }
)

onMounted(() => {
  loadData()
  pollingTimer = window.setInterval(loadData, 10000)
})

onUnmounted(() => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
})

const formatDate = (dateStr: string) => {
  return formatAppDate(dateStr, localeStore.currentLocale)
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'PENDING': return 'warning'
    case 'PROCESSING': return 'info'
    case 'SHIPPED': return 'secondary'
    case 'DELIVERED': return 'success'
    case 'CANCELLED': return 'error'
    default: return 'grey'
  }
}

const topProductText = computed(() => {
  const top = adminStore.summary?.topProducts[0]
  return top ? `${top.name} (${top.quantity} ${t('soldCount').replace('{count}', '')})` : t('noSalesData')
})

// Build Chart Data
const chartData = computed(() => {
  const products = adminStore.summary?.topProducts || []
  return {
    labels: products.map((p) => p.name),
    datasets: [
      {
        label: t('totalItemsSold'),
        backgroundColor: '#D49B54', // Kalmera metallic bronze
        borderRadius: 8,
        data: products.map((p) => p.quantity),
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      ticks: { color: '#BFA893' },
      grid: { color: 'rgba(212, 155, 84, 0.1)' }
    },
    y: {
      beginAtZero: true,
      ticks: {
        precision: 0,
        color: '#BFA893'
      },
      grid: { color: 'rgba(212, 155, 84, 0.1)' }
    },
  },
  plugins: {
    legend: {
      labels: { color: '#F7F3ED' }
    }
  }
}
</script>

<style scoped>
.border-left-primary {
  border-left: 6px solid #D49B54 !important;
}
.border-left-secondary {
  border-left: 6px solid #D9531E !important;
}
.border-left-info {
  border-left: 6px solid #C5853B !important;
}
</style>

