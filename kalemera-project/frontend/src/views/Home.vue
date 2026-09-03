<template>
  <div>
    <!-- Hero Banner Section -->
    <v-sheet color="#141210" class="py-8 py-sm-10 px-2 px-sm-4 position-relative border-b-bronze hero-banner overflow-hidden">
      <v-container>
        <v-row align="center" justify="center" class="text-center">
          <v-col cols="12" md="8">
            <!-- Central Shield Logo -->
            <v-img
              src="/logo.webp"
              alt="Calmera Logo"
              max-width="160"
              class="mx-auto mb-4 hero-logo-badge"
              contain
            ></v-img>
            
            <h1 class="text-h4 text-sm-h2 font-weight-black text-bronze-gradient mb-2">
              {{ localeStore.currentLocale === 'ar' ? 'كالميرا' : 'CALMERA' }}
            </h1>
            <p class="text-subtitle-1 text-sm-h6 text-copper-muted font-weight-medium mb-6">
              {{ localeStore.currentLocale === 'ar' ? 'مطعم | ماركت' : 'RESTAURANT & MARKET' }}
            </p>

            <!-- Feature Tags -->
            <div class="d-flex flex-wrap justify-center ga-2 ga-sm-3 mb-6">
              <v-chip color="primary" variant="flat" size="small" size-sm="large" prepend-icon="mdi-silverware-fork-knife" class="font-weight-bold">
                {{ localeStore.t('restaurant') }}
              </v-chip>
              <v-chip color="secondary" variant="flat" size="small" size-sm="large" prepend-icon="mdi-shopping" class="font-weight-bold">
                {{ localeStore.t('market') }}
              </v-chip>
              <v-chip color="accent" variant="outlined" size="small" size-sm="large" prepend-icon="mdi-coffee" class="font-weight-bold text-primary">
                {{ localeStore.t('cafe') }}
              </v-chip>
              <v-chip color="primary" variant="outlined" size="small" size-sm="large" prepend-icon="mdi-fire" class="font-weight-bold">
                {{ localeStore.t('grills') }}
              </v-chip>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </v-sheet>

    <v-container class="py-6 py-sm-8 px-3 px-sm-6">
      <!-- Business Hours Status Banner (OPEN / CLOSED) -->
      <v-alert
        v-if="storeStatusLoaded"
        :type="storeClosed ? 'warning' : 'success'"
        variant="tonal"
        density="compact"
        class="mb-4 rounded-lg"
      >
        <div class="d-flex align-center ga-2 flex-wrap">
          <v-icon>{{ storeClosed ? 'mdi-clock-alert' : 'mdi-clock-check-outline' }}</v-icon>
          <span class="font-weight-bold">
            {{ storeClosed ? localeStore.t('storeClosed') : localeStore.t('storeOpen') }}
          </span>
        </div>
      </v-alert>

      <!-- Search Bar (Always Visible) -->
      <v-row class="mb-6 mb-sm-8" justify="center">
        <v-col cols="12" md="8">
          <v-text-field
            v-model="searchQuery"
            :label="localeStore.t('searchPlaceholder')"
            prepend-inner-icon="mdi-magnify"
            clearable
            variant="outlined"
            density="comfortable"
            hide-details
            class="bg-surface rounded-xl border-bronze search-bar"
            color="primary"
            @input="debouncedSearch"
            @click:clear="clearSearch"
          ></v-text-field>
        </v-col>
      </v-row>

      <!-- Loading State -->
      <div v-if="productStore.loading" class="d-flex justify-center my-12">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
      </div>

      <!-- State 1: Categories View (Default) -->
      <div v-else-if="selectedCategory === null && !searchQuery">
        <div class="text-center mb-6 mb-sm-8">
          <h2 class="text-h5 text-sm-h4 font-weight-black text-bronze-gradient mb-2">{{ localeStore.t('exploreMenu') }}</h2>
          <p class="text-body-2 text-sm-subtitle-1 text-copper-muted">{{ localeStore.t('exploreSub') }}</p>
        </div>

        <v-row>
          <v-col
            v-for="cat in productStore.categories"
            :key="cat.id"
            cols="6"
            sm="4"
            md="3"
            lg="3"
            class="pa-2 pa-sm-3"
          >
            <v-card
              class="category-card rounded-xl overflow-hidden elevation-6 bg-surface border-bronze text-center py-4 py-sm-6 px-2 px-sm-4 cursor-pointer d-flex flex-column align-center justify-center fill-height"
              @click="selectCategory(cat)"
            >
              <v-avatar color="primary" variant="tonal" size="48" size-sm="64" class="mb-2 mb-sm-4">
                <v-icon size="28" size-sm="36" color="primary">{{ getCategoryIcon(cat.name) }}</v-icon>
              </v-avatar>
              
              <div class="text-subtitle-2 text-sm-h6 font-weight-black text-bronze-gradient mb-2 text-break-word line-clamp-2">
                {{ getCategoryDisplayName(cat.name) }}
              </div>
              
              <v-chip color="secondary" size="x-small" class="font-weight-bold text-primary px-2 px-sm-3">
                {{ cat.product_count || 0 }} {{ localeStore.currentLocale === 'ar' ? 'منتج' : 'Items' }}
              </v-chip>
            </v-card>
          </v-col>
        </v-row>
      </div>

      <!-- State 2: Products Inside Category or Search Results -->
      <div v-else>
        <!-- Navigation Header -->
        <div class="d-flex flex-column flex-sm-row align-start align-sm-center justify-space-between mb-6 ga-4">
          <v-btn
            variant="tonal"
            color="primary"
            :prepend-icon="localeStore.currentLocale === 'ar' ? 'mdi-arrow-right' : 'mdi-arrow-left'"
            class="font-weight-bold rounded-lg"
            @click="backToCategories"
          >
            {{ localeStore.t('backToCategories') }}
          </v-btn>

          <div>
            <h2 class="text-h4 font-weight-black text-bronze-gradient mb-1">
              {{ searchHeaderTitle }}
            </h2>
          </div>
        </div>

        <!-- Sort and Controls (Only in list view) -->
        <v-row class="mb-6" justify="end">
          <v-col cols="12" sm="6" md="4" lg="3">
            <v-select
              v-model="selectedSort"
              :items="sortOptions"
              item-title="label"
              item-value="value"
              :label="localeStore.t('sortBy')"
              variant="outlined"
              density="comfortable"
              hide-details
              class="bg-surface rounded-lg border-bronze"
              color="primary"
              prepend-inner-icon="mdi-sort"
              @update:model-value="onSortChange"
            ></v-select>
          </v-col>
        </v-row>

        <!-- Empty State inside list -->
        <div v-if="productStore.products.length === 0" class="text-center my-12 bg-surface pa-8 rounded-xl border-bronze mx-4">
          <v-icon size="64" color="copper-muted">mdi-food-off</v-icon>
          <h3 class="text-h5 text-primary font-weight-bold mt-4">{{ localeStore.t('noProductsTitle') }}</h3>
          <p class="text-copper-muted">{{ localeStore.t('noProductsSub') }}</p>
        </div>

        <!-- Product Grid -->
        <v-row v-else>
          <v-col
            v-for="product in productStore.products"
            :key="product.id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
            <ProductCard
              :product="product"
              :category-name="getCategoryName(product.category_id)"
              @add-to-cart="addToCart"
            />
          </v-col>
        </v-row>

        <!-- Pagination -->
        <v-row v-if="totalPages > 1" justify="center" class="mt-8">
          <v-pagination
            v-model="page"
            :length="totalPages"
            color="primary"
            active-color="secondary"
            @update:model-value="onPageChange"
          ></v-pagination>
        </v-row>
      </div>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useProductStore } from '../stores/products'
