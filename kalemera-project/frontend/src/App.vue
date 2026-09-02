<template>
  <v-app :key="localeStore.currentLocale" class="kalmera-app">
    <!-- AppBar -->
    <v-app-bar app color="surface" elevation="4" class="px-2 border-b-bronze">
      <!-- Back Navigation (history-aware) -->
      <v-btn
        v-if="canGoBack"
        icon
        color="primary"
        size="small"
        :aria-label="localeStore.t('back')"
        class="mr-1"
        @click="goBack"
      >
        <v-icon size="small">
          {{ localeStore.currentLocale === 'ar' ? 'mdi-arrow-right' : 'mdi-arrow-left' }}
        </v-icon>
      </v-btn>

      <!-- Nav Drawer Toggle (Only Customer view/Admin view sidebar) -->
      <v-app-bar-nav-icon aria-label="Toggle Navigation Drawer" @click="drawer = !drawer" color="primary"></v-app-bar-nav-icon>
      
      <!-- Brand Logo & Title -->
      <router-link to="/" class="d-flex align-center text-decoration-none mr-2">
        <v-avatar size="44" :class="localeStore.currentLocale === 'ar' ? 'ml-3' : 'mr-3'" class="logo-avatar">
          <v-img src="/logo.jpg" alt="Kalmera Logo" cover></v-img>
        </v-avatar>
        <div class="d-flex flex-column">
          <span class="font-weight-black text-h6 text-bronze-gradient line-height-tight">{{ localeStore.t('title') }}</span>
          <span class="text-caption text-copper-muted line-height-tight">{{ localeStore.t('subtitle') }}</span>
        </div>
      </router-link>

      <v-spacer></v-spacer>

      <!-- Quick Category Chips for restaurant / market (Desktop Only) -->
      <div class="hidden-sm-and-down mr-4 d-flex align-center ga-2">
        <v-chip color="primary" variant="outlined" size="small" prepend-icon="mdi-silverware-fork-knife" to="/">
          {{ localeStore.t('restaurant') }}
        </v-chip>
        <v-chip color="secondary" variant="outlined" size="small" prepend-icon="mdi-basket-outline" to="/">
          {{ localeStore.t('market') }}
        </v-chip>
      </div>

      <!-- Action Group: Language, Theme, Cart, Notifications -->
      <div class="d-flex align-center ga-1 ga-sm-2">
        <!-- Language Switcher (Text on medium+, icon only on small) -->
        <v-btn variant="text" color="primary" class="font-weight-black px-1 px-sm-2 text-subtitle-2 rounded-lg hidden-xs" @click="toggleLanguage">
          🌐 {{ localeStore.currentLocale === 'ar' ? 'EN' : 'عربي' }}
        </v-btn>
        <v-btn icon size="small" color="primary" class="d-none d-xs-flex" @click="toggleLanguage" aria-label="Toggle Language">
          <v-icon>mdi-translate</v-icon>
        </v-btn>

        <!-- Theme Switcher -->
        <v-btn icon color="primary" size="small" @click="toggleTheme" aria-label="Toggle Theme">
          <v-icon size="small">
            {{ theme.global.name.value === 'kalmeraDark' ? 'mdi-white-balance-sunny' : 'mdi-weather-night' }}
          </v-icon>
        </v-btn>

        <!-- Cart Button -->
        <v-btn icon to="/cart" aria-label="View Cart" color="primary" size="small">
          <v-badge :content="cartStore.itemCount" :value="cartStore.itemCount" color="secondary">
            <v-icon size="small">mdi-cart</v-icon>
          </v-badge>
        </v-btn>

        <!-- Notifications Icon -->
        <v-menu v-if="authStore.isAuthenticated" offset-y transition="scale-transition">
          <template v-slot:activator="{ props }">
            <v-btn icon v-bind="props" aria-label="View Notifications" color="primary" size="small">
              <v-badge :content="notificationStore.notifications.length" :value="notificationStore.notifications.length" color="secondary">
                <v-icon size="small">mdi-bell</v-icon>
              </v-badge>
            </v-btn>
          </template>
          <v-list width="320" max-height="400" class="overflow-y-auto bg-surface border-bronze">
            <v-list-item v-if="notificationStore.notifications.length === 0">
              <v-list-item-title class="text-center text-grey">{{ localeStore.t('noNotifications') }}</v-list-item-title>
            </v-list-item>
            <v-list-item
              v-for="notif in notificationStore.notifications"
              :key="notif.id"
              @click="markRead(notif.id)"
              lines="two"
              class="border-bottom"
            >
              <template v-slot:prepend>
                <v-icon color="secondary">mdi-fire</v-icon>
              </template>
              <v-list-item-title class="text-wrap font-weight-medium" style="font-size: 0.9rem;">
                {{ notif.message }}
              </v-list-item-title>
              <v-list-item-subtitle class="text-copper-muted" style="font-size: 0.8rem;">
                {{ localeStore.t('dismissNotification') }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-menu>

        <!-- Auth Actions (Admin Console, Welcome, Logout) -->
        <template v-if="authStore.isAuthenticated">
          <v-btn v-if="authStore.isAdmin" color="secondary" variant="flat" to="/admin" class="hidden-sm-and-down mr-2 rounded-pill font-weight-bold">
            <v-icon start>mdi-shield-crown</v-icon>
            {{ localeStore.t('adminConsoleBtn') }}
          </v-btn>
          
          <span class="hidden-md-and-down text-primary font-weight-medium text-caption max-width-120 text-truncate">
            {{ localeStore.t('welcome', { name: authStore.currentUser?.full_name }) }}
          </span>

          <v-btn icon @click="logout" aria-label="Log Out" color="error" size="small">
            <v-icon size="small">mdi-logout</v-icon>
          </v-btn>
        </template>
        <template v-else>
          <v-btn variant="outlined" color="primary" size="small" class="hidden-xs rounded-lg" to="/login">{{ localeStore.t('login') }}</v-btn>
          <v-btn variant="flat" color="secondary" size="small" class="hidden-xs rounded-lg" to="/register">{{ localeStore.t('register') }}</v-btn>
        </template>
      </div>
    </v-app-bar>

    <!-- Navigation Drawer -->
    <v-navigation-drawer v-model="drawer" temporary class="bg-surface border-r-bronze" :location="localeStore.currentLocale === 'ar' ? 'right' : 'left'">
      <!-- Drawer Header with Logo -->
      <div class="pa-4 text-center border-b-bronze bg-surface-variant">
        <v-img src="/logo.jpg" alt="Logo" max-height="110" class="mx-auto mb-2 logo-badge-img" contain></v-img>
        <div class="text-h6 font-weight-black text-bronze-gradient">{{ localeStore.t('title') }}</div>
        <div class="text-caption text-copper-muted">{{ localeStore.t('subtitle') }}</div>
      </div>

      <v-list class="pa-2">
        <v-list-item to="/" prepend-icon="mdi-home" :title="localeStore.t('home')" value="home" color="primary"></v-list-item>
        
        <v-list-item to="/cart" prepend-icon="mdi-cart" :title="localeStore.t('cart')" value="cart" color="primary">
          <template v-slot:append>
            <v-chip v-if="cartStore.itemCount > 0" size="x-small" color="secondary">
              {{ cartStore.itemCount }}
            </v-chip>
          </template>
        </v-list-item>

        <!-- Authenticated Routes -->
        <template v-if="authStore.isAuthenticated">
          <v-list-item to="/orders" prepend-icon="mdi-history" :title="localeStore.t('myOrders')" value="orders" color="primary"></v-list-item>
        </template>

        <!-- Mobile Auth buttons when logged out -->
        <template v-if="!authStore.isAuthenticated">
          <v-list-item to="/login" prepend-icon="mdi-login" :title="localeStore.t('login')" value="login" color="primary" class="hidden-sm-and-up"></v-list-item>
          <v-list-item to="/register" prepend-icon="mdi-account-plus" :title="localeStore.t('register')" value="register" color="primary" class="hidden-sm-and-up"></v-list-item>
        </template>

        <!-- Admin Routes -->
        <template v-if="authStore.isAuthenticated && authStore.isAdmin">
          <v-divider class="my-3 border-bronze"></v-divider>
          <v-list-subheader class="text-secondary font-weight-bold">{{ localeStore.t('adminConsole') }}</v-list-subheader>
          
          <!-- Admin Console mobile redirect -->
          <v-list-item to="/admin" prepend-icon="mdi-shield-crown" :title="localeStore.t('adminConsoleBtn')" value="admin-console-mob" color="primary" class="hidden-md-and-up"></v-list-item>
          
          <v-list-item to="/admin" prepend-icon="mdi-view-dashboard" :title="localeStore.t('dashboard')" value="admin-dash" color="primary"></v-list-item>
          <v-list-item to="/admin/products" prepend-icon="mdi-package-variant-closed" :title="localeStore.t('manageProducts')" value="admin-prod" color="primary"></v-list-item>
          <v-list-item to="/admin/categories" prepend-icon="mdi-shape" :title="localeStore.t('manageCategories')" value="admin-cat" color="primary"></v-list-item>
          <v-list-item to="/admin/reports" prepend-icon="mdi-chart-line" :title="localeStore.t('reportsTitle')" value="admin-rep" color="primary"></v-list-item>
        </template>
      </v-list>
    </v-navigation-drawer>

    <!-- Main Content -->
    <v-main class="bg-background">
      <router-view></router-view>
    </v-main>

    <!-- Notification Snackbar -->
    <v-snackbar
      v-model="snackbar.show"
      :timeout="5000"
      color="secondary"
      :location="localeStore.currentLocale === 'ar' ? 'top left' : 'top right'"
      elevation="8"
      class="border-bronze"
    >
      <div class="d-flex align-center">
        <v-icon start color="white">mdi-bell-ring</v-icon>
        <span class="font-weight-bold text-break-word">{{ snackbar.message }}</span>
      </div>
      <template v-slot:actions>
        <v-btn color="white" variant="text" @click="snackbar.show = false">{{ localeStore.t('close') }}</v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useCartStore } from './stores/cart'
