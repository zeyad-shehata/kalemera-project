<template>
  <v-container class="fill-height py-6 py-sm-12 px-3 px-sm-6" fluid>
    <v-row align="center" justify="center" class="ma-0 w-100">
      <v-col cols="12" sm="8" md="5" lg="4" class="pa-0 pa-sm-3">
        <v-card class="elevation-16 rounded-xl pa-4 pa-sm-6 bg-surface border-bronze mx-auto" max-width="460">
          <v-card-item class="text-center">
            <v-img src="/logo.webp" alt="Calmera Logo" max-width="120" class="mx-auto mb-3 logo-badge-img" contain></v-img>
            <v-card-title class="text-h4 font-weight-black text-bronze-gradient mb-1">{{ t('login') }}</v-card-title>
            <v-card-subtitle class="text-copper-muted">{{ t('welcomeBackSubtitle') }}</v-card-subtitle>
          </v-card-item>

          <v-card-text class="mt-4">
            <v-form ref="form" v-model="valid" @submit.prevent="handleLogin">
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
                color="primary"
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
                color="primary"
              ></v-text-field>

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
                {{ t('login') }}
              </v-btn>
            </v-form>
          </v-card-text>

          <v-card-actions class="justify-center mt-2">
            <span class="text-copper-muted mr-1">{{ t('dontHaveAccount') }}</span>
            <router-link to="/register" class="text-primary font-weight-bold text-decoration-none">{{ t('createAccount') }}</router-link>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useLocaleStore } from '../stores/locale'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { t, currentLocale } = useLocaleStore()

const valid = ref(false)
const phone = ref('')
const password = ref('')
const errorMessage = ref('')

const phoneRules = [
  (v: string) => !!v || t('phoneNumber') + (currentLocale === 'ar' ? ' مطلوب' : ' is required'),
  (v: string) => /^01[0-9]{9}$/.test(v || '') || (currentLocale === 'ar' ? 'رقم هاتف مصري مكون من 11 رقم' : 'Must be 11-digit Egyptian number starting with 01'),
]

const passwordRules = [
  (v: string) => !!v || t('passwordRequired'),
]

const handleLogin = async () => {
  if (!valid.value) return
  
  errorMessage.value = ''
  try {
    const user = await authStore.login({ phone: phone.value, password: password.value })
    const redirectUrl = (route.query.redirect as string) || (user.role === 'ADMIN' ? '/admin' : '/')
    router.push(redirectUrl)
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
      errorMessage.value = t('loginFail')
    }
  }
}
</script>
