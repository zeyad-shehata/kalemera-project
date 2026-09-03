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
import './style.css'

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
          primary: '#FF7A00',      // Vibrant Calmera Logo Orange
          secondary: '#2A2A2A',    // Deep Charcoal Noir
          accent: '#FFA726',       // Bright Warm Amber
          background: '#0F0F0F',   // Deep Charcoal Noir Background
          surface: '#1A1A1A',      // Dark Card Surface
          'surface-variant': '#262626',
          error: '#E74C3C',
          info: '#3498DB',
          success: '#2ECC71',
          warning: '#F39C12',
          onPrimary: '#FFFFFF',
          onSecondary: '#FFFFFF',
          onBackground: '#F7F3ED',
          onSurface: '#F7F3ED',
        },
      },
      kalmeraLight: {
        dark: false,
        colors: {
          primary: '#E65100',      // Deep Calmera Orange for high contrast
          secondary: '#212121',    // Dark Noir
          accent: '#FF7A00',       // Vibrant Orange Accent
          background: '#FAF8F5',   // Very light warm cream
          surface: '#FFFFFF',      // Pure White card surface
          'surface-variant': '#F5F0E8', // Warm cream container background
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