import { useLocaleStore } from '../stores/locale'
import type { Product, Category } from '../types'
import { useCartStore } from '../stores/cart'
import ProductCard from '../components/ProductCard.vue'
import { API_BASE_URL } from '../api'

const productStore = useProductStore()
const cartStore = useCartStore()
const localeStore = useLocaleStore()

const searchQuery = ref('')
const selectedCategory = ref<number | null>(null)
const selectedSort = ref('name_asc')
const page = ref(1)
const size = 8 // items per page

const storeClosed = ref(false)
const storeStatusLoaded = ref(false)
let statusTimer: number | null = null

const checkBusinessHours = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/business-hours`)
    const data = await res.json()
    storeClosed.value = Boolean(data?.closed)
    storeStatusLoaded.value = true
  } catch (e) {
    storeStatusLoaded.value = false
  }
}

// Static Category metadata with VALID MDI icons (Salads updated to mdi-bowl-mix)
const categoryMeta: Record<string, { nameAr: string; nameEn: string; icon: string }> = {
  "Pizza": { nameAr: "البيتزا", nameEn: "Pizza", icon: "mdi-pizza" },
  "Crepe": { nameAr: "الكريب", nameEn: "Crepe", icon: "mdi-food-croissant" },
  "Burgers": { nameAr: "البرجر", nameEn: "Burgers", icon: "mdi-hamburger" },
  "Chicken Sandwiches": { nameAr: "سندوتشات فراخ", nameEn: "Chicken Sandwiches", icon: "mdi-food-drumstick" },
  "Meat Sandwiches": { nameAr: "سندوتشات لحوم", nameEn: "Meat Sandwiches", icon: "mdi-food-steak" },
  "Meals": { nameAr: "الوجبات", nameEn: "Meals", icon: "mdi-silverware-fork-knife" },
  "Rice & Pasta": { nameAr: "أرز ومكرونة", nameEn: "Rice & Pasta", icon: "mdi-pasta" },
  "Salads": { nameAr: "السلطات", nameEn: "Salads", icon: "mdi-bowl-mix" },
  "Potato": { nameAr: "البطاطس", nameEn: "Potato", icon: "mdi-french-fries" },
  "Sauces": { nameAr: "الصوصات", nameEn: "Sauces", icon: "mdi-soy-sauce" },
  "Drinks": { nameAr: "المشروبات", nameEn: "Drinks", icon: "mdi-cup-water" },
  "Market": { nameAr: "الماركت", nameEn: "Market", icon: "mdi-shopping" },
  "الخضار والفاكهة": { nameAr: "الخضار والفاكهة", nameEn: "Vegetables & Fruits", icon: "mdi-vegetable" },
  "العروض": { nameAr: "العروض", nameEn: "Offers", icon: "mdi-tag" }
}

const getCategoryIcon = (name: string) => {
  return categoryMeta[name]?.icon || 'mdi-food'
}

const getCategoryAr = (name: string) => {
  return categoryMeta[name]?.nameAr || name
}

const getCategoryEn = (name: string) => {
  return categoryMeta[name]?.nameEn || name
}

const getCategoryDisplayName = (name: string) => {
  return localeStore.currentLocale === 'en' ? getCategoryEn(name) : getCategoryAr(name)
}

const sortOptions = computed(() => [
  { label: localeStore.currentLocale === 'en' ? 'Name: A to Z' : 'الاسم: أ إلى ي', value: 'name_asc' },
  { label: localeStore.currentLocale === 'en' ? 'Name: Z to A' : 'الاسم: ي إلى أ', value: 'name_desc' },
  { label: localeStore.currentLocale === 'en' ? 'Price: Low to High' : 'السعر: من الأقل إلى الأعلى', value: 'price_asc' },
  { label: localeStore.currentLocale === 'en' ? 'Price: High to Low' : 'السعر: من الأعلى إلى الأقل', value: 'price_desc' },
  { label: localeStore.currentLocale === 'en' ? 'Newest First' : 'الأحدث', value: 'newest' },
  { label: localeStore.currentLocale === 'en' ? 'Best Selling' : 'الأكثر مبيعاً', value: 'best_selling' },
])

const parseSortParams = () => {
  const val = selectedSort.value
  if (val === 'newest') return { sort_by: 'newest', sort_order: 'desc' }
  if (val === 'best_selling') return { sort_by: 'best_selling', sort_order: 'desc' }
  const [sort_by, sort_order] = val.split('_')
  return { sort_by, sort_order }
}

const loadProducts = () => {
  if (selectedCategory.value === null && !searchQuery.value) return

  const { sort_by, sort_order } = parseSortParams()
  productStore.fetchProducts({
    search: searchQuery.value || undefined,
    category: selectedCategory.value || undefined,
    sort_by,
    sort_order,
    page: page.value,
    size: size,
  })
}

const searchHeaderTitle = computed(() => {
  if (searchQuery.value) {
    return localeStore.currentLocale === 'en'
      ? `Search Results for: "${searchQuery.value}"`
      : `نتائج البحث عن: "${searchQuery.value}"`
  }
  const cat = productStore.categories.find(c => c.id === selectedCategory.value)
  return cat ? getCategoryDisplayName(cat.name) : ''
})

const selectCategory = (cat: Category) => {
  selectedCategory.value = cat.id
  page.value = 1
  loadProducts()
}

const backToCategories = () => {
  selectedCategory.value = null
  searchQuery.value = ''
  page.value = 1
}

const clearSearch = () => {
  searchQuery.value = ''
  if (selectedCategory.value !== null) {
    loadProducts()
  }
}

onMounted(() => {
  productStore.fetchCategories()
  checkBusinessHours()
  statusTimer = window.setInterval(checkBusinessHours, 60000)
})

onUnmounted(() => {
  if (statusTimer) window.clearInterval(statusTimer)
})

const totalPages = computed(() => {
  return Math.ceil(productStore.totalProducts / size)
})

const getCategoryName = (categoryId: number) => {
  const cat = productStore.categories.find((c) => c.id == categoryId)
  if (!cat) return 'Unknown'
  return getCategoryDisplayName(cat.name)
}

let searchTimeout: number | null = null
const debouncedSearch = () => {
  if (searchTimeout) window.clearTimeout(searchTimeout)
  searchTimeout = window.setTimeout(() => {
    page.value = 1
    loadProducts()
  }, 500)
}

const onSortChange = () => {
  page.value = 1
  loadProducts()
}

const onPageChange = (val: number) => {
  page.value = val
  loadProducts()
}

const addToCart = (product: Product, variant?: any) => {
  cartStore.addToCart(product, 1, variant)
}
</script>

<style scoped>
.hero-logo-badge {
  filter: drop-shadow(0 0 20px rgba(212, 155, 84, 0.4));
  transition: transform 0.3s ease;
}

.hero-logo-badge:hover {
  transform: scale(1.05);
}

.hero-banner {
  background: radial-gradient(circle at center, #241F1A 0%, #141210 100%);
}

.category-card {
  transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s ease, border-color 0.3s ease;
}

.category-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 24px rgba(212, 155, 84, 0.25) !important;
  border-color: rgba(212, 155, 84, 0.6) !important;
}

.search-bar {
  transition: border-color 0.3s ease;
}
</style>
