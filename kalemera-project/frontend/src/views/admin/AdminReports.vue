<template>
  <v-container class="pa-0">
    <div class="d-flex align-center justify-space-between mb-6">
      <h1 class="text-h4 font-weight-black text-bronze-gradient">{{ t('reportsTitle') }}</h1>
    </div>

    <!-- Section 1: Accounting Summary Reports -->
    <v-card class="elevation-6 rounded-xl pa-6 bg-surface border-bronze mb-6">
      <div class="d-flex flex-column flex-sm-row align-start align-sm-center justify-space-between mb-6 ga-4">
        <div>
          <h3 class="text-h6 font-weight-bold text-bronze-gradient">{{ t('accountingTitle') }}</h3>
          <p class="text-caption text-copper-muted">{{ t('accountingSub') }}</p>
        </div>

        <v-btn-toggle
          v-model="period"
          color="primary"
          mandatory
          variant="outlined"
          class="rounded-lg border-bronze"
          @update:model-value="loadAccounting"
        >
          <v-btn value="today" class="font-weight-bold">{{ t('today') }}</v-btn>
          <v-btn value="week" class="font-weight-bold">{{ t('week') }}</v-btn>
          <v-btn value="month" class="font-weight-bold">{{ t('month') }}</v-btn>
        </v-btn-toggle>
      </div>

      <!-- Loading State -->
      <div v-if="loadingAccounting" class="d-flex justify-center my-8">
        <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
      </div>

      <div v-else-if="accountingData">
        <!-- Summary Cards Grid -->
        <v-row class="mb-6">
          <v-col cols="12" sm="6" md="3">
            <v-card class="pa-4 bg-surface border rounded-xl elevation-3 border-left-bronze">
              <span class="text-caption text-copper-muted font-weight-bold text-uppercase">{{ t('revenueLabel') }}</span>
              <h3 class="text-h5 font-weight-black text-primary mt-1">
                {{ accountingData.totalSales.toFixed(2) }} EGP
              </h3>
            </v-card>
          </v-col>
          
          <v-col cols="12" sm="6" md="3">
            <v-card class="pa-4 bg-surface border rounded-xl elevation-3 border-left-bronze">
              <span class="text-caption text-copper-muted font-weight-bold text-uppercase">{{ t('ordersToday') }}</span>
              <h3 class="text-h5 font-weight-black text-secondary mt-1">
                {{ accountingData.totalOrders }}
              </h3>
            </v-card>
          </v-col>

          <v-col cols="12" sm="6" md="3">
            <v-card class="pa-4 bg-surface border rounded-xl elevation-3 border-left-bronze">
              <span class="text-caption text-copper-muted font-weight-bold text-uppercase">{{ t('avgOrderValue') }}</span>
              <h3 class="text-h5 font-weight-black text-primary mt-1">
                {{ accountingData.averageOrderValue.toFixed(2) }} EGP
              </h3>
            </v-card>
          </v-col>

          <v-col cols="12" sm="6" md="3">
            <v-card class="pa-4 bg-surface border rounded-xl elevation-3 border-left-bronze">
              <span class="text-caption text-copper-muted font-weight-bold text-uppercase">{{ t('totalItemsSold') }}</span>
              <h3 class="text-h5 font-weight-black text-secondary mt-1">
                {{ accountingData.totalItemsSold }}
              </h3>
            </v-card>
          </v-col>
        </v-row>

        <v-row>
          <!-- Left: Sales by Category table -->
          <v-col cols="12" md="8">
            <v-card class="pa-4 rounded-xl border bg-surface">
              <h4 class="text-subtitle-1 font-weight-bold text-bronze-gradient mb-3">{{ t('salesByCategory') }}</h4>
              <v-table class="bg-transparent text-copper-muted">
                <thead>
                  <tr>
                    <th class="text-left font-weight-bold text-primary">{{ t('categoryHeader') }}</th>
                    <th class="text-left font-weight-bold text-primary">{{ t('qtyHeader') }}</th>
                    <th class="text-left font-weight-bold text-primary">{{ t('salesHeader') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="cat in accountingData.salesByCategory" :key="cat.category">
                    <td class="font-weight-bold">{{ cat.category }}</td>
                    <td>{{ cat.quantity }}</td>
                    <td class="font-weight-bold text-primary">{{ cat.sales.toFixed(2) }} EGP</td>
                  </tr>
                  <tr v-if="accountingData.salesByCategory.length === 0">
                    <td colspan="3" class="text-center py-4">{{ t('noCategorySales') }}</td>
                  </tr>
                </tbody>
              </v-table>
            </v-card>
          </v-col>

          <!-- Right: Best Sellers List -->
          <v-col cols="12" md="4">
            <v-card class="pa-4 rounded-xl border bg-surface">
              <h4 class="text-subtitle-1 font-weight-bold text-bronze-gradient mb-3">{{ t('bestSellers') }}</h4>
              <v-list class="bg-transparent pa-0">
                <v-list-item
                  v-for="(item, index) in accountingData.bestSellers"
                  :key="index"
                  class="px-0 py-2 border-bottom"
                >
                  <template v-slot:prepend>
                    <v-avatar color="primary" variant="tonal" size="32" class="mr-3 font-weight-black">
                      {{ index + 1 }}
                    </v-avatar>
                  </template>
                  <v-list-item-title class="font-weight-bold text-copper-muted">
                    {{ item.name }}
                  </v-list-item-title>
                  <template v-slot:append>
                    <v-chip color="secondary" size="small" class="font-weight-bold">
                      {{ t('soldCount', { count: item.quantity }) }}
                    </v-chip>
                  </template>
                </v-list-item>
                <div v-if="accountingData.bestSellers.length === 0" class="text-center py-8 text-copper-muted">
                  {{ t('noSalesData') }}
                </div>
              </v-list>
            </v-card>
          </v-col>
        </v-row>
      </div>
    </v-card>

    <!-- Section 2: Range Sales Line Chart (Existing) -->
    <v-card class="elevation-6 rounded-xl pa-6 bg-surface border-bronze">
      <div class="mb-4">
        <h3 class="text-h6 font-weight-bold text-bronze-gradient">{{ t('dailyRevenueChart') }}</h3>
        <p class="text-caption text-copper-muted">{{ t('dailyChartSub') }}</p>
      </div>

      <!-- Filters Row -->
      <v-row align="center" class="mb-6">
        <v-col cols="12" sm="4">
          <v-text-field
            v-model="startDate"
            :label="t('startDate')"
            type="date"
            variant="outlined"
            density="comfortable"
            hide-details
            class="bg-surface rounded-lg border-bronze"
            color="primary"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="4">
          <v-text-field
            v-model="endDate"
            :label="t('endDate')"
            type="date"
            variant="outlined"
            density="comfortable"
            hide-details
            class="bg-surface rounded-lg border-bronze"
            color="primary"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="4">
          <v-btn
            color="primary"
            size="large"
            block
            class="font-weight-bold rounded-lg"
            prepend-icon="mdi-chart-areaspline"
            @click="loadReport"
          >
            {{ t('generateChart') }}
          </v-btn>
        </v-col>
      </v-row>

      <!-- Chart Visualization -->
      <div v-if="adminStore.loading" class="d-flex justify-center my-12">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
      </div>

      <div v-else>
        <div class="d-flex justify-space-between align-center mb-4">
          <h3 class="text-subtitle-1 font-weight-bold text-bronze-gradient">{{ t('rangeRevenue') }}</h3>
          <span class="text-h6 font-weight-black text-primary">
            {{ totalRangeSales.toFixed(2) }} EGP
          </span>
        </div>
        
        <div class="chart-container" style="position: relative; height: 350px;">
          <Line v-if="chartData.datasets[0].data.length > 0" :data="chartData" :options="chartOptions" />
          <div v-else class="d-flex align-center justify-center fill-height">
            <span class="text-copper-muted">{{ t('noSalesRange') }}</span>
          </div>
        </div>
      </div>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAdminStore } from '../../stores/admin'
import { useLocaleStore } from '../../stores/locale'
import { Line } from 'vue-chartjs'
import api from '../../api'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale)

