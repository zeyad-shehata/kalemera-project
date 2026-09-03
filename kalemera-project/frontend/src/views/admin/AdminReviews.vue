<template>
  <v-container class="pa-0">
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-black text-bronze-gradient">{{ t('reviewsTitle') }}</h1>
        <p class="text-copper-muted">{{ t('reviewsSub') }}</p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="d-flex justify-center my-12">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <!-- Error State -->
    <v-alert v-else-if="error" type="error" variant="tonal" class="rounded-xl">
      {{ error }}
    </v-alert>

    <!-- Empty State -->
    <v-card v-else-if="reviews.length === 0" class="elevation-6 rounded-xl pa-12 bg-surface border-bronze text-center">
      <v-icon size="64" color="grey-lighten-1">mdi-star-outline</v-icon>
      <h3 class="text-h6 text-copper-muted mt-4">{{ t('noReviewsYet') }}</h3>
    </v-card>

    <!-- Reviews List -->
    <v-card v-else class="elevation-6 rounded-xl pa-4 pa-sm-6 bg-surface border-bronze">
      <v-list class="bg-transparent pa-0">
        <v-list-item
          v-for="review in reviews"
          :key="review.id"
          class="px-0 py-3 border-bottom"
        >
          <div class="d-flex align-center justify-space-between flex-wrap ga-2 mb-1">
            <div class="d-flex align-center ga-2">
              <v-rating :model-value="review.rating" readonly density="compact" size="small" color="amber"></v-rating>
              <span class="font-weight-bold text-copper-muted">{{ review.reviewer_name || t('reviewerLabel') }}</span>
            </div>
            <div class="d-flex align-center ga-2">
              <v-chip size="small" color="primary" variant="tonal" class="font-weight-bold">
                {{ t('orderRefLabel') }} #{{ review.order_id }}
              </v-chip>
              <span class="text-caption text-copper-muted">{{ formatDate(review.created_at) }}</span>
            </div>
          </div>
          <p v-if="review.comment" class="text-body-2 font-italic text-copper-muted mb-0">"{{ review.comment }}"</p>
        </v-list-item>
      </v-list>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useLocaleStore } from '../../stores/locale'
import api from '../../api'
import { formatAppDate } from '../../utils/date'

interface AdminReview {
  id: number
  order_id: number
  rating: number
  comment: string | null
  created_at: string
  reviewer_name: string | null
}

const localeStore = useLocaleStore()
const { t } = localeStore

const reviews = ref<AdminReview[]>([])
const loading = ref(false)
const error = ref('')

const loadReviews = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await api.get<AdminReview[]>('/api/reviews/admin')
    reviews.value = response.data
  } catch (e) {
    error.value = t('failLoadReviews')
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr: string) => {
  return formatAppDate(dateStr, localeStore.currentLocale)
}

onMounted(() => {
  loadReviews()
})
</script>

<style scoped>
.border-bottom {
  border-bottom: 1px solid rgba(212, 155, 84, 0.12);
}
</style>
