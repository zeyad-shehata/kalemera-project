<template>
  <v-container class="py-12">
    <h1 class="text-h4 font-weight-bold mb-6">{{ t('shoppingCart') }}</h1>

    <!-- Empty Cart State -->
    <v-row v-if="cartStore.items.length === 0" justify="center" class="my-12">
      <v-col cols="12" class="text-center">
        <v-icon size="80" color="grey-lighten-1">mdi-cart-outline</v-icon>
        <h3 class="text-h6 text-grey mt-4">{{ t('emptyCartTitle') }}</h3>
        <p class="text-grey mb-6">{{ t('emptyCartSubtitle') }}</p>
        <v-btn color="primary" size="large" to="/" class="font-weight-bold">{{ t('startShopping') }}</v-btn>
      </v-col>
    </v-row>

    <!-- Cart Content -->
    <v-row v-else>
      <!-- Cart Items Table -->
      <v-col cols="12" md="8">
        <v-card class="elevation-3 rounded-lg overflow-hidden overflow-x-auto">
          <v-table class="table-responsive">
            <thead>
              <tr>
                <th class="text-left font-weight-bold">{{ t('product') }}</th>
                <th class="text-center font-weight-bold">{{ t('price') }}</th>
                <th class="text-center font-weight-bold" style="width: 150px;">{{ t('quantity') }}</th>
                <th class="text-right font-weight-bold">{{ t('subtotal') }}</th>
                <th class="text-center font-weight-bold"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in cartStore.items" :key="item.product.id + '-' + (item.variant?.id || 'none')">
                <!-- Product Column -->
                <td class="py-4">
                  <div class="d-flex align-center">
                    <v-img
                      :src="resolveImageUrl(item.product.image_path, 'https://placehold.co/100x75?text=No+Image')"
                      :alt="localeStore.currentLocale === 'en' && item.product.name_en ? item.product.name_en : item.product.name"
                      width="70"
                      height="50"
                      cover
                      class="rounded-lg mr-4 bg-grey-lighten-2"
                    ></v-img>
                    <div>
                      <div class="font-weight-bold text-subtitle-2 d-flex align-center">
                        {{ localeStore.currentLocale === 'en' && item.product.name_en ? item.product.name_en : item.product.name }}
                        <v-chip size="x-small" color="primary" class="ml-2 font-weight-bold" v-if="item.variant">
                          {{ t('sizePrefix') }} {{ item.variant.name }}
                        </v-chip>
                      </div>
                      <div class="text-caption text-grey">{{ t('stockLabel') }} {{ item.product.stock }}</div>
                    </div>
                  </div>
                </td>
                
                <!-- Price Column -->
                <td class="text-center py-4">{{ (item.variant ? item.variant.price : item.product.price).toFixed(2) }} EGP</td>
                
                <!-- Quantity Column -->
                <td class="text-center py-4">
                  <div class="d-flex align-center justify-center">
                    <v-btn
                      icon
                      variant="text"
                      density="comfortable"
                      :disabled="item.quantity <= 1"
                      @click="cartStore.updateQuantity(item.product.id, item.variant?.id, item.quantity - 1)"
                    >
                      <v-icon size="small">mdi-minus</v-icon>
                    </v-btn>
                    <span class="mx-3 font-weight-bold">{{ item.quantity }}</span>
                    <v-btn
                      icon
                      variant="text"
                      density="comfortable"
                      :disabled="item.quantity >= item.product.stock"
                      @click="cartStore.updateQuantity(item.product.id, item.variant?.id, item.quantity + 1)"
                    >
                      <v-icon size="small">mdi-plus</v-icon>
                    </v-btn>
                  </div>
                </td>
                
                <!-- Subtotal Column -->
                <td class="text-right font-weight-bold py-4">
                  {{ ((item.variant ? item.variant.price : item.product.price) * item.quantity).toFixed(2) }} EGP
                </td>
                
                <!-- Actions Column -->
                <td class="text-center py-4">
                  <v-btn
                    icon
                    variant="text"
                    color="error"
                    density="comfortable"
                    @click="cartStore.removeFromCart(item.product.id, item.variant?.id)"
                  >
                    <v-icon size="small">mdi-trash-can</v-icon>
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>

      <!-- Cart Summary Column -->
      <v-col cols="12" md="4">
        <v-card class="elevation-3 rounded-lg pa-6 bg-grey-lighten-5 border">
          <h2 class="text-h6 font-weight-bold mb-4">{{ t('orderSummary') }}</h2>
          
          <div class="d-flex justify-space-between mb-3 text-subtitle-1">
            <span>{{ t('totalItems') }}</span>
            <span class="font-weight-bold">{{ cartStore.itemCount }}</span>
          </div>

          <div class="d-flex justify-space-between mb-4 text-subtitle-1">
            <span>{{ t('subtotal') }}:</span>
            <span class="font-weight-bold">{{ cartStore.subtotal.toFixed(2) }} EGP</span>
          </div>

          <v-divider class="mb-4"></v-divider>

          <div class="d-flex justify-space-between mb-6 text-h6 font-weight-bold">
            <span>{{ t('estTotal') }}</span>
            <span class="color-primary">{{ cartStore.subtotal.toFixed(2) }} EGP</span>
          </div>

          <v-btn
            color="primary"
            size="large"
            block
            class="font-weight-bold text-uppercase rounded-lg"
            to="/checkout"
          >
            {{ t('proceedCheckout') }}
          </v-btn>
          
          <v-btn
            variant="text"
            color="secondary"
            block
            class="font-weight-bold text-uppercase rounded-lg mt-2"
            to="/"
          >
            {{ t('continueShopping') }}
          </v-btn>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useCartStore } from '../stores/cart'
import { useLocaleStore } from '../stores/locale'
import { resolveImageUrl } from '../utils/image'

const cartStore = useCartStore()
const localeStore = useLocaleStore()
const { t } = localeStore
</script>
