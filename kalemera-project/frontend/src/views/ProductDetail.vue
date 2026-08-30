<template>
  <v-container class="py-12">
    <!-- Loading State -->
    <div v-if="productStore.loading" class="d-flex justify-center my-12">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <!-- Error/Not Found State -->
    <v-row v-else-if="!productStore.currentProduct" justify="center" class="my-12">
      <v-col cols="12" class="text-center">
        <v-icon size="64" color="error">mdi-alert-circle-outline</v-icon>
        <h3 class="text-h6 mt-2">{{ t('orderNotFound') }}</h3>
        <v-btn color="primary" class="mt-4" to="/">{{ t('backToCatalog') }}</v-btn>
      </v-col>
    </v-row>

    <!-- Product Detail View -->
    <v-row v-else class="mt-4">
      <!-- Image Carousel Section -->
      <v-col cols="12" md="6">
        <v-card class="elevation-3 rounded-lg overflow-hidden">
          <!-- Even though there is a single image path, we use v-carousel to support multiple slides or fallbacks -->
          <v-carousel hide-delimiters show-arrows="hover" height="400">
            <v-carousel-item
              :src="productStore.currentProduct.image_path ? `${apiBaseUrl}${productStore.currentProduct.image_path}` : 'https://placehold.co/600x450?text=No+Image'"
              cover
            ></v-carousel-item>
            <!-- Carousel placeholders for rich aesthetic effect -->
            <v-carousel-item
              v-if="!productStore.currentProduct.image_path"
              src="https://placehold.co/600x450?text=Alternate+View+1"
              cover
            ></v-carousel-item>
          </v-carousel>
        </v-card>
      </v-col>

      <!-- Information & Purchase Section -->
      <v-col cols="12" md="6" class="d-flex flex-column">
        <div>
          <!-- Category Chip -->
          <v-chip color="secondary" class="font-weight-bold mb-3">
            {{ categoryName }}
          </v-chip>
 
          <!-- Product Name -->
          <h1 class="text-h4 font-weight-bold mb-2">
            {{ localeStore.currentLocale === 'en' && productStore.currentProduct.name_en ? productStore.currentProduct.name_en : productStore.currentProduct.name }}
          </h1>
 
          <!-- Rating Placeholder for Premium feel -->
          <div class="d-flex align-center mb-4">
            <v-rating :model-value="4.5" color="amber" density="compact" readonly half-increments></v-rating>
            <span class="text-subtitle-2 text-grey ml-2">({{ t('reviewsCount', { count: 45 }) }})</span>
          </div>
 
          <v-divider class="mb-4"></v-divider>
 
          <!-- Price & Stock -->
          <div class="d-flex align-center mb-6">
            <span class="text-h4 text-primary font-weight-black mr-6">{{ displayPrice }} EGP</span>
            <v-chip :color="stockColor" size="small" class="font-weight-bold">
              {{ stockText }}
            </v-chip>
          </div>
 
          <!-- Size Selection -->
          <div v-if="productStore.currentProduct.variants && productStore.currentProduct.variants.length > 0" class="mb-6">
            <h3 class="text-subtitle-1 font-weight-bold text-primary mb-2">{{ t('chooseSize') }}</h3>
            <v-radio-group v-model="selectedVariantId" inline hide-details color="primary">
              <v-radio
                v-for="variant in productStore.currentProduct.variants"
                :key="variant.id"
                :label="`${t('sizePrefix')} ${variant.name} — ${variant.price.toFixed(2)} EGP`"
                :value="variant.id"
                class="font-weight-bold"
              ></v-radio>
            </v-radio-group>
          </div>
 
          <!-- Description -->
          <h2 class="text-subtitle-1 font-weight-bold mb-2">{{ t('descLabel') }}</h2>
          <p class="text-body-1 text-grey-darken-2 mb-6" style="line-height: 1.6;">
            {{ (localeStore.currentLocale === 'en' && productStore.currentProduct.description_en ? productStore.currentProduct.description_en : productStore.currentProduct.description) || t('noDesc') }}
          </p>
        </div>
 
        <v-spacer></v-spacer>
 
        <!-- Actions -->
        <v-card class="pa-4 bg-grey-lighten-5 rounded-lg border">
          <v-row align="center">
            <v-col cols="4">
              <v-select
                v-model="qty"
                :items="qtyOptions"
                :label="t('quantity')"
                density="comfortable"
                variant="outlined"
                hide-details
                :disabled="productStore.currentProduct.stock <= 0"
              ></v-select>
            </v-col>
            <v-col cols="8">
              <v-btn
                color="primary"
                prepend-icon="mdi-cart-plus"
                size="large"
                block
                class="font-weight-bold text-uppercase"
                :disabled="productStore.currentProduct.stock <= 0"
                @click="addToCart"
              >
                {{ productStore.currentProduct.stock > 0 ? t('addToCart') : t('outOfStock') }}
              </v-btn>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProductStore } from '../stores/products'