const adminStore = useAdminStore()
const { t } = useLocaleStore()

interface AccountingReport {
  totalOrders: number
  totalSales: number
  averageOrderValue: number
  totalItemsSold: number
  bestSellers: { name: string; quantity: number }[]
  salesByCategory: { category: string; sales: number; quantity: number }[]
}

const period = ref('today')
const accountingData = ref<AccountingReport | null>(null)
const loadingAccounting = ref(false)

const loadAccounting = async () => {
  loadingAccounting.value = true
  try {
    const response = await api.get<AccountingReport>('/api/reports/accounting', {
      params: { period: period.value }
    })
    accountingData.value = response.data
  } catch (error) {
    console.error(error)
  } finally {
    loadingAccounting.value = false
  }
}

// Default date range: 30 days ago to today
const today = new Date()
const thirtyDaysAgo = new Date()
thirtyDaysAgo.setDate(today.getDate() - 30)

const formatDate = (d: Date) => d.toISOString().split('T')[0]

const startDate = ref(formatDate(thirtyDaysAgo))
const endDate = ref(formatDate(today))

const loadReport = () => {
  if (startDate.value && endDate.value) {
    adminStore.fetchSalesReport(startDate.value, endDate.value)
  }
}

onMounted(() => {
  loadAccounting()
  loadReport()
})

const totalRangeSales = computed(() => {
  return adminStore.salesData.reduce((sum, item) => sum + item.sales, 0)
})

// Build Chart Data
const chartData = computed(() => {
  const dataPoints = adminStore.salesData || []
  return {
    labels: dataPoints.map((item) => item.date),
    datasets: [
      {
        label: t('dailyRevenueChart') + ' (EGP)',
        borderColor: '#D49B54', // Kalmera bronze
        backgroundColor: 'rgba(212, 155, 84, 0.1)',
        data: dataPoints.map((item) => item.sales),
        tension: 0.2,
        fill: true,
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
        color: '#BFA893',
        callback: (value: any) => `${value} EGP`,
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
.border-left-bronze {
  border-left: 6px solid #D49B54 !important;
}
.border-bottom {
  border-bottom: 1px solid rgba(212, 155, 84, 0.12);
}
</style>
