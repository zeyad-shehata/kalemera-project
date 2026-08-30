<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12 rounded-lg pa-6">
          <v-card-item class="text-center">
            <v-icon color="secondary" size="x-large" class="mb-2">mdi-account-plus-outline</v-icon>
            <v-card-title class="text-h5 font-weight-bold">{{ t('createAccount') }}</v-card-title>
            <v-card-subtitle>{{ t('joinToday') }}</v-card-subtitle>
          </v-card-item>

          <v-card-text>
            <v-form ref="form" v-model="valid" @submit.prevent="handleRegister">
              <v-text-field
                v-model="fullName"
                :label="t('fullName')"
                name="fullName"
                prepend-inner-icon="mdi-account"
                :rules="nameRules"
                required
                variant="outlined"
                class="mb-3"
              ></v-text-field>

              <v-text-field
                v-model="phone"
                :label="t('phoneNumber')"
                name="phone"
                prepend-inner-icon="mdi-phone"
                type="tel"
                :rules="phoneRules"
                required
                variant="outlined"
                class="mb-3"
              ></v-text-field>

              <v-text-field
                v-model="password"
                :label="t('password')"
                name="password"
                prepend-inner-icon="mdi-lock"
                type="password"
                :rules="passwordRules"
                required
                variant="outlined"
                class="mb-4"
              ></v-text-field>

              <v-alert v-if="successMessage" type="success" variant="tonal" class="mb-4">
                {{ successMessage }}
              </v-alert>

              <v-alert v-if="errorMessage" type="error" variant="tonal" class="mb-4" closable @click:close="errorMessage = ''">
                {{ errorMessage }}
              </v-alert>

              <v-btn
                :loading="authStore.loading"
                :disabled="!valid"
                type="submit"
                color="secondary"
                block
                size="large"
                class="rounded-lg font-weight-bold"
              >
                {{ t('register') }}
              </v-btn>
            </v-form>
          </v-card-text>

          <v-card-actions class="justify-center">
            <span class="text-grey-darken-1 mr-1">{{ t('alreadyHaveAccount') }}</span>
            <router-link to="/login" class="text-secondary font-weight-bold text-decoration-none">{{ t('login') }}</router-link>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useLocaleStore } from '../stores/locale'

const router = useRouter()
const authStore = useAuthStore()
const { t, currentLocale } = useLocaleStore()

const valid = ref(false)
const fullName = ref('')
const phone = ref('')
const password = ref('')
const errorMessage = ref('')
const successMessage = ref('')

const nameRules = [
  (v: string) => !!v || t('nameRequired'),
]

const phoneRules = [
  (v: string) => !!v || t('phoneNumber') + (currentLocale === 'ar' ? ' مطلوب' : ' is required'),
  (v: string) => /^01[0-9]{9}$/.test(v || '') || (currentLocale === 'ar' ? 'رقم هاتف مصري مكون من 11 رقم' : 'Must be 11-digit Egyptian number starting with 01'),
]

const passwordRules = [
  (v: string) => !!v || t('passwordRequired'),
  (v: string) => (v && v.length >= 6) || t('passwordMin'),
]

const handleRegister = async () => {
  if (!valid.value) return
  
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await authStore.register({
      phone: phone.value,
      password: password.value,
      full_name: fullName.value,
    })
    successMessage.value = t('regSuccess')
    setTimeout(() => {
      router.push('/')
    }, 800)
  } catch (error: any) {
    const detail = error.response?.data?.detail
    if (detail) {
      if (typeof detail === 'string') {
        errorMessage.value = detail
      } else if (Array.isArray(detail)) {
        errorMessage.value = detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
      } else {
        errorMessage.value = JSON.stringify(detail)
      }
    } else {
      errorMessage.value = t('regFail')
    }
  }
}
</script>
