<template>
  <v-container class="pa-0">
    <div class="d-flex align-center justify-space-between mb-6">
      <h1 class="text-h4 font-weight-bold">{{ t('manageCategories') }}</h1>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">{{ t('addCategory') }}</v-btn>
    </div>

    <!-- Categories Card List -->
    <v-card class="elevation-3 rounded-lg border">
      <v-table>
        <thead>
          <tr>
            <th class="font-weight-bold" style="width: 100px;">{{ t('idLabel') }}</th>
            <th class="font-weight-bold">{{ t('categoryNameAr') }}</th>
            <th class="font-weight-bold">{{ t('createdAt') }}</th>
            <th class="font-weight-bold text-center" style="width: 150px;">{{ t('actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cat in productStore.categories" :key="cat.id">
            <td class="font-weight-bold">#{{ cat.id }}</td>
            <td class="font-weight-bold">{{ cat.name }}</td>
            <td>{{ formatDate(cat.created_at) }}</td>
            <td class="text-center">
              <v-btn icon variant="text" color="primary" @click="openEditDialog(cat)" :aria-label="t('edit')">
                <v-icon size="small">mdi-pencil</v-icon>
              </v-btn>
              <v-btn icon variant="text" color="error" @click="deleteCategory(cat.id)" :aria-label="t('delete')">
                <v-icon size="small">mdi-delete</v-icon>
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>

      <!-- Empty State -->
      <div v-if="productStore.categories.length === 0" class="text-center pa-8 text-grey">
        {{ t('noCategoriesAdmin') }}
      </div>
    </v-card>

    <!-- Create/Edit Modal Dialog -->
    <v-dialog v-model="dialog.show" max-width="450px" persistent>
      <v-card class="rounded-lg pa-4">
        <v-card-title class="text-h5 font-weight-bold">
          {{ dialog.isEdit ? t('editCategory') : t('addCategory') }}
        </v-card-title>
        
        <v-card-text>
          <v-form ref="form" v-model="dialog.valid">
            <v-text-field
              v-model="dialog.name"
              :label="t('categoryNameAr')"
              required
              :rules="[(v) => !!v || t('nameRequiredErr')]"
              variant="outlined"
              class="mb-2"
              @keyup.enter="saveCategory"
            ></v-text-field>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" color="secondary" @click="dialog.show = false">{{ t('cancel') }}</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            class="px-6 font-weight-bold"
            :disabled="!dialog.valid"
            :loading="saving"
            @click="saveCategory"
          >
            {{ t('save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useProductStore } from '../../stores/products'
import type { Category } from '../../stores/products'
import { useAdminStore } from '../../stores/admin'
import { useLocaleStore } from '../../stores/locale'

const productStore = useProductStore()
const adminStore = useAdminStore()
const { t } = useLocaleStore()

const saving = ref(false)

const dialog = ref({
  show: false,
  isEdit: false,
  valid: false,
  id: 0,
  name: '',
})

onMounted(() => {
  productStore.fetchCategories()
})

const formatDate = (dateStr: string) => {
  const d = new Date(dateStr)
  return d.toLocaleDateString()
}

const openCreateDialog = () => {
  dialog.value = {
    show: true,
    isEdit: false,
    valid: false,
    id: 0,
    name: '',
  }
}

const openEditDialog = (cat: Category) => {
  dialog.value = {
    show: true,
    isEdit: true,
    valid: true,
    id: cat.id,
    name: cat.name,
  }
}

const saveCategory = async () => {
  if (!dialog.value.valid) return
  saving.value = true
  try {
    if (dialog.value.isEdit) {
      await adminStore.updateCategory(dialog.value.id, dialog.value.name)
    } else {
      await adminStore.createCategory(dialog.value.name)
    }
    dialog.value.show = false
    productStore.fetchCategories()
  } catch (error: any) {
    alert(error.response?.data?.detail || t('failOrder'))
  } finally {
    saving.value = false
  }
}

const deleteCategory = async (id: number) => {
  if (confirm(t('confirmDeleteCategory'))) {
    try {
      await adminStore.deleteCategory(id)
      productStore.fetchCategories()
    } catch (error) {
      alert(t('failOrder'))
    }
  }
}
</script>