import { useLocaleStore } from '../stores/locale'
import { useCartStore } from '../stores/cart'
import { API_BASE_URL } from '../api'

const route = useRoute()
const productStore = useProductStore()
const cartStore = useCartStore()
const localeStore = useLocaleStore()
const { t } = localeStore
 
const apiBaseUrl = API_BASE_URL
const qty = ref(1)
const selectedVariantId = ref<number | null>(null)
 
const productId = computed(() => Number(route.params.id))
 
onMounted(async () => {
  productStore.fetchCategories()
  await productStore.fetchProduct(productId.value)
  if (productStore.currentProduct?.variants && productStore.currentProduct.variants.length > 0) {
    selectedVariantId.value = productStore.currentProduct.variants[0].id
  }
})
 
const displayPrice = computed(() => {
  if (!productStore.currentProduct) return '0.00'
  if (productStore.currentProduct.variants && productStore.currentProduct.variants.length > 0) {
    const selected = productStore.currentProduct.variants.find(v => v.id === selectedVariantId.value)
    return selected ? selected.price.toFixed(2) : productStore.currentProduct.price.toFixed(2)
  }
  return productStore.currentProduct.price.toFixed(2)
})
 
const categoryName = computed(() => {
  if (!productStore.currentProduct) return 'Unknown'
  const cat = productStore.categories.find((c) => c.id == productStore.currentProduct?.category_id)
  if (!cat) return 'Unknown'
  // Static Category metadata mapping for consistency with Home.vue
  const categoryMeta: Record<string, { nameAr: string; nameEn: string }> = {
    "Pizza": { nameAr: "البيتزا", nameEn: "Pizza" },
    "Crepe": { nameAr: "الكريب", nameEn: "Crepe" },
    "Burgers": { nameAr: "البرجر", nameEn: "Burgers" },
    "Chicken Sandwiches": { nameAr: "سندوتشات فراخ", nameEn: "Chicken Sandwiches" },
    "Meat Sandwiches": { nameAr: "سندوتشات لحوم", nameEn: "Meat Sandwiches" },
    "Meals": { nameAr: "الوجبات", nameEn: "Meals" },
    "Rice & Pasta": { nameAr: "أرز ومكرونة", nameEn: "Rice & Pasta" },
    "Salads": { nameAr: "السلطات", nameEn: "Salads" },
    "Potato": { nameAr: "البطاطس", nameEn: "Potato" },
    "Sauces": { nameAr: "الصوصات", nameEn: "Sauces" },
    "Drinks": { nameAr: "المشروبات", nameEn: "Drinks" },
    "Market": { nameAr: "الماركت", nameEn: "Market" }
  }
  const meta = categoryMeta[cat.name]
  return localeStore.currentLocale === 'en' ? (meta?.nameEn || cat.name) : (meta?.nameAr || cat.name)
})
 
const stockText = computed(() => {
  const stock = productStore.currentProduct?.stock || 0
  if (stock <= 0) return t('outOfStock')
  if (stock < 5) return t('onlyLeft', { count: stock })
  return t('inStock')
})

const stockColor = computed(() => {
  const stock = productStore.currentProduct?.stock || 0
  if (stock <= 0) return 'error'
  if (stock < 5) return 'warning'
  return 'success'
})

const qtyOptions = computed(() => {
  const stock = productStore.currentProduct?.stock || 0
  const max = Math.min(10, stock)
  return Array.from({ length: max }, (_, i) => i + 1)
})

const addToCart = () => {
  if (productStore.currentProduct) {
    const selectedVariant = productStore.currentProduct.variants?.find(v => v.id === selectedVariantId.value)
    cartStore.addToCart(productStore.currentProduct, qty.value, selectedVariant)
  }
}
</script>

