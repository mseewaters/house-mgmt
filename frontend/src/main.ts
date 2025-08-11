// src/main.ts
// Minimal TypeScript - just what Vue needs

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

// Import our simple API service and store test
import './services/api.js'
import './stores/storeTest.js'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

if (import.meta.env.DEV) {
  console.log('🚀 House Management App - Development Mode')
  console.log('📡 API Base URL:', import.meta.env.VITE_API_BASE_URL || 'Default URL')
  console.log('🧪 Test API: window.apiTest.runAll()')
}