import { useNotificationStore } from './stores/notifications'
import { useLocaleStore } from './stores/locale'
import { useTheme, useLocale } from 'vuetify'
import { resolveBackTarget } from './utils/navigation'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const cartStore = useCartStore()
const notificationStore = useNotificationStore()
const localeStore = useLocaleStore()
const theme = useTheme()
const { current: vuetifyLocale } = useLocale()

const drawer = ref(false)

const snackbar = ref({
  show: false,
  message: ''
})

// History-aware back navigation: returns to the actual previous route entry.
// Falls back to Home only when there is no valid browser/router history.
const canGoBack = computed(() => route.path !== '/')

const goBack = () => {
  const target = resolveBackTarget(router.options.history.state)
  if (target) {
    router.back()
  } else {
    // No valid previous history entry — safe fallback to Home.
    router.push('/')
  }
}

const toggleLanguage = () => {
  const target = localeStore.currentLocale === 'ar' ? 'en' : 'ar'
  localeStore.setLocale(target)
  vuetifyLocale.value = target
}

const toggleTheme = () => {
  const targetTheme = theme.global.name.value === 'kalmeraDark' ? 'kalmeraLight' : 'kalmeraDark'
  theme.global.name.value = targetTheme
  localStorage.setItem('theme', targetTheme)
}

