<template>
  <v-container fluid class="pa-6">
    <v-row>
      <!-- Left sidebar menu for desktop -->
      <v-col cols="12" md="3" class="hidden-sm-and-down">
        <v-card class="elevation-8 rounded-xl py-4 bg-surface border-bronze">
          <div class="px-4 py-2 text-center">
            <v-img src="/logo.webp" alt="Calmera Logo" max-width="80" class="mx-auto mb-2 logo-badge-img" contain></v-img>
            <div class="text-h6 font-weight-black text-bronze-gradient">{{ t('adminConsole') }}</div>
            <div class="text-caption text-copper-muted">{{ t('adminConsoleBtn') }}</div>
          </div>
          
          <v-divider class="my-3 border-bronze"></v-divider>
          
          <v-list nav class="bg-transparent pa-2">
            <v-list-item to="/admin" exact prepend-icon="mdi-view-dashboard" :title="t('dashboard')" value="dashboard" color="primary"></v-list-item>
            <v-list-item to="/admin/products" prepend-icon="mdi-package-variant-closed" :title="t('manageProducts')" value="products" color="primary"></v-list-item>
            <v-list-item to="/admin/categories" prepend-icon="mdi-shape" :title="t('manageCategories')" value="categories" color="primary"></v-list-item>
            <v-list-item to="/admin/reports" prepend-icon="mdi-chart-line" :title="t('reportsTitle')" value="reports" color="primary"></v-list-item>
            <v-list-item to="/admin/reviews" prepend-icon="mdi-star-outline" :title="t('reviewsTitle')" value="reviews" color="primary"></v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <!-- Main Admin Content -->
      <v-col cols="12" md="9">
        <router-view></router-view>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useLocaleStore } from '../../stores/locale'
const { t } = useLocaleStore()
</script>
