<template>
  <v-container class="pa-0">
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-black text-bronze-gradient">{{ t('manageProducts') }}</h1>
        <p class="text-copper-muted">{{ t('productsSub') }}</p>
      </div>
      <v-btn color="primary" prepend-icon="mdi-plus" class="rounded-lg font-weight-bold" @click="openCreateDialog">
        {{ t('addProduct') }}
      </v-btn>
    </div>

    <!-- Search Field -->
    <v-row class="mb-6" align="center">
      <v-col cols="12" sm="6" md="4">
        <v-text-field
          v-model="searchQuery"
          :label="t('searchPlaceholder')"
          prepend-inner-icon="mdi-magnify"
          clearable
          variant="outlined"
          density="comfortable"
          hide-details
          class="bg-surface rounded-lg border-bronze"
          color="primary"
          @input="debouncedSearch"
          @click:clear="clearSearch"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="6" md="8">
        <p v-if="searchQuery" class="text-caption text-copper-muted">
          {{ productStore.products.length }} result(s)
        </p>
      </v-col>
    </v-row>

    <!-- Products Table -->
    <v-card class="elevation-6 rounded-xl border-bronze bg-surface overflow-x-auto">
      <v-table class="table-responsive bg-transparent text-copper-muted">
        <thead>
          <tr>
            <th class="font-weight-bold text-primary">{{ t('imageHeader') }}</th>
            <th class="font-weight-bold text-primary">{{ t('productName') }}</th>
            <th class="font-weight-bold text-primary">{{ t('category') }}</th>
            <th class="font-weight-bold text-primary">{{ t('price') }}</th>
            <th class="font-weight-bold text-primary">{{ t('stockHeader') }}</th>
            <th class="font-weight-bold text-center text-primary">{{ t('actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in productStore.products" :key="product.id">
            <td>
              <v-img
                :src="resolveImageUrl(product.image_path, 'https://placehold.co/100x75?text=Kalmera')"
                width="60"
                height="45"
                cover
                class="rounded-lg bg-surface-variant my-1"
              ></v-img>
            </td>
            <td class="font-weight-bold">
              <div class="text-copper-muted">{{ product.name }}</div>
              <div class="text-caption text-grey" v-if="product.name_en">{{ product.name_en }}</div>
            </td>
            <td>{{ getCategoryName(product.category_id) }}</td>
            <td class="font-weight-bold text-secondary">{{ product.price.toFixed(2) }} EGP</td>
            <td>
              <v-chip :color="product.stock > 0 ? 'success' : 'error'" size="small" class="font-weight-bold">
                {{ product.stock }}
              </v-chip>
            </td>
            <td class="text-center">
              <v-btn icon variant="text" color="primary" @click="openEditDialog(product)" aria-label="Edit Product">
                <v-icon size="small">mdi-pencil</v-icon>
              </v-btn>
              <v-btn icon variant="text" color="error" @click="deleteProduct(product.id)" aria-label="Delete Product">
                <v-icon size="small">mdi-delete</v-icon>
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>

      <!-- Empty State -->
      <div v-if="productStore.products.length === 0" class="text-center pa-8 text-copper-muted">
        {{ t('noProductsAvailable') }}
      </div>
    </v-card>

    <!-- Create/Edit Dialog Modal -->
    <v-dialog v-model="dialog.show" max-width="650px" persistent>
      <v-card class="rounded-xl pa-4 bg-surface border-bronze">
        <v-card-title class="text-h5 font-weight-black text-bronze-gradient">
          {{ dialog.isEdit ? t('editProduct') : t('addProduct') }}
        </v-card-title>
        
        <v-card-text>
          <v-form ref="form" v-model="dialog.valid">
            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="dialog.name"
                  :label="t('productNameAr')"
                  required
                  :rules="[(v) => !!v || t('nameRequired')]"
                  variant="outlined"
                  class="mb-1"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="dialog.nameEn"
                  :label="t('productNameEn')"
                  variant="outlined"
                  class="mb-1"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-select
              v-model="dialog.categoryId"
              :items="productStore.categories"
              item-title="name"
              item-value="id"
              :label="t('category')"
              required
              :rules="[(v) => !!v || t('categoryRequired')]"
              variant="outlined"
              class="mb-3"
            ></v-select>

            <!-- Pizza Variants Price inputs -->
            <v-row v-if="isPizzaCategory">
              <v-col cols="6">
                <v-text-field
                  v-model.number="dialog.priceS"
                  :label="`${t('price')} S (EGP)`"
                  type="number"
                  variant="outlined"
                  class="mb-3"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="dialog.priceL"
                  :label="`${t('price')} L (EGP)`"
                  type="number"
                  variant="outlined"
                  class="mb-3"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model.number="dialog.price"
                  :label="`${t('price')} (EGP)`"
                  type="number"
                  required
                  :rules="[!isPizzaCategory ? (v => v > 0 || t('pricePositive')) : () => true]"
                  variant="outlined"
                  class="mb-3"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="dialog.stock"
                  :label="t('stock')"
                  type="number"
                  required
                  :rules="[(v) => v >= 0 || t('stockPositive')]"
                  variant="outlined"
                  class="mb-3"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" sm="6">
                <v-textarea
                  v-model="dialog.description"
                  :label="t('descriptionAr')"
                  variant="outlined"
                  rows="2"
                  class="mb-1"
                ></v-textarea>
              </v-col>
              <v-col cols="12" sm="6">
                <v-textarea
                  v-model="dialog.descriptionEn"
                  :label="t('descriptionEn')"
                  variant="outlined"
                  rows="2"
                  class="mb-1"
                ></v-textarea>
              </v-col>
            </v-row>

            <!-- Reusable Modular FileUploader -->
            <FileUploader
              v-model="dialog.imageFile"
              :initial-image-url="imagePreviewUrl"
              @remove-initial="removeImage"
            />
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" color="secondary" @click="closeDialog">{{ t('cancel') }}</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            class="px-6 font-weight-bold"
            :disabled="!dialog.valid"
            :loading="saving"
            @click="saveProduct"
          >
            {{ t('save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProductStore } from '../../stores/products'
import type { Product } from '../../types'
import { useAdminStore } from '../../stores/admin'
import { useLocaleStore } from '../../stores/locale'
import { resolveImageUrl } from '../../utils/image'
import FileUploader from '../../components/FileUploader.vue'

const productStore = useProductStore()
const adminStore = useAdminStore()
const { t } = useLocaleStore()

const saving = ref(false)
const imagePreviewUrl = ref<string | null>(null)
const searchQuery = ref('')
let searchTimeout: number | null = null

const dialog = ref({
  show: false,
  isEdit: false,
  valid: false,
  id: 0,
  name: '',
  nameEn: '',
  categoryId: null as number | null,
  price: 0,
  stock: 0,
  description: '',
  descriptionEn: '',
  priceS: '' as number | string,
  priceL: '' as number | string,
  imageFile: null as File | null,
  removeImageFlag: false,
})

const isPizzaCategory = computed(() => {
  const cat = productStore.categories.find(c => c.id === dialog.value.categoryId)
  return cat ? cat.name.toLowerCase() === 'pizza' || cat.name === 'البيتزا' : false
})

// Debounced search function (500ms delay)
const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = window.setTimeout(async () => {
    await performSearch()
  }, 500)
}

const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    // If search is empty, load all products
    productStore.fetchProducts({ page: 1, size: 100 })
  } else {
    // Perform server-side search with the query
    productStore.fetchProducts({ 
      page: 1, 
      size: 100,
      search: searchQuery.value 
    })
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  if (searchTimeout) clearTimeout(searchTimeout)
  productStore.fetchProducts({ page: 1, size: 100 })
}

const loadData = () => {
  productStore.fetchProducts({ page: 1, size: 100 })
  productStore.fetchCategories()
}

onMounted(() => {
  loadData()
})

const getCategoryName = (id: number) => {
  const cat = productStore.categories.find((c) => c.id == id)
  return cat ? cat.name : 'Unknown'
}

const openCreateDialog = () => {
  dialog.value = {
    show: true,
    isEdit: false,
    valid: false,
    id: 0,
    name: '',
    nameEn: '',
    categoryId: null,
    price: 0,
    stock: 0,
    description: '',
    descriptionEn: '',
    priceS: '',
    priceL: '',
    imageFile: null,
    removeImageFlag: false,
  }
  imagePreviewUrl.value = null
}

const openEditDialog = (product: Product) => {
  const variantS = product.variants?.find(v => v.name === 'S')
  const variantL = product.variants?.find(v => v.name === 'L')

  dialog.value = {
    show: true,
    isEdit: true,
    valid: true,
    id: product.id,
    name: product.name,
    nameEn: product.name_en || '',
    categoryId: product.category_id,
    price: product.price,
    stock: product.stock,
    description: product.description || '',
    descriptionEn: product.description_en || '',
    priceS: variantS ? variantS.price : '',
    priceL: variantL ? variantL.price : '',
    imageFile: null,
    removeImageFlag: false,
  }
  imagePreviewUrl.value = product.image_path ? resolveImageUrl(product.image_path) : null
}

const closeDialog = () => {
  dialog.value.show = false
  imagePreviewUrl.value = null
}

const removeImage = () => {
  dialog.value.imageFile = null
  imagePreviewUrl.value = null
  dialog.value.removeImageFlag = true
}

const saveProduct = async () => {
  if (!dialog.value.valid) return
  saving.value = true
  
  const formData = new FormData()
  formData.append('name', dialog.value.name)
  if (dialog.value.nameEn) formData.append('name_en', dialog.value.nameEn)
  formData.append('category_id', String(dialog.value.categoryId))
  formData.append('price', String(dialog.value.price))
  formData.append('stock', String(dialog.value.stock))
  if (dialog.value.description) formData.append('description', dialog.value.description)
  if (dialog.value.descriptionEn) formData.append('description_en', dialog.value.descriptionEn)
  formData.append('remove_image', String(dialog.value.removeImageFlag))

  if (isPizzaCategory.value) {
    if (dialog.value.priceS) formData.append('price_s', String(dialog.value.priceS))
    if (dialog.value.priceL) formData.append('price_l', String(dialog.value.priceL))
  }
  
  if (dialog.value.imageFile) {
    formData.append('image', dialog.value.imageFile)
  }

  try {
    if (dialog.value.isEdit) {
      await adminStore.updateProduct(dialog.value.id, formData)
    } else {
      await adminStore.createProduct(formData)
    }
    closeDialog()
    loadData()
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Failed to save product.')
  } finally {
    saving.value = false
  }
}

const deleteProduct = async (id: number) => {
  if (confirm('Are you sure you want to delete this product?')) {
    try {
      await adminStore.deleteProduct(id)
      loadData()
    } catch (error) {
      alert('Failed to delete product.')
    }
  }
}
</script>
