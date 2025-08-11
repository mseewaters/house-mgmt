<template>
  <div class="container" :class="containerClasses">
    <!-- Three-State Weather Sidebar -->
    <WeatherSidebar 
      :state="weatherState"
      @toggle-state="toggleWeatherState"
    />
    
    <!-- Main Content Area -->
    <div class="main-content" :class="contentClasses">
      <!-- Tab Navigation -->
      <TabNavigation />
      
      <!-- Dynamic Content Area -->
      <div class="content-area">
        <component :is="currentTabComponent" />
      </div>
    </div>
  </div>
</template>

<script setup>

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useHouseStore } from '../stores/house.js'
import WeatherSidebar from '../components/WeatherSidebar.vue'
import TabNavigation from '../components/TabNavigation.vue'

// Import tab components
import FocusView from '../components/FocusView.vue'
import DailyTasksView from '../components/DailyTasksView.vue'
import MealsView from '../components/MealsView.vue'
import AdminView from '../components/AdminView.vue'

// Store
const store = useHouseStore()

// Weather sidebar state management
const weatherState = ref('default') // 'collapsed', 'default', 'expanded'

// Auto-collapse timer (return to default after inactivity)
let autoCollapseTimer = null
const AUTO_COLLAPSE_DELAY = 300000 // 5 minutes

// Tab component mapping
const tabComponents = {
  focus: FocusView,
  daily: DailyTasksView,
  meals: MealsView,
  admin: AdminView
}

// Computed properties
const currentTabComponent = computed(() => {
  return tabComponents[store.activeTab] || FocusView
})

const containerClasses = computed(() => ({
  'weather-collapsed': weatherState.value === 'collapsed',
  'weather-default': weatherState.value === 'default',
  'weather-expanded': weatherState.value === 'expanded'
}))

const contentClasses = computed(() => ({
  'content-collapsed': weatherState.value === 'expanded',
  'content-default': weatherState.value === 'default',
  'content-full': weatherState.value === 'collapsed'
}))

// Methods
function toggleWeatherState() {
  // Cycle through states: default → expanded → collapsed → default
  const states = ['default', 'expanded', 'collapsed']
  const currentIndex = states.indexOf(weatherState.value)
  const nextIndex = (currentIndex + 1) % states.length
  weatherState.value = states[nextIndex]
  
  console.log(`🌤️ Weather state: ${weatherState.value}`)
  
  // Reset auto-collapse timer
  resetAutoCollapseTimer()
}

function resetAutoCollapseTimer() {
  if (autoCollapseTimer) {
    clearTimeout(autoCollapseTimer)
  }
  
  // Only auto-collapse if not in default state
  if (weatherState.value !== 'default') {
    autoCollapseTimer = setTimeout(() => {
      weatherState.value = 'default'
      console.log('🕐 Auto-returned to default weather state')
    }, AUTO_COLLAPSE_DELAY)
  }
}

// Lifecycle
onMounted(async () => {
  console.log('🏠 HomePage mounted - initializing data...')
  
  // Initialize store data
  await store.initializeData()
  
  // Start time updates
  const timeInterval = setInterval(() => {
    store.updateDateTime()
  }, 60000) // Update every minute
  
  // Store cleanup function
  onUnmounted(() => {
    clearInterval(timeInterval)
    if (autoCollapseTimer) {
      clearTimeout(autoCollapseTimer)
    }
  })
  
  console.log('✅ HomePage ready!')
})
</script>

<style scoped>
/* Container Layout */
.container {
  display: flex;
  width: var(--container-width);
  height: var(--container-height);
  margin: 20px auto;
  background: var(--bg-container);
  box-shadow: 0 0 20px rgba(0,0,0,0.1);
  font-family: var(--font-family-primary);
  transition: var(--transition-normal);
  overflow: hidden;
}

/* Weather State Classes */
.container.weather-collapsed {
  /* Weather sidebar is collapsed */
}

.container.weather-default {
  /* Weather sidebar is normal size */
}

.container.weather-expanded {
  /* Weather sidebar is expanded */
}

/* Main Content Area */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  transition: var(--transition-normal);
  min-width: 0; /* Allows flex child to shrink */
}

/* Content Area States */
.main-content.content-full {
  /* Weather collapsed - full content width */
  margin-left: 0;
}

.main-content.content-default {
  /* Default weather sidebar */
  /* Default flex behavior */
}

.main-content.content-collapsed {
  /* Weather expanded - reduced content width */
  /* Content gets less space */
}

/* Content Area */
.content-area {
  flex: 1;
  padding: 20px;
  overflow: hidden;
  background: var(--bg-content);
  display: flex;
  flex-direction: column;
}

/* Responsive adjustments */
@media (max-width: 1280px) {
  .container {
    width: 100vw;
    height: 100vh;
    margin: 0;
  }
}

/* Debug helpers (remove in production) */
.container::before {
  content: attr(class);
  position: absolute;
  top: 5px;
  right: 5px;
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  z-index: 1000;
  pointer-events: none;
}
</style>