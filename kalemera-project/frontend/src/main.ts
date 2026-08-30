import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

const savedTheme = localStorage.getItem('theme') || 'kalmeraDark'
const savedLang = localStorage.getItem('lang') || 'ar'

const vuetify = createVuetify({
  components,
  directives,
  locale: {
    locale: savedLang,
    fallback: 'ar',
  },
  theme: {
    defaultTheme: savedTheme,
    themes: {
      kalmeraDark: {
        dark: true,
        colors: {
          primary: '#D49B54',      // Warm Metallic Bronze Gold
          secondary: '#D9531E',    // Flame Amber Orange
          accent: '#C5853B',       // Deep Copper
          background: '#0F0E0D',   // Deep Ebony Charcoal
          surface: '#1A1715',      // Dark Bronze Card Surface
          'surface-variant': '#26221D',
          error: '#E74C3C',
          info: '#3498DB',
          success: '#2ECC71',
          warning: '#F39C12',
          onPrimary: '#121110',
          onSecondary: '#FFFFFF',
          onBackground: '#F7F3ED',
          onSurface: '#F7F3ED',
        },
      },
      kalmeraLight: {
        dark: false,
        colors: {
          primary: '#A86D2C',      // Deep bronze gold for better contrast
          secondary: '#D9531E',    // Flame Amber Orange
          accent: '#C5853B',       // Deep copper
          background: '#FAF8F5',   // Very light warm cream
          surface: '#FFFFFF',      // White card surface
          'surface-variant': '#F4EFE6', // Warm cream container background
          error: '#E74C3C',
          info: '#3498DB',
          success: '#2ECC71',
          warning: '#F39C12',
          onPrimary: '#FFFFFF',
          onSecondary: '#FFFFFF',
          onBackground: '#1C1A17',  // Dark readable text
          onSurface: '#1C1A17',
        },
      },
    },
  },
})

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(vuetify)

// Expose vuetify globally so that locale changes apply dynamically
;(window as any).vuetify = vuetify

app.mount('#app')
