<template>
  <v-card class="elevation-3 rounded-lg border pa-4 mb-6 bg-surface">
    <div class="d-flex align-center justify-space-between mb-3">
      <div class="d-flex align-center">
        <v-avatar color="primary" variant="tonal" size="42" class="mr-3 ml-1">
          <v-icon color="primary" size="24">mdi-server-security</v-icon>
        </v-avatar>
        <div>
          <h3 class="text-subtitle-1 font-weight-bold">{{ t('storageOverviewTitle') }}</h3>
          <p class="text-caption text-grey mb-0">{{ t('storageOverviewSubtitle') }}</p>
        </div>
      </div>

      <div class="d-flex ga-2">
        <v-btn
          color="primary"
          variant="tonal"
          size="small"
          prepend-icon="mdi-database-arrow-down"
          :loading="backupLoading"
          @click="handleBackup"
        >
          {{ t('backupNow') }}
        </v-btn>
        <v-btn
          color="secondary"
          variant="outlined"
          size="small"
          prepend-icon="mdi-broom"
          :loading="cleanLoading"
          @click="handleCleanOrphans"
        >
          {{ t('cleanMedia') }}
        </v-btn>
      </div>
    </div>

    <!-- Progress bar against 5GB limit -->
    <div class="mb-4" v-if="adminStore.storage">
      <div class="d-flex justify-space-between text-caption font-weight-bold mb-1">
        <span>{{ t('hostingUsage') }}: {{ adminStore.storage.total_app_mb }} MB / {{ adminStore.storage.hosting_limit_gb }} GB</span>
        <span :class="adminStore.storage.usage_percent > 80 ? 'text-error' : 'text-primary'">
          {{ adminStore.storage.usage_percent }}%
        </span>
      </div>
      <v-progress-linear
        :model-value="adminStore.storage.usage_percent"
        :color="adminStore.storage.usage_percent > 80 ? 'error' : 'primary'"
        height="10"
        rounded
      ></v-progress-linear>
    </div>

    <!-- Breakdown Grid -->
    <v-row dense v-if="adminStore.storage">
      <v-col cols="6" sm="3">
        <div class="pa-2 bg-surface-variant rounded border text-center">
          <span class="text-caption text-grey">{{ t('productImages') }}</span>
          <div class="text-subtitle-2 font-weight-bold text-primary">{{ adminStore.storage.images_mb }} MB</div>
        </div>
      </v-col>
      <v-col cols="6" sm="3">
        <div class="pa-2 bg-surface-variant rounded border text-center">
          <span class="text-caption text-grey">{{ t('databaseSize') }}</span>
          <div class="text-subtitle-2 font-weight-bold text-secondary">{{ adminStore.storage.database_mb }} MB</div>
        </div>
      </v-col>
      <v-col cols="6" sm="3">
        <div class="pa-2 bg-surface-variant rounded border text-center">
          <span class="text-caption text-grey">{{ t('backupsSize') }}</span>
          <div class="text-subtitle-2 font-weight-bold text-accent">{{ adminStore.storage.backups_mb }} MB</div>
        </div>
      </v-col>
      <v-col cols="6" sm="3">
        <div class="pa-2 bg-surface-variant rounded border text-center">
          <span class="text-caption text-grey">{{ t('freeDiskSpace') }}</span>
          <div class="text-subtitle-2 font-weight-bold text-success">{{ adminStore.storage.disk_free_gb }} GB</div>
        </div>
      </v-col>
    </v-row>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminStore } from '../stores/admin'
import { useLocaleStore } from '../stores/locale'

const adminStore = useAdminStore()
const { t } = useLocaleStore()

const backupLoading = ref(false)
const cleanLoading = ref(false)

onMounted(() => {
  adminStore.fetchStorageOverview()
})

const handleBackup = async () => {
  backupLoading.value = true
  try {
    const res = await adminStore.triggerBackup()
    alert(t('backupSuccess', { filename: res.filename }))
  } catch (err) {
    alert(t('backupFail'))
  } finally {
    backupLoading.value = false
  }
}

const handleCleanOrphans = async () => {
  if (confirm(t('confirmCleanMedia'))) {
    cleanLoading.value = true
    try {
      const res = await adminStore.cleanOrphanImages()
      alert(t('cleanSuccess', { count: res.cleaned_files, mb: res.cleaned_mb }))
    } catch (err) {
      alert(t('cleanFail'))
    } finally {
      cleanLoading.value = false
    }
  }
}
</script>
