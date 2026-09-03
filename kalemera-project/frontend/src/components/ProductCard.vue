<template>
  <v-card class="d-flex flex-column h-100 product-card rounded-xl overflow-hidden bg-surface border-bronze elevation-4">
    <!-- Product Image -->
    <div class="position-relative">
      <v-img
        :src="productImageSrc"
        :alt="displayName"
        height="210"
        cover
        class="bg-surface-variant"
      ></v-img>
      <v-chip
        size="small"
        color="primary"
        variant="flat"
        class="position-absolute font-weight-bold"
        style="top: 12px; right: 12px; z-index: 2;"
        v-if="categoryName"
      >
        {{ categoryName }}
      </v-chip>
    </div>

    <!-- Product Details -->
    <v-card-item class="flex-grow-1 pa-4">
      <v-card-title class="font-weight-bold text-h6 text-bronze-gradient text-truncate mb-1">
        {{ displayName }}
      </v-card-title>
      
      <div class="d-flex align-center justify-space-between mt-2 mb-3">
        <span class="text-h5 text-secondary font-weight-black" v-if="product.variants && product.variants.length > 0">
          {{ minVariantPrice }} EGP
        </span>
        <span class="text-h5 text-secondary font-weight-black" v-else>
          {{ product.price.toFixed(2) }} EGP
        </span>
        
        <span :class="product.stock > 0 ? 'text-success' : 'text-error'" class="text-caption font-weight-bold">
          {{ product.stock > 0 ? t('inStock') : t('outOfStock') }}
        </span>
      </div>
      
      <p class="text-caption text-copper-muted line-clamp-3 mb-0">
        {{ displayDescription || t('noDesc') }}
      </p>
    </v-card-item>

    <v-divider class="border-bronze"></v-divider>

    <!-- Card Actions -->
    <v-card-actions class="pa-4 bg-surface-variant">
      <v-btn
        variant="outlined"
        color="primary"
        size="small"
        class="font-weight-bold rounded-lg"
        :to="`/product/${product.id}`"
      >
        {{ t('details') }}
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn
        color="secondary"
        variant="flat"
        prepend-icon="mdi-cart-plus"
        class="font-weight-bold rounded-lg"
        :disabled="product.stock <= 0"
        @click="handleAddToCart"
      >
        {{ product.stock > 0 ? (product.variants && product.variants.length > 0 ? t('chooseSize') || t('addToCart') : t('addToCart')) : t('notAvailable') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Product, ProductVariant } from '../types'
import { useLocaleStore } from '../stores/locale'
import { resolveImageUrl } from '../utils/image'

const props = defineProps<{
  product: Product
  categoryName?: string
}>()

const emit = defineEmits<{
  (e: 'add-to-cart', product: Product, variant?: ProductVariant): void
}>()

const handleAddToCart = () => {
  const defaultVariant = props.product.variants && props.product.variants.length > 0 ? props.product.variants[0] : undefined
  emit('add-to-cart', props.product, defaultVariant)
}

const localeStore = useLocaleStore()
const { t } = localeStore

const displayName = computed(() => {
  if (localeStore.currentLocale === 'en' && props.product.name_en) {
    return props.product.name_en
  }
  return props.product.name
})

const displayDescription = computed(() => {
  if (localeStore.currentLocale === 'en' && props.product.description_en) {
    return props.product.description_en
  }
  return props.product.description
})

const productImageSrc = computed(() => {
  return resolveImageUrl(props.product.image_path)
})

const minVariantPrice = computed(() => {
  if (!props.product.variants || props.product.variants.length === 0) return '0.00'
  const min = Math.min(...props.product.variants.map((v) => v.price))
  return min.toFixed(2)
})
</script>

<style scoped>
.product-card {
  transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s ease, border-color 0.3s ease;
}

.product-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 24px rgba(212, 155, 84, 0.25) !important;
  border-color: rgba(212, 155, 84, 0.6) !important;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  height: 54px;
}
</style>