// Watch auth state to trigger/stop notifications polling
watch(
  () => authStore.isAuthenticated,
  (isAuth) => {
    if (isAuth) {
      notificationStore.startPolling(10000)
    } else {
      notificationStore.stopPolling()
      notificationStore.notifications = []
    }
  },
  { immediate: true }
)

// Watch for incoming new notifications to trigger snackbar
watch(
  () => notificationStore.notifications,
  (newNotifs, oldNotifs) => {
    if (newNotifs.length > (oldNotifs?.length || 0)) {
      const latest = newNotifs[0]
      if (latest) {
        snackbar.value.message = latest.message
        snackbar.value.show = true
        notificationStore.markAsRead(latest.id)
      }
    }
  },
  { deep: true }
)

// Watch for cart additions to show success snackbar
watch(
  () => cartStore.justAdded,
  (added) => {
    if (added) {
      snackbar.value.message = localeStore.t('cartAddedSuccess')
      snackbar.value.show = true
      cartStore.clearJustAdded()
    }
  }
)

onMounted(() => {
  cartStore.loadCart()

  // Restore theme from localStorage
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme && (savedTheme === 'kalmeraDark' || savedTheme === 'kalmeraLight')) {
    theme.global.name.value = savedTheme
  }
})

onUnmounted(() => {
  notificationStore.stopPolling()
})

const markRead = async (id: number) => {
  await notificationStore.markAsRead(id)
}

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>

<style>
/* CSS global resets, themes, and Kalmera branding */
body {
  margin: 0;
  font-family: 'Cairo', 'Tajawal', 'Outfit', sans-serif;
  background-color: #0F0E0D;
  color: #F7F3ED;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.kalmera-app {
  font-family: 'Cairo', 'Tajawal', 'Outfit', sans-serif !important;
}

.text-bronze-gradient {
  background: linear-gradient(135deg, #F3D19E 0%, #D49B54 50%, #A86D2C 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: inline-block;
}

.text-copper-muted {
  color: #BFA893 !important;
}

.border-b-bronze {
  border-bottom: 1px solid rgba(212, 155, 84, 0.25) !important;
}

.border-r-bronze {
  border-right: 1px solid rgba(212, 155, 84, 0.25) !important;
}

.border-bronze {
  border: 1px solid rgba(212, 155, 84, 0.3) !important;
}

.logo-avatar {
  border: 2px solid #D49B54;
  box-shadow: 0 0 10px rgba(212, 155, 84, 0.4);
}

.logo-badge-img {
  filter: drop-shadow(0 4px 12px rgba(212, 155, 84, 0.3));
  border-radius: 12px;
}

.line-height-tight {
  line-height: 1.2;
}

.border-bottom {
  border-bottom: 1px solid rgba(212, 155, 84, 0.15);
}
</style>
