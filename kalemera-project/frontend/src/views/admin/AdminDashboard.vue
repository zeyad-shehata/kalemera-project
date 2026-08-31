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

      <!-- Admin Orders Management Section -->
      <v-card class="elevation-6 rounded-xl pa-6 bg-surface border-bronze mt-6 overflow-x-auto">
        <div class="d-flex align-center justify-space-between mb-4">
          <div>
            <h3 class="text-h6 font-weight-bold text-bronze-gradient">{{ t('manageOrders') }}</h3>
            <p class="text-caption text-copper-muted">{{ t('ordersSub') }}</p>
          </div>
        </div>

        <v-table class="table-responsive bg-transparent text-copper-muted">
          <thead>
            <tr>
              <th class="text-left font-weight-bold text-primary">{{ t('orderHeader') }}</th>
              <th class="text-left font-weight-bold text-primary">{{ t('customerHeader') }}</th>
              <th class="text-left font-weight-bold text-primary">{{ t('dateHeader') }}</th>
              <th class="text-left font-weight-bold text-primary">{{ t('totalHeader') }}</th>
              <th class="text-left font-weight-bold text-primary">{{ t('statusHeader') }}</th>
              <th class="text-center font-weight-bold text-primary">{{ t('actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in orders" :key="order.id">
              <td class="font-weight-bold">#{{ order.id }}</td>
              <td>
                <div class="font-weight-bold text-copper-muted">{{ order.user?.full_name || 'N/A' }}</div>
                <div class="text-caption text-copper-muted">{{ order.user?.phone || 'N/A' }}</div>
              </td>
              <td>{{ formatDate(order.created_at) }}</td>
              <td class="font-weight-bold text-primary">{{ order.total_price.toFixed(2) }} EGP</td>
              <td>
                <v-chip :color="getStatusColor(order.status)" size="small" class="font-weight-bold text-uppercase">
                  {{ order.status }}
                </v-chip>
              </td>
              <td class="text-center">
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn
                      color="primary"
                      variant="tonal"
                      size="small"
                      class="font-weight-bold mr-2"
                      v-bind="props"
                    >
                      {{ t('changeStatus') }}
                    </v-btn>
                  </template>
                  <v-list>
                    <v-list-item
                      v-for="statusOpt in ['PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED']"
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
                  class="font-weight-bold"
                  @click="viewOrderDetails(order)"
                >
                  {{ t('details') }}
                </v-btn>
              </td>
            </tr>
          </tbody>
        </v-table>

        <!-- Empty State -->
        <div v-if="orders.length === 0" class="text-center pa-8 text-copper-muted">
          {{ t('noOrdersAdmin') }}
        </div>
      </v-card>

      <!-- Order Details Dialog -->
      <v-dialog v-model="detailsDialog" max-width="500px">
        <v-card class="rounded-xl pa-4 bg-surface border-bronze">
          <v-card-title class="text-h5 font-weight-black text-bronze-gradient">
            {{ t('orderDetailTitle') }} #{{ selectedOrder?.id }}
          </v-card-title>
          <v-card-text>
            <div class="mb-4 text-copper-muted">
              <strong>{{ t('customerLabel') }}:</strong> {{ selectedOrder?.user?.full_name }} ({{ selectedOrder?.user?.phone }})
            </div>
            <div v-if="selectedOrder?.delivery_address" class="mb-4 text-copper-muted">
              <strong>{{ t('deliveryAddress') }}:</strong> {{ selectedOrder.delivery_address }}
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
            <div class="d-flex justify-space-between text-h6 font-weight-black text-primary">
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
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAdminStore } from '../../stores/admin'
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
const orders = ref<Order[]>([])
const detailsDialog = ref(false)
const selectedOrder = ref<Order | null>(null)

const loadOrders = async () => {
  try {
    const response = await api.get<Order[]>('/api/orders/')
    orders.value = response.data
  } catch (error) {
    console.error(error)
  }
}

const updateStatus = async (orderId: number, status: string) => {
  try {
    await adminStore.updateOrderStatus(orderId, status)
    await loadOrders()
    await loadData()
  } catch (error) {
    alert('Failed to update status.')
  }
}

const viewOrderDetails = (order: Order) => {
  selectedOrder.value = order
  detailsDialog.value = true
}

const loadData = () => {
  adminStore.fetchDashboardSummary()
  loadOrders()
}

onMounted(() => {
  loadData()
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
