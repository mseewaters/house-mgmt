<template>
  <div class="container">
    <!-- Weather Sidebar (Left Zone) -->
    <WeatherSidebar />
    
    <!-- Main Content Area (Center + Right Zones) -->
    <div class="main-content">
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
import ActivitiesView from '../components/ActivitiesView.vue'
import MealsView from '../components/MealsView.vue'
import AdminView from '../components/AdminView.vue'

// Store
const store = useHouseStore()

// Tab component mapping - simplified
const tabComponents = {
  focus: ActivitiesView,      
  daily: ActivitiesView,      
  meals: MealsView,
  admin: AdminView
}

// Computed properties
const currentTabComponent = computed(() => {
  return tabComponents[store.activeTab] || ActivitiesView
})

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
  })
  
  console.log('✅ HomePage ready!')
})
</script>

<style scoped>
/* Container Layout - Clean Three Zone Structure */
.container {
  display: flex;
  width: var(--container-width);
  height: var(--container-height);
  margin: 20px auto;
  background: var(--bg-container);
  box-shadow: 0 0 20px rgba(0,0,0,0.1);
  font-family: var(--font-family-primary);
  overflow: hidden;
}

/* Main Content Area (Center + Right zones) */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0; /* Allows flex child to shrink */
}

/* Content Area - Where ActivitiesView renders */
.content-area {
  flex: 1;
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
</style>