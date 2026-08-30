<template>
  <div class="file-uploader-container">
    <label class="text-caption font-weight-bold mb-2 d-block text-grey">{{ label || t('productImage') }}</label>

    <!-- Hidden file input for camera (capture="environment") -->
    <input
      ref="cameraInput"
      type="file"
      accept="image/jpeg,image/png,image/webp,image/jpg"
      capture="environment"
      class="d-none"
      @change="onFileSelected"
    />

    <!-- Hidden file input for gallery/files -->
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png,image/webp,image/jpg"
      class="d-none"
      @change="onFileSelected"
    />

    <!-- Action Buttons -->
    <div class="d-flex ga-2 mb-3">
      <v-btn
        color="primary"
        variant="tonal"
        size="small"
        prepend-icon="mdi-camera"
        class="font-weight-bold"
        @click="triggerCamera"
      >
        {{ t('takePhoto') }}
      </v-btn>
      <v-btn
        color="secondary"
        variant="tonal"
        size="small"
        prepend-icon="mdi-image"
        class="font-weight-bold"
        @click="triggerFilePicker"
      >
        {{ t('chooseImage') }}
      </v-btn>
    </div>

    <!-- Preview Container -->
    <div v-if="previewUrl" class="position-relative border rounded-lg overflow-hidden bg-surface-variant mb-2" style="max-width: 320px;">
      <v-img :src="previewUrl" height="180" cover class="bg-surface"></v-img>
      
      <!-- Size / Format Badge -->
      <v-chip
        size="x-small"
        color="primary"
        variant="flat"
        class="position-absolute font-weight-bold"
        style="top: 8px; left: 8px; z-index: 2;"
        v-if="selectedFileSize"
      >
        {{ selectedFileSize }}
      </v-chip>

      <v-btn
        icon="mdi-close"
        size="x-small"
        color="error"
        variant="flat"
        class="position-absolute"
        style="top: 8px; right: 8px; z-index: 2;"
        @click="clearImage"
      ></v-btn>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useLocaleStore } from '../stores/locale'

const props = defineProps<{
  modelValue?: File | null
  initialImageUrl?: string | null
  label?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', file: File | null): void
  (e: 'remove-initial'): void
}>()

const { t } = useLocaleStore()

const cameraInput = ref<HTMLInputElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const previewUrl = ref<string | null>(props.initialImageUrl || null)
const selectedFileSize = ref<string | null>(null)

watch(() => props.initialImageUrl, (newVal) => {
  if (!props.modelValue && newVal) {
    previewUrl.value = newVal
    selectedFileSize.value = null
  }
})

const triggerCamera = () => {
  cameraInput.value?.click()
}

const triggerFilePicker = () => {
  fileInput.value?.click()
}

const onFileSelected = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  // Check file size (max 10MB)
  if (file.size > 10 * 1024 * 1024) {
    alert(t('fileTooLarge'))
    return
  }

  // Format file size
  if (file.size > 1024 * 1024) {
    selectedFileSize.value = `${(file.size / (1024 * 1024)).toFixed(1)} MB`
  } else {
    selectedFileSize.value = `${(file.size / 1024).toFixed(0)} KB`
  }

  previewUrl.value = URL.createObjectURL(file)
  emit('update:modelValue', file)
}

const clearImage = () => {
  previewUrl.value = null
  selectedFileSize.value = null
  emit('update:modelValue', null)
  emit('remove-initial')
}
</script>

<style scoped>
.file-uploader-container {
  width: 100%;
}
</style>